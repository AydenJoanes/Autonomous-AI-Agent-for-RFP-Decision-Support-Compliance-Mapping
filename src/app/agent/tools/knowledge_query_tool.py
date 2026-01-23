from typing import List, Type, Optional
import json
from datetime import datetime
from loguru import logger
from pydantic import BaseModel, Field

from langchain.tools import BaseTool

from src.app.database.connection import SessionLocal
from src.app.database.repositories.project_repository import ProjectRepository
from src.app.models.compliance import ComplianceLevel, ToolResult

class KnowledgeQueryInput(BaseModel):
    requirement_text: str = Field(..., description="The requirement text to search for")
    requirement_embedding: List[float] = Field(..., description="The vector embedding of the requirement")

class KnowledgeQueryTool(BaseTool):
    name: str = "knowledge_query"
    description: str = "Searches past project portfolio for similar projects using semantic search. Input should be a requirement text with embedding."
    args_schema: Type[BaseModel] = KnowledgeQueryInput

    # Private attributes (excluded from Pydantic schema via private_attrs if needed, 
    # but BaseTool handles unannotated attributes okay usually. 
    # Better to initialize in _run or use PrivateAttr if strictly Pydantic v2)
    # For simplicity in this env, we'll initialize session in _run to ensure thread safety 
    # and avoiding deepcopy issues with SQLAlchemy sessions in LangChain.
    
    def _run(self, requirement_text: str, requirement_embedding: List[float]) -> str:
        logger.info(f"KnowledgeQueryTool: Searching for '{requirement_text[:50]}...'")
        
        session = SessionLocal()
        repository = ProjectRepository(session)
        
        # Initialize LLM client
        from src.app.utils.llm_client import LLMClient
        from src.app.services.llm_config import get_llm_config, LLM_AVAILABLE
        
        try:
            llm_client = LLMClient() if LLM_AVAILABLE else None
            llm_config = get_llm_config() if LLM_AVAILABLE else None
        except Exception as e:
            logger.warning(f"Failed to initialize LLM client (likely openai version mismatch): {e}")
            llm_client = None
            llm_config = None
        
        try:
            # Step 1: Search similar projects
            # Fetch slightly more to filter by threshold
            results = repository.search_similar(embedding=requirement_embedding, limit=10)
            if results:
                logger.info(f"Top result: {results[0].get('name')} (distance: {results[0].get('distance'):.4f})")
            else:
                logger.info("No results returned from repository.")
            
            # Step 1: Filter by similarity threshold
            # Use config threshold (similarity) -> convert to distance (1 - sim)
            # Default to 0.5 similarity (0.5 distance) if config missing
            sim_threshold = llm_config.relevance_threshold if llm_config else 0.5
            dist_threshold = 1.0 - sim_threshold
            
            similar_projects = []
            
            # Initial Search
            for p in results:
                distance = p.get('distance', 1.0)
                if distance <= dist_threshold:
                    similar_projects.append(p)
            
            logger.info(f"[TOOL] Knowledge Query: Found {len(similar_projects)} projects with sim >= {sim_threshold} (dist <= {dist_threshold})")
            
            # Fallback/Retry Logic: If no results, try looser threshold
            if not similar_projects and results:
                logger.info("[TOOL] No projects found with strict threshold. Attempting looser search...")
                # Reduce similarity req by 0.15 (e.g., 0.5 -> 0.35)
                fallback_sim = max(0.3, sim_threshold - 0.15)
                fallback_dist = 1.0 - fallback_sim
                
                for p in results:
                    distance = p.get('distance', 1.0)
                    if distance <= fallback_dist:
                        similar_projects.append(p)
                
                if similar_projects:
                    logger.info(f"[TOOL] Fallback Search: Found {len(similar_projects)} projects with sim >= {fallback_sim:.2f}")
                else:
                    logger.info(f"[TOOL] Fallback Search: No results even with sim >= {fallback_sim:.2f}")
            
            # Step 2: LLM Relevance Assessment (if enabled)
            relevant_projects = []
            if LLM_AVAILABLE and llm_config and llm_config.enable_llm_relevance and similar_projects:
                try:
                    logger.info("[TOOL] Enhancing similarity results with LLM relevance check")
                    relevant_projects = self._check_relevance_with_llm(
                        llm_client, 
                        llm_config, 
                        requirement_text, 
                        similar_projects
                    )
                except Exception as e:
                    logger.warning(f"[TOOL] LLM relevance check failed: {e}. Falling back to vector match.")
                    relevant_projects = similar_projects
            else:
                relevant_projects = similar_projects

            # Step 3: Determine compliance and confidence
            similar_count = len(relevant_projects)
            successful_projects = [
                p for p in relevant_projects 
                if p.get('outcome', '').lower() in ['success', 'partial success']
            ]
            success_count = len(successful_projects)
            
            compliance_level = ComplianceLevel.UNKNOWN
            confidence = 0.3
            details = {
                "similar_count": similar_count,
                "success_count": success_count,
                "project_names": [p.get('name') for p in relevant_projects],
                "matches": []
            }

            # Populate match details
            for p in relevant_projects:
                details['matches'].append({
                    "name": p.get('name'),
                    "outcome": p.get('outcome'),
                    "similarity": 1.0 - p.get('distance', 1.0),
                    "relevance_reason": p.get('relevance_reason', 'Vector similarity match')
                })

            # Logic
            if success_count >= 3:
                compliance_level = ComplianceLevel.COMPLIANT
                # Avg similarity of successful matches
                avg_sim = sum(1.0 - p.get('distance', 1.0) for p in successful_projects) / success_count
                confidence = float(f"{avg_sim:.2f}")
            
            elif 1 <= success_count <= 2:
                # Found 1-2 successful projects
                compliance_level = ComplianceLevel.PARTIAL
                confidence = 0.6
                
            elif similar_count > 0 and success_count == 0:
                # Found similar projects but NONE were successful
                compliance_level = ComplianceLevel.WARNING
                confidence = 0.7
                
            else:
                # No similar projects found
                compliance_level = ComplianceLevel.UNKNOWN
                confidence = 0.3

            status = f"Found {similar_count} relevant projects ({success_count} successful)"
            
            # Generate summary with LLM if available
            message = ""
            if LLM_AVAILABLE and llm_config and llm_config.enable_llm_relevance and relevant_projects:
                try:
                    message = self._generate_experience_summary(
                        llm_client, 
                        llm_config, 
                        requirement_text, 
                        relevant_projects
                    )
                except Exception as e:
                    logger.warning(f"[TOOL] XP summary generation failed: {e}")
                    message = self._generate_fallback_message(similar_count, success_count, compliance_level)
            else:
                message = self._generate_fallback_message(similar_count, success_count, compliance_level)

            # Step 4: Build ToolResult
            result = ToolResult(
                tool_name=self.name,
                requirement=requirement_text,
                status=status,
                compliance_level=compliance_level,
                confidence=confidence,
                details=details,
                risks=[], 
                message=message
            )
            
            # Step 5: Return as JSON string
            return result.model_dump_json()

        except Exception as e:
            logger.error(f"KnowledgeQueryTool Error: {e}")
            error_result = ToolResult(
                tool_name=self.name,
                requirement=requirement_text,
                status="Error",
                compliance_level=ComplianceLevel.UNKNOWN,
                confidence=0.0,
                details={"error": str(e)},
                message=f"System error during knowledge query: {str(e)}"
            )
            return error_result.model_dump_json()
            
        finally:
            session.close()

    def _generate_fallback_message(self, count, success, level):
        """Generate standard templated message"""
        msg = f"Analysis based on {count} past projects. "
        if level == ComplianceLevel.COMPLIANT:
            msg += "Strong evidence of capability from multiple successful projects."
        elif level == ComplianceLevel.PARTIAL:
            msg += "Limited evidence from past successful projects."
        elif level == ComplianceLevel.WARNING:
            msg += "Similar past projects exist but had issues/failures."
        else:
            msg += "No relevant past project experience found."
        return msg

    def _check_relevance_with_llm(self, client, config, requirement, projects):
        """Use LLM to verify if vector matches are actually relevant"""
        validated_projects = []
        
        # Prepare context for batch processing
        projects_text = "\n\n".join([
            f"Project {i+1}: {p.get('name')}\nDescription: {p.get('description', 'N/A')}\nOutcome: {p.get('outcome')}"
            for i, p in enumerate(projects)
        ])
        
        prompt = f"""
        Analyze if these past projects demonstrate capability for the following Requirement.
        
        Requirement: "{requirement}"
        
        Projects:
        {projects_text}
        
        For each project, determine if it is RELEVANT or IRRELEVANT to the requirement.
        Be extremely inclusive. If the project is in the same broad industry (e.g. Healthcare, Public Sector) or uses the requested technology, mark it as RELEVANT. match on sub-domains (e.g. Medicaid matches Healthcare).
        
        Return JSON format:
        {{
            "analysis": [
                {{
                    "project_index": 1,
                    "is_relevant": true,
                    "reason": "Demonstrates specific experience with X"
                }}
            ]
        }}
        """
        
        response = client.call_llm_json(
            system_prompt="You are an expert RFP analyst helping to evaluate if past projects match new requirements.",
            user_prompt=prompt,
            model=config.llm_relevance_model,
            temperature=config.relevance_temperature
        )
        
        if response and 'analysis' in response:
            for item in response['analysis']:
                if item.get('is_relevant', False):
                    idx = item.get('project_index', 0) - 1
                    if 0 <= idx < len(projects):
                        proj = projects[idx]
                        proj['relevance_reason'] = item.get('reason')
                        validated_projects.append(proj)
                        
        return validated_projects if validated_projects else projects

    def _generate_experience_summary(self, client, config, requirement, projects):
        """Generate a natural language summary of experience"""
        context = "\n".join([
            f"- {p.get('name')} ({p.get('outcome')}): {p.get('relevance_reason', 'Similar project')}"
            for p in projects
        ])
        
        prompt = f"""
        Summarize our organization's experience regarding this requirement based on past projects.
        
        Requirement: "{requirement}"
        
        Relevant Experience:
        {context}
        
        Write a concise 1-2 sentence statement proving our capability.
        Focus on successful outcomes.
        """
        
        return client.call_llm(
            system_prompt="You are an expert RFP analyst summarizing vendor experience.",
            user_prompt=prompt,
            model=config.llm_relevance_model,
            temperature=config.relevance_temperature
        )

    def _arun(self, requirement_text: str, requirement_embedding: List[float]):
        raise NotImplementedError("Async not implemented")

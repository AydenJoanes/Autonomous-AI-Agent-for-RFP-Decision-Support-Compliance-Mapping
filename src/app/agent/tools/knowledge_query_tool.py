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
        
        try:
            # Step 1: Search similar projects
            # Fetch slightly more to filter by threshold
            results = repository.search_similar(embedding=requirement_embedding, limit=10)
            
            # Filter by similarity threshold (0.7 -> Distance <= 0.3)
            similar_projects = []
            for p in results:
                # distance is returned by search_similar
                distance = p.get('distance', 1.0)
                if distance <= 0.3:
                    similar_projects.append(p)
            
            # Step 2: Determine compliance and confidence
            similar_count = len(similar_projects)
            successful_projects = [
                p for p in similar_projects 
                if p.get('outcome', '').lower() in ['success', 'partial success']
            ]
            success_count = len(successful_projects)
            
            compliance_level = ComplianceLevel.UNKNOWN
            confidence = 0.3
            details = {
                "similar_count": similar_count,
                "success_count": success_count,
                "project_names": [p.get('name') for p in similar_projects],
                "matches": []
            }

            # Populate match details
            for p in similar_projects:
                details['matches'].append({
                    "name": p.get('name'),
                    "outcome": p.get('outcome'),
                    "similarity": 1.0 - p.get('distance', 1.0)
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

            status = f"Found {similar_count} similar projects ({success_count} successful)"
            message = f"Analysis based on {similar_count} past projects. "
            if compliance_level == ComplianceLevel.COMPLIANT:
                message += "Strong evidence of capability from multiple successful projects."
            elif compliance_level == ComplianceLevel.PARTIAL:
                message += "Limited evidence from past successful projects."
            elif compliance_level == ComplianceLevel.WARNING:
                message += "Similar past projects exist but had issues/failures."
            else:
                message += "No relevant past project experience found."

            # Step 3: Build ToolResult
            result = ToolResult(
                tool_name=self.name,
                requirement=requirement_text,
                status=status,
                compliance_level=compliance_level,
                confidence=confidence,
                details=details,
                risks=[], # Logic for risks could be added here
                message=message
            )
            
            # Step 4: Return as JSON string
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

    def _arun(self, requirement_text: str, requirement_embedding: List[float]):
        raise NotImplementedError("Async not implemented")

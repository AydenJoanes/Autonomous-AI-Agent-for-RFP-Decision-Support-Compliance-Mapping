from typing import Type
import json
from loguru import logger
from pydantic import BaseModel, Field

from langchain.tools import BaseTool

from src.app.database.connection import SessionLocal
from src.app.database.repositories.strategic_preferences_repository import StrategicPreferencesRepository
from src.app.models.compliance import ComplianceLevel, ToolResult


class StrategyEvaluatorInput(BaseModel):
    rfp_context: str = Field(..., description="JSON string with keys: industry, technologies, project_type, client_sector")


class StrategyEvaluatorTool(BaseTool):
    name: str = "strategy_evaluator"
    description: str = "Evaluates RFP strategic alignment. Input should be JSON with: industry, technologies, project_type, client_sector."
    args_schema: Type[BaseModel] = StrategyEvaluatorInput

    def _run(self, rfp_context: str) -> str:
        logger.info(f"StrategyEvaluatorTool: Evaluating strategic alignment")
        
        session = SessionLocal()
        repository = StrategicPreferencesRepository(session)
        
        try:
            # Step 1: Parse input
            try:
                context = json.loads(rfp_context)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse RFP context JSON: {e}")
                result = ToolResult(
                    tool_name=self.name,
                    requirement=rfp_context,
                    status="INVALID_INPUT",
                    compliance_level=ComplianceLevel.UNKNOWN,
                    confidence=0.0,
                    details={"error": str(e)},
                    message="Invalid JSON input format"
                )
                return result.json()
            
            industry = context.get('industry', '').strip()
            technologies = context.get('technologies', [])
            project_type = context.get('project_type', '').strip()
            client_sector = context.get('client_sector', '').strip()
            
            # Ensure technologies is a list
            if isinstance(technologies, str):
                technologies = [tech.strip() for tech in technologies.split(',')]
            
            details = {
                "rfp_industry": industry,
                "rfp_technologies": technologies,
                "rfp_project_type": project_type,
                "rfp_client_sector": client_sector
            }
            
            # Step 2: Query strategic preferences
            all_preferences = repository.get_all()
            
            # Group by type
            preferences_by_type = {}
            for pref in all_preferences:
                pref_type = pref.get('preference_type', 'unknown')
                if pref_type not in preferences_by_type:
                    preferences_by_type[pref_type] = []
                preferences_by_type[pref_type].append(pref)
            
            details["preference_categories"] = list(preferences_by_type.keys())
            details["total_preferences"] = len(all_preferences)
            
            # Step 3: Calculate dimension scores
            industry_score = self._calculate_industry_score(industry, preferences_by_type.get('industry', []))
            technology_score = self._calculate_technology_score(technologies, preferences_by_type)
            project_type_score = self._calculate_project_type_score(project_type, preferences_by_type.get('project_type', []))
            sector_score = self._calculate_sector_score(client_sector, preferences_by_type.get('client', []))
            
            details["dimension_scores"] = {
                "industry": round(industry_score, 2),
                "technology": round(technology_score, 2),
                "project_type": round(project_type_score, 2),
                "client_sector": round(sector_score, 2)
            }
            
            # Step 4: Calculate composite score
            # Weights: Industry 30%, Technology 25%, Project type 25%, Sector 10%, Other 10%
            composite_score = (
                industry_score * 0.30 +
                technology_score * 0.25 +
                project_type_score * 0.25 +
                sector_score * 0.10 +
                0.5 * 0.10  # Other factors (baseline 0.5)
            ) * 100
            
            composite_score = min(100, max(0, composite_score))  # Clamp to 0-100
            details["composite_score"] = round(composite_score, 1)
            details["weights"] = {
                "industry": "30%",
                "technology": "25%",
                "project_type": "25%",
                "client_sector": "10%",
                "other": "10%"
            }
            
            # Step 5: Determine compliance and confidence
            compliance_level = ComplianceLevel.UNKNOWN
            final_status = "UNKNOWN"
            confidence = 0.5
            message = ""
            risks = []
            
            if composite_score >= 80:
                # STRONG ALIGNMENT
                compliance_level = ComplianceLevel.COMPLIANT
                final_status = "STRONG_ALIGNMENT"
                confidence = composite_score / 100
                message = f"RFP shows strong strategic alignment (score: {composite_score:.0f}/100). Highly recommended."
            
            elif composite_score >= 60:
                # MODERATE ALIGNMENT
                compliance_level = ComplianceLevel.PARTIAL
                final_status = "MODERATE_ALIGNMENT"
                confidence = 0.7
                message = f"RFP shows moderate strategic alignment (score: {composite_score:.0f}/100). Acceptable with some reservations."
                risks.append("Strategic fit is moderate - evaluate business case carefully")
            
            elif composite_score >= 40:
                # WEAK ALIGNMENT
                compliance_level = ComplianceLevel.WARNING
                final_status = "WEAK_ALIGNMENT"
                confidence = 0.6
                message = f"RFP shows weak strategic alignment (score: {composite_score:.0f}/100). Proceed with caution."
                risks.append("Poor strategic fit - requires strong business justification")
                risks.append("May divert resources from core competencies")
            
            else:
                # MISALIGNMENT
                compliance_level = ComplianceLevel.NON_COMPLIANT
                final_status = "MISALIGNMENT"
                confidence = 0.8
                message = f"RFP is strategically misaligned (score: {composite_score:.0f}/100). Not recommended."
                risks.append("Significant strategic misalignment")
                risks.append("Project does not fit company direction")
                risks.append("High opportunity cost")
            
            # Step 6: Generate strategic flags
            strategic_flags = []
            
            # Core competency check (high scores across all dimensions)
            if industry_score >= 0.8 and technology_score >= 0.8 and project_type_score >= 0.7:
                strategic_flags.append("CORE_COMPETENCY")
            
            # Strategic expansion (good industry/sector fit but lower tech score)
            elif industry_score >= 0.7 and sector_score >= 0.6 and technology_score < 0.6:
                strategic_flags.append("STRATEGIC_EXPANSION")
            
            # Off-strategy (low alignment)
            if composite_score < 50:
                strategic_flags.append("OFF_STRATEGY")
            
            # Priority industry
            if industry_score >= 0.9:
                strategic_flags.append("PRIORITY_INDUSTRY")
            
            # Technology mismatch
            if technology_score < 0.4:
                strategic_flags.append("TECHNOLOGY_MISMATCH")
                risks.append("Required technologies do not match company expertise")
            
            details["strategic_flags"] = strategic_flags
            
            # Add strategic insights
            if industry_score < 0.5:
                risks.append(f"Industry '{industry}' is not a strategic priority")
            
            if project_type_score < 0.5:
                risks.append(f"Project type '{project_type}' is not a preferred engagement type")
            
            # Step 7: Return ToolResult as JSON string
            result = ToolResult(
                tool_name=self.name,
                requirement=rfp_context,
                status=final_status,
                compliance_level=compliance_level,
                confidence=confidence,
                details=details,
                risks=risks,
                message=message
            )
            
            return result.json()
        
        except Exception as e:
            logger.error(f"StrategyEvaluatorTool Error: {e}")
            error_result = ToolResult(
                tool_name=self.name,
                requirement=rfp_context,
                status="ERROR",
                compliance_level=ComplianceLevel.UNKNOWN,
                confidence=0.0,
                details={"error": str(e)},
                message=f"System error during strategy evaluation: {str(e)}"
            )
            return error_result.json()
        
        finally:
            session.close()
    
    def _calculate_industry_score(self, industry: str, industry_prefs: list) -> float:
        """
        Calculate industry alignment score (0-1).
        """
        if not industry or not industry_prefs:
            return 0.5  # Neutral if no data
        
        # Normalize industry string for comparison
        industry_lower = industry.lower().strip()
        
        for pref in industry_prefs:
            pref_value = pref.get('value', '').lower().strip()
            priority = pref.get('priority', 5)
            
            # Check for exact or partial match
            if industry_lower == pref_value or industry_lower in pref_value or pref_value in industry_lower:
                # Higher priority = higher score
                # Priority 10 = 1.0, Priority 1 = 0.5
                return 0.5 + (priority / 10) * 0.5
        
        return 0.3  # No match
    
    def _calculate_technology_score(self, technologies: list, preferences_by_type: dict) -> float:
        """
        Calculate technology alignment score (0-1).
        """
        if not technologies:
            return 0.5
        
        # Look for technology in strategic preferences (might be in different preference types)
        all_tech_related = []
        for pref_type in ['project_type', 'priority']:
            all_tech_related.extend(preferences_by_type.get(pref_type, []))
        
        if not all_tech_related:
            return 0.5
        
        # Calculate matches
        match_scores = []
        for tech in technologies:
            tech_lower = tech.lower().strip()
            best_match = 0.0
            
            for pref in all_tech_related:
                pref_value = pref.get('value', '').lower().strip()
                priority = pref.get('priority', 5)
                
                if tech_lower in pref_value or pref_value in tech_lower:
                    score = 0.5 + (priority / 10) * 0.5
                    best_match = max(best_match, score)
            
            match_scores.append(best_match if best_match > 0 else 0.3)
        
        # Average of all technology scores
        return sum(match_scores) / len(match_scores) if match_scores else 0.5
    
    def _calculate_project_type_score(self, project_type: str, project_type_prefs: list) -> float:
        """
        Calculate project type alignment score (0-1).
        """
        if not project_type or not project_type_prefs:
            return 0.5
        
        project_type_lower = project_type.lower().strip()
        
        for pref in project_type_prefs:
            pref_value = pref.get('value', '').lower().strip()
            priority = pref.get('priority', 5)
            
            if project_type_lower == pref_value or project_type_lower in pref_value or pref_value in project_type_lower:
                return 0.5 + (priority / 10) * 0.5
        
        return 0.3
    
    def _calculate_sector_score(self, client_sector: str, client_prefs: list) -> float:
        """
        Calculate client sector alignment score (0-1).
        """
        if not client_sector or not client_prefs:
            return 0.5
        
        sector_lower = client_sector.lower().strip()
        
        for pref in client_prefs:
            pref_value = pref.get('value', '').lower().strip()
            priority = pref.get('priority', 5)
            
            if sector_lower == pref_value or sector_lower in pref_value or pref_value in sector_lower:
                return 0.5 + (priority / 10) * 0.5
        
        return 0.4  # Slightly penalize non-matching sectors
    
    def _arun(self, rfp_context: str):
        raise NotImplementedError("Async not implemented")

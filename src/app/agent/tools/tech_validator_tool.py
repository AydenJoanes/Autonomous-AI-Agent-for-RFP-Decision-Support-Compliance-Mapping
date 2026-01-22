from typing import Type
from datetime import datetime, timedelta
from loguru import logger
from pydantic import BaseModel, Field

from langchain.tools import BaseTool

from src.app.database.connection import SessionLocal
from src.app.database.repositories.tech_repository import TechRepository
from src.app.models.compliance import ComplianceLevel, ToolResult


class TechValidatorInput(BaseModel):
    technology: str = Field(..., description="The technology name to validate")


class TechValidatorTool(BaseTool):
    name: str = "tech_validator"
    description: str = "Validates company technology expertise. Input should be technology name."
    args_schema: Type[BaseModel] = TechValidatorInput

    def _run(self, technology: str) -> str:
        logger.info(f"TechValidatorTool: Validating '{technology}'")
        
        session = SessionLocal()
        repository = TechRepository(session)
        
        try:
            # Step 1: Search technology (normalize and try variants)
            normalized_tech = technology.strip()
            
            # Try exact match first
            tech = repository.get_by_name(normalized_tech)
            
            # If not found, try common variants
            if not tech:
                tech = self._try_variants(repository, normalized_tech)
            
            # Step 2: Determine status and compliance
            if not tech:
                # NOT FOUND
                result = ToolResult(
                    tool_name=self.name,
                    requirement=technology,
                    status="NOT_IN_DATABASE",
                    compliance_level=ComplianceLevel.UNKNOWN,
                    confidence=0.8,
                    details={"searched_technology": normalized_tech},
                    message="Technology not in official stack. Team might still have expertise."
                )
                return result.model_dump_json()
            
            # Found technology - analyze it
            tech_name = tech.get('technology', normalized_tech)
            proficiency = tech.get('proficiency', 'unknown').lower()
            years_experience = tech.get('years_experience', 0)
            team_size = tech.get('team_size', 0)
            last_used = tech.get('last_used')
            
            compliance_level = ComplianceLevel.UNKNOWN
            confidence = 0.5
            risks = []
            message = ""
            final_status = "UNKNOWN"
            
            details = {
                "technology": tech_name,
                "proficiency": proficiency,
                "years_experience": years_experience,
                "team_size": team_size,
                "last_used": str(last_used) if last_used else None
            }
            
            # Proficiency assessment
            if proficiency == "expert":
                compliance_level = ComplianceLevel.COMPLIANT
                confidence = 1.0
                final_status = "EXPERT"
                message = f"Team has expert-level proficiency in {tech_name}."
            
            elif proficiency == "advanced":
                compliance_level = ComplianceLevel.COMPLIANT
                confidence = 0.9
                final_status = "ADVANCED"
                message = f"Team has advanced proficiency in {tech_name}."
            
            elif proficiency == "intermediate":
                compliance_level = ComplianceLevel.PARTIAL
                confidence = 0.7
                final_status = "INTERMEDIATE"
                message = f"Team has intermediate proficiency in {tech_name}."
                risks.append("Proficiency level is intermediate, may need expert support for complex requirements")
            
            elif proficiency == "beginner":
                compliance_level = ComplianceLevel.PARTIAL
                confidence = 0.5
                final_status = "BEGINNER"
                message = f"Team has beginner-level proficiency in {tech_name}."
                risks.append("Low proficiency level, significant learning curve expected")
            
            else:
                compliance_level = ComplianceLevel.UNKNOWN
                confidence = 0.4
                final_status = "UNKNOWN_PROFICIENCY"
                message = f"Technology {tech_name} found but proficiency level unknown."
                risks.append("Proficiency level not documented")
            
            # Recency check
            if last_used:
                today = datetime.now().date()
                days_since_use = (today - last_used).days
                years_since_use = days_since_use / 365.25
                
                details["days_since_last_use"] = days_since_use
                details["years_since_last_use"] = round(years_since_use, 2)
                
                if years_since_use < 1:  # < 1 year
                    # No change, recently used
                    message += f" Last used {days_since_use} days ago (current)."
                
                elif 1 <= years_since_use < 2:  # 1-2 years
                    confidence = max(0.0, confidence - 0.1)
                    risks.append(f"Technology last used {round(years_since_use, 1)} years ago")
                    message += f" Last used {round(years_since_use, 1)} years ago. Skills may need refreshing."
                    # Keep current compliance_level but add warning
                
                elif 2 <= years_since_use < 5:  # 2-5 years
                    confidence = max(0.0, confidence - 0.2)
                    compliance_level = ComplianceLevel.WARNING
                    final_status = "STALE"
                    risks.append(f"Technology not used in {round(years_since_use, 1)} years, skills may be outdated")
                    message += f" WARNING: Last used {round(years_since_use, 1)} years ago. Expertise may be stale."
                
                else:  # > 5 years
                    confidence = max(0.0, confidence - 0.3)
                    compliance_level = ComplianceLevel.PARTIAL
                    final_status = "OUTDATED"
                    risks.append(f"Technology not used in {round(years_since_use, 1)} years, significant skill gap likely")
                    message += f" WARNING: Last used {round(years_since_use, 1)} years ago. Expertise is outdated."
            
            # Team size considerations
            if team_size > 0:
                details["team_members_with_skill"] = team_size
                if team_size == 1:
                    risks.append("Only 1 team member has this skill (single point of failure)")
                elif team_size == 2:
                    risks.append("Only 2 team members have this skill (limited coverage)")
            else:
                risks.append("Team size for this technology not documented")
            
            # Additional experience context
            if years_experience > 0:
                message += f" Team has {years_experience} years of experience."
            
            # Step 3: Return ToolResult as JSON string
            result = ToolResult(
                tool_name=self.name,
                requirement=technology,
                status=final_status,
                compliance_level=compliance_level,
                confidence=confidence,
                details=details,
                risks=risks,
                message=message
            )
            
            return result.model_dump_json()
        
        except Exception as e:
            logger.error(f"TechValidatorTool Error: {e}")
            error_result = ToolResult(
                tool_name=self.name,
                requirement=technology,
                status="ERROR",
                compliance_level=ComplianceLevel.UNKNOWN,
                confidence=0.0,
                details={"error": str(e)},
                message=f"System error during technology validation: {str(e)}"
            )
            return error_result.model_dump_json()
        
        finally:
            session.close()
    
    def _try_variants(self, repository: TechRepository, tech_name: str):
        """
        Try common technology name variants.
        e.g., Python = python = Python3 = python3
        """
        variants = [
            tech_name.lower(),
            tech_name.upper(),
            tech_name.capitalize(),
            tech_name.replace(" ", ""),
            tech_name.replace("-", ""),
            tech_name.replace("_", ""),
            tech_name + "3",  # Python3
            tech_name + ".js",  # React.js
            tech_name.replace(".js", ""),  # React
        ]
        
        for variant in variants:
            tech = repository.get_by_name(variant)
            if tech:
                logger.info(f"Matched '{tech_name}' to variant '{variant}'")
                return tech
        
        # Try partial search as last resort
        search_results = repository.search_technology(tech_name)
        if search_results:
            logger.info(f"Partial matched '{tech_name}' to '{search_results[0].get('technology')}'")
            return search_results[0]
        
        return None
    
    def _arun(self, technology: str):
        raise NotImplementedError("Async not implemented")

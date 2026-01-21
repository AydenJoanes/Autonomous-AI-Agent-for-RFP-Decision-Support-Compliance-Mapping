from typing import Type
import re
from loguru import logger
from pydantic import BaseModel, Field

from langchain.tools import BaseTool

from src.app.database.connection import SessionLocal
from src.app.database.repositories.project_repository import ProjectRepository
from src.app.models.compliance import ComplianceLevel, ToolResult


class TimelineAssessorInput(BaseModel):
    timeline: str = Field(..., description="The timeline duration (e.g., '4 months', '16 weeks', '6')")


class TimelineAssessorTool(BaseTool):
    name: str = "timeline_assessor"
    description: str = "Assesses timeline feasibility. Input should be timeline in months."
    args_schema: Type[BaseModel] = TimelineAssessorInput

    def _run(self, timeline: str) -> str:
        logger.info(f"TimelineAssessorTool: Assessing timeline '{timeline}'")
        
        session = SessionLocal()
        
        try:
            # Step 1: Parse timeline
            timeline_months = self._parse_timeline(timeline)
            
            if timeline_months is None or timeline_months <= 0:
                result = ToolResult(
                    tool_name=self.name,
                    requirement=timeline,
                    status="INVALID_TIMELINE",
                    compliance_level=ComplianceLevel.UNKNOWN,
                    confidence=0.0,
                    details={"raw_timeline": timeline},
                    message=f"Could not parse timeline: {timeline}"
                )
                return result.json()
            
            # Step 2: Get current capacity
            company_profile = self._get_company_profile(session)
            team_size = company_profile.get('team_size', 0) if company_profile else 0
            current_utilization = 0.70  # Hardcoded for now
            available_capacity = team_size * (1 - current_utilization)
            
            details = {
                "timeline_months": timeline_months,
                "team_size": team_size,
                "current_utilization": current_utilization,
                "available_capacity": round(available_capacity, 1)
            }
            
            # Step 3: Query historical projects
            project_repo = ProjectRepository(session)
            historical_projects = project_repo.get_all()
            
            compliance_level = ComplianceLevel.UNKNOWN
            confidence = 0.5
            risks = []
            message = ""
            final_status = "UNKNOWN"
            
            # Filter projects with valid duration data
            valid_projects = [p for p in historical_projects if p.get('duration_months', 0) > 0]
            
            # Step 4: Determine status and compliance
            if not valid_projects or len(valid_projects) == 0:
                # NO HISTORICAL DATA
                final_status = "NO_HISTORICAL_DATA"
                compliance_level = ComplianceLevel.UNKNOWN
                confidence = 0.4
                message = f"Timeline of {timeline_months} months requested. No historical project data available for comparison."
                risks.append("No historical timeline data to validate feasibility")
                details["historical_data_available"] = False
            
            else:
                # Historical data available
                durations = [p.get('duration_months') for p in valid_projects]
                avg_duration = sum(durations) / len(durations)
                min_duration = min(durations)
                max_duration = max(durations)
                
                details["historical_avg_duration"] = round(avg_duration, 1)
                details["historical_min_duration"] = min_duration
                details["historical_max_duration"] = max_duration
                details["historical_project_count"] = len(valid_projects)
                details["deviation_from_avg"] = round(((timeline_months - avg_duration) / avg_duration * 100) if avg_duration > 0 else 0, 1)
                
                # Determine status based on timeline comparison
                if min_duration <= timeline_months <= max_duration:
                    # WITHIN HISTORICAL RANGE
                    compliance_level = ComplianceLevel.COMPLIANT
                    
                    # Check proximity to average
                    deviation_percent = abs((timeline_months - avg_duration) / avg_duration * 100) if avg_duration > 0 else 0
                    
                    if deviation_percent <= 20:
                        # Near average
                        final_status = "FEASIBLE"
                        confidence = 0.9
                        message = f"Timeline of {timeline_months} months is feasible (close to historical average of {avg_duration:.1f} months)."
                    
                    elif timeline_months <= (min_duration + (max_duration - min_duration) * 0.25):
                        # Near minimum (first quartile)
                        final_status = "TIGHT"
                        confidence = 0.7
                        message = f"Timeline of {timeline_months} months is tight but achievable (near historical minimum of {min_duration} months)."
                        risks.append("Timeline is at the shorter end of historical range, may require careful planning")
                    
                    else:
                        # Somewhere in the middle or upper range
                        final_status = "FEASIBLE"
                        confidence = 0.8
                        message = f"Timeline of {timeline_months} months is feasible (within historical range: {min_duration}-{max_duration} months)."
                
                elif timeline_months < min_duration:
                    # BELOW HISTORICAL MINIMUM (AGGRESSIVE)
                    percent_of_min = (timeline_months / min_duration * 100) if min_duration > 0 else 0
                    details["percent_of_historical_min"] = round(percent_of_min, 1)
                    
                    if percent_of_min >= 80:
                        # 80-100% of minimum - slight aggressive but doable
                        final_status = "TIGHT"
                        compliance_level = ComplianceLevel.COMPLIANT
                        confidence = 0.7
                        message = f"Timeline of {timeline_months} months is slightly shorter than historical minimum ({min_duration} months, {percent_of_min:.0f}%). Tight but achievable."
                        risks.append(f"Timeline {100-percent_of_min:.0f}% shorter than fastest historical project")
                    
                    elif percent_of_min >= 50:
                        # 50-80% of minimum - aggressive
                        final_status = "AGGRESSIVE"
                        compliance_level = ComplianceLevel.WARNING
                        confidence = 0.6
                        message = f"Timeline of {timeline_months} months is aggressive ({percent_of_min:.0f}% of historical minimum). May require additional resources or scope reduction."
                        risks.append(f"Timeline significantly shorter than historical minimum ({min_duration} months)")
                        risks.append("May require overtime, additional staff, or reduced scope")
                    
                    else:
                        # < 50% of minimum - unrealistic
                        final_status = "UNREALISTIC"
                        compliance_level = ComplianceLevel.NON_COMPLIANT
                        confidence = 0.8
                        message = f"Timeline of {timeline_months} months is unrealistic ({percent_of_min:.0f}% of historical minimum {min_duration} months). Not feasible with current capacity."
                        risks.append("Timeline far below historical minimum - likely unachievable")
                        risks.append("Would require major changes to staffing, scope, or methodology")
                
                elif timeline_months > avg_duration * 1.5:
                    # > 150% of average - CONSERVATIVE
                    final_status = "CONSERVATIVE"
                    compliance_level = ComplianceLevel.COMPLIANT
                    confidence = 1.0
                    percent_over_avg = ((timeline_months / avg_duration - 1) * 100) if avg_duration > 0 else 0
                    message = f"Timeline of {timeline_months} months is conservative ({percent_over_avg:.0f}% longer than average). Provides ample buffer for quality and risk mitigation."
                    details["percent_over_avg"] = round(percent_over_avg, 1)
                
                else:
                    # Between max historical and 150% of average
                    final_status = "FEASIBLE"
                    compliance_level = ComplianceLevel.COMPLIANT
                    confidence = 0.9
                    message = f"Timeline of {timeline_months} months is feasible and comfortable (above historical average of {avg_duration:.1f} months)."
            
            # Step 5: Capacity check
            if current_utilization > 0.8:
                confidence = max(0.0, confidence - 0.1)
                risks.append(f"Team utilization is high ({current_utilization:.0%}), may impact ability to meet timeline")
                message += f" Note: Current team utilization is {current_utilization:.0%}."
            
            if team_size > 0 and timeline_months > 0:
                # Estimate required team members for this timeline
                # (This is a simplified estimation - could be more sophisticated)
                if valid_projects:
                    avg_team_effort = sum([p.get('team_size', 0) * p.get('duration_months', 0) for p in valid_projects]) / len(valid_projects) if len(valid_projects) > 0 else 0
                    estimated_team_needed = (avg_team_effort / timeline_months) if timeline_months > 0 else 0
                    
                    if estimated_team_needed > 0:
                        details["estimated_team_needed"] = round(estimated_team_needed, 1)
                        
                        if estimated_team_needed > available_capacity:
                            risks.append(f"Estimated {estimated_team_needed:.1f} team members needed but only {available_capacity:.1f} available")
                            if compliance_level == ComplianceLevel.COMPLIANT:
                                confidence = max(0.0, confidence - 0.15)
            
            # Step 6: Return ToolResult as JSON string
            result = ToolResult(
                tool_name=self.name,
                requirement=timeline,
                status=final_status,
                compliance_level=compliance_level,
                confidence=confidence,
                details=details,
                risks=risks,
                message=message
            )
            
            return result.json()
        
        except Exception as e:
            logger.error(f"TimelineAssessorTool Error: {e}")
            error_result = ToolResult(
                tool_name=self.name,
                requirement=timeline,
                status="ERROR",
                compliance_level=ComplianceLevel.UNKNOWN,
                confidence=0.0,
                details={"error": str(e)},
                message=f"System error during timeline assessment: {str(e)}"
            )
            return error_result.json()
        
        finally:
            session.close()
    
    def _parse_timeline(self, timeline_str: str) -> int:
        """
        Parse timeline string to months.
        Handles formats: "4 months", "4", "16 weeks", "1 year"
        """
        try:
            # Clean the input
            cleaned = timeline_str.strip().lower()
            
            # Extract number using regex
            number_match = re.search(r'(\d+(?:\.\d+)?)', cleaned)
            if not number_match:
                return None
            
            value = float(number_match.group(1))
            
            # Determine unit
            if 'week' in cleaned:
                # Convert weeks to months (approximately)
                return int(value / 4.33)
            elif 'year' in cleaned:
                # Convert years to months
                return int(value * 12)
            elif 'day' in cleaned:
                # Convert days to months (approximately)
                return int(value / 30)
            else:
                # Assume months if no unit specified
                return int(value)
        
        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to parse timeline '{timeline_str}': {e}")
            return None
    
    def _get_company_profile(self, session):
        """
        Get company profile from database.
        """
        try:
            from sqlalchemy import text
            query = text("SELECT * FROM company_profiles LIMIT 1")
            result = session.execute(query).mappings().first()
            return dict(result) if result else {}
        except Exception as e:
            logger.error(f"Failed to retrieve company profile: {e}")
            return {}
    
    def _arun(self, timeline: str):
        raise NotImplementedError("Async not implemented")

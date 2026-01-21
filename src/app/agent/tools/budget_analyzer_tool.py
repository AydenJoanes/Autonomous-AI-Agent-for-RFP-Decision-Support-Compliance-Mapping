from typing import Type
import re
from loguru import logger
from pydantic import BaseModel, Field

from langchain.tools import BaseTool

from src.app.database.connection import SessionLocal
from src.app.database.repositories.project_repository import ProjectRepository
from src.app.models.compliance import ComplianceLevel, ToolResult


class BudgetAnalyzerInput(BaseModel):
    budget: str = Field(..., description="The budget amount in USD (string format)")


class BudgetAnalyzerTool(BaseTool):
    name: str = "budget_analyzer"
    description: str = "Analyzes RFP budget feasibility. Input should be budget amount in USD."
    args_schema: Type[BaseModel] = BudgetAnalyzerInput

    def _run(self, budget: str) -> str:
        logger.info(f"BudgetAnalyzerTool: Analyzing budget '{budget}'")
        
        session = SessionLocal()
        
        try:
            # Step 1: Parse budget
            budget_amount = self._parse_budget(budget)
            
            if budget_amount is None or budget_amount <= 0:
                result = ToolResult(
                    tool_name=self.name,
                    requirement=budget,
                    status="INVALID_BUDGET",
                    compliance_level=ComplianceLevel.UNKNOWN,
                    confidence=0.0,
                    details={"raw_budget": budget},
                    message=f"Could not parse budget: {budget}"
                )
                return result.json()
            
            # Step 2: Get company capacity
            company_profile = self._get_company_profile(session)
            
            if not company_profile:
                result = ToolResult(
                    tool_name=self.name,
                    requirement=budget,
                    status="NO_COMPANY_DATA",
                    compliance_level=ComplianceLevel.UNKNOWN,
                    confidence=0.5,
                    details={"budget_amount": budget_amount},
                    message="Company profile not found in database. Cannot assess budget feasibility."
                )
                return result.json()
            
            budget_min = company_profile.get('budget_capacity_min', 0)
            budget_max = company_profile.get('budget_capacity_max', 0)
            
            compliance_level = ComplianceLevel.UNKNOWN
            confidence = 0.5
            risks = []
            message = ""
            final_status = "UNKNOWN"
            
            details = {
                "budget_amount": budget_amount,
                "company_budget_min": budget_min,
                "company_budget_max": budget_max,
                "formatted_budget": f"${budget_amount:,}"
            }
            
            # Step 3: Determine status and compliance
            if budget_amount < budget_min:
                # BELOW MINIMUM
                final_status = "BELOW_MINIMUM"
                compliance_level = ComplianceLevel.WARNING
                confidence = 0.8
                message = f"Budget (${budget_amount:,}) is below typical minimum (${budget_min:,}). Low priority unless strategically valuable."
                risks.append("Budget below minimum threshold may reduce project attractiveness")
                details["percentage_of_minimum"] = round((budget_amount / budget_min * 100) if budget_min > 0 else 0, 1)
            
            elif budget_amount > budget_max:
                # EXCEEDS MAXIMUM
                final_status = "EXCEEDS_MAXIMUM"
                compliance_level = ComplianceLevel.NON_COMPLIANT
                confidence = 0.9
                message = f"Budget (${budget_amount:,}) exceeds company capacity (${budget_max:,}). Company cannot handle project of this size."
                risks.append("Budget exceeds maximum capacity - project too large")
                details["excess_amount"] = budget_amount - budget_max
                details["percentage_over_max"] = round((budget_amount / budget_max * 100 - 100) if budget_max > 0 else 0, 1)
            
            else:
                # WITHIN RANGE - Calculate percentile
                budget_range = budget_max - budget_min
                if budget_range > 0:
                    percentile = ((budget_amount - budget_min) / budget_range) * 100
                    details["percentile"] = round(percentile, 1)
                    
                    if percentile <= 25:
                        # LOW END
                        final_status = "LOW_END"
                        compliance_level = ComplianceLevel.COMPLIANT
                        confidence = 0.9
                        message = f"Budget (${budget_amount:,}) is at the lower end ({percentile:.0f}th percentile) of company capacity. Well within capabilities."
                    
                    elif percentile <= 75:
                        # ACCEPTABLE RANGE
                        final_status = "ACCEPTABLE"
                        compliance_level = ComplianceLevel.COMPLIANT
                        confidence = 1.0
                        message = f"Budget (${budget_amount:,}) is in the sweet spot ({percentile:.0f}th percentile) of company capacity. Ideal fit."
                    
                    else:
                        # HIGH END
                        final_status = "HIGH_END"
                        compliance_level = ComplianceLevel.WARNING
                        confidence = 0.8
                        message = f"Budget (${budget_amount:,}) is at the higher end ({percentile:.0f}th percentile) of company capacity. May strain resources."
                        risks.append("Large budget may strain capacity and require significant resource allocation")
                else:
                    # Range is 0 (min == max)
                    final_status = "EXACT_MATCH"
                    compliance_level = ComplianceLevel.COMPLIANT
                    confidence = 1.0
                    message = f"Budget (${budget_amount:,}) matches company capacity exactly."
            
            # Step 4: Compare with historical projects
            project_repo = ProjectRepository(session)
            historical_projects = project_repo.get_all()
            
            if historical_projects and len(historical_projects) > 0:
                budgets = [p.get('budget', 0) for p in historical_projects if p.get('budget', 0) > 0]
                
                if budgets:
                    avg_budget = sum(budgets) / len(budgets)
                    min_historical = min(budgets)
                    max_historical = max(budgets)
                    
                    details["historical_avg_budget"] = round(avg_budget)
                    details["historical_min_budget"] = min_historical
                    details["historical_max_budget"] = max_historical
                    details["historical_project_count"] = len(budgets)
                    
                    # Check if significantly different from historical average
                    deviation_percent = abs((budget_amount - avg_budget) / avg_budget * 100) if avg_budget > 0 else 0
                    details["deviation_from_avg"] = round(deviation_percent, 1)
                    
                    if deviation_percent > 50:
                        risks.append(f"Budget is {deviation_percent:.0f}% different from historical average (${avg_budget:,.0f})")
                        message += f" Note: Significantly different from historical average of ${avg_budget:,.0f}."
                    
                    # Check if within historical range
                    if budget_amount < min_historical:
                        risks.append(f"Budget lower than any historical project (min: ${min_historical:,})")
                    elif budget_amount > max_historical:
                        risks.append(f"Budget higher than any historical project (max: ${max_historical:,})")
                        message += f" This would be the largest project undertaken."
                else:
                    # No budget data in historical projects
                    confidence = max(0.0, confidence - 0.1)
                    risks.append("Historical budget data incomplete")
            else:
                # No historical data
                confidence = max(0.0, confidence - 0.2)
                risks.append("No historical project data available for comparison")
                details["historical_data_available"] = False
            
            # Step 5: Return ToolResult as JSON string
            result = ToolResult(
                tool_name=self.name,
                requirement=budget,
                status=final_status,
                compliance_level=compliance_level,
                confidence=confidence,
                details=details,
                risks=risks,
                message=message
            )
            
            return result.json()
        
        except Exception as e:
            logger.error(f"BudgetAnalyzerTool Error: {e}")
            error_result = ToolResult(
                tool_name=self.name,
                requirement=budget,
                status="ERROR",
                compliance_level=ComplianceLevel.UNKNOWN,
                confidence=0.0,
                details={"error": str(e)},
                message=f"System error during budget analysis: {str(e)}"
            )
            return error_result.json()
        
        finally:
            session.close()
    
    def _parse_budget(self, budget_str: str) -> int:
        """
        Parse budget string to integer.
        Handles formats: "$150,000", "150000", "150k", etc.
        """
        try:
            # Remove common currency symbols and whitespace
            cleaned = budget_str.strip().replace("$", "").replace("USD", "").replace(",", "").replace(" ", "")
            
            # Handle 'k' notation (e.g., "150k" = 150000)
            if cleaned.lower().endswith('k'):
                cleaned = cleaned[:-1]
                return int(float(cleaned) * 1000)
            
            # Handle 'm' notation (e.g., "1.5m" = 1500000)
            if cleaned.lower().endswith('m'):
                cleaned = cleaned[:-1]
                return int(float(cleaned) * 1000000)
            
            # Parse as float then convert to int (handles decimals)
            return int(float(cleaned))
        
        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to parse budget '{budget_str}': {e}")
            return None
    
    def _get_company_profile(self, session):
        """
        Get company profile from database.
        Assumes there's only one company profile.
        """
        try:
            from sqlalchemy import text
            query = text("SELECT * FROM company_profiles LIMIT 1")
            result = session.execute(query).mappings().first()
            return dict(result) if result else None
        except Exception as e:
            logger.error(f"Failed to retrieve company profile: {e}")
            return None
    
    def _arun(self, budget: str):
        raise NotImplementedError("Async not implemented")

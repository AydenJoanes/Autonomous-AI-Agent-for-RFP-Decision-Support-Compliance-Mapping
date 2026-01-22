"""
Clarification Question Generator
Generates deterministic, human-readable clarification questions based on analysis gaps.
"""
from typing import List, Dict
from loguru import logger

from src.app.models.recommendation import RiskItem, RiskSeverity, ComplianceSummary
from src.app.models.compliance import ToolResult, ComplianceLevel

class ClarificationGenerator:
    """
    Identifies gaps and generates clarification questions using deterministic rules.
    does NOT use LLMs.
    """

    def generate(
        self, 
        compliance_summary: ComplianceSummary, 
        tool_results: List[ToolResult], 
        decision: Dict, 
        risks: List[RiskItem]
    ) -> List[str]:
        """
        Generate clarification questions based on analysis inputs.

        Args:
            compliance_summary: Summary of compliance status
            tool_results: Detailed tool execution results
            decision: The generated decision (used for context if needed)
            risks: List of identified risks

        Returns:
            List of unique clarification questions strings
        """
        questions = set()
        
        # 1. Certification Uncertainty
        self._check_tool_uncertainty(
            questions, tool_results, "certification_checker", 
            "Can the vendor provide documented proof of the required certification (e.g., ISO, SOC, HIPAA)?"
        )

        # 2. Timeline Ambiguity
        self._check_tool_or_risk(
            questions, tool_results, risks, 
            tool_name="timeline_assessor", 
            risk_category="timeline",
            template="Can the vendor clarify whether the proposed delivery timeline is firm and achievable for the full scope?"
        )

        # 3. Budget Uncertainty
        self._check_tool_or_risk(
            questions, tool_results, risks, 
            tool_name="budget_analyzer", 
            risk_category="budget",
            template="Can the vendor confirm whether the stated budget covers the full scope, including implementation and support?"
        )

        # 4. Technical Capability Ambiguity
        # Triggers on UNKNOWN or PARTIAL for tech_validator
        self._check_tool_status(
            questions, tool_results, "tech_validator", [ComplianceLevel.UNKNOWN, ComplianceLevel.PARTIAL],
            "Can the vendor provide evidence of prior experience with the required technologies at the proposed scale?"
        )

        # 5. Data / Access Uncertainty
        # Check for knowledge_query issues (often reflected as missing inputs or UNKNOWN results)
        # We'll use a specific check for knowledge_query tool returning UNKNOWN
        self._check_tool_uncertainty(
            questions, tool_results, "knowledge_query",
            "Can the client confirm data availability, access constraints, and ownership responsibilities?"
        )

        # 6. Strategic Fit Uncertainty
        self._check_tool_uncertainty(
            questions, tool_results, "strategy_evaluator",
            "Can the client clarify expectations around domain experience and long-term engagement goals?"
        )

        # 7. General Mandatory Requirement Gaps
        if compliance_summary.mandatory_unknown:
             questions.add("Can the client provide missing details for mandatory requirements marked as UNKNOWN?")

        # Convert to list and sort for consistency
        sorted_questions = sorted(list(questions))
        logger.info(f"[CLARIFICATION] Generated {len(sorted_questions)} questions")
        return sorted_questions

    def _check_tool_uncertainty(self, questions: set, tool_results: List[ToolResult], tool_name: str, template: str):
        """Add question if specific tool returned UNKNOWN."""
        for res in tool_results:
            if res.tool_name == tool_name and res.compliance_level == ComplianceLevel.UNKNOWN:
                questions.add(template)
                break

    def _check_tool_or_risk(self, questions: set, tool_results: List[ToolResult], risks: List[RiskItem], tool_name: str, risk_category: str, template: str):
        """Add question if tool is UNKNOWN OR risk is HIGH/MEDIUM."""
        # Check Tool
        for res in tool_results:
            if res.tool_name == tool_name and res.compliance_level == ComplianceLevel.UNKNOWN:
                questions.add(template)
                return

        # Check Risk
        for risk in risks:
            if risk.category.lower() == risk_category.lower() and risk.severity in [RiskSeverity.HIGH, RiskSeverity.MEDIUM]:
                questions.add(template)
                return

    def _check_tool_status(self, questions: set, tool_results: List[ToolResult], tool_name: str, statuses: List[str], template: str):
        """Add question if tool matches any of the provided statuses."""
        for res in tool_results:
            if res.tool_name == tool_name and res.compliance_level in statuses:
                questions.add(template)
                break

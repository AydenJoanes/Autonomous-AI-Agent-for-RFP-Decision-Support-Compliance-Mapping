"""
Evidence Synthesizer
Holistic analysis of tool results before decision engine.
"""

import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from loguru import logger

from src.app.models.compliance import ToolResult, ComplianceLevel
from src.app.models.requirement import Requirement
from src.app.utils.llm_client import get_llm_client
from src.app.services.llm_config import get_llm_config


class SynthesisReport(BaseModel):
    """Synthesis report from evidence analysis."""
    overall_assessment: str  # STRONG_FIT, MODERATE_FIT, WEAK_FIT, POOR_FIT
    key_strengths: List[str]
    key_gaps: List[str]
    conflicts_identified: List[str]
    confidence_factors_positive: List[str]
    confidence_factors_negative: List[str]
    recommended_mitigations: List[str]
    human_review_triggers: List[str]


# System prompt for synthesis
SYNTHESIS_SYSTEM_PROMPT = """You are synthesizing compliance analysis results for an RFP bid decision.

Analyze these results holistically and provide:

1. OVERALL_ASSESSMENT: One of STRONG_FIT, MODERATE_FIT, WEAK_FIT, POOR_FIT
   - STRONG_FIT: Majority compliant, no critical gaps, experience aligns
   - MODERATE_FIT: Mixed results, some gaps but addressable
   - WEAK_FIT: Significant gaps, would require substantial effort
   - POOR_FIT: Critical requirements not met, high risk

2. KEY_STRENGTHS: List 2-4 strongest compliance points with specific evidence

3. KEY_GAPS: List critical gaps or concerns with specific evidence

4. CONFLICTS_IDENTIFIED: Any contradictions or tensions in the results
   - Example: "Azure expertise is strong but Azure partnership certification has expired"

5. CONFIDENCE_FACTORS: What factors increase or decrease confidence in this assessment
   - Positive: Clear matches, recent relevant projects, active certifications
   - Negative: Many unknowns, expired certifications, no similar experience

6. RECOMMENDED_MITIGATIONS: For each key gap, suggest a potential mitigation

7. HUMAN_REVIEW_TRIGGERS: Specific reasons why human review might be needed

Respond with a JSON object matching this structure:
{
  "overall_assessment": "MODERATE_FIT",
  "key_strengths": ["strength 1", "strength 2"],
  "key_gaps": ["gap 1", "gap 2"],
  "conflicts_identified": ["conflict 1"],
  "confidence_factors": {
    "positive": ["factor 1"],
    "negative": ["factor 1"]
  },
  "recommended_mitigations": ["mitigation 1"],
  "human_review_triggers": ["trigger 1"]
}"""


def build_synthesis_user_prompt(
    tool_results: List[ToolResult],
    requirements: List[Requirement]
) -> str:
    """
    Build user prompt for synthesis.
    
    Args:
        tool_results: Tool execution results
        requirements: Original requirements
        
    Returns:
        Formatted user prompt
    """
    # Format tool results
    results_summary = []
    for result in tool_results:
        results_summary.append({
            "tool": result.tool_name,
            "compliance": result.compliance_level.value,
            "details": result.details,
            "evidence": result.details.get("evidence")[:200] if result.details.get("evidence") else None
        })
    
    # Format requirements
    req_summary = []
    for req in requirements:
        req_summary.append({
            "type": req.type.value,
            "value": req.extracted_value,
            "mandatory": req.is_mandatory
        })
    
    return f"""Synthesize these compliance analysis results:

TOOL RESULTS:
{json.dumps(results_summary, indent=2)}

REQUIREMENTS ANALYZED:
{json.dumps(req_summary, indent=2)}

Provide holistic synthesis as JSON."""


class EvidenceSynthesizer:
    """Synthesize tool results into holistic analysis."""
    
    def __init__(self):
        """Initialize the synthesizer."""
        self.llm_client = get_llm_client()
        self.config = get_llm_config()
    
    def identify_conflicts(self, tool_results: List[ToolResult]) -> List[str]:
        """
        Identify conflicts in tool results using rule-based detection.
        
        Args:
            tool_results: Tool execution results
            
        Returns:
            List of conflict descriptions
        """
        conflicts = []
        
        # Build result map by tool
        results_by_tool: Dict[str, List[ToolResult]] = {}
        for result in tool_results:
            tool_name = result.tool_name
            if tool_name not in results_by_tool:
                results_by_tool[tool_name] = []
            results_by_tool[tool_name].append(result)
        
        # Check for tech compliant but related cert expired
        tech_results = results_by_tool.get("tech_validator", [])
        cert_results = results_by_tool.get("certification_checker", [])
        
        for tech_result in tech_results:
            if tech_result.compliance_level == ComplianceLevel.COMPLIANT:
                tech_name = tech_result.message.lower()
                # Check if there's a related certification that's not compliant
                for cert_result in cert_results:
                    if cert_result.compliance_level in [ComplianceLevel.NON_COMPLIANT, ComplianceLevel.PARTIAL]:
                        cert_name = cert_result.message.lower()
                        # Look for related terms (e.g., "azure" in both)
                        if any(word in cert_name and word in tech_name for word in ["azure", "aws", "gcp", "microsoft", "amazon", "google"]):
                            conflicts.append(
                                f"Technology expertise ({tech_result.message}) is strong but "
                                f"related certification ({cert_result.message}) is {cert_result.compliance_level.value}"
                            )
        
        # Check for experience found but different industry
        knowledge_results = results_by_tool.get("knowledge_query", [])
        for kq_result in knowledge_results:
            if kq_result.compliance_level == ComplianceLevel.PARTIAL:
                if "different" in kq_result.message.lower() or "adjacent" in kq_result.message.lower():
                    conflicts.append(
                        f"Experience found but in different domain: {kq_result.message}"
                    )
        
        # Check for timeline feasible but other constraints
        timeline_results = results_by_tool.get("timeline_assessor", [])
        budget_results = results_by_tool.get("budget_analyzer", [])
        
        for timeline_result in timeline_results:
            if timeline_result.compliance_level == ComplianceLevel.COMPLIANT:
                for budget_result in budget_results:
                    if budget_result.compliance_level == ComplianceLevel.NON_COMPLIANT:
                        conflicts.append(
                            f"Timeline is feasible but budget constraint exists: {budget_result.message}"
                        )
        
        return conflicts
    
    def parse_synthesis_response(self, response: Dict[str, Any]) -> SynthesisReport:
        """
        Parse LLM synthesis response.
        
        Args:
            response: Parsed JSON response from LLM
            
        Returns:
            SynthesisReport object
        """
        # Extract confidence factors
        confidence_factors = response.get("confidence_factors", {})
        
        return SynthesisReport(
            overall_assessment=response.get("overall_assessment", "MODERATE_FIT"),
            key_strengths=response.get("key_strengths", []),
            key_gaps=response.get("key_gaps", []),
            conflicts_identified=response.get("conflicts_identified", []),
            confidence_factors_positive=confidence_factors.get("positive", []),
            confidence_factors_negative=confidence_factors.get("negative", []),
            recommended_mitigations=response.get("recommended_mitigations", []),
            human_review_triggers=response.get("human_review_triggers", [])
        )
    
    def synthesize_evidence(
        self,
        tool_results: List[ToolResult],
        requirements: List[Requirement]
    ) -> SynthesisReport:
        """
        Synthesize tool results into holistic analysis.
        
        Args:
            tool_results: Tool execution results
            requirements: Original requirements
            
        Returns:
            Synthesis report
        """
        logger.info(f"Synthesizing evidence from {len(tool_results)} tool results")
        
        # First, identify conflicts using rules
        rule_based_conflicts = self.identify_conflicts(tool_results)
        
        try:
            # Build prompts
            user_prompt = build_synthesis_user_prompt(tool_results, requirements)
            
            # Call LLM
            response = self.llm_client.call_llm_json(
                system_prompt=SYNTHESIS_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                model=self.config.llm_synthesis_model,
                temperature=self.config.synthesis_temperature,
                timeout=self.config.synthesis_timeout
            )
            
            # Parse response
            synthesis = self.parse_synthesis_response(response)
            
            # Merge rule-based conflicts with LLM-identified conflicts
            all_conflicts = list(set(rule_based_conflicts + synthesis.conflicts_identified))
            synthesis.conflicts_identified = all_conflicts
            
            logger.info(
                f"Synthesis complete: {synthesis.overall_assessment} | "
                f"Strengths: {len(synthesis.key_strengths)} | "
                f"Gaps: {len(synthesis.key_gaps)} | "
                f"Conflicts: {len(synthesis.conflicts_identified)}"
            )
            
            return synthesis
            
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            # Return minimal synthesis on error
            return SynthesisReport(
                overall_assessment="MODERATE_FIT",
                key_strengths=[],
                key_gaps=[],
                conflicts_identified=rule_based_conflicts,
                confidence_factors_positive=[],
                confidence_factors_negative=["Synthesis analysis failed"],
                recommended_mitigations=[],
                human_review_triggers=["Automated synthesis unavailable - manual review recommended"]
            )

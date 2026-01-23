"""
Reflection Engine
Analyzes generated recommendations for quality, consistency, and risks.
Provides a "read-only" cognitive layer that adds meta-data to decisions.
"""
from typing import Dict, Any, List
from loguru import logger

from src.app.models.recommendation import Recommendation, RecommendationDecision, RiskSeverity

class ReflectionEngine:
    """
    Analyzes decisions to identify potential issues, overconfidence, or gaps.
    This analysis is appended to the recommendation as 'reflection_notes'.
    """

    def reflect(self, recommendation: Recommendation, synthesis_report=None) -> Dict[str, Any]:
        """
        Perform reflection on a generated recommendation, with optional LLM enhancement.

        Args:
            recommendation: The complete recommendation object
            synthesis_report: Optional synthesis report from evidence synthesizer

        Returns:
            Dictionary of reflection notes/signals
        """
        logger.info("[REFLECTION] Starting reflection analysis")
        
        reflection_data = {
            "flags": [],
            "consistency_score": 1.0,
            "observations": []
        }

        # Deterministic Checks (Base Layer)
        self._check_overconfidence(recommendation, reflection_data)
        self._check_uncertainty(recommendation, reflection_data)
        self._check_consistency(recommendation, reflection_data)
        
        # LLM Enhanced Reflection (Cognitive Layer)
        from src.app.services.llm_config import get_llm_config, LLM_AVAILABLE
        from src.app.utils.llm_client import LLMClient
        
        if LLM_AVAILABLE:
            config = get_llm_config()
            if config.enable_llm_reflection:
                try:
                    logger.info("[REFLECTION] Performing deep reflection with LLM")
                    client = LLMClient()
                    self._reflect_with_llm(client, config, recommendation, synthesis_report, reflection_data)
                except Exception as e:
                    logger.warning(f"[REFLECTION] LLM reflection failed: {e}")

        logger.info(f"[REFLECTION] Completed with {len(reflection_data['flags'])} flags")
        return reflection_data

    def _reflect_with_llm(self, client, config, rec, synthesis, data: Dict[str, Any]):
        """Use LLM to find subtle inconsistencies and bias."""
        
        # Prepare context
        verdict = rec.recommendation.value
        score = rec.confidence_score
        
        risks_text = "\n".join([f"- {r.severity}: {r.description}" for r in rec.risks])
        
        synthesis_text = "No synthesis report available."
        if synthesis:
            synthesis_text = f"""
            Overall Assessment: {synthesis.overall_assessment}
            Conflicts: {', '.join(synthesis.conflicts_identified) or 'None'}
            Gaps: {', '.join(synthesis.key_gaps) or 'None'}
            """
            
        prompt = f"""
        Act as a critical reviewer (Devil's Advocate) for this RFP Bid Decision.
        Analyze the decision for logical fallacies, cognitive bias, or missed risks.

        Decision: {verdict}
        Confidence Score: {score}/100
        
        Identified Risks:
        {risks_text}
        
        Evidence Synthesis:
        {synthesis_text}
        
        Tasks:
        1. Identify any "Blind Spots" (what are we missing?)
        2. Check for "Confirmation Bias" (ignoring contradictory evidence?)
        3. Flag "Overconfidence" if score is high but risks are severe.
        
        Return JSON:
        {{
            "critique": [
                {{
                    "type": "BLIND_SPOT | BIAS | INCONSISTENCY",
                    "observation": "Description of the issue"
                }}
            ]
        }}
        """
        
        response = client.call_llm_json(
            prompt=prompt,
            model=config.llm_reflection_model,
            temperature=config.reflection_temperature
        )
        
        if response and 'critique' in response:
            for item in response['critique']:
                flag_type = item.get('type', 'LLM_OBSERVATION')
                obs = item.get('observation', '')
                
                # Add to reflection data
                data["flags"].append(flag_type)
                data["observations"].append(f"[AI Critique] {obs}")
                
                # Penalize consistency score for verified biases
                if flag_type in ['BIAS', 'INCONSISTENCY']:
                    data["consistency_score"] -= 0.1

    def _check_overconfidence(self, rec: Recommendation, data: Dict[str, Any]):
        """Check for high confidence despite significant risks."""
        high_severity_risks = [r for r in rec.risks if r.severity == RiskSeverity.HIGH]
        
        if rec.confidence_score > 85 and high_severity_risks:
            flag = "OVERCONFIDENCE_RISK"
            msg = f"High confidence ({rec.confidence_score}%) despite {len(high_severity_risks)} HIGH severity risks."
            data["flags"].append(flag)
            data["observations"].append(msg)
            # data["consistency_score"] -= 0.2  # Simple penalty logic

    def _check_uncertainty(self, rec: Recommendation, data: Dict[str, Any]):
        """Check for high volume of unknown requirements."""
        summary = rec.compliance_summary
        total = summary.total_evaluated
        if total > 0:
            unknown_ratio = summary.unknown_count / total
            if unknown_ratio > 0.25:
                flag = "HIGH_UNCERTAINTY"
                msg = f"High uncertainty: {unknown_ratio:.1%} of requirements are UNKNOWN."
                data["flags"].append(flag)
                data["observations"].append(msg)

    def _check_consistency(self, rec: Recommendation, data: Dict[str, Any]):
        """Check if decision aligns with compliance metrics."""
        summary = rec.compliance_summary
        
        # Case: NO_BID but High Compliance
        if rec.recommendation == RecommendationDecision.NO_BID:
            if summary.compliant_count > (summary.total_evaluated * 0.8) and not rec.risks:
                flag = "CONSERVATIVE_DECISION"
                msg = "Decision is NO_BID despite high compliance (>80%) and no identified risks."
                data["flags"].append(flag)
                data["observations"].append(msg)

        # Case: BID but Low Compliance
        if rec.recommendation == RecommendationDecision.BID:
            if summary.non_compliant_count > (summary.total_evaluated * 0.3):
                flag = "AGGRESSIVE_DECISION"
                msg = "Decision is BID despite significant non-compliance (>30%)."
                data["flags"].append(flag)
                data["observations"].append(msg)

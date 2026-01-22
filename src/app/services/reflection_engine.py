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

    def reflect(self, recommendation: Recommendation) -> Dict[str, Any]:
        """
        Perform deterministic reflection on a generated recommendation.

        Args:
            recommendation: The complete recommendation object

        Returns:
            Dictionary of reflection notes/signals
        """
        logger.info("[REFLECTION] Starting reflection analysis")
        
        reflection_data = {
            "flags": [],
            "consistency_score": 1.0,
            "observations": []
        }

        self._check_overconfidence(recommendation, reflection_data)
        self._check_uncertainty(recommendation, reflection_data)
        self._check_consistency(recommendation, reflection_data)
        
        logger.info(f"[REFLECTION] Completed with {len(reflection_data['flags'])} flags")
        return reflection_data

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

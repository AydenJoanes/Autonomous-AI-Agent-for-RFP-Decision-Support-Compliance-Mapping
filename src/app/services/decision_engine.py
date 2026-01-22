"""
Decision Engine Service
Pure logic module that determines Bid/No-Bid based on compliance summary.
"""

from typing import List, Dict, Tuple, Any
from loguru import logger

from src.app.models.compliance import ComplianceLevel
from src.app.models.recommendation import (
    RecommendationDecision,
    ComplianceSummary,
    RiskItem,
    RiskSeverity
)


class DecisionEngine:
    """
    Pure logic module making Bid/No-Bid decisions.
    Uses heuristic scoring and decision matrix.
    """

    # Scoring Constants
    CONFIDENCE_BASE_SCORES = {
        ComplianceLevel.COMPLIANT: 90,
        ComplianceLevel.PARTIAL: 60,
        ComplianceLevel.WARNING: 50,
        ComplianceLevel.UNKNOWN: 50,
        ComplianceLevel.NON_COMPLIANT: 0
    }

    MANDATORY_MET_BONUS = 10
    MANDATORY_FAILED_PENALTY = 100  # Immediate fail
    
    CONFIDENCE_AVG_BASELINE = 0.8
    CONFIDENCE_AVG_MULTIPLIER = 20  # +2 pts for every 0.1 above baseline
    
    NON_COMPLIANT_PENALTY = 30
    WARNING_PENALTY = 10
    UNKNOWN_PENALTY = 2
    MAX_PENALTY_CAP = 50

    # Decision Thresholds
    BID_CONFIDENCE_THRESHOLD = 80
    CONDITIONAL_CONFIDENCE_THRESHOLD = 50
    UNKNOWN_HEAVY_THRESHOLD = 0.5  # 50% unknown
    
    # Review Trigger Thresholds
    BORDERLINE_CONFIDENCE_LOW = 55
    BORDERLINE_CONFIDENCE_HIGH = 65
    HIGH_RISK_COUNT_THRESHOLD = 2

    def __init__(self):
        """Initialize the decision engine with empty trace."""
        self._trace: List[str] = []

    def _log_trace(self, message: str):
        """
        Add message to trace and log at DEBUG level.
        
        Args:
            message: Trace message to log
        """
        self._trace.append(message)
        logger.debug(f"[DECISION_TRACE] {message}")

    def get_trace(self) -> List[str]:
        """
        Return copy of decision trace.
        
        Returns:
            List of trace messages
        """
        return list(self._trace)

    def calculate_confidence_score(self, compliance_summary: ComplianceSummary) -> int:
        """
        Calculate heuristic confidence score (0-100).
        
        Args:
            compliance_summary: Compliance summary to evaluate
            
        Returns:
            Calculated score between 0 and 100
        """
        # Reset trace
        self._trace = []
        
        # Base score based on overall compliance level
        base = self.CONFIDENCE_BASE_SCORES.get(compliance_summary.overall_compliance, 40)
        self._log_trace(f"Base score for {compliance_summary.overall_compliance}: {base}")
        
        # Mandatory requirements adjustment
        mandatory_adj = 0
        if compliance_summary.mandatory_met:
            mandatory_adj = self.MANDATORY_MET_BONUS
            self._log_trace(f"Mandatory met: +{self.MANDATORY_MET_BONUS}")
        else:
            mandatory_adj = -self.MANDATORY_FAILED_PENALTY
            self._log_trace(f"Mandatory failed: -{self.MANDATORY_FAILED_PENALTY}")
            
        # Confidence average adjustment
        confidence_adj = (compliance_summary.confidence_avg - self.CONFIDENCE_AVG_BASELINE) * self.CONFIDENCE_AVG_MULTIPLIER
        self._log_trace(f"Confidence avg adjustment: {confidence_adj:+.1f}")
        
        # Penalty Calculation
        penalties_raw = (
            compliance_summary.non_compliant_count * self.NON_COMPLIANT_PENALTY +
            compliance_summary.warning_count * self.WARNING_PENALTY +
            compliance_summary.unknown_count * self.UNKNOWN_PENALTY
        )
        
        penalties = min(penalties_raw, self.MAX_PENALTY_CAP)
        self._log_trace(f"Penalties: {penalties_raw} (capped to {penalties})")
        
        # Final Score Calculation
        score = base + mandatory_adj + confidence_adj - penalties
        score = max(0, min(100, int(score)))  # Clamp to 0-100
        
        self._log_trace(f"Final confidence score: {score}")
        return score

    def determine_recommendation(self, compliance_summary: ComplianceSummary, confidence_score: int) -> RecommendationDecision:
        """
        Determine BID, NO_BID, or CONDITIONAL_BID.
        
        Args:
            compliance_summary: Compliance summary
            confidence_score: Calculated confidence score
            
        Returns:
            Recommendation decision enum
        """
        decision = None
        
        # Priority 1: Mandatory NON_COMPLIANT
        if compliance_summary.mandatory_failed:
            self._log_trace("Decision: NO_BID (mandatory requirement NON_COMPLIANT)")
            decision = RecommendationDecision.NO_BID
            
        # Priority 2: Mandatory UNKNOWN (needs human verification)
        elif compliance_summary.mandatory_unknown:
            self._log_trace("Decision: CONDITIONAL_BID (mandatory requirement UNKNOWN - needs verification)")
            decision = RecommendationDecision.CONDITIONAL_BID
            
        # Priority 2: Overall NON_COMPLIANT
        elif compliance_summary.overall_compliance == ComplianceLevel.NON_COMPLIANT:
            self._log_trace("Decision: NO_BID (overall NON_COMPLIANT)")
            decision = RecommendationDecision.NO_BID
            
        # Priority 3: High confidence + good compliance
        elif confidence_score >= self.BID_CONFIDENCE_THRESHOLD:
            if compliance_summary.overall_compliance in [ComplianceLevel.COMPLIANT, ComplianceLevel.PARTIAL]:
                self._log_trace(f"Decision: BID (confidence {confidence_score} >= {self.BID_CONFIDENCE_THRESHOLD})")
                decision = RecommendationDecision.BID
        
        if decision is None:
            # Priority 4: Medium confidence OR warning state
            if confidence_score >= self.CONDITIONAL_CONFIDENCE_THRESHOLD:
                self._log_trace(f"Decision: CONDITIONAL_BID (confidence {confidence_score} in range)")
                decision = RecommendationDecision.CONDITIONAL_BID
                
            # Priority 5: UNKNOWN-heavy (>50%)
            elif compliance_summary.total_evaluated > 0:
                unknown_ratio = compliance_summary.unknown_count / compliance_summary.total_evaluated
                if unknown_ratio > self.UNKNOWN_HEAVY_THRESHOLD:
                    self._log_trace(f"Decision: CONDITIONAL_BID (UNKNOWN ratio {unknown_ratio:.1%} > threshold)")
                    decision = RecommendationDecision.CONDITIONAL_BID
        
        # Priority 6: Low confidence
        if decision is None:
            self._log_trace(f"Decision: NO_BID (confidence {confidence_score} < {self.CONDITIONAL_CONFIDENCE_THRESHOLD})")
            decision = RecommendationDecision.NO_BID
            
        # Policy Assertion: UNKNOWN alone never triggers NO_BID
        # If NO_BID, ensure it's backed by failures or low score
        if decision == RecommendationDecision.NO_BID:
            is_valid_no_bid = (
                compliance_summary.non_compliant_count > 0 or 
                not compliance_summary.mandatory_met or
                confidence_score < self.CONDITIONAL_CONFIDENCE_THRESHOLD or
                compliance_summary.overall_compliance == ComplianceLevel.NON_COMPLIANT
            )
            
            if not is_valid_no_bid:
                # Fallback safeguard - should be unreachable with current logic but good for safety
                logger.warning("[DECISION_ENGINE] Policy violation detected: NO_BID without sufficient cause. Defaulting to CONDITIONAL_BID.")
                self._log_trace("Policy correction: Switched to CONDITIONAL_BID (safeguard)")
                decision = RecommendationDecision.CONDITIONAL_BID
                
        return decision

    def determine_human_review(
        self, 
        compliance_summary: ComplianceSummary, 
        confidence_score: int, 
        risks: List[RiskItem], 
        recommendation: RecommendationDecision
    ) -> Tuple[bool, List[str]]:
        """
        Determine if human review is needed and why.
        
        Args:
            compliance_summary: Compliance calculation summary
            confidence_score: Calculated score
            risks: List of identifies risks
            recommendation: Proposed recommendation
            
        Returns:
            Tuple of (requires_review boolean, list of reason strings)
        """
        requires_review = False
        reasons = []

        # Trigger 1: Mandatory UNKNOWN
        if compliance_summary.mandatory_unknown:
            requires_review = True
            reasons.append("Mandatory requirement could not be verified - needs human review")
            self._log_trace("Human review: Mandatory UNKNOWN")
            
        # Trigger 1.5: General UNKNOWN (logic update)
        elif compliance_summary.unknown_count > 0 and compliance_summary.overall_compliance != ComplianceLevel.COMPLIANT:
            # Keep this as a secondary check if mandatory not triggered
            requires_review = True
            reasons.append("Some requirements could not be verified automatically")
            self._log_trace("Human review: UNKNOWN requirements present")

        # Trigger 2: Borderline confidence
        if self.BORDERLINE_CONFIDENCE_LOW <= confidence_score <= self.BORDERLINE_CONFIDENCE_HIGH:
            requires_review = True
            reasons.append("Borderline confidence requires human judgment")
            self._log_trace(f"Human review: Borderline confidence ({confidence_score})")

        # Trigger 3: Multiple HIGH risks
        high_risks = [r for r in risks if r.severity == RiskSeverity.HIGH]
        if len(high_risks) > self.HIGH_RISK_COUNT_THRESHOLD:
            requires_review = True
            reasons.append(f"Multiple high-severity risks identified ({len(high_risks)})")
            self._log_trace(f"Human review: {len(high_risks)} HIGH risks")

        # Trigger 4: CONDITIONAL_BID always needs review
        if recommendation == RecommendationDecision.CONDITIONAL_BID:
            requires_review = True
            # Only add specific reason if not covered by other reasons (fuzzy match)
            if not any("condition" in r.lower() for r in reasons):
                reasons.append("Conditional recommendation requires business decision")
            self._log_trace("Human review: CONDITIONAL_BID")

        # Trigger 5: Overall WARNING
        if compliance_summary.overall_compliance == ComplianceLevel.WARNING:
            requires_review = True
            reasons.append("Warning flags require business decision")
            self._log_trace("Human review: WARNING compliance")

        return requires_review, reasons

    def generate_decision(self, compliance_summary: ComplianceSummary, risks: List[RiskItem]) -> Dict[str, Any]:
        """
        Orchestrate all decision methods to generate final decision.
        
        Args:
            compliance_summary: Summary of compliance analysis
            risks: List of identified risks
            
        Returns:
            Dictionary containing decision components
        """
        # 1. Calculate Score
        score = self.calculate_confidence_score(compliance_summary)
        
        # 2. Determine Recommendation
        rec = self.determine_recommendation(compliance_summary, score)
        
        # 3. Check for Human Review
        requires_review, reasons = self.determine_human_review(compliance_summary, score, risks, rec)
        
        return {
            "recommendation": rec,
            "confidence_score": score,
            "requires_human_review": requires_review,
            "review_reasons": reasons,
            "decision_trace": self.get_trace()
        }

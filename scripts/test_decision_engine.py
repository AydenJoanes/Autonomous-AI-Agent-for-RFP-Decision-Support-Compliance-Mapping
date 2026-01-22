"""
Phase 5 Test: Decision Engine
Tests confidence calculation, recommendation logic, human review triggers.
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
from src.app.services.decision_engine import DecisionEngine
from src.app.models.recommendation import (
    RecommendationDecision,
    ComplianceSummary,
    RiskItem,
    RiskSeverity,
    RiskCategory
)
from src.app.models.compliance import ComplianceLevel


class TestDecisionEngine(unittest.TestCase):
    """Test suite for DecisionEngine."""

    @classmethod
    def setUpClass(cls):
        cls.engine = DecisionEngine()

    def _create_summary(self, **kwargs):
        """Helper to create ComplianceSummary with defaults."""
        defaults = {
            "overall_compliance": ComplianceLevel.COMPLIANT,
            "compliant_count": 10,
            "non_compliant_count": 0,
            "partial_count": 0,
            "warning_count": 0,
            "unknown_count": 0,
            "confidence_avg": 0.9,
            "mandatory_met": True,
            "mandatory_unknown": False,
            "mandatory_failed": False,
        }
        defaults.update(kwargs)
        return ComplianceSummary(**defaults)

    # === Confidence Score Tests ===

    def test_01_confidence_all_compliant(self):
        """All COMPLIANT yields score 80+."""
        summary = self._create_summary(
            overall_compliance=ComplianceLevel.COMPLIANT,
            compliant_count=10,
            confidence_avg=0.9
        )
        score = self.engine.calculate_confidence_score(summary)
        self.assertGreaterEqual(score, 80)

    def test_02_confidence_all_partial(self):
        """All PARTIAL yields score 55-75."""
        summary = self._create_summary(
            overall_compliance=ComplianceLevel.PARTIAL,
            compliant_count=0,
            partial_count=10,
            confidence_avg=0.7
        )
        score = self.engine.calculate_confidence_score(summary)
        self.assertGreaterEqual(score, 55)
        self.assertLessEqual(score, 75)

    def test_03_confidence_with_non_compliant(self):
        """Mix with NON_COMPLIANT yields lower score."""
        summary = self._create_summary(
            overall_compliance=ComplianceLevel.PARTIAL,
            compliant_count=5,
            non_compliant_count=3,
            confidence_avg=0.6
        )
        score = self.engine.calculate_confidence_score(summary)
        self.assertLess(score, 60)

    def test_04_confidence_unknown_heavy(self):
        """UNKNOWN heavy yields score 40-55."""
        summary = self._create_summary(
            overall_compliance=ComplianceLevel.UNKNOWN,
            compliant_count=2,
            unknown_count=8,
            confidence_avg=0.5
        )
        score = self.engine.calculate_confidence_score(summary)
        self.assertGreaterEqual(score, 30)
        self.assertLessEqual(score, 60)

    def test_05_confidence_mandatory_met_bonus(self):
        """Mandatory met adds bonus."""
        summary1 = self._create_summary(mandatory_met=True)
        summary2 = self._create_summary(mandatory_met=False, mandatory_failed=True)
        
        score1 = self.engine.calculate_confidence_score(summary1)
        score2 = self.engine.calculate_confidence_score(summary2)
        
        self.assertGreater(score1, score2)

    def test_06_confidence_penalty_cap(self):
        """Penalty cap prevents extreme low scores."""
        summary = self._create_summary(
            overall_compliance=ComplianceLevel.WARNING,
            non_compliant_count=20,
            warning_count=10,
            confidence_avg=0.3
        )
        score = self.engine.calculate_confidence_score(summary)
        self.assertGreaterEqual(score, 0)

    def test_07_confidence_clamped_0_100(self):
        """Score always 0-100."""
        summary = self._create_summary(
            overall_compliance=ComplianceLevel.COMPLIANT,
            confidence_avg=1.0
        )
        score = self.engine.calculate_confidence_score(summary)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    # === Recommendation Decision Tests ===

    def test_08_decision_high_confidence_compliant_bid(self):
        """High confidence + COMPLIANT = BID."""
        summary = self._create_summary(
            overall_compliance=ComplianceLevel.COMPLIANT,
            confidence_avg=0.9
        )
        score = self.engine.calculate_confidence_score(summary)
        decision = self.engine.determine_recommendation(summary, score)
        self.assertEqual(decision, RecommendationDecision.BID)

    def test_09_decision_medium_confidence_conditional(self):
        """Medium confidence = CONDITIONAL_BID."""
        summary = self._create_summary(
            overall_compliance=ComplianceLevel.PARTIAL,
            compliant_count=5,
            partial_count=5,
            confidence_avg=0.65
        )
        score = 60  # Force medium confidence
        decision = self.engine.determine_recommendation(summary, score)
        self.assertEqual(decision, RecommendationDecision.CONDITIONAL_BID)

    def test_10_decision_low_confidence_no_bid(self):
        """Low confidence = NO_BID."""
        summary = self._create_summary(
            overall_compliance=ComplianceLevel.PARTIAL,
            confidence_avg=0.4
        )
        score = 40  # Force low confidence
        decision = self.engine.determine_recommendation(summary, score)
        self.assertEqual(decision, RecommendationDecision.NO_BID)

    def test_11_decision_mandatory_failed_no_bid(self):
        """Mandatory failed = NO_BID regardless of score."""
        summary = self._create_summary(
            mandatory_met=False,
            mandatory_failed=True
        )
        score = 90  # High score but mandatory failed
        decision = self.engine.determine_recommendation(summary, score)
        self.assertEqual(decision, RecommendationDecision.NO_BID)

    def test_12_decision_mandatory_unknown_conditional(self):
        """Mandatory UNKNOWN = CONDITIONAL_BID."""
        summary = self._create_summary(
            mandatory_met=True,
            mandatory_unknown=True,
            mandatory_failed=False
        )
        score = 80
        decision = self.engine.determine_recommendation(summary, score)
        self.assertEqual(decision, RecommendationDecision.CONDITIONAL_BID)

    def test_13_decision_overall_non_compliant_no_bid(self):
        """Overall NON_COMPLIANT = NO_BID."""
        summary = self._create_summary(
            overall_compliance=ComplianceLevel.NON_COMPLIANT,
            non_compliant_count=5
        )
        score = 70
        decision = self.engine.determine_recommendation(summary, score)
        self.assertEqual(decision, RecommendationDecision.NO_BID)

    def test_14_decision_unknown_alone_not_no_bid(self):
        """UNKNOWN alone never triggers NO_BID."""
        summary = self._create_summary(
            overall_compliance=ComplianceLevel.UNKNOWN,
            compliant_count=0,
            unknown_count=10,
            non_compliant_count=0,
            mandatory_met=True,
            mandatory_unknown=False,
            mandatory_failed=False,
            confidence_avg=0.5
        )
        score = 55
        decision = self.engine.determine_recommendation(summary, score)
        self.assertNotEqual(decision, RecommendationDecision.NO_BID)

    # === Human Review Tests ===

    def test_15_review_borderline_confidence(self):
        """Borderline confidence triggers review."""
        summary = self._create_summary()
        score = 50
        risks = []
        decision = RecommendationDecision.CONDITIONAL_BID
        
        requires, reasons = self.engine.determine_human_review(
            summary, score, risks, decision
        )
        self.assertTrue(requires)

    def test_16_review_multiple_high_risks(self):
        """Multiple HIGH risks trigger review."""
        summary = self._create_summary()
        score = 80
        risks = [
            RiskItem(category=RiskCategory.TECHNICAL, severity=RiskSeverity.HIGH,
                    description="Risk 1", source_tool="test"),
            RiskItem(category=RiskCategory.BUDGET, severity=RiskSeverity.HIGH,
                    description="Risk 2", source_tool="test"),
            RiskItem(category=RiskCategory.TIMELINE, severity=RiskSeverity.HIGH,
                    description="Risk 3", source_tool="test"),
        ]
        decision = RecommendationDecision.BID
        
        requires, reasons = self.engine.determine_human_review(
            summary, score, risks, decision
        )
        self.assertTrue(requires)

    def test_17_review_conditional_always_review(self):
        """CONDITIONAL_BID always requires review."""
        summary = self._create_summary()
        score = 65
        risks = []
        decision = RecommendationDecision.CONDITIONAL_BID
        
        requires, reasons = self.engine.determine_human_review(
            summary, score, risks, decision
        )
        self.assertTrue(requires)

    def test_18_review_reasons_populated(self):
        """Review reasons list populated."""
        summary = self._create_summary(mandatory_unknown=True)
        score = 50
        risks = []
        decision = RecommendationDecision.CONDITIONAL_BID
        
        requires, reasons = self.engine.determine_human_review(
            summary, score, risks, decision
        )
        self.assertTrue(len(reasons) > 0)

    # === Decision Trace Tests ===

    def test_19_trace_captures_base_score(self):
        """Trace captures base score."""
        summary = self._create_summary()
        self.engine.calculate_confidence_score(summary)
        trace = self.engine.get_trace()
        
        trace_text = " ".join(trace)
        self.assertIn("Base score", trace_text)

    def test_20_trace_captures_final_decision(self):
        """Trace captures final decision."""
        summary = self._create_summary()
        score = self.engine.calculate_confidence_score(summary)
        self.engine.determine_recommendation(summary, score)
        trace = self.engine.get_trace()
        
        trace_text = " ".join(trace)
        self.assertIn("Decision", trace_text)


def run_tests():
    """Run tests and save output."""
    output_dir = Path("data/test_output/logs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = output_dir / f"test_decision_{timestamp}.log"
    
    with open(log_file, 'w', encoding='utf-8') as f:
        runner = unittest.TextTestRunner(stream=f, verbosity=2)
        suite = unittest.TestLoader().loadTestsFromTestCase(TestDecisionEngine)
        result = runner.run(suite)
    
    print(f"\n{'='*60}")
    print("DECISION ENGINE TEST RESULTS")
    print(f"{'='*60}")
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Log saved: {log_file}")
    print(f"{'='*60}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

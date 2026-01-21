import sys
import os
import unittest

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.app.services.decision_config import (
    CONFIDENCE_BASE_SCORES,
    MANDATORY_MET_BONUS,
    MANDATORY_FAILED_PENALTY,
    CONFIDENCE_AVG_MULTIPLIER,
    CONFIDENCE_AVG_BASELINE,
    NON_COMPLIANT_PENALTY,
    WARNING_PENALTY,
    UNKNOWN_PENALTY,
    MAX_PENALTY_CAP,
    BID_CONFIDENCE_THRESHOLD,
    CONDITIONAL_CONFIDENCE_THRESHOLD,
    UNKNOWN_HEAVY_THRESHOLD,
    BORDERLINE_CONFIDENCE_LOW,
    BORDERLINE_CONFIDENCE_HIGH,
    HIGH_RISK_COUNT_THRESHOLD,
    JUSTIFICATION_MODEL,
    JUSTIFICATION_TEMPERATURE,
    MAX_RETRIES,
    RETRY_BASE_DELAY
)
from src.app.models.compliance import ComplianceLevel

class TestPhase5Config(unittest.TestCase):

    def test_2_1_confidence_base_scores(self):
        """Verify CONFIDENCE_BASE_SCORES dict"""
        self.assertIsInstance(CONFIDENCE_BASE_SCORES, dict)
        self.assertEqual(len(CONFIDENCE_BASE_SCORES), 5)
        for level in ComplianceLevel:
            self.assertIn(level, CONFIDENCE_BASE_SCORES)
            score = CONFIDENCE_BASE_SCORES[level]
            self.assertTrue(0 <= score <= 100)

    def test_2_2_adjustment_constants(self):
        """Verify Adjustment Constants"""
        self.assertEqual(MANDATORY_MET_BONUS, 10)
        self.assertEqual(MANDATORY_FAILED_PENALTY, 15)
        self.assertEqual(CONFIDENCE_AVG_MULTIPLIER, 20)
        self.assertEqual(CONFIDENCE_AVG_BASELINE, 0.7)

    def test_2_3_penalty_constants(self):
        """Verify Penalty Constants"""
        self.assertEqual(NON_COMPLIANT_PENALTY, 5)
        self.assertEqual(WARNING_PENALTY, 2)
        self.assertEqual(UNKNOWN_PENALTY, 3)
        self.assertEqual(MAX_PENALTY_CAP, 40)

    def test_2_4_threshold_constants(self):
        """Verify Threshold Constants"""
        self.assertEqual(BID_CONFIDENCE_THRESHOLD, 75)
        self.assertEqual(CONDITIONAL_CONFIDENCE_THRESHOLD, 50)
        self.assertEqual(UNKNOWN_HEAVY_THRESHOLD, 0.5)

    def test_2_5_human_review_constants(self):
        """Verify Human Review Constants"""
        self.assertEqual(BORDERLINE_CONFIDENCE_LOW, 40)
        self.assertEqual(BORDERLINE_CONFIDENCE_HIGH, 60)
        self.assertEqual(HIGH_RISK_COUNT_THRESHOLD, 2)

    def test_2_6_llm_configuration(self):
        """Verify LLM Configuration"""
        self.assertTrue(isinstance(JUSTIFICATION_MODEL, str))
        self.assertTrue(len(JUSTIFICATION_MODEL) > 0)
        self.assertTrue(0 <= JUSTIFICATION_TEMPERATURE <= 1)
        self.assertTrue(MAX_RETRIES > 0)
        self.assertTrue(RETRY_BASE_DELAY > 0)

if __name__ == "__main__":
    print("Config Test Results:")
    unittest.main(verbosity=2)

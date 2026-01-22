"""
Phase 5 Test: Justification Generator
Tests LLM justification and fallback logic.
"""

import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
from src.app.services.justification_generator import JustificationGenerator
from src.app.models.recommendation import (
    RecommendationDecision,
    ComplianceSummary,
    RiskItem,
    RiskSeverity,
    RiskCategory
)
from src.app.models.compliance import ComplianceLevel


class TestJustificationGenerator(unittest.TestCase):
    """Test suite for JustificationGenerator."""

    @classmethod
    def setUpClass(cls):
        cls.generator = JustificationGenerator()
        cls.sample_summary = ComplianceSummary(
            overall_compliance=ComplianceLevel.PARTIAL,
            compliant_count=5,
            partial_count=2,
            non_compliant_count=1,
            warning_count=1,
            unknown_count=1,
            confidence_avg=0.72,
            mandatory_met=True
        )
        cls.sample_decision = {
            "recommendation": RecommendationDecision.CONDITIONAL_BID,
            "confidence_score": 67,
            "decision_trace": ["Base: 60", "Mandatory: +10", "Penalties: -3"]
        }
        cls.sample_risks = [
            RiskItem(
                category=RiskCategory.TIMELINE,
                severity=RiskSeverity.MEDIUM,
                description="Timeline aggressive",
                source_tool="timeline_assessor"
            )
        ]

    def test_01_context_prompt_built(self):
        """Context prompt is built correctly."""
        prompt = self.generator._build_context_prompt(
            self.sample_summary,
            self.sample_decision,
            self.sample_risks
        )
        self.assertIsInstance(prompt, str)
        self.assertGreater(len(prompt), 100)

    def test_02_context_contains_compliance(self):
        """Context contains compliance level."""
        prompt = self.generator._build_context_prompt(
            self.sample_summary,
            self.sample_decision,
            self.sample_risks
        )
        self.assertIn("PARTIAL", prompt.upper())

    def test_03_context_contains_confidence(self):
        """Context contains confidence score."""
        prompt = self.generator._build_context_prompt(
            self.sample_summary,
            self.sample_decision,
            self.sample_risks
        )
        self.assertIn("67", prompt)

    def test_04_fallback_justification_valid(self):
        """Fallback justification meets minimum length."""
        fallback = self.generator._generate_fallback_justification(
            self.sample_summary,
            RecommendationDecision.BID,
            80
        )
        self.assertGreaterEqual(len(fallback), 50)

    def test_05_fallback_summary_valid(self):
        """Fallback summary meets minimum length."""
        fallback = self.generator._generate_fallback_summary(
            RecommendationDecision.BID,
            80,
            self.sample_summary,
            self.sample_risks
        )
        self.assertGreaterEqual(len(fallback), 20)

    @patch.object(JustificationGenerator, '_generate_with_retry')
    def test_06_fallback_on_llm_failure(self, mock_retry):
        """Fallback used when LLM fails."""
        mock_retry.return_value = None
        
        justification, summary = self.generator.generate(
            self.sample_summary,
            self.sample_decision,
            self.sample_risks
        )
        
        self.assertGreaterEqual(len(justification), 50)
        self.assertGreaterEqual(len(summary), 20)

    @patch.object(JustificationGenerator, '_generate_with_retry')
    def test_07_llm_response_accepted(self, mock_retry):
        """Valid LLM response is accepted."""
        mock_retry.return_value = "A" * 100
        
        justification, summary = self.generator.generate(
            self.sample_summary,
            self.sample_decision,
            self.sample_risks
        )
        
        self.assertIsInstance(justification, str)
        self.assertIsInstance(summary, str)

    def test_08_generate_returns_tuple(self):
        """Generate returns (justification, summary) tuple."""
        with patch.object(self.generator, '_generate_with_retry', return_value="A" * 100):
            result = self.generator.generate(
                self.sample_summary,
                self.sample_decision,
                self.sample_risks
            )
        
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)


def run_tests():
    """Run tests and save output."""
    output_dir = Path("data/test_output/logs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = output_dir / f"test_justification_{timestamp}.log"
    
    with open(log_file, 'w', encoding='utf-8') as f:
        runner = unittest.TextTestRunner(stream=f, verbosity=2)
        suite = unittest.TestLoader().loadTestsFromTestCase(TestJustificationGenerator)
        result = runner.run(suite)
    
    print(f"\n{'='*60}")
    print("JUSTIFICATION GENERATOR TEST RESULTS")
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

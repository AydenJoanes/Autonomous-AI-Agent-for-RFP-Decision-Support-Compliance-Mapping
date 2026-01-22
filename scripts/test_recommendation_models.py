"""
Phase 5 Test: Recommendation Models
Tests all Pydantic models for validation and constraints.
"""

import sys
import os
import json
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
from pydantic import ValidationError

from src.app.models.recommendation import (
    RecommendationDecision,
    RiskSeverity,
    RiskCategory,
    RiskItem,
    ToolResultSummary,
    ComplianceSummary,
    RFPMetadata,
    Recommendation
)
from src.app.models.compliance import ComplianceLevel


class TestRecommendationModels(unittest.TestCase):
    """Test suite for recommendation models."""

    def test_01_recommendation_decision_enum_values(self):
        """RecommendationDecision enum has exactly 3 values."""
        values = [e.value for e in RecommendationDecision]
        self.assertEqual(len(values), 3)
        self.assertIn("BID", values)
        self.assertIn("NO_BID", values)
        self.assertIn("CONDITIONAL_BID", values)

    def test_02_risk_severity_enum_values(self):
        """RiskSeverity enum has exactly 3 values."""
        values = [e.value for e in RiskSeverity]
        self.assertEqual(len(values), 3)
        self.assertIn("HIGH", values)
        self.assertIn("MEDIUM", values)
        self.assertIn("LOW", values)

    def test_03_risk_category_enum_values(self):
        """RiskCategory enum has exactly 6 values."""
        values = [e.value for e in RiskCategory]
        self.assertEqual(len(values), 6)
        expected = ["timeline", "budget", "technical", "compliance", "strategic", "resource"]
        for exp in expected:
            self.assertIn(exp, values)

    def test_04_risk_item_valid_creation(self):
        """RiskItem accepts valid data."""
        risk = RiskItem(
            category=RiskCategory.TECHNICAL,
            severity=RiskSeverity.HIGH,
            description="Test risk description",
            source_tool="test_tool"
        )
        self.assertEqual(risk.category, "technical")
        self.assertEqual(risk.severity, "HIGH")

    def test_05_risk_item_rejects_missing_category(self):
        """RiskItem rejects missing category."""
        with self.assertRaises(ValidationError):
            RiskItem(
                severity=RiskSeverity.HIGH,
                description="Test",
                source_tool="test"
            )

    def test_06_risk_item_rejects_missing_severity(self):
        """RiskItem rejects missing severity."""
        with self.assertRaises(ValidationError):
            RiskItem(
                category=RiskCategory.TECHNICAL,
                description="Test",
                source_tool="test"
            )

    def test_07_tool_result_summary_valid(self):
        """ToolResultSummary accepts valid data."""
        summary = ToolResultSummary(
            tool_name="test_tool",
            requirement="Test requirement",
            compliance_level=ComplianceLevel.COMPLIANT,
            confidence=0.95,
            status="VALID"
        )
        self.assertEqual(summary.confidence, 0.95)

    def test_08_tool_result_summary_truncates_long_requirement(self):
        """ToolResultSummary truncates requirements over 100 chars."""
        long_req = "A" * 150
        summary = ToolResultSummary(
            tool_name="test",
            requirement=long_req,
            compliance_level=ComplianceLevel.COMPLIANT,
            confidence=0.9,
            status="OK"
        )
        self.assertEqual(len(summary.requirement), 100)
        self.assertTrue(summary.requirement.endswith("..."))

    def test_09_compliance_summary_valid(self):
        """ComplianceSummary accepts valid data."""
        summary = ComplianceSummary(
            overall_compliance=ComplianceLevel.PARTIAL,
            compliant_count=5,
            partial_count=2,
            non_compliant_count=1,
            warning_count=1,
            unknown_count=1,
            confidence_avg=0.75,
            mandatory_met=True
        )
        self.assertEqual(summary.total_evaluated, 10)

    def test_10_compliance_summary_auto_calculates_total(self):
        """ComplianceSummary auto-calculates total_evaluated."""
        summary = ComplianceSummary(
            overall_compliance=ComplianceLevel.COMPLIANT,
            compliant_count=3,
            partial_count=2,
            non_compliant_count=0,
            warning_count=0,
            unknown_count=0,
            confidence_avg=0.9,
            mandatory_met=True
        )
        self.assertEqual(summary.total_evaluated, 5)

    def test_11_rfp_metadata_valid(self):
        """RFPMetadata accepts valid data."""
        metadata = RFPMetadata(
            filename="test.pdf",
            file_path="/path/to/test.pdf",
            word_count=1000,
            requirement_count=10
        )
        self.assertIsNotNone(metadata.processed_date)

    def test_12_recommendation_valid(self):
        """Recommendation accepts valid data."""
        rec = Recommendation(
            recommendation=RecommendationDecision.BID,
            confidence_score=85,
            justification="A" * 60,
            executive_summary="B" * 25,
            compliance_summary=ComplianceSummary(
                overall_compliance=ComplianceLevel.COMPLIANT,
                compliant_count=5,
                confidence_avg=0.9,
                mandatory_met=True
            ),
            requires_human_review=False,
            rfp_metadata=RFPMetadata(
                filename="test.pdf",
                file_path="/test.pdf"
            )
        )
        self.assertEqual(rec.confidence_score, 85)

    def test_13_recommendation_rejects_confidence_over_100(self):
        """Recommendation rejects confidence > 100."""
        with self.assertRaises(ValidationError):
            Recommendation(
                recommendation=RecommendationDecision.BID,
                confidence_score=150,
                justification="A" * 60,
                executive_summary="B" * 25,
                compliance_summary=ComplianceSummary(
                    overall_compliance=ComplianceLevel.COMPLIANT,
                    confidence_avg=0.9,
                    mandatory_met=True
                ),
                requires_human_review=False,
                rfp_metadata=RFPMetadata(filename="t.pdf", file_path="/t.pdf")
            )

    def test_14_recommendation_rejects_confidence_negative(self):
        """Recommendation rejects confidence < 0."""
        with self.assertRaises(ValidationError):
            Recommendation(
                recommendation=RecommendationDecision.BID,
                confidence_score=-10,
                justification="A" * 60,
                executive_summary="B" * 25,
                compliance_summary=ComplianceSummary(
                    overall_compliance=ComplianceLevel.COMPLIANT,
                    confidence_avg=0.9,
                    mandatory_met=True
                ),
                requires_human_review=False,
                rfp_metadata=RFPMetadata(filename="t.pdf", file_path="/t.pdf")
            )

    def test_15_recommendation_rejects_short_justification(self):
        """Recommendation rejects justification < 50 chars."""
        with self.assertRaises(ValidationError):
            Recommendation(
                recommendation=RecommendationDecision.BID,
                confidence_score=80,
                justification="Too short",
                executive_summary="B" * 25,
                compliance_summary=ComplianceSummary(
                    overall_compliance=ComplianceLevel.COMPLIANT,
                    confidence_avg=0.9,
                    mandatory_met=True
                ),
                requires_human_review=False,
                rfp_metadata=RFPMetadata(filename="t.pdf", file_path="/t.pdf")
            )

    def test_16_recommendation_auto_generates_timestamp(self):
        """Recommendation auto-generates timestamp."""
        rec = Recommendation(
            recommendation=RecommendationDecision.BID,
            confidence_score=80,
            justification="A" * 60,
            executive_summary="B" * 25,
            compliance_summary=ComplianceSummary(
                overall_compliance=ComplianceLevel.COMPLIANT,
                confidence_avg=0.9,
                mandatory_met=True
            ),
            requires_human_review=False,
            rfp_metadata=RFPMetadata(filename="t.pdf", file_path="/t.pdf")
        )
        self.assertIsNotNone(rec.timestamp)

    def test_17_compliance_summary_mandatory_unknown_field(self):
        """ComplianceSummary has mandatory_unknown field."""
        summary = ComplianceSummary(
            overall_compliance=ComplianceLevel.UNKNOWN,
            confidence_avg=0.5,
            mandatory_met=True,
            mandatory_unknown=True,
            mandatory_failed=False
        )
        self.assertTrue(summary.mandatory_unknown)
        self.assertFalse(summary.mandatory_failed)


def run_tests():
    """Run tests and save output."""
    # Create output directory
    output_dir = Path("data/test_output/logs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = output_dir / f"test_models_{timestamp}.log"
    
    # Run tests with output capture
    with open(log_file, 'w', encoding='utf-8') as f:
        runner = unittest.TextTestRunner(stream=f, verbosity=2)
        suite = unittest.TestLoader().loadTestsFromTestCase(TestRecommendationModels)
        result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print("MODELS TEST RESULTS")
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

import sys
import os
import unittest
from pydantic import ValidationError

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.app.models.recommendation import (
    RecommendationDecision, RiskSeverity, RiskCategory, RiskItem,
    ToolResultSummary, ComplianceSummary, RFPMetadata, Recommendation
)
from src.app.models.compliance import ComplianceLevel

class TestPhase5Models(unittest.TestCase):
    
    def test_1_1_recommendation_decision_enum(self):
        """Verify RecommendationDecision Enum"""
        self.assertEqual(len(RecommendationDecision), 3)
        self.assertEqual(RecommendationDecision.BID.value, "BID")
        self.assertEqual(RecommendationDecision.NO_BID.value, "NO_BID")
        self.assertEqual(RecommendationDecision.CONDITIONAL_BID.value, "CONDITIONAL_BID")

    def test_1_2_risk_severity_enum(self):
        """Verify RiskSeverity Enum"""
        self.assertEqual(len(RiskSeverity), 3)
        self.assertIn("HIGH", [e.value for e in RiskSeverity])
        self.assertIn("MEDIUM", [e.value for e in RiskSeverity])
        self.assertIn("LOW", [e.value for e in RiskSeverity])

    def test_1_3_risk_category_enum(self):
        """Verify RiskCategory Enum"""
        self.assertEqual(len(RiskCategory), 6)

    def test_1_4_risk_item_model(self):
        """Verify RiskItem Model"""
        # Valid creation
        risk = RiskItem(
            category=RiskCategory.BUDGET,
            severity=RiskSeverity.HIGH,
            description="Test Risk",
            source_tool="budget_checker"
        )
        self.assertEqual(risk.category, RiskCategory.BUDGET)
        
        # Missing category
        with self.assertRaises(ValidationError):
            RiskItem(
                severity=RiskSeverity.HIGH,
                description="Test Risk",
                source_tool="budget_checker"
            )

        # Missing severity
        with self.assertRaises(ValidationError):
            RiskItem(
                category=RiskCategory.BUDGET,
                description="Test Risk",
                source_tool="budget_checker"
            )

        # Invalid category string (Pydantic might coerce if valid string, but here we test invalid)
        with self.assertRaises(ValidationError):
             RiskItem(
                category="INVALID_CATEGORY",
                severity=RiskSeverity.HIGH,
                description="Test Risk",
                source_tool="budget_checker"
            )

    def test_1_5_tool_result_summary_model(self):
        """Verify ToolResultSummary Model"""
        # Valid creation
        summary = ToolResultSummary(
            tool_name="test_tool",
            requirement="Short req",
            compliance_level=ComplianceLevel.COMPLIANT,
            confidence=0.9,
            status="OK"
        )
        self.assertEqual(summary.requirement, "Short req")

        # Truncation
        long_req = "a" * 150
        summary_long = ToolResultSummary(
            tool_name="test_tool",
            requirement=long_req,
            compliance_level=ComplianceLevel.COMPLIANT,
            confidence=0.9,
            status="OK"
        )
        self.assertTrue(summary_long.requirement.endswith("..."))
        self.assertLessEqual(len(summary_long.requirement), 100)

        # Confidence validation
        with self.assertRaises(ValidationError):
            ToolResultSummary(
                tool_name="test_tool",
                requirement="req",
                compliance_level=ComplianceLevel.COMPLIANT,
                confidence=1.5,
                status="OK"
            )

    def test_1_6_compliance_summary_model(self):
        """Verify ComplianceSummary Model"""
        # Valid creation
        summary = ComplianceSummary(
            overall_compliance=ComplianceLevel.COMPLIANT,
            compliant_count=5,
            non_compliant_count=2,
            total_evaluated=7 # Matching sum
        )
        self.assertEqual(summary.total_evaluated, 7)

        # Auto-calculate total
        summary_auto = ComplianceSummary(
            overall_compliance=ComplianceLevel.COMPLIANT,
            compliant_count=5,
            non_compliant_count=5,
            total_evaluated=0 # Mismatch, should auto-correct or be validated in logic if validator forces it
        )
        # The validator provided in description says "Verify total_evaluated auto-calculates from counts"
        # Let's check if the logic does that. The logic in recommendation.py:92 corrects it if >0 but mismatch. 
        # If passed 0, it might just return expected sum if the logic allows. 
        # The implementation logic I saw: if v != expected and expected > 0: return expected.
        # So providing 0 might NOT trigger it if v==0 and expected>0? No, v != expected (0 != 10) is true.
        self.assertEqual(summary_auto.total_evaluated, 10)

        # Confidence average
        with self.assertRaises(ValidationError):
             ComplianceSummary(
                overall_compliance=ComplianceLevel.COMPLIANT,
                confidence_avg=1.1
            )

    def test_1_7_rfp_metadata_model(self):
        """Verify RFPMetadata Model"""
        meta = RFPMetadata(
            filename="test.pdf",
            file_path="/tmp/test.pdf"
        )
        self.assertIsNotNone(meta.processed_date)
        self.assertEqual(meta.word_count, 0)

    def test_1_8_recommendation_model(self):
        """Verify Recommendation Model"""
        valid_summary = ComplianceSummary(overall_compliance=ComplianceLevel.COMPLIANT)
        valid_meta = RFPMetadata(filename="t.pdf", file_path="p")
        
        # Valid
        rec = Recommendation(
            recommendation=RecommendationDecision.BID,
            confidence_score=80,
            justification="This is a very long justification that definitely exceeds the fifty character limit required by the model validator.",
            executive_summary="This is a summary that is long enough.",
            compliance_summary=valid_summary,
            requires_human_review=False,
            rfp_metadata=valid_meta
        )
        self.assertIsNotNone(rec.timestamp)

        # Invalid confidence
        with self.assertRaises(ValidationError):
            Recommendation(
                recommendation=RecommendationDecision.BID,
                confidence_score=150,
                justification="This is a very long justification that definitely exceeds the fifty character limit required by the model validator.",
                executive_summary="This is a summary that is long enough.",
                compliance_summary=valid_summary,
                requires_human_review=False,
                rfp_metadata=valid_meta
            )
        
        # Short justification
        with self.assertRaises(ValidationError):
             Recommendation(
                recommendation=RecommendationDecision.BID,
                confidence_score=80,
                justification="Too short",
                executive_summary="This is a summary that is long enough.",
                compliance_summary=valid_summary,
                requires_human_review=False,
                rfp_metadata=valid_meta
            )

if __name__ == "__main__":
    print("Models Test Results:")
    unittest.main(verbosity=2)

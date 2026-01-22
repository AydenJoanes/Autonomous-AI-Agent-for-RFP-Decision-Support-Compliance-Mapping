"""
Phase 5 Test: Recommendation Service
Tests service orchestration and error handling.
"""

import sys
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
from src.app.services.recommendation_service import RecommendationService
from src.app.models.recommendation import Recommendation, RecommendationDecision


class TestRecommendationService(unittest.TestCase):
    """Test suite for RecommendationService."""

    @classmethod
    def setUpClass(cls):
        cls.service = RecommendationService()
        cls.test_dir = Path("data/test_output/samples")
        cls.test_dir.mkdir(parents=True, exist_ok=True)

    def test_01_service_initializes(self):
        """Service initializes with all dependencies."""
        self.assertIsNotNone(self.service._tool_executor)
        self.assertIsNotNone(self.service._decision_engine)
        self.assertIsNotNone(self.service._justification_generator)

    def test_02_process_rfp_missing_file(self):
        """process_rfp raises FileNotFoundError for missing file."""
        with self.assertRaises(FileNotFoundError):
            self.service.process_rfp("/nonexistent/file.pdf")

    def test_03_process_rfp_unsupported_extension(self):
        """process_rfp raises ValueError for unsupported extension."""
        # Create temp file with wrong extension
        temp_file = self.test_dir / "test.xyz"
        temp_file.touch()
        
        try:
            with self.assertRaises(ValueError):
                self.service.process_rfp(str(temp_file))
        finally:
            temp_file.unlink()

    @patch.object(RecommendationService, 'process_rfp')
    @patch.object(RecommendationService, 'analyze_requirements')
    def test_04_generate_recommendation_returns_valid(self, mock_analyze, mock_process):
        """generate_recommendation returns valid Recommendation."""
        from src.app.models.compliance import ComplianceLevel
        from src.app.models.recommendation import ComplianceSummary, RFPMetadata
        
        # Setup mocks
        mock_process.return_value = (
            "Test content",
            [MagicMock(text="Test req", embedding=[0.1]*1536)],
            RFPMetadata(filename="test.pdf", file_path="/test.pdf")
        )
        mock_analyze.return_value = (
            [],
            ComplianceSummary(
                overall_compliance=ComplianceLevel.COMPLIANT,
                compliant_count=1,
                confidence_avg=0.9,
                mandatory_met=True
            )
        )
        
        with patch.object(self.service._tool_executor, 'extract_risks_from_results', return_value=[]):
            with patch.object(self.service._justification_generator, 'generate', return_value=("A"*60, "B"*25)):
                result = self.service.generate_recommendation("/fake/path.pdf")
        
        self.assertIsInstance(result, Recommendation)

    def test_05_create_error_recommendation(self):
        """_create_error_recommendation returns NO_BID."""
        result = self.service._create_error_recommendation("/test.pdf", "Test error")
        
        self.assertEqual(result.recommendation, RecommendationDecision.NO_BID)
        self.assertEqual(result.confidence_score, 0)
        self.assertTrue(result.requires_human_review)

    def test_06_create_no_requirements_recommendation(self):
        """_create_no_requirements_recommendation returns CONDITIONAL_BID."""
        from src.app.models.recommendation import RFPMetadata
        
        metadata = RFPMetadata(filename="test.pdf", file_path="/test.pdf")
        result = self.service._create_no_requirements_recommendation(metadata)
        
        self.assertEqual(result.recommendation, RecommendationDecision.CONDITIONAL_BID)
        self.assertEqual(result.confidence_score, 30)
        self.assertTrue(result.requires_human_review)

    def test_07_generate_report_produces_markdown(self):
        """generate_recommendation_report produces markdown."""
        from src.app.models.recommendation import RFPMetadata, ComplianceSummary
        from src.app.models.compliance import ComplianceLevel
        
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
            rfp_metadata=RFPMetadata(filename="test.pdf", file_path="/test.pdf")
        )
        
        report = self.service.generate_recommendation_report(rec)
        
        self.assertIn("# RFP Bid Recommendation Report", report)
        self.assertIn("Executive Summary", report)
        self.assertIn("Compliance Summary", report)

    def test_08_report_saved_to_file(self):
        """Report can be saved to file."""
        from src.app.models.recommendation import RFPMetadata, ComplianceSummary
        from src.app.models.compliance import ComplianceLevel
        
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
            rfp_metadata=RFPMetadata(filename="test.pdf", file_path="/test.pdf")
        )
        
        report = self.service.generate_recommendation_report(rec)
        report_file = self.test_dir / "sample_report.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        self.assertTrue(report_file.exists())


def run_tests():
    """Run tests and save output."""
    output_dir = Path("data/test_output/logs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = output_dir / f"test_service_{timestamp}.log"
    
    with open(log_file, 'w', encoding='utf-8') as f:
        runner = unittest.TextTestRunner(stream=f, verbosity=2)
        suite = unittest.TestLoader().loadTestsFromTestCase(TestRecommendationService)
        result = runner.run(suite)
    
    print(f"\n{'='*60}")
    print("RECOMMENDATION SERVICE TEST RESULTS")
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

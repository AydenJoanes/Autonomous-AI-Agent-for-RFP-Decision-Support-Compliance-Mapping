"""
Phase 5 Test: Integration Tests
End-to-end tests with sample RFP.
"""

import sys
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
from src.app.agent.recommendation_agent import RecommendationAgent
from src.app.models.recommendation import Recommendation, RecommendationDecision


class TestPhase5Integration(unittest.TestCase):
    """Integration test suite for Phase 5."""

    @classmethod
    def setUpClass(cls):
        cls.output_dir = Path("data/test_output")
        cls.output_dir.mkdir(parents=True, exist_ok=True)
        (cls.output_dir / "logs").mkdir(exist_ok=True)
        (cls.output_dir / "samples").mkdir(exist_ok=True)
        
        # Create dummy test RFP if not exists
        cls.test_rfp = Path("data/sample_rfps/dummy_test.pdf")
        cls.test_rfp.parent.mkdir(parents=True, exist_ok=True)

    def test_01_agent_initializes(self):
        """Agent initializes successfully."""
        agent = RecommendationAgent()
        self.assertIsNotNone(agent._service)

    def test_02_agent_health_check(self):
        """Agent health check returns valid response."""
        agent = RecommendationAgent()
        health = agent.health_check()
        
        self.assertEqual(health["status"], "ok")
        self.assertEqual(health["tools_available"], 6)
        self.assertTrue(health["service_ready"])

    @patch('src.app.agent.tools.RFPParserTool._run')
    @patch('src.app.agent.tools.RequirementProcessorTool._run')
    def test_03_full_pipeline_mocked(self, mock_processor, mock_parser):
        """Full pipeline with mocked external calls."""
        # Setup mocks
        mock_parser.return_value = "Budget: $150,000\nMust use Python"
        mock_processor.return_value = [
            MagicMock(text="Budget: $150,000", embedding=None, type="BUDGET"),
            MagicMock(text="Must use Python", embedding=None, type="TECHNICAL")
        ]
        
        agent = RecommendationAgent()
        
        # Run with mocked LLM
        with patch.object(agent._service._justification_generator, 'generate', 
                         return_value=("A"*60, "B"*25)):
            recommendation, report = agent.run_with_report(str(self.test_rfp))
        
        # Verify recommendation
        self.assertIsInstance(recommendation, Recommendation)
        self.assertIn(recommendation.recommendation, 
                     [RecommendationDecision.BID, RecommendationDecision.NO_BID, 
                      RecommendationDecision.CONDITIONAL_BID])
        
        # Verify report
        self.assertIn("# RFP Bid Recommendation Report", report)
        
        # Save outputs
        self._save_outputs(recommendation, report)

    def test_04_recommendation_fields_populated(self):
        """All Recommendation fields are populated."""
        agent = RecommendationAgent()
        
        with patch.object(agent._service, 'generate_recommendation') as mock:
            from src.app.models.recommendation import RFPMetadata, ComplianceSummary
            from src.app.models.compliance import ComplianceLevel
            
            mock.return_value = Recommendation(
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
            
            rec = agent.run("/fake.pdf")
        
        # Check all required fields
        self.assertIsNotNone(rec.recommendation)
        self.assertIsNotNone(rec.confidence_score)
        self.assertIsNotNone(rec.justification)
        self.assertIsNotNone(rec.executive_summary)
        self.assertIsNotNone(rec.compliance_summary)
        self.assertIsNotNone(rec.rfp_metadata)
        self.assertIsNotNone(rec.timestamp)

    def test_05_api_health_endpoint(self):
        """API health endpoint accessible."""
        try:
            from fastapi.testclient import TestClient
            from src.app.main import app
            
            client = TestClient(app)
            response = client.get("/api/v1/recommendation/health")
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["status"], "ok")
        except ImportError:
            self.skipTest("FastAPI TestClient not available")

    def _save_outputs(self, recommendation: Recommendation, report: str):
        """Save test outputs for debugging."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save recommendation JSON
        rec_file = self.output_dir / "samples" / f"recommendation_{timestamp}.json"
        with open(rec_file, 'w', encoding='utf-8') as f:
            json.dump(recommendation.model_dump(), f, indent=2, default=str)
        
        # Save report markdown
        report_file = self.output_dir / "samples" / f"report_{timestamp}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n[OUTPUT] Recommendation saved: {rec_file}")
        print(f"[OUTPUT] Report saved: {report_file}")


def run_tests():
    """Run tests and save output."""
    output_dir = Path("data/test_output/logs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = output_dir / f"test_integration_{timestamp}.log"
    
    with open(log_file, 'w', encoding='utf-8') as f:
        runner = unittest.TextTestRunner(stream=f, verbosity=2)
        suite = unittest.TestLoader().loadTestsFromTestCase(TestPhase5Integration)
        result = runner.run(suite)
    
    print(f"\n{'='*60}")
    print("INTEGRATION TEST RESULTS")
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

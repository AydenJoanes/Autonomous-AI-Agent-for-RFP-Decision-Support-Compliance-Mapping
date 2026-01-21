import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.app.services.justification_generator import JustificationGenerator
from src.app.models.recommendation import RecommendationDecision, RiskCategory, RiskSeverity, RiskItem

class TestPhase5Justification(unittest.TestCase):
    
    def setUp(self):
        self.generator = JustificationGenerator()
        
    def test_6_1_context_prompt_building(self):
        """Verify _build_context_prompt"""
        summary = MagicMock()
        summary.overall_compliance.value = "COMPLIANT" # Ensure value is str
        summary.overall_compliance = "COMPLIANT" # Or just str if template uses it directly
        # The template uses {overall_compliance}. In impl it passes compliance_summary.overall_compliance.
        # If it's an Enum, str(Enum) might be used.
        # Let's set it to simple string or Enum mock
        summary.overall_compliance = "COMPLIANT"
        summary.compliant_count = 10
        summary.partial_count = 0
        summary.non_compliant_count = 0
        summary.warning_count = 0
        summary.unknown_count = 0
        summary.total_evaluated = 10
        summary.confidence_avg = 0.9 # FLOAT
        summary.mandatory_met = True
        summary.tool_results = []
        
        decision = {
            "recommendation": "BID",
            "confidence_score": 90,
            "requires_human_review": False,
            "decision_trace": ["Step 1", "Step 2"]
        }
        
        risks = []
        
        prompt = self.generator._build_context_prompt(summary, decision, risks)
        self.assertIsInstance(prompt, str)
        self.assertIn("COMPLIANT", prompt)
        self.assertIn("90", prompt)
        self.assertIn("BID", prompt)

    def test_6_2_fallback_templates(self):
        """Verify Fallback Templates Logic"""
        # We test via _generate_fallback_justification
        recommendation = RecommendationDecision.BID
        score = 90
        prompt = "test context"
        
        just = self.generator._generate_fallback_justification(prompt, recommendation, score)
        self.assertTrue(len(just) >= 50)
        self.assertIn("BID", just)
        self.assertIn("90", just)

    def test_6_3_fallback_trigger(self):
        """Verify Fallback Trigger on LLM Failure"""
        summary = MagicMock()
        summary.overall_compliance.value = "COMPLIANT"
        summary.overall_compliance = "COMPLIANT" # scalar
        summary.compliant_count = 10
        summary.partial_count = 0 
        summary.non_compliant_count = 0
        summary.warning_count = 0
        summary.unknown_count = 0
        summary.total_evaluated = 10
        summary.confidence_avg = 0.9
        summary.mandatory_met = True
        summary.tool_results = []

        decision = {
            "recommendation": RecommendationDecision.BID, 
            "confidence_score": 90,
            "decision_trace": []
        }
        risks = []
        
        # Mock LLM call to return None (simulating failure caught by retry)
        with patch.object(self.generator, '_generate_with_retry', return_value=None):
            just, exec_sum = self.generator.generate(summary, decision, risks)
            
            # Should fallback
            self.assertTrue(len(just) >= 50)
            self.assertTrue(len(exec_sum) >= 20)

    def test_6_5_generate_orchestrator(self):
        """Verify Generate Orchestrator"""
        summary = MagicMock()
        summary.overall_compliance.value = "COMPLIANT"
        summary.overall_compliance = "COMPLIANT" # scalar
        summary.compliant_count = 10
        summary.partial_count = 0 
        summary.non_compliant_count = 0
        summary.warning_count = 0
        summary.unknown_count = 0
        summary.total_evaluated = 10
        summary.confidence_avg = 0.9
        summary.mandatory_met = True
        summary.tool_results = []
        
        decision = {
            "recommendation": RecommendationDecision.BID, 
            "confidence_score": 90,
            "decision_trace": []
        }
        risks = []
        
        # Mock LLM to return valid text for both calls
        with patch.object(self.generator, '_generate_with_retry', return_value="This is a valid generated string that meets the length requirements."):
            just, exec_sum = self.generator.generate(summary, decision, risks)
            self.assertIsInstance(just, str)
            self.assertIsInstance(exec_sum, str)
            self.assertTrue(len(just) > 20)

if __name__ == "__main__":
    print("Justification Generator Test Results:")
    unittest.main(verbosity=2)

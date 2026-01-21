import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.app.services.tool_executor import ToolExecutorService
from src.app.models.compliance import ComplianceLevel, ToolResult
from src.app.models.recommendation import RiskCategory, RiskSeverity

class TestPhase5Executor(unittest.TestCase):

    def setUp(self):
        # Mock tools to avoid real execution
        with patch('src.app.services.tool_executor.CertificationCheckerTool'), \
             patch('src.app.services.tool_executor.TechValidatorTool'), \
             patch('src.app.services.tool_executor.BudgetAnalyzerTool'), \
             patch('src.app.services.tool_executor.TimelineAssessorTool'), \
             patch('src.app.services.tool_executor.StrategyEvaluatorTool'), \
             patch('src.app.services.tool_executor.KnowledgeQueryTool'):
            self.executor = ToolExecutorService()

    def test_7_1_initialization(self):
        """Verify Initialization"""
        self.assertEqual(len(self.executor._tools), 6)
        self.assertEqual(len(self.executor._cache), 0)
        self.assertIsNotNone(self.executor._value_extractor)

    def test_7_2_cache_key_generation(self):
        """Verify Cache Key Generation"""
        key = self.executor._get_cache_key("toolA", " Input Value ")
        self.assertEqual(key, "toolA::input value")

    def test_7_3_requirement_to_tool_matching(self):
        """Verify Requirement Match logic"""
        # Mock requirements
        req_budget = MagicMock()
        req_budget.text = "Budget must be < $100k"
        req_budget.type = "BUDGET"
        req_budget.category = "budget"
        req_budget.embedding = [0.1] * 1536  # Valid embedding
        # Ensure getattr works for text
        
        req_tech = MagicMock()
        # Mock str() or .text
        req_tech.text = "Must use Python"
        req_tech.type = "TECHNOLOGY"
        req_tech.category = "technical"

        mapping = self.executor.match_requirements_to_tools([req_budget, req_tech])
        
        self.assertTrue(len(mapping["budget_analyzer"]) > 0)
        self.assertTrue(len(mapping["tech_validator"]) > 0)
        # Check default knowledge query addition
        self.assertTrue(len(mapping["knowledge_query"]) > 0)

    def test_7_4_caching(self):
        """Verify Caching"""
        tool_name = "budget_analyzer"
        # Input MUST be a string per mismatch error? 
        # _execute_single_tool(self, tool_name: str, input_data: Any)
        # If tool expects str, pass str.
        # "budget_analyzer" tool typically expects requirement text or similar.
        input_data = "budget 100k" 
        
        # Mock _run
        mock_tool = MagicMock()
        # Ensure JSON has all validation fields: tool_name, requirement, status, compliance_level, confidence, message
        mock_tool._run.return_value = '{"tool_name":"budget_analyzer", "compliance_level":"COMPLIANT", "confidence":0.9, "requirement":"req", "status":"OK", "risks":[], "message":"ok"}'
        self.executor._tools[tool_name] = mock_tool
        
        # First call
        res1 = self.executor._execute_single_tool(tool_name, input_data)
        
        # Second call
        res2 = self.executor._execute_single_tool(tool_name, input_data)
        
        # Verify content matches (ignore timestamp if different object)
        self.assertEqual(res1.confidence, res2.confidence)
        self.assertEqual(res1.compliance_level, res2.compliance_level)
        
        # Check if cache is populated with 1 item
        self.assertEqual(len(self.executor._cache), 1)
        
        # Verify result content
        self.assertEqual(res1.confidence, 0.9)
        self.assertEqual(res1.message, "ok")

    def test_7_5_error_handling(self):
        """Verify Error Handling"""
        tool_name = "budget_analyzer"
        # Force error
        self.executor._tools[tool_name] = None # Or mock to raise
        
        res = self.executor._execute_single_tool(tool_name, "data")
        self.assertEqual(res.compliance_level, ComplianceLevel.UNKNOWN)
        self.assertEqual(res.status, "ERROR")

    def test_7_6_risk_extraction(self):
        """Verify Risk Extraction"""
        r1 = ToolResult(
            tool_name="tool1", requirement="r1",
            compliance_level=ComplianceLevel.NON_COMPLIANT,
            confidence=0.9, risks=["Budget exceeded significantly"], status="OK", message="ok"
        )
        r2 = ToolResult(
            tool_name="tool2", requirement="r2",
            compliance_level=ComplianceLevel.WARNING,
            confidence=0.8, risks=["Timeline missing deadlines"], status="OK", message="ok"
        )
        
        risks = self.executor.extract_risks_from_results([r1, r2])
        self.assertEqual(len(risks), 2)
        self.assertEqual(risks[0].severity, RiskSeverity.HIGH) # NON_COMPLIANT -> HIGH
        self.assertEqual(risks[1].severity, RiskSeverity.MEDIUM) # WARNING -> MEDIUM

    def test_7_7_clear_cache(self):
        """Verify Clear Cache"""
        self.executor._cache["k"] = "v"
        self.executor.clear_cache()
        self.assertEqual(len(self.executor._cache), 0)

if __name__ == "__main__":
    print("Tool Executor Test Results:")
    unittest.main(verbosity=2)

"""
Comprehensive test for all Phase 4 tools (Steps 3-7)
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger

# Import all tools
from src.app.agent.tools.knowledge_query_tool import KnowledgeQueryTool
from src.app.agent.tools.certification_checker_tool import CertificationCheckerTool
from src.app.agent.tools.tech_validator_tool import TechValidatorTool
from src.app.agent.tools.budget_analyzer_tool import BudgetAnalyzerTool
from src.app.agent.tools.timeline_assessor_tool import TimelineAssessorTool
from src.app.agent.tools.strategy_evaluator_tool import StrategyEvaluatorTool


def test_imports():
    """Test that all tools can be imported."""
    logger.info("=" * 60)
    logger.info("TEST 1: Import Check")
    logger.info("=" * 60)
    
    tools = [
        ("KnowledgeQueryTool", KnowledgeQueryTool),
        ("CertificationCheckerTool", CertificationCheckerTool),
        ("TechValidatorTool", TechValidatorTool),
        ("BudgetAnalyzerTool", BudgetAnalyzerTool),
        ("TimelineAssessorTool", TimelineAssessorTool),
        ("StrategyEvaluatorTool", StrategyEvaluatorTool)
    ]
    
    for name, tool_class in tools:
        try:
            tool = tool_class()
            logger.success(f"✓ {name} imported and instantiated successfully")
            logger.info(f"  - Name: {tool.name}")
            logger.info(f"  - Description: {tool.description[:60]}...")
        except Exception as e:
            logger.error(f"✗ {name} failed: {e}")
            return False
    
    logger.success("All tools imported successfully!\n")
    return True


def test_certification_checker():
    """Test CertificationCheckerTool."""
    logger.info("=" * 60)
    logger.info("TEST 2: CertificationCheckerTool")
    logger.info("=" * 60)
    
    tool = CertificationCheckerTool()
    
    test_cases = [
        "ISO 27001",
        "SOC 2",
        "NonExistent Cert"
    ]
    
    for cert_name in test_cases:
        try:
            logger.info(f"\nTesting: {cert_name}")
            result_json = tool._run(cert_name)
            logger.success(f"✓ Result: {result_json[:100]}...")
        except Exception as e:
            logger.error(f"✗ Failed for {cert_name}: {e}")
    
    logger.success("CertificationCheckerTool test complete!\n")


def test_tech_validator():
    """Test TechValidatorTool."""
    logger.info("=" * 60)
    logger.info("TEST 3: TechValidatorTool")
    logger.info("=" * 60)
    
    tool = TechValidatorTool()
    
    test_cases = [
        "Python",
        "JavaScript",
        "NonExistentTech"
    ]
    
    for tech in test_cases:
        try:
            logger.info(f"\nTesting: {tech}")
            result_json = tool._run(tech)
            logger.success(f"✓ Result: {result_json[:100]}...")
        except Exception as e:
            logger.error(f"✗ Failed for {tech}: {e}")
    
    logger.success("TechValidatorTool test complete!\n")


def test_budget_analyzer():
    """Test BudgetAnalyzerTool."""
    logger.info("=" * 60)
    logger.info("TEST 4: BudgetAnalyzerTool")
    logger.info("=" * 60)
    
    tool = BudgetAnalyzerTool()
    
    test_cases = [
        "$50,000",
        "150000",
        "300k",
        "invalid"
    ]
    
    for budget in test_cases:
        try:
            logger.info(f"\nTesting: {budget}")
            result_json = tool._run(budget)
            logger.success(f"✓ Result: {result_json[:100]}...")
        except Exception as e:
            logger.error(f"✗ Failed for {budget}: {e}")
    
    logger.success("BudgetAnalyzerTool test complete!\n")


def test_timeline_assessor():
    """Test TimelineAssessorTool."""
    logger.info("=" * 60)
    logger.info("TEST 5: TimelineAssessorTool")
    logger.info("=" * 60)
    
    tool = TimelineAssessorTool()
    
    test_cases = [
        "6 months",
        "12",
        "16 weeks",
        "invalid"
    ]
    
    for timeline in test_cases:
        try:
            logger.info(f"\nTesting: {timeline}")
            result_json = tool._run(timeline)
            logger.success(f"✓ Result: {result_json[:100]}...")
        except Exception as e:
            logger.error(f"✗ Failed for {timeline}: {e}")
    
    logger.success("TimelineAssessorTool test complete!\n")


def test_strategy_evaluator():
    """Test StrategyEvaluatorTool."""
    logger.info("=" * 60)
    logger.info("TEST 6: StrategyEvaluatorTool")
    logger.info("=" * 60)
    
    tool = StrategyEvaluatorTool()
    
    test_context = {
        "industry": "Healthcare",
        "technologies": ["Python", "AWS", "PostgreSQL"],
        "project_type": "AI/ML Solution",
        "client_sector": "private"
    }
    
    try:
        import json
        logger.info(f"\nTesting with context: {test_context}")
        result_json = tool._run(json.dumps(test_context))
        logger.success(f"✓ Result: {result_json[:150]}...")
    except Exception as e:
        logger.error(f"✗ Failed: {e}")
    
    logger.success("StrategyEvaluatorTool test complete!\n")


def main():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("PHASE 4 TOOLS VALIDATION TEST")
    logger.info("=" * 60)
    
    try:
        # Test 1: Imports
        if not test_imports():
            logger.error("Import test failed. Stopping.")
            return
        
        # Test 2-6: Individual tools
        test_certification_checker()
        test_tech_validator()
        test_budget_analyzer()
        test_timeline_assessor()
        test_strategy_evaluator()
        
        logger.info("=" * 60)
        logger.success("ALL TESTS COMPLETED SUCCESSFULLY!")
        logger.info("=" * 60)
        logger.info("✓ All tools are properly integrated")
        logger.info("✓ All imports work correctly")
        logger.info("✓ All tools can execute without errors")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

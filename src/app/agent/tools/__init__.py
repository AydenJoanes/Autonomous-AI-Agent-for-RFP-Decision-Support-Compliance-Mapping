"""
RFP Agent Tools Package
Exports all reasoning and parsing tools for LangChain integration.
"""

from loguru import logger

# Import Reasoning Tools
from src.app.agent.tools.knowledge_query_tool import KnowledgeQueryTool
from src.app.agent.tools.certification_checker_tool import CertificationCheckerTool
from src.app.agent.tools.tech_validator_tool import TechValidatorTool
from src.app.agent.tools.budget_analyzer_tool import BudgetAnalyzerTool
from src.app.agent.tools.timeline_assessor_tool import TimelineAssessorTool
from src.app.agent.tools.strategy_evaluator_tool import StrategyEvaluatorTool

# Import Parser Tools
from src.app.agent.tools.rfp_parser_tool import RFPParserTool
from src.app.agent.tools.requirement_processor_tool import RequirementProcessorTool

logger.info("[INIT] Importing reasoning tools...")

try:
    # Instantiate Reasoning Tools
    knowledge_query = KnowledgeQueryTool()
    certification_checker = CertificationCheckerTool()
    tech_validator = TechValidatorTool()
    budget_analyzer = BudgetAnalyzerTool()
    timeline_assessor = TimelineAssessorTool()
    strategy_evaluator = StrategyEvaluatorTool()

    REASONING_TOOLS = [
        knowledge_query,
        certification_checker,
        tech_validator,
        budget_analyzer,
        timeline_assessor,
        strategy_evaluator
    ]
    logger.info(f"[INIT] REASONING_TOOLS loaded: {len(REASONING_TOOLS)} tools")

    # Instantiate Parser Tools
    rfp_parser = RFPParserTool()
    req_processor = RequirementProcessorTool()

    PARSER_TOOLS = [
        rfp_parser,
        req_processor
    ]

    ALL_TOOLS = REASONING_TOOLS + PARSER_TOOLS
    logger.info(f"[INIT] ALL_TOOLS loaded: {len(ALL_TOOLS)} tools")

    # Create Registry
    TOOL_REGISTRY = {
        "knowledge_query": KnowledgeQueryTool,
        "certification_checker": CertificationCheckerTool,
        "tech_validator": TechValidatorTool,
        "budget_analyzer": BudgetAnalyzerTool,
        "timeline_assessor": TimelineAssessorTool,
        "strategy_evaluator": StrategyEvaluatorTool,
        "rfp_parser": RFPParserTool,
        "requirement_processor": RequirementProcessorTool
    }
    logger.info("[INIT] Tools package initialized successfully")

except Exception as e:
    logger.error(f"[INIT] Failed to initialize tools: {e}")
    raise e

__all__ = [
    "REASONING_TOOLS",
    "PARSER_TOOLS",
    "ALL_TOOLS",
    "TOOL_REGISTRY",
    "KnowledgeQueryTool",
    "CertificationCheckerTool",
    "TechValidatorTool",
    "BudgetAnalyzerTool",
    "TimelineAssessorTool",
    "StrategyEvaluatorTool",
    "RFPParserTool",
    "RequirementProcessorTool"
]

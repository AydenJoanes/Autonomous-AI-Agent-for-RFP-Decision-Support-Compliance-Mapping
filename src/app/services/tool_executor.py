"""
Tool Executor Service
Orchestrates running all reasoning tools against extracted requirements.
"""

from typing import Dict, List, Tuple, Any
from loguru import logger
import json

from langchain.tools import BaseTool

from src.app.agent.tools import (
    CertificationCheckerTool,
    TechValidatorTool,
    BudgetAnalyzerTool,
    TimelineAssessorTool,
    StrategyEvaluatorTool,
    KnowledgeQueryTool,
)
from src.app.models.compliance import ComplianceLevel, ToolResult
from src.app.models.recommendation import RiskItem, RiskCategory, RiskSeverity
from src.app.services.value_extractor import ValueExtractor

# LLM Intelligent Router
try:
    from src.app.services.llm_config import get_llm_config
    from src.app.services.intelligent_router import IntelligentRouter
    LLM_ROUTING_AVAILABLE = True
except ImportError:
    LLM_ROUTING_AVAILABLE = False
    logger.warning("Intelligent router not available, using keyword-based routing")


class ToolExecutorService:
    """Orchestrate tool execution and risk extraction."""

    def __init__(self):
        """Initialize the tool executor with cache, value extractor, and tools."""
        self._cache: Dict[str, ToolResult] = {}
        self._value_extractor = ValueExtractor()
        self._tools: Dict[str, BaseTool] = {
            "certification_checker": CertificationCheckerTool(),
            "tech_validator": TechValidatorTool(),
            "budget_analyzer": BudgetAnalyzerTool(),
            "timeline_assessor": TimelineAssessorTool(),
            "strategy_evaluator": StrategyEvaluatorTool(),
            "knowledge_query": KnowledgeQueryTool(),
        }
        
        # Initialize intelligent router if available
        if LLM_ROUTING_AVAILABLE:
            try:
                self._llm_config = get_llm_config()
                self._intelligent_router = IntelligentRouter()
                logger.info("[EXECUTOR] Intelligent router initialized")
            except Exception as e:
                logger.warning(f"[EXECUTOR] Intelligent router initialization failed: {e}")
                self._llm_config = None
                self._intelligent_router = None
        else:
            self._llm_config = None
            self._intelligent_router = None
        
        logger.info(f"[EXECUTOR] Initialized with {len(self._tools)} tools")

    def _get_cache_key(self, tool_name: str, input_value: str) -> str:
        """
        Generate cache key for deduplication.
        
        Args:
            tool_name: Name of the tool
            input_value: Input value to the tool
            
        Returns:
            Cache key string
        """
        return f"{tool_name}::{input_value.lower().strip()}"

    def _execute_single_tool(self, tool_name: str, input_data: Any) -> ToolResult:
        """
        Execute a single tool and parse response.
        
        Args:
            tool_name: Name of the tool to execute
            input_data: Input data for the tool
            
        Returns:
            ToolResult from the tool execution
        """
        try:
            # Check cache
            cache_key = self._get_cache_key(tool_name, str(input_data))
            if cache_key in self._cache:
                logger.debug(f"[EXECUTOR] Cache hit for {tool_name}: {cache_key[:50]}...")
                return self._cache[cache_key]
            
            # Get tool
            tool = self._tools.get(tool_name)
            if not tool:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            # Execute tool
            if isinstance(input_data, dict):
                response = tool._run(**input_data)
            else:
                response = tool._run(input_data)
            
            # Parse response - handle dict, model, or string
            if isinstance(response, ToolResult):
                result = response
            elif isinstance(response, dict):
                result = ToolResult.model_validate(response)
            elif isinstance(response, str):
                result = ToolResult.model_validate_json(response)
            else:
                raise ValueError(f"Unexpected response type: {type(response)}")
            
            # Cache result
            self._cache[cache_key] = result
            
            logger.info(f"[EXECUTOR] {tool_name} completed: {result.compliance_level}, confidence={result.confidence}")
            return result
            
        except Exception as e:
            logger.error(f"[EXECUTOR] {tool_name} failed: {e}")
            # Return error ToolResult
            return ToolResult(
                tool_name=tool_name,
                requirement=str(input_data),
                status="ERROR",
                compliance_level=ComplianceLevel.UNKNOWN,
                confidence=0.0,
                details={"error": str(e)},
                message=f"Tool execution failed: {e}"
            )

    # Keyword maps for tool matching
    TOOL_KEYWORDS = {
        "certification_checker": ["certification", "certified", "ISO", "SOC", "compliance", "accredited", "HIPAA", "GDPR", "PCI"],
        "tech_validator": ["technology", "programming", "framework", "language", "platform", "stack", "Python", "Java", "AWS", "cloud"],
        "budget_analyzer": ["budget", "cost", "price", "funding", "$", "USD", "financial", "fee"],
        "timeline_assessor": ["timeline", "duration", "deadline", "months", "weeks", "delivery", "schedule", "complete by"],
        "strategy_evaluator": ["industry", "sector", "strategic", "domain", "experience", "portfolio"],
    }

    # Type to tool mapping
    TYPE_TO_TOOL = {
        "BUDGET": "budget_analyzer",
        "TIMELINE": "timeline_assessor",
        "CERTIFICATION": "certification_checker",
        "TECHNOLOGY": "tech_validator",
        "COMPLIANCE": "certification_checker",
        "STRATEGIC": "strategy_evaluator",
    }

    def match_requirements_to_tools(self, requirements: List[Any]) -> Dict[str, List[Tuple[Any, Dict]]]:
        """
        Map requirements to appropriate tools with extracted inputs.
        
        Args:
            requirements: List of Requirement objects
            
        Returns:
            Dictionary mapping tool names to list of (requirement, input_dict) tuples
        """
        # Try intelligent routing first if available
        if (LLM_ROUTING_AVAILABLE and self._llm_config and 
            self._llm_config.enable_llm_routing and self._intelligent_router):
            try:
                logger.info("[EXECUTOR] Using intelligent routing")
                routing_map = self._intelligent_router.route_requirements_to_tools(requirements)
                return self._build_mapping_from_routing(requirements, routing_map)
            except Exception as e:
                logger.warning(f"[EXECUTOR] Intelligent routing failed, falling back to keyword-based: {e}")
                # Fall through to keyword-based routing
        
        # Keyword-based routing (original logic)
        return self._keyword_based_routing(requirements)
    
    def _build_mapping_from_routing(
        self, 
        requirements: List[Any], 
        routing_map: Dict[str, str]
    ) -> Dict[str, List[Tuple[Any, Dict]]]:
        """Build tool mapping from intelligent router output."""
        mapping: Dict[str, List[Tuple[Any, Dict]]] = {
            tool_name: [] for tool_name in self._tools.keys()
        }
        
        for requirement in requirements:
            req_text = getattr(requirement, 'text', str(requirement))
            req_type = getattr(requirement, 'type', '').upper()
            
            # Get tool from routing map
            req_id = f"{req_type}:{getattr(requirement, 'extracted_value', req_text)}"
            tool_name = routing_map.get(req_id, "knowledge_query")
            
            # Skip if routed to SKIP
            if tool_name == "SKIP":
                logger.debug(f"[EXECUTOR] Skipping requirement: {req_text[:50]}...")
                continue
            
            # Build input dict
            input_dict = self._build_tool_input(tool_name, requirement)
            mapping[tool_name].append((requirement, input_dict))
            
            logger.debug(f"[EXECUTOR] Routed '{req_text[:30]}...' to {tool_name}")
        
        return mapping
    
    def _build_tool_input(self, tool_name: str, requirement: Any) -> Dict:
        """Build input dictionary for a specific tool."""
        req_text = getattr(requirement, 'text', str(requirement))
        req_category = getattr(requirement, 'category', '').lower()
        req_type = getattr(requirement, 'type', '').upper()
        extracted = self._value_extractor.extract_all(req_text)
        
        if tool_name == "certification_checker":
            return {"certification_name": extracted.get("certification") or req_text}
        elif tool_name == "tech_validator":
            return {"technology": extracted.get("technology") or req_text}
        elif tool_name == "budget_analyzer":
            return {"budget": extracted.get("budget") or req_text}
        elif tool_name == "timeline_assessor":
            return {"timeline": extracted.get("timeline") or req_text}
        elif tool_name == "strategy_evaluator":
            context = {
                "industry": req_category if req_category else "general",
                "technologies": [extracted.get("technology")] if extracted.get("technology") else [],
                "project_type": req_type.lower() if req_type else "other",
                "client_sector": "unknown",
                "requirement_text": req_text
            }
            return {"rfp_context": json.dumps(context)}
        else:  # knowledge_query
            req_embedding = getattr(requirement, 'embedding', None)
            if req_embedding:
                return {
                    "requirement_text": req_text,
                    "requirement_embedding": req_embedding
                }
            else:
                return {"requirement_text": req_text, "requirement_embedding": []}
    
    def _keyword_based_routing(self, requirements: List[Any]) -> Dict[str, List[Tuple[Any, Dict]]]:
        """Original keyword-based routing logic."""
        mapping: Dict[str, List[Tuple[Any, Dict]]] = {
            tool_name: [] for tool_name in self._tools.keys()
        }
        
        for requirement in requirements:
            req_text = getattr(requirement, 'text', str(requirement))
            req_type = getattr(requirement, 'type', '').upper()
            req_category = getattr(requirement, 'category', '').lower()
            
            # Calculate scores for each tool
            tool_scores = {}
            for tool_name, keywords in self.TOOL_KEYWORDS.items():
                score = 0
                
                # +1 for each keyword match
                for keyword in keywords:
                    if keyword.lower() in req_text.lower():
                        score += 1
                
                # +2 for type match
                if self.TYPE_TO_TOOL.get(req_type) == tool_name:
                    score += 2
                
                # +1 for category match
                if req_category in [kw.lower() for kw in keywords]:
                    score += 1
                
                tool_scores[tool_name] = score
            
            # Select tool with highest score (threshold > 0)
            best_tool = max(tool_scores, key=tool_scores.get)
            best_score = tool_scores[best_tool]
            
            if best_score == 0:
                best_tool = "knowledge_query"
            
            # Build input dict
            input_dict = self._build_tool_input(best_tool, requirement)
            
            # Add to mapping
            mapping[best_tool].append((requirement, input_dict))
            
            # Also add to knowledge_query for experience check
            if best_tool != "knowledge_query":
                req_embedding = getattr(requirement, 'embedding', None)
                if req_embedding and len(req_embedding) == 1536:
                    mapping["knowledge_query"].append((requirement, {
                        "requirement_text": req_text,
                        "requirement_embedding": req_embedding
                    }))
                else:
                    logger.debug(f"[EXECUTOR] Skipping knowledge_query for '{req_text[:30]}...' - no valid 1536-dim embedding")
            
            logger.debug(f"[EXECUTOR] Matched '{req_text[:30]}...' to {best_tool} (score: {best_score})")
        
        logger.info(f"[EXECUTOR] Matched {len(requirements)} requirements to tools")
        return mapping

    def execute_all_tools(self, requirements: List) -> List[ToolResult]:
        """
        Execute all tools for all requirements.
        
        Args:
            requirements: List of Requirement objects
            
        Returns:
            List of ToolResult objects from all tool executions
        """
        logger.info(f"[EXECUTOR] Starting tool execution for {len(requirements)} requirements")
        
        # Match requirements to tools
        mapping = self.match_requirements_to_tools(requirements)
        
        results: List[ToolResult] = []
        
        # Execute each tool for its matched requirements
        for tool_name, requirement_list in mapping.items():
            for requirement, input_data in requirement_list:
                result = self._execute_single_tool(tool_name, input_data)
                results.append(result)
        
        logger.info(f"[EXECUTOR] Tool execution complete: {len(results)} results")
        return results

    # Category assignment based on tool name
    TOOL_TO_CATEGORY = {
        "certification_checker": RiskCategory.COMPLIANCE,
        "tech_validator": RiskCategory.TECHNICAL,
        "budget_analyzer": RiskCategory.BUDGET,
        "timeline_assessor": RiskCategory.TIMELINE,
        "strategy_evaluator": RiskCategory.STRATEGIC,
        "knowledge_query": RiskCategory.RESOURCE,
    }

    def extract_risks_from_results(self, tool_results: List[ToolResult]) -> List[RiskItem]:
        """
        Extract and deduplicate risks from all tool results.
        
        Args:
            tool_results: List of ToolResult objects
            
        Returns:
            Deduplicated and sorted list of RiskItem objects
        """
        from difflib import SequenceMatcher
        
        risks: List[RiskItem] = []
        seen_descriptions: List[str] = []
        
        for result in tool_results:
            # Skip if no risks in result
            if not result.risks:
                continue
            
            for risk_text in result.risks:
                # Determine severity
                # Check for explicit severity override in text
                if "(high risk)" in risk_text.lower():
                    severity = RiskSeverity.HIGH
                elif "(medium risk)" in risk_text.lower():
                    severity = RiskSeverity.MEDIUM
                elif "(low risk)" in risk_text.lower():
                    severity = RiskSeverity.LOW
                else:
                    # Default heuristic based on compliance level
                    if result.compliance_level == ComplianceLevel.NON_COMPLIANT:
                        severity = RiskSeverity.HIGH
                    elif result.compliance_level == ComplianceLevel.WARNING:
                        severity = RiskSeverity.MEDIUM
                    elif result.compliance_level == ComplianceLevel.PARTIAL and result.confidence < 0.5:
                        severity = RiskSeverity.MEDIUM
                    else:
                        severity = RiskSeverity.LOW
                
                # Determine category
                category = self.TOOL_TO_CATEGORY.get(result.tool_name, RiskCategory.RESOURCE)
                
                # Normalize description for deduplication
                normalized_desc = risk_text.lower().strip()
                
                # Check for similar existing description (>80% similarity)
                is_duplicate = False
                for existing in seen_descriptions:
                    similarity = SequenceMatcher(None, normalized_desc, existing).ratio()
                    if similarity > 0.8:
                        is_duplicate = True
                        break
                
                if is_duplicate:
                    continue
                
                # Add risk
                risk = RiskItem(
                    category=category,
                    severity=severity,
                    description=risk_text,
                    source_tool=result.tool_name,
                    requirement_text=result.requirement[:100] if result.requirement else None
                )
                risks.append(risk)
                seen_descriptions.append(normalized_desc)
        
        # Sort by severity: HIGH first, then MEDIUM, then LOW
        severity_order = {RiskSeverity.HIGH: 0, RiskSeverity.MEDIUM: 1, RiskSeverity.LOW: 2}
        risks.sort(key=lambda r: severity_order.get(r.severity, 3))
        
        logger.info(f"[EXECUTOR] Extracted {len(risks)} risks from {len(tool_results)} results")
        return risks

    def clear_cache(self):
        """Clear the result cache."""
        self._cache.clear()
        logger.info("[EXECUTOR] Cache cleared")





"""
Intelligent Router
Routes requirements to appropriate tools using semantic understanding.
"""

import json
from typing import List, Dict, Optional
from loguru import logger

from src.app.models.requirement import Requirement, RequirementType
from src.app.utils.llm_client import get_llm_client
from src.app.services.llm_config import get_llm_config


# Known patterns for rule-based routing
CERTIFICATION_PATTERNS = {
    "iso", "soc", "hipaa", "gdpr", "pci", "fedramp", "cmmi", "itil",
    "certification", "certified", "accreditation", "compliance"
}

TECHNOLOGY_PATTERNS = {
    "azure", "aws", "gcp", "python", "java", "react", "angular", "docker",
    "kubernetes", "terraform", "sql", "nosql", "api", "microservices"
}


# System prompt for intelligent routing
ROUTING_SYSTEM_PROMPT = """You are routing RFP requirements to analysis tools. Each tool has a specific purpose:

AVAILABLE TOOLS:

certification_checker
- Purpose: Verify if vendor holds required certifications
- Use when: Requirement mentions specific certifications (ISO, SOC, HIPAA, GDPR, PCI-DSS, FedRAMP, etc.)
- Example: "Must be ISO 27001 certified" → certification_checker

tech_validator
- Purpose: Verify if vendor has expertise in specific technologies
- Use when: Requirement mentions specific technologies, platforms, languages, or frameworks
- Example: "Experience with Microsoft Azure required" → tech_validator

budget_analyzer
- Purpose: Check if project budget aligns with vendor capacity
- Use when: Requirement specifies explicit budget amount or range
- Example: "Budget not to exceed $500,000" → budget_analyzer
- DO NOT USE for: "cost analysis features", "cost calculations", "cost metrics" (these are delivery scope)

timeline_assessor
- Purpose: Check if timeline aligns with vendor capacity
- Use when: Requirement specifies project duration, deadlines, or contract length
- Example: "Project must complete within 6 months" → timeline_assessor

knowledge_query
- Purpose: Find similar past projects demonstrating relevant experience
- Use when: Requirement asks for domain experience, past work, or demonstrated capability
- Example: "Prior healthcare analytics experience required" → knowledge_query

strategy_evaluator
- Purpose: Assess strategic alignment and fit
- Use when: Requirement involves geographic presence, industry focus, engagement model, or organizational fit
- Example: "Vendor must have North American presence" → strategy_evaluator

SKIP (no tool)
- Use when: Requirement is actually delivery scope that slipped through validation
- Example: "System must provide real-time analytics" → SKIP

For each requirement, return the single best tool or SKIP. Respond with a JSON object containing a "routing" array."""


def build_routing_user_prompt(requirements: List[Requirement]) -> str:
    """
    Build user prompt for routing.
    
    Args:
        requirements: Requirements to route
        
    Returns:
        Formatted user prompt
    """
    # Convert requirements to simple dict format
    req_dicts = []
    for i, req in enumerate(requirements):
        req_dicts.append({
            "index": i,
            "type": req.type.value,
            "original_text": req.text,
            "extracted_value": req.extracted_value
        })
    
    return f"""Route these requirements to the appropriate analysis tools:

{json.dumps(req_dicts, indent=2)}

For each requirement, return:
- requirement_index: The index in the input array
- tool: The tool name or "SKIP"
- confidence: Your confidence (0.0 to 1.0)
- reasoning: Brief explanation (under 50 characters)

Return as a JSON object with a "routing" array."""


class IntelligentRouter:
    """Route requirements to tools using semantic understanding."""
    
    def __init__(self):
        """Initialize the router."""
        self.llm_client = get_llm_client()
        self.config = get_llm_config()
    
    def rule_based_route(self, requirement: Requirement) -> Optional[str]:
        """
        Fast rule-based routing for obvious cases.
        
        Args:
            requirement: Requirement to route
            
        Returns:
            Tool name or None if ambiguous
        """
        req_type = requirement.type
        extracted_value = requirement.extracted_value.lower()
        original_text = requirement.text.lower()
        
        # CERTIFICATION type with known patterns
        if req_type == RequirementType.CERTIFICATION:
            return "certification_checker"
        
        # TECHNOLOGY type with known patterns
        if req_type == RequirementType.TECHNOLOGY:
            return "tech_validator"
        
        # BUDGET type with dollar amount
        if req_type == RequirementType.BUDGET:
            if "$" in extracted_value or "usd" in extracted_value:
                return "budget_analyzer"
        
        # TIMELINE type with duration
        if req_type == RequirementType.TIMELINE:
            return "timeline_assessor"
        
        # EXPERIENCE type
        if req_type == RequirementType.EXPERIENCE:
            return "knowledge_query"
        
        # GEOGRAPHIC type
        if req_type == RequirementType.GEOGRAPHIC:
            return "strategy_evaluator"
        
        # TEAM type - could be strategy or knowledge query
        if req_type == RequirementType.TEAM:
            # If mentions specific roles/skills, use knowledge_query
            if any(word in original_text for word in ["experience", "expertise", "background"]):
                return "knowledge_query"
            # Otherwise use strategy
            return "strategy_evaluator"
        
        # Check for certification patterns in text
        if any(pattern in extracted_value or pattern in original_text for pattern in CERTIFICATION_PATTERNS):
            return "certification_checker"
        
        # Check for technology patterns in text
        if any(pattern in extracted_value or pattern in original_text for pattern in TECHNOLOGY_PATTERNS):
            return "tech_validator"
        
        # Ambiguous - needs LLM
        return None
    
    def parse_routing_response(self, response: Dict[str, any]) -> List[Dict[str, any]]:
        """
        Parse LLM routing response.
        
        Args:
            response: Parsed JSON response from LLM
            
        Returns:
            List of routing decisions
        """
        routing = response.get("routing", [])
        
        if not isinstance(routing, list):
            logger.error("Invalid routing response format")
            return []
        
        return routing
    
    def llm_route_ambiguous(self, requirements: List[Requirement]) -> Dict[int, str]:
        """
        Route ambiguous requirements using LLM.
        
        Args:
            requirements: Requirements to route
            
        Returns:
            Dictionary mapping requirement index to tool name
        """
        if not requirements:
            return {}
        
        logger.info(f"Routing {len(requirements)} ambiguous requirements using LLM")
        
        try:
            # Build prompts
            user_prompt = build_routing_user_prompt(requirements)
            
            # Call LLM
            response = self.llm_client.call_llm_json(
                system_prompt=ROUTING_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                model=self.config.llm_routing_model,
                temperature=self.config.routing_temperature,
                timeout=self.config.routing_timeout
            )
            
            # Parse routing decisions
            routing_decisions = self.parse_routing_response(response)
            
            # Build index-to-tool map
            routing_map = {}
            for decision in routing_decisions:
                idx = decision.get("requirement_index")
                tool = decision.get("tool", "SKIP")
                confidence = decision.get("confidence", 0.0)
                reasoning = decision.get("reasoning", "")
                
                if idx is not None:
                    routing_map[idx] = tool
                    logger.debug(
                        f"Routed requirement {idx} to {tool} "
                        f"(confidence: {confidence:.2f}, reason: {reasoning})"
                    )
            
            return routing_map
            
        except Exception as e:
            logger.error(f"LLM routing failed: {e}")
            # Fallback: route all to knowledge_query (safest default)
            return {i: "knowledge_query" for i in range(len(requirements))}
    
    def route_requirements_to_tools(self, requirements: List[Requirement]) -> Dict[str, str]:
        """
        Route requirements to appropriate tools.
        
        Args:
            requirements: Requirements to route
            
        Returns:
            Dictionary mapping requirement ID to tool name
        """
        if not requirements:
            return {}
        
        logger.info(f"Routing {len(requirements)} requirements to tools")
        
        routing_map = {}
        ambiguous_requirements = []
        ambiguous_indices = []
        
        # First pass: rule-based routing
        for i, req in enumerate(requirements):
            tool = self.rule_based_route(req)
            
            if tool:
                # Generate requirement ID
                req_id = f"{req.type.value}:{req.extracted_value}"
                routing_map[req_id] = tool
                logger.debug(f"Rule-based routing: {req_id} → {tool}")
            else:
                # Ambiguous - needs LLM
                ambiguous_requirements.append(req)
                ambiguous_indices.append(i)
        
        logger.info(
            f"Rule-based routing: {len(routing_map)}/{len(requirements)} requirements routed"
        )
        
        # Second pass: LLM routing for ambiguous cases
        if ambiguous_requirements:
            llm_routing = self.llm_route_ambiguous(ambiguous_requirements)
            
            for local_idx, global_idx in enumerate(ambiguous_indices):
                req = requirements[global_idx]
                tool = llm_routing.get(local_idx, "knowledge_query")
                
                if tool != "SKIP":
                    req_id = f"{req.type.value}:{req.extracted_value}"
                    routing_map[req_id] = tool
                    logger.debug(f"LLM routing: {req_id} → {tool}")
        
        logger.info(f"Total routed: {len(routing_map)} requirements")
        
        return routing_map

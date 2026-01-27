from typing import List, Optional, Dict
from loguru import logger
from src.app.models.compliance import ComplianceLevel, ToolResult

def map_status_to_compliance(tool_name: str, status: str, details: Optional[Dict] = None) -> ComplianceLevel:
    """
    Maps tool-specific status strings to standardized ComplianceLevel enum.
    """
    status = status.upper() if status else ""
    details = details or {}
    
    # 1. Certification Checker
    if tool_name == "certification_checker":
        if status == "VALID":
            return ComplianceLevel.COMPLIANT
        elif status == "EXPIRING_SOON":
            return ComplianceLevel.WARNING
        elif status == "EXPIRED":
            return ComplianceLevel.NON_COMPLIANT
        elif status == "PENDING":
            return ComplianceLevel.PARTIAL
        elif status == "NOT_FOUND":
            return ComplianceLevel.UNKNOWN

    # 2. Tech Validator
    elif tool_name == "tech_validator":
        if status == "AVAILABLE":
            proficiency = details.get('proficiency', '').lower()
            if proficiency in ['expert', 'advanced']:
                return ComplianceLevel.COMPLIANT
            elif proficiency in ['intermediate', 'beginner']:
                return ComplianceLevel.PARTIAL
            else:
                logger.warning(f"Unknown proficiency '{proficiency}' for AVAILABLE tech. Defaulting to PARTIAL.")
                return ComplianceLevel.PARTIAL
        elif status == "NOT_IN_DATABASE":
            return ComplianceLevel.UNKNOWN
        elif status == "STALE":
            return ComplianceLevel.WARNING
        # Additional mappings if needed, assuming default UNKNOWN for others

    # 3. Budget Analyzer
    elif tool_name == "budget_analyzer":
        if status == "ACCEPTABLE":
            return ComplianceLevel.COMPLIANT
        elif status == "LOW_END":
            return ComplianceLevel.COMPLIANT
        elif status == "HIGH_END":
            return ComplianceLevel.WARNING
        elif status == "BELOW_MINIMUM":
            return ComplianceLevel.WARNING
        elif status == "EXCEEDS_MAXIMUM":
            return ComplianceLevel.NON_COMPLIANT

    # 4. Timeline Assessor
    elif tool_name == "timeline_assessor":
        if status == "FEASIBLE":
            return ComplianceLevel.COMPLIANT
        elif status == "CONSERVATIVE":
            return ComplianceLevel.COMPLIANT
        elif status == "TIGHT":
            return ComplianceLevel.WARNING
        elif status == "AGGRESSIVE":
            return ComplianceLevel.WARNING
        elif status == "UNREALISTIC":
            return ComplianceLevel.NON_COMPLIANT
        elif status == "NO_HISTORICAL_DATA":
            return ComplianceLevel.UNKNOWN

    # 5. Strategy Evaluator
    elif tool_name == "strategy_evaluator":
        if status == "STRONG_ALIGNMENT":
            return ComplianceLevel.COMPLIANT
        elif status == "MODERATE_ALIGNMENT":
            return ComplianceLevel.PARTIAL
        elif status == "WEAK_ALIGNMENT":
            return ComplianceLevel.WARNING
        elif status == "MISALIGNMENT":
            return ComplianceLevel.NON_COMPLIANT

    # 6. Knowledge Query (Self-determined)
    elif tool_name == "knowledge_query":
        # This tool sets its own logical compliance in the step.
        # We return UNKNOWN as standard mapping is not needed/handled internally by the tool logic flow before this map is called.
        return ComplianceLevel.UNKNOWN

    logger.warning(f"Unknown status '{status}' for tool '{tool_name}'.")
    return ComplianceLevel.UNKNOWN


def aggregate_compliance(tool_results: List[ToolResult], mandatory_tools: Optional[List[str]] = None) -> Dict:
    """
    Aggregates a list of ToolResult objects into an overall compliance assessment.
    """
    if not tool_results:
        return {
            "overall_compliance": ComplianceLevel.UNKNOWN,
            "compliant_count": 0,
            "non_compliant_count": 0,
            "partial_count": 0,
            "unknown_count": 0,
            "warning_count": 0,
            "confidence_avg": 0.0,
            "mandatory_requirements_met": True, # Default to true if no reqs
            "total_evaluated": 0
        }

    mandatory_tools = mandatory_tools or []
    
    counts = {
        ComplianceLevel.COMPLIANT: 0,
        ComplianceLevel.NON_COMPLIANT: 0,
        ComplianceLevel.PARTIAL: 0,
        ComplianceLevel.UNKNOWN: 0,
        ComplianceLevel.WARNING: 0
    }
    
    total_confidence = 0.0
    mandatory_met = True
    
    for res in tool_results:
        counts[res.compliance_level] = counts.get(res.compliance_level, 0) + 1
        total_confidence += res.confidence
        
        # Check mandatory
        if res.tool_name in mandatory_tools:
            # Mandatory is met if COMPLIANT or PARTIAL (as per requirements)
            # "A mandatory requirement is 'met' if its compliance_level is COMPLIANT or PARTIAL"
            if res.compliance_level not in [ComplianceLevel.COMPLIANT, ComplianceLevel.PARTIAL]:
                mandatory_met = False

    total_count = len(tool_results)
    confidence_avg = total_confidence / total_count if total_count > 0 else 0.0
    
    # Priority Logic
    if not mandatory_met:
        # If mandatory failed (implied NON_COMPLIANT/WARNING/UNKNOWN for mandatory tool)
        # Note: Logic says "If ANY mandatory requirement is NON_COMPLIANT -> overall = NON_COMPLIANT"
        # And "If ANY mandatory requirement is UNKNOWN -> overall = UNKNOWN"
        # We need to act on the specific failure of mandatory.
        
        # Refined check based on priority list:
        # 1. If ANY mandatory is NON_COMPLIANT -> NON_COMPLIANT
        mandatory_results = [r for r in tool_results if r.tool_name in mandatory_tools]
        if any(r.compliance_level == ComplianceLevel.NON_COMPLIANT for r in mandatory_results):
            overall = ComplianceLevel.NON_COMPLIANT
        elif any(r.compliance_level == ComplianceLevel.UNKNOWN for r in mandatory_results):
            overall = ComplianceLevel.UNKNOWN
        else:
            # Fallback if mandatory is WARNING (not explicitly in "met" definition but might happen)
            # or if logic falls through. 
            # If mandatory is NOT (Compliant or Partial), it failed the "met" check.
            # If it's pure Warning, it's failed "met" check. 
            # Let's align with the priority list strictly.
            overall = ComplianceLevel.NON_COMPLIANT # Fallback for failed mandatory
            
    else:
        # Mandatory met (or no mandatory tools)
        if counts[ComplianceLevel.NON_COMPLIANT] > 0:
            overall = ComplianceLevel.NON_COMPLIANT
        elif counts[ComplianceLevel.WARNING] > 0 and counts[ComplianceLevel.NON_COMPLIANT] == 0:
            overall = ComplianceLevel.WARNING
        elif counts[ComplianceLevel.COMPLIANT] == total_count:
            overall = ComplianceLevel.COMPLIANT
        elif (counts[ComplianceLevel.COMPLIANT] + counts[ComplianceLevel.PARTIAL]) == total_count:
            # Mix of COMPLIANT + PARTIAL (and no others, implied by previous elifs)
            overall = ComplianceLevel.PARTIAL # Logic 6
        elif (counts[ComplianceLevel.COMPLIANT] + counts[ComplianceLevel.PARTIAL]) > 0:
             # Basic Mix
             overall = ComplianceLevel.PARTIAL
        elif counts[ComplianceLevel.UNKNOWN] > (total_count / 2):
            overall = ComplianceLevel.UNKNOWN # Logic 7: Mostly UNKNOWN
        else:
            overall = ComplianceLevel.PARTIAL # Default fallback

    # Re-apply strict priority list from requirements to be safe
    # 1. Any mandatory NON_COMPLIANT -> NON_COMPLIANT
    # 2. Any mandatory UNKNOWN -> UNKNOWN
    # 3. All COMPLIANT -> COMPLIANT
    # 4. Any NON_COMPLIANT -> NON_COMPLIANT
    # 5. Mix has WARNING but no NON_COMPLIANT -> WARNING
    # 6. Mix of COMPLIANT + PARTIAL -> PARTIAL
    # 7. Mostly UNKNOWN -> UNKNOWN
    # 8. Default -> PARTIAL
    
    # Let's overwrite `overall` with strict logic flow
    
    # 1. Mandatory Checks
    mandatory_res = [r for r in tool_results if r.tool_name in mandatory_tools]
    if any(r.compliance_level == ComplianceLevel.NON_COMPLIANT for r in mandatory_res):
        overall = ComplianceLevel.NON_COMPLIANT
    elif any(r.compliance_level == ComplianceLevel.UNKNOWN for r in mandatory_res):
        overall = ComplianceLevel.UNKNOWN
    elif counts[ComplianceLevel.COMPLIANT] == total_count:
        overall = ComplianceLevel.COMPLIANT
    elif counts[ComplianceLevel.NON_COMPLIANT] > 0:
        overall = ComplianceLevel.NON_COMPLIANT
    elif counts[ComplianceLevel.WARNING] > 0:
        overall = ComplianceLevel.WARNING
    elif (counts[ComplianceLevel.COMPLIANT] + counts[ComplianceLevel.PARTIAL]) == total_count:
        # If majority are COMPLIANT, overall should be COMPLIANT
        if counts[ComplianceLevel.COMPLIANT] >= counts[ComplianceLevel.PARTIAL]:
            overall = ComplianceLevel.COMPLIANT
        else:
            overall = ComplianceLevel.PARTIAL
    elif (counts[ComplianceLevel.COMPLIANT] + counts[ComplianceLevel.PARTIAL]) > 0:
        # Mixed bag with some unknowns
        if counts[ComplianceLevel.COMPLIANT] >= (total_count / 2):
            overall = ComplianceLevel.COMPLIANT
        else:
            overall = ComplianceLevel.PARTIAL
    elif counts[ComplianceLevel.UNKNOWN] > (total_count / 2):
        overall = ComplianceLevel.UNKNOWN
    else:
        overall = ComplianceLevel.PARTIAL

    # Track mandatory status details
    mandatory_unknown = False
    mandatory_failed = False

    for result in tool_results:
        # Check if this is a mandatory requirement result
        is_mandatory = getattr(result, 'is_mandatory', False)
        if is_mandatory:
            if result.compliance_level == ComplianceLevel.UNKNOWN:
                mandatory_unknown = True
            elif result.compliance_level == ComplianceLevel.NON_COMPLIANT:
                mandatory_failed = True

    return {
        "overall_compliance": overall,
        "compliant_count": counts[ComplianceLevel.COMPLIANT],
        "non_compliant_count": counts[ComplianceLevel.NON_COMPLIANT],
        "partial_count": counts[ComplianceLevel.PARTIAL],
        "unknown_count": counts[ComplianceLevel.UNKNOWN],
        "warning_count": counts[ComplianceLevel.WARNING],
        "confidence_avg": float(f"{confidence_avg:.2f}"),
        "mandatory_requirements_met": mandatory_met,
        "mandatory_unknown": mandatory_unknown,
        "mandatory_failed": mandatory_failed,
        "total_evaluated": total_count
    }

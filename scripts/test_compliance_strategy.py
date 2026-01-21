import sys
import os
from pathlib import Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import datetime
from src.app.strategies.compliance_strategy import map_status_to_compliance, aggregate_compliance
from src.app.models.compliance import ComplianceLevel, ToolResult

def run_mapping_tests():
    print("\n" + "="*80)
    print("MAPPING TESTS")
    print("-" * 80)
    print(f"{'Tool':<25} | {'Status':<25} | {'Expected':<15} | {'Actual':<15} | {'Result'}")
    print("-" * 80)
    
    tests = [
        # Certification Checker
        ("certification_checker", "VALID", None, ComplianceLevel.COMPLIANT),
        ("certification_checker", "EXPIRING_SOON", None, ComplianceLevel.WARNING),
        ("certification_checker", "EXPIRED", None, ComplianceLevel.NON_COMPLIANT),
        ("certification_checker", "PENDING", None, ComplianceLevel.PARTIAL),
        ("certification_checker", "NOT_FOUND", None, ComplianceLevel.UNKNOWN),
        
        # Tech Validator
        ("tech_validator", "AVAILABLE", {"proficiency": "expert"}, ComplianceLevel.COMPLIANT),
        ("tech_validator", "AVAILABLE", {"proficiency": "advanced"}, ComplianceLevel.COMPLIANT),
        ("tech_validator", "AVAILABLE", {"proficiency": "intermediate"}, ComplianceLevel.PARTIAL),
        ("tech_validator", "AVAILABLE", {"proficiency": "beginner"}, ComplianceLevel.PARTIAL),
        ("tech_validator", "NOT_IN_DATABASE", None, ComplianceLevel.UNKNOWN),
        ("tech_validator", "STALE", None, ComplianceLevel.WARNING),
        
        # Budget Analyzer
        ("budget_analyzer", "ACCEPTABLE", None, ComplianceLevel.COMPLIANT),
        ("budget_analyzer", "LOW_END", None, ComplianceLevel.COMPLIANT),
        ("budget_analyzer", "HIGH_END", None, ComplianceLevel.WARNING),
        ("budget_analyzer", "BELOW_MINIMUM", None, ComplianceLevel.WARNING),
        ("budget_analyzer", "EXCEEDS_MAXIMUM", None, ComplianceLevel.NON_COMPLIANT),
        
        # Timeline Assessor
        ("timeline_assessor", "FEASIBLE", None, ComplianceLevel.COMPLIANT),
        ("timeline_assessor", "TIGHT", None, ComplianceLevel.WARNING),
        ("timeline_assessor", "AGGRESSIVE", None, ComplianceLevel.WARNING),
        ("timeline_assessor", "UNREALISTIC", None, ComplianceLevel.NON_COMPLIANT),
        ("timeline_assessor", "NO_HISTORICAL_DATA", None, ComplianceLevel.UNKNOWN),
        ("timeline_assessor", "CONSERVATIVE", None, ComplianceLevel.COMPLIANT),
        
        # Strategy Evaluator
        ("strategy_evaluator", "STRONG_ALIGNMENT", None, ComplianceLevel.COMPLIANT),
        ("strategy_evaluator", "MODERATE_ALIGNMENT", None, ComplianceLevel.PARTIAL),
        ("strategy_evaluator", "WEAK_ALIGNMENT", None, ComplianceLevel.WARNING),
        ("strategy_evaluator", "MISALIGNMENT", None, ComplianceLevel.NON_COMPLIANT),
        
        
        # Knowledge Query - Removed as tool sets compliance directly
        # ("knowledge_query", "STRONG_EVIDENCE", None, ComplianceLevel.COMPLIANT),
        # ("knowledge_query", "LIMITED_EVIDENCE", None, ComplianceLevel.PARTIAL),
        # ("knowledge_query", "WEAK_EVIDENCE", None, ComplianceLevel.WARNING),
        # ("knowledge_query", "NO_EVIDENCE", None, ComplianceLevel.UNKNOWN),
        
        
        # Edge Cases
        ("unknown_tool", "VALID", None, ComplianceLevel.UNKNOWN),
        ("certification_checker", "weird_status", None, ComplianceLevel.UNKNOWN),
        ("certification_checker", "", None, ComplianceLevel.UNKNOWN),
    ]
    
    passed = 0
    for tool, status, details, expected in tests:
        actual = map_status_to_compliance(tool, status, details)
        result_icon = "✅ PASS" if actual == expected else "❌ FAIL"
        if actual == expected:
            passed += 1
            
        status_disp = status if status else "None/Empty"
        if details:
             status_disp += f" ({details['proficiency']})"
             
        print(f"{tool:<25} | {status_disp:<25} | {expected.value:<15} | {actual.value:<15} | {result_icon}")

    print("-" * 80)
    print(f"Passed: {passed}/{len(tests)}")
    return passed == len(tests)

def create_mock_result(tool_name, compliance, confidence=0.8):
    return ToolResult(
        tool_name=tool_name,
        requirement="mock req",
        status="mock status",
        compliance_level=compliance,
        confidence=confidence,
        message="mock msg"
    )

def run_aggregation_tests():
    print("\n" + "="*80)
    print("AGGREGATION TESTS")
    print("-" * 80)
    print(f"{'Scenario':<30} | {'Overall Exp':<15} | {'Overall Act':<15} | {'Mandatory':<5} | {'Result'}")
    print("-" * 80)
    
    # Scenarios
    scenarios = []
    
    # 1. All Compliant
    scenarios.append({
        "name": "All COMPLIANT",
        "results": [
            create_mock_result("t1", ComplianceLevel.COMPLIANT),
            create_mock_result("t2", ComplianceLevel.COMPLIANT),
            create_mock_result("t3", ComplianceLevel.COMPLIANT)
        ],
        "mandatory": [],
        "exp_overall": ComplianceLevel.COMPLIANT,
        "exp_mandatory_met": True
    })
    
    # 2. Mixed COMPLIANT + PARTIAL
    scenarios.append({
        "name": "Mixed COMPLIANT + PARTIAL",
        "results": [
            create_mock_result("t1", ComplianceLevel.COMPLIANT),
            create_mock_result("t2", ComplianceLevel.PARTIAL),
        ],
        "mandatory": [],
        "exp_overall": ComplianceLevel.PARTIAL,
        "exp_mandatory_met": True
    })
    
    # 3. One NON_COMPLIANT among COMPLIANT
    scenarios.append({
        "name": "One NON_COMPLIANT",
        "results": [
            create_mock_result("t1", ComplianceLevel.COMPLIANT),
            create_mock_result("t2", ComplianceLevel.NON_COMPLIANT),
        ],
        "mandatory": [],
        "exp_overall": ComplianceLevel.NON_COMPLIANT,
        "exp_mandatory_met": True # No mandatory tools defined, so technically true based on logic
    })
    
    # 4. All UNKNOWN
    scenarios.append({
        "name": "All UNKNOWN",
        "results": [
            create_mock_result("t1", ComplianceLevel.UNKNOWN),
            create_mock_result("t2", ComplianceLevel.UNKNOWN),
        ],
        "mandatory": [],
        "exp_overall": ComplianceLevel.UNKNOWN,
        "exp_mandatory_met": True
    })

    # 5. Mandatory requirement NON_COMPLIANT
    scenarios.append({
        "name": "Mandatory NON_COMPLIANT",
        "results": [
            create_mock_result("certification_checker", ComplianceLevel.NON_COMPLIANT),
            create_mock_result("t2", ComplianceLevel.COMPLIANT),
        ],
        "mandatory": ["certification_checker"],
        "exp_overall": ComplianceLevel.NON_COMPLIANT,
        "exp_mandatory_met": False
    })
    
    # 6. Mandatory met, others failed
    scenarios.append({
        "name": "Mandatory Met, Others Fail",
        "results": [
            create_mock_result("certification_checker", ComplianceLevel.COMPLIANT),
            create_mock_result("t2", ComplianceLevel.NON_COMPLIANT),
        ],
        "mandatory": ["certification_checker"],
        "exp_overall": ComplianceLevel.NON_COMPLIANT,
        "exp_mandatory_met": True
    })
    
    # 7. Empty list
    scenarios.append({
        "name": "Empty List",
        "results": [],
        "mandatory": [],
        "exp_overall": ComplianceLevel.UNKNOWN,
        "exp_mandatory_met": True
    })
    
    passed = 0
    for sc in scenarios:
        res = aggregate_compliance(sc["results"], sc["mandatory"])
        actual_overall = res["overall_compliance"]
        actual_mandatory = res["mandatory_requirements_met"]
        
        matches = (actual_overall == sc["exp_overall"]) and (actual_mandatory == sc["exp_mandatory_met"])
        result_icon = "✅ PASS" if matches else "❌ FAIL"
        if matches:
            passed += 1
            
        print(f"{sc['name']:<30} | {sc['exp_overall'].value:<15} | {actual_overall.value:<15} | {str(actual_mandatory):<5} | {result_icon}")
        
    print("-" * 80)
    print(f"Passed: {passed}/{len(scenarios)}")
    return passed == len(scenarios)

if __name__ == "__main__":
    map_pass = run_mapping_tests()
    agg_pass = run_aggregation_tests()
    
    if map_pass and agg_pass:
        print("\nALL TESTS PASSED")
        sys.exit(0)
    else:
        print("\nSOME TESTS FAILED")
        sys.exit(1)

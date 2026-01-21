import sys
import os
from pathlib import Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from loguru import logger
from langchain.tools import BaseTool

def run_integration_tests():
    print("\n" + "="*80)
    print("PHASE 4 INTEGRATION TEST")
    print("="*80)
    
    passed = 0
    total_checks = 0
    
    # 1. Import Tests
    print("\nIMPORT TESTS")
    print("-" * 80)
    
    try:
        from src.app.agent.tools import REASONING_TOOLS, ALL_TOOLS, TOOL_REGISTRY
        from src.app.agent.tools import KnowledgeQueryTool, CertificationCheckerTool
        print(f"{'Import REASONING_TOOLS':<60} ✅ PASS")
        passed += 1
    except ImportError as e:
        print(f"{'Import REASONING_TOOLS':<60} ❌ FAIL ({e})")
    
    total_checks += 1
    
    if 'REASONING_TOOLS' in locals():
        # Check counts
        r_count = len(REASONING_TOOLS)
        all_count = len(ALL_TOOLS)
        
        if r_count == 6:
            print(f"{'REASONING_TOOLS count = 6':<60} ✅ PASS")
            passed += 1
        else:
            print(f"{f'REASONING_TOOLS count = {r_count} (Expected 6)':<60} ❌ FAIL")
        total_checks += 1
        
        if all_count == 8:
            print(f"{'ALL_TOOLS count = 8':<60} ✅ PASS")
            passed += 1
        else:
            print(f"{f'ALL_TOOLS count = {all_count} (Expected 8)':<60} ❌ FAIL")
        total_checks += 1
        
        # 2. Tool Instantiation Tests
        print("\nTOOL INSTANTIATION TESTS")
        print("-" * 80)
        
        for tool in REASONING_TOOLS:
            name_check = hasattr(tool, 'name') and tool.name
            desc_check = hasattr(tool, 'description') and tool.description
            run_check = hasattr(tool, '_run')
            base_check = isinstance(tool, BaseTool)
            schema_check = hasattr(tool, 'args_schema')
            
            tool_name = tool.name if name_check else "Unknown Tool"
            
            print(f"Tool: {tool_name}")
            if name_check:
                print(f"  - Has name attribute{'':<39} ✅ PASS")
                passed += 1
            else:
                print(f"  - Has name attribute{'':<39} ❌ FAIL")
            
            if desc_check:
                print(f"  - Has description attribute{'':<32} ✅ PASS")
                passed += 1
            else:
                print(f"  - Has description attribute{'':<32} ❌ FAIL")

            if base_check:
                print(f"  - Is BaseTool instance{'':<37} ✅ PASS")
                passed += 1
            else:
                print(f"  - Is BaseTool instance{'':<37} ❌ FAIL")

            total_checks += 3

    # 3. Tool Registry Tests
    print("\nTOOL REGISTRY TESTS")
    print("-" * 80)
    
    expected_tools = [
        "knowledge_query", "certification_checker", "tech_validator",
        "budget_analyzer", "timeline_assessor", "strategy_evaluator"
    ]
    
    if 'TOOL_REGISTRY' in locals():
        for t_name in expected_tools:
            if t_name in TOOL_REGISTRY:
                print(f"{f'{t_name} in registry':<60} ✅ PASS")
                passed += 1
            else:
                print(f"{f'{t_name} in registry':<60} ❌ FAIL")
            total_checks += 1
            
    # 4. Compliance Strategy Tests
    print("\nCOMPLIANCE STRATEGY TESTS")
    print("-" * 80)
    
    try:
        from src.app.strategies.compliance_strategy import map_status_to_compliance, aggregate_compliance
        print(f"{'Import Compliance Strategy':<60} ✅ PASS")
        passed += 1
        
        if callable(map_status_to_compliance) and callable(aggregate_compliance):
            print(f"{'Functions callable':<60} ✅ PASS")
            passed += 1
        else:
            print(f"{'Functions callable':<60} ❌ FAIL")
            
    except ImportError:
        print(f"{'Import Compliance Strategy':<60} ❌ FAIL")
        
    total_checks += 2

    print("\n" + "="*80)
    print(f"SUMMARY: {passed}/{total_checks} tests passed")
    if passed == total_checks:
         print("PHASE 4 INTEGRATION: READY ✅")
         return True
    else:
         print("PHASE 4 INTEGRATION: FAILED ❌")
         return False
    print("="*80)

if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)

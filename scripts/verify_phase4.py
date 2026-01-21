import sys
import os
from pathlib import Path
from datetime import datetime
import importlib.util

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import print as rprint
    CONSOLE = Console()
except ImportError:
    class MockConsole:
        def print(self, *args, **kwargs): print(*args)
        def rule(self, *args, **kwargs): print("-" * 80)
    CONSOLE = MockConsole()
    rprint = print
    # Simple table mock if needed, but we'll try to stick to basic printing fallback or assume rich is there based on reqs.

from src.app.models.compliance import ComplianceLevel, ToolResult
from src.app.strategies.compliance_strategy import map_status_to_compliance, aggregate_compliance
from src.app.agent.tools import REASONING_TOOLS, ALL_TOOLS, TOOL_REGISTRY

# ------------------------------------------------------------------------------
# CONSTANTS & SETUP
# ------------------------------------------------------------------------------
REPORT_PATH = Path("docs/PHASE4_VERIFICATION.md")

class VerificationSuite:
    def __init__(self):
        self.results = []
        self.passed_count = 0
        self.total_count = 0
        self.start_time = datetime.now()

    def check(self, name: str, condition: bool, details: str = ""):
        self.total_count += 1
        if condition:
            self.passed_count += 1
            status = "PASS"
            icon = "✅"
        else:
            status = "FAIL"
            icon = "❌"
        
        self.results.append({
            "name": name,
            "condition": condition,
            "details": details,
            "status": status,
            "icon": icon
        })
        
        # Console output
        if condition:
            CONSOLE.print(f"[green]✓ {name}[/green]")
        else:
            CONSOLE.print(f"[red]✗ {name} - {details}[/red]")

    def section(self, name: str):
        CONSOLE.rule(f"[bold blue]{name}[/bold blue]")

    def generate_report(self):
        duration = datetime.now() - self.start_time
        
        md_content = f"""# Phase 4 Verification Report
**Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Duration:** {duration.total_seconds():.2f}s
**Status:** {"✅ PASSED" if self.passed_count == self.total_count else "❌ FAILED"}

## Summary
| Metric | Value |
|---|---|
| Total Tests | {self.total_count} |
| Passed | {self.passed_count} |
| Failed | {self.total_count - self.passed_count} |
| Pass Rate | {(self.passed_count/self.total_count)*100:.1f}% |

## Detailed Results

"""
        # Group by section (naive, based on order)
        md_content += "| Test Case | Result | Details |\n|---|---|---|\n"
        for r in self.results:
            md_content += f"| {r['name']} | {r['icon']} {r['status']} | {r['details']} |\n"
            
        return md_content

# ------------------------------------------------------------------------------
# TEST SUITES
# ------------------------------------------------------------------------------
def run_model_validation(suite: VerificationSuite):
    suite.section("1. Model Validation (Rigorous)")
    
    # ToolResult validation
    try:
        ToolResult(
            tool_name="test",
            requirement="req",
            status="stat",
            compliance_level=ComplianceLevel.COMPLIANT,
            confidence=1.5, # Invalid
            message="msg"
        )
        suite.check("ToolResult detects invalid confidence > 1.0", False, "Should have raised ValueError")
    except ValueError:
        suite.check("ToolResult detects invalid confidence > 1.0", True)
        
    try:
        ToolResult(
            tool_name="test",
            requirement="req",
            status="stat",
            compliance_level=ComplianceLevel.COMPLIANT,
            confidence=-0.1, # Invalid
            message="msg"
        )
        suite.check("ToolResult detects invalid confidence < 0.0", False, "Should have raised ValueError")
    except ValueError:
        suite.check("ToolResult detects invalid confidence < 0.0", True)

    # ComplianceLevel enum
    suite.check("ComplianceLevel has 5 members", len(ComplianceLevel) == 5)
    suite.check("ComplianceLevel.UNKNOWN string value", ComplianceLevel.UNKNOWN.value == "UNKNOWN")

def run_strategy_logic(suite: VerificationSuite):
    suite.section("2. Compliance Strategy Logic (Rigorous)")
    
    # 2.1 Mapping Tests (Sample of critical ones + edge cases)
    mappings = [
        ("certification_checker", "VALID", ComplianceLevel.COMPLIANT),
        ("certification_checker", "EXPIRED", ComplianceLevel.NON_COMPLIANT),
        ("timeline_assessor", "CONSERVATIVE", ComplianceLevel.COMPLIANT), # New case
        ("budget_analyzer", "EXCEEDS_MAXIMUM", ComplianceLevel.NON_COMPLIANT),
        ("tech_validator", "STALE", ComplianceLevel.WARNING),
        ("unknown_tool", "ANY", ComplianceLevel.UNKNOWN),
        ("timeline_assessor", "", ComplianceLevel.UNKNOWN), # Empty status
    ]
    
    for tool, status, expected in mappings:
        actual = map_status_to_compliance(tool, status)
        suite.check(f"Map {tool}::{status} -> {expected.value}", actual == expected, f"Got {actual}")

    # 2.2 Aggregation Logic (Complex Scenarios)
    
    # Scenario: Tie breaker? (Logic doesn't specify sort, but priority rules)
    # Priority: Non-Compliant > Warning > Compliant
    
    # Case: Warning + Partial (Result should be WARNING based on priority 5 vs 6)
    # Priority 5: If mix has WARNING but no NON_COMPLIANT -> overall = WARNING
    res_warn = ToolResult(tool_name="t1", requirement="r", status="s", compliance_level=ComplianceLevel.WARNING, confidence=0.8, message="m")
    res_part = ToolResult(tool_name="t2", requirement="r", status="s", compliance_level=ComplianceLevel.PARTIAL, confidence=0.5, message="m")
    agg_res = aggregate_compliance([res_warn, res_part])
    suite.check("Aggregation: Warning + Partial = WARNING", agg_res["overall_compliance"] == ComplianceLevel.WARNING)
    
    # Case: Mandatory tool missing (if not in list passed to function?) 
    # Logic: "mandatory_requirements_met" flag checks if specific tools PASSED. 
    # If mandatory tool was not run (not in results), it technically isn't checked for failure, 
    # but practically the orchestrator ensures it runs. Strategy just aggregates *provided* results.
    # If a mandatory tool returns UNKNOWN -> UNKNOWN
    res_unk = ToolResult(tool_name="mandatory_tool", requirement="r", status="s", compliance_level=ComplianceLevel.UNKNOWN, confidence=0.1, message="m")
    agg_res_unk = aggregate_compliance([res_unk], mandatory_tools=["mandatory_tool"])
    suite.check("Aggregation: Mandatory UNKNOWN -> UNKNOWN", agg_res_unk["overall_compliance"] == ComplianceLevel.UNKNOWN)

    # Case: Confidence Averaging
    # 0.9 + 0.1 = 1.0 / 2 = 0.5
    res_conf_high = ToolResult(tool_name="t1", requirement="r", status="s", compliance_level=ComplianceLevel.COMPLIANT, confidence=0.9, message="m")
    res_conf_low = ToolResult(tool_name="t2", requirement="r", status="s", compliance_level=ComplianceLevel.COMPLIANT, confidence=0.1, message="m")
    agg_conf = aggregate_compliance([res_conf_high, res_conf_low])
    suite.check("Aggregation: Confirmation Average", agg_conf["confidence_avg"] == 0.5)

def run_integration_sanity(suite: VerificationSuite):
    suite.section("3. Integration Sanity (Rigorous)")
    
    # 3.1 Tool Registry
    suite.check("REASONING_TOOLS exported", len(REASONING_TOOLS) == 6)
    suite.check("ALL_TOOLS exported", len(ALL_TOOLS) == 8)
    
    # 3.2 Tool Instance Validity
    for tool in REASONING_TOOLS:
        is_pydantic = hasattr(tool, 'args_schema') and tool.args_schema is not None
        suite.check(f"Tool {tool.name} has args_schema", is_pydantic)
        
        # Check description populated
        suite.check(f"Tool {tool.name} has description", len(tool.description) > 10)

def main():
    CONSOLE.print(Panel.fit("[bold white]PHASE 4 RIGOROUS VERIFICATION[/bold white]", style="bold blue"))
    
    suite = VerificationSuite()
    
    run_model_validation(suite)
    run_strategy_logic(suite)
    run_integration_sanity(suite)
    
    # Report Generation
    report_content = suite.generate_report()
    REPORT_PATH.write_text(report_content, encoding="utf-8")
    
    CONSOLE.rule("[bold blue]VERIFICATION COMPLETE[/bold blue]")
    
    if suite.passed_count == suite.total_count:
        CONSOLE.print(f"[bold green]SUCCESS: All {suite.total_count} tests passed![/bold green]")
        CONSOLE.print(f"Detailed report saved to: [underline]{REPORT_PATH}[/underline]")
    else:
        CONSOLE.print(f"[bold red]FAILURE: {suite.total_count - suite.passed_count} tests failed![/bold red]")
        sys.exit(1)

if __name__ == "__main__":
    main()

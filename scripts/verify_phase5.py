"""
Phase 5 Master Verification Script
Runs all test scripts and generates summary report.
"""

import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path

# Test scripts to run in order
TEST_SCRIPTS = [
    ("Models", "scripts/test_recommendation_models.py"),
    ("Extractor", "scripts/test_value_extractor.py"),
    ("Decision", "scripts/test_decision_engine.py"),
    ("Justification", "scripts/test_justification_generator.py"),
    ("Service", "scripts/test_recommendation_service.py"),
    ("Integration", "scripts/test_phase5_integration.py"),
]


def run_test(name: str, script_path: str) -> dict:
    """Run a single test script and capture results."""
    print(f"\n{'='*60}")
    print(f"RUNNING: {name}")
    print(f"{'='*60}")
    
    start_time = datetime.now()
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        return {
            "name": name,
            "script": script_path,
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "elapsed_seconds": elapsed,
            "stdout": result.stdout[-2000:] if result.stdout else "",
            "stderr": result.stderr[-1000:] if result.stderr else "",
        }
    except subprocess.TimeoutExpired:
        return {
            "name": name,
            "script": script_path,
            "success": False,
            "returncode": -1,
            "elapsed_seconds": 120,
            "stdout": "",
            "stderr": "TIMEOUT after 120 seconds",
        }
    except Exception as e:
        return {
            "name": name,
            "script": script_path,
            "success": False,
            "returncode": -1,
            "elapsed_seconds": 0,
            "stdout": "",
            "stderr": str(e),
        }


def generate_summary(results: list) -> str:
    """Generate markdown summary report."""
    total = len(results)
    passed = sum(1 for r in results if r["success"])
    failed = total - passed
    
    report = f"""# Phase 5 Verification Report

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Summary

| Metric | Value |
|--------|-------|
| Total Test Suites | {total} |
| Passed | {passed} |
| Failed | {failed} |
| Success Rate | {(passed/total)*100:.1f}% |

## Results by Suite

| Suite | Status | Time | Details |
|-------|--------|------|---------|
"""
    
    for r in results:
        status = "[PASS]" if r["success"] else "[FAIL]"
        time_str = f"{r['elapsed_seconds']:.2f}s"
        details = "OK" if r["success"] else r["stderr"][:50]
        report += f"| {r['name']} | {status} | {time_str} | {details} |\n"
    
    report += f"""
## Overall Status

**{'PHASE 5 VERIFIED' if failed == 0 else 'VERIFICATION FAILED'}**

"""
    
    if failed > 0:
        report += "### Failed Suites\n\n"
        for r in results:
            if not r["success"]:
                report += f"#### {r['name']}\n```\n{r['stderr']}\n```\n\n"
    
    return report


def main():
    """Run all tests and generate report."""
    print("=" * 60)
    print("PHASE 5 VERIFICATION")
    print("=" * 60)
    
    # Create output directory
    output_dir = Path("data/test_output/reports")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run all tests
    results = []
    for name, script in TEST_SCRIPTS:
        result = run_test(name, script)
        results.append(result)
        
        if result["success"]:
            print(f"[PASS] {name}")
        else:
            print(f"[FAIL] {name}")

    # Generate reports
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # JSON report
    json_file = output_dir / f"test_summary_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    # Markdown report
    md_report = generate_summary(results)
    md_file = output_dir / f"test_summary_{timestamp}.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(md_report)
    
    # Also save as latest
    latest_md = output_dir / "test_summary_latest.md"
    with open(latest_md, 'w', encoding='utf-8') as f:
        f.write(md_report)
    
    # Print summary
    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)
    
    total = len(results)
    passed = sum(1 for r in results if r["success"])
    
    print(f"Passed: {passed}/{total}")
    print(f"Reports saved to: {output_dir}")
    print(f"  - {json_file.name}")
    print(f"  - {md_file.name}")
    
    # Exit with appropriate code
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())

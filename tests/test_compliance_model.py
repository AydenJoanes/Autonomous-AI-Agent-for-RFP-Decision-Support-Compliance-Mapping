from datetime import datetime
import sys
import os
from pathlib import Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.app.models.compliance import ComplianceLevel, ToolResult
import pytest

def test_compliance_level_enum():
    assert ComplianceLevel.COMPLIANT.value == "COMPLIANT"
    assert ComplianceLevel.NON_COMPLIANT.value == "NON_COMPLIANT"
    assert ComplianceLevel.PARTIAL.value == "PARTIAL"
    assert ComplianceLevel.UNKNOWN.value == "UNKNOWN"
    assert ComplianceLevel.WARNING.value == "WARNING"

def test_tool_result_creation():
    result = ToolResult(
        tool_name="test_tool",
        requirement="Must have Python",
        status="success",
        compliance_level=ComplianceLevel.COMPLIANT,
        confidence=0.95,
        details={"version": "3.10"},
        risks=[],
        message="Python 3.10 found"
    )
    
    assert result.tool_name == "test_tool"
    assert result.compliance_level == ComplianceLevel.COMPLIANT
    assert result.confidence == 0.95
    assert isinstance(result.timestamp, datetime)

def test_tool_result_validation():
    # Test invalid confidence
    with pytest.raises(ValueError):
        ToolResult(
            tool_name="test",
            requirement="req",
            status="status",
            compliance_level=ComplianceLevel.UNKNOWN,
            confidence=1.5, # Invalid
            message="msg"
        )

if __name__ == "__main__":
    test_compliance_level_enum()
    test_tool_result_creation()
    test_tool_result_validation()
    print("All compliance model tests passed!")

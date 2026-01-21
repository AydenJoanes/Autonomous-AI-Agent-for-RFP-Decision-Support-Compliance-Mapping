from enum import Enum
from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel, Field, validator

class ComplianceLevel(str, Enum):
    """
    Standardized compliance levels for all tools.
    """
    COMPLIANT = "COMPLIANT"              # Fully meets requirement
    NON_COMPLIANT = "NON_COMPLIANT"      # Does not meet requirement
    PARTIAL = "PARTIAL"                  # Partially meets requirement
    UNKNOWN = "UNKNOWN"                  # Cannot determine (data missing)
    WARNING = "WARNING"                  # Meets but with concerns (expiring, stale, risky)

class ToolResult(BaseModel):
    """
    Standardized result object for agent tools.
    """
    tool_name: str = Field(..., description="Name of the tool that generated this result")
    requirement: str = Field(..., description="The original requirement text being analyzed")
    status: str = Field(..., description="Tool-specific status string")
    compliance_level: ComplianceLevel = Field(..., description="Standardized compliance level")
    confidence: float = Field(..., description="Confidence score between 0.0 and 1.0")
    details: Dict = Field(default_factory=dict, description="Tool-specific details and evidence")
    risks: List[str] = Field(default_factory=list, description="List of identified risks")
    message: str = Field(..., description="Human-readable explanation or summary")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Time of result generation")

    @validator('confidence')
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v

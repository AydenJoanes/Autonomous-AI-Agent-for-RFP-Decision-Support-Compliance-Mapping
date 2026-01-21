from enum import Enum
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator

from src.app.models.compliance import ComplianceLevel


# ============================================================================
# ENUMS
# ============================================================================

class RecommendationDecision(str, Enum):
    """Final bid decision recommendation."""
    BID = "BID"  # Recommend proceeding with bid
    NO_BID = "NO_BID"  # Recommend not bidding
    CONDITIONAL_BID = "CONDITIONAL_BID"  # Bid only if conditions resolved


class RiskSeverity(str, Enum):
    """Risk severity levels."""
    HIGH = "HIGH"  # Critical risk, may block bid
    MEDIUM = "MEDIUM"  # Significant risk, needs mitigation
    LOW = "LOW"  # Minor risk, acceptable


class RiskCategory(str, Enum):
    """Risk categorization."""
    TIMELINE = "timeline"
    BUDGET = "budget"
    TECHNICAL = "technical"
    COMPLIANCE = "compliance"
    STRATEGIC = "strategic"
    RESOURCE = "resource"


# ============================================================================
# DATA MODELS
# ============================================================================

class RiskItem(BaseModel):
    """Individual risk identified during analysis."""
    category: RiskCategory = Field(..., description="Risk category")
    severity: RiskSeverity = Field(..., description="Risk severity level")
    description: str = Field(..., description="Human-readable risk description")
    source_tool: str = Field(..., description="Tool that identified this risk")
    requirement_text: Optional[str] = Field(None, description="Original requirement if applicable")

    class Config:
        use_enum_values = True


class ToolResultSummary(BaseModel):
    """Condensed view of ToolResult for compliance summary."""
    tool_name: str = Field(..., description="Name of the tool")
    requirement: str = Field(..., description="Requirement text (truncated)")
    compliance_level: ComplianceLevel = Field(..., description="Result compliance level")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Result confidence (0-1)")
    status: str = Field(..., description="Tool-specific status string")

    @validator('requirement')
    def truncate_requirement(cls, v):
        """Truncate requirement to 100 characters."""
        if len(v) > 100:
            return v[:97] + "..."
        return v


class ComplianceSummary(BaseModel):
    """Aggregated compliance analysis summary."""
    overall_compliance: ComplianceLevel = Field(..., description="Aggregated compliance level")
    compliant_count: int = Field(0, ge=0, description="Count of COMPLIANT results")
    non_compliant_count: int = Field(0, ge=0, description="Count of NON_COMPLIANT results")
    partial_count: int = Field(0, ge=0, description="Count of PARTIAL results")
    warning_count: int = Field(0, ge=0, description="Count of WARNING results")
    unknown_count: int = Field(0, ge=0, description="Count of UNKNOWN results")
    total_evaluated: int = Field(0, ge=0, description="Total requirements evaluated")
    confidence_avg: float = Field(0.0, ge=0.0, le=1.0, description="Average confidence (0-1)")
    mandatory_met: bool = Field(True, description="All mandatory requirements passed")
    tool_results: List[ToolResultSummary] = Field(default_factory=list, description="Individual result summaries")

    @validator('total_evaluated', always=True)
    def validate_total(cls, v, values):
        """Ensure total matches sum of counts."""
        expected = (
            values.get('compliant_count', 0) +
            values.get('non_compliant_count', 0) +
            values.get('partial_count', 0) +
            values.get('warning_count', 0) +
            values.get('unknown_count', 0)
        )
        if v != expected and expected > 0:
            # Auto-correct if mismatch
            return expected
        return v


class RFPMetadata(BaseModel):
    """RFP document metadata."""
    filename: str = Field(..., description="Original filename")
    file_path: str = Field(..., description="Full file path")
    processed_date: datetime = Field(default_factory=datetime.utcnow, description="When processing occurred")
    word_count: int = Field(0, ge=0, description="Document word count")
    requirement_count: int = Field(0, ge=0, description="Extracted requirements count")


class Recommendation(BaseModel):
    """Final bid/no-bid recommendation."""
    recommendation: RecommendationDecision = Field(..., description="Final decision")
    confidence_score: int = Field(..., ge=0, le=100, description="Confidence score (0-100)")
    justification: str = Field(..., min_length=50, description="Natural language explanation")
    executive_summary: str = Field(..., min_length=20, description="2-3 sentence summary")
    risks: List[RiskItem] = Field(default_factory=list, description="Identified risks")
    compliance_summary: ComplianceSummary = Field(..., description="Aggregated compliance data")
    requires_human_review: bool = Field(..., description="Whether human review needed")
    review_reasons: List[str] = Field(default_factory=list, description="Why human review needed")
    rfp_metadata: RFPMetadata = Field(..., description="Document metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When recommendation created")

    @validator('confidence_score')
    def validate_confidence(cls, v):
        """Ensure confidence is 0-100."""
        if not 0 <= v <= 100:
            raise ValueError("Confidence score must be between 0 and 100")
        return v

    @validator('justification')
    def validate_justification_length(cls, v):
        """Ensure justification has minimum length."""
        if len(v.strip()) < 50:
            raise ValueError("Justification must be at least 50 characters")
        return v.strip()

    @validator('executive_summary')
    def validate_summary_length(cls, v):
        """Ensure executive summary has minimum length."""
        if len(v.strip()) < 20:
            raise ValueError("Executive summary must be at least 20 characters")
        return v.strip()

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

"""
RFP Document Models
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class Requirement(BaseModel):
    """A requirement extracted from an RFP document."""
    
    id: str
    category: str
    description: str
    priority: Optional[str] = None
    compliance_required: bool = False


class RFPDocument(BaseModel):
    """Represents a parsed RFP document."""
    
    id: str
    title: str
    client_name: str
    submission_deadline: Optional[str] = None
    requirements: List[Requirement] = Field(default_factory=list)
    budget: Optional[str] = None
    description: str


class ComplianceGap(BaseModel):
    """Represents a compliance gap."""
    
    requirement_id: str
    capability_id: Optional[str] = None
    gap_description: str
    severity: str  # HIGH, MEDIUM, LOW
    recommendation: str


class CapabilityAssessment(BaseModel):
    """Assessment of company capabilities against RFP."""
    
    rfp_id: str
    total_requirements: int
    met_requirements: int
    compliance_gaps: List[ComplianceGap] = Field(default_factory=list)
    overall_compliance_score: float
    recommendation: str  # BID, NO_BID, CONDITIONAL

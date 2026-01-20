from typing import List
from pydantic import BaseModel, Field, field_validator

class Recommendation(BaseModel):
    decision: str = Field(..., description="BID or NO_BID")
    confidence_score: int = Field(..., ge=0, le=100)
    justification: str = Field(..., min_length=1)
    risks: List[str] = Field(default_factory=list)
    requirements_met: List[str] = Field(default_factory=list)
    requirements_failed: List[str] = Field(default_factory=list)
    clarification_questions: List[str] = Field(default_factory=list)
    escalation_needed: bool = False
    reasoning_steps: List[str] = Field(default_factory=list)

    @field_validator('decision')
    @classmethod
    def validate_decision_uppercase(cls, v: str) -> str:
        if v != v.upper():
            raise ValueError("Decision must be uppercase (e.g., BID, NO_BID)")
        return v

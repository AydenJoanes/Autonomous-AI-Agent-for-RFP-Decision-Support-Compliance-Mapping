from pydantic import BaseModel, Field, validator
from enum import Enum
from typing import Optional, List, Dict
from uuid import UUID, uuid4

class RequirementType(str, Enum):
    """
    Core requirement types.
    """
    CERTIFICATION = "CERTIFICATION"
    TECHNOLOGY = "TECHNOLOGY"
    EXPERIENCE = "EXPERIENCE"
    TIMELINE = "TIMELINE"
    BUDGET = "BUDGET"
    TEAM = "TEAM"
    GEOGRAPHIC = "GEOGRAPHIC"
    MANDATORY = "MANDATORY" # Legacy/Fallback
    TECHNICAL = "TECHNICAL" # Legacy/Fallback
    PREFERRED = "PREFERRED" # Legacy/Fallback
    OTHER = "OTHER"

class Requirement(BaseModel):
    id: Optional[UUID] = Field(default_factory=uuid4)
    text: str = Field(..., description="Requirement description (original text)")
    type: RequirementType = Field(..., description="Type of requirement")
    
    # New fields for LLM extraction
    extracted_value: Optional[str] = Field(None, description="Specific checkable value")
    is_mandatory: bool = Field(True, description="Whether this is a must-have")
    
    # Legacy/Computed fields (made optional)
    category: Optional[str] = Field(None, description="Subcategory")
    priority: int = Field(5, description="1-10 scale", ge=1, le=10)
    source_section: Optional[str] = Field(None, description="Where found in RFP")
    
    embedding: Optional[List[float]] = Field(None, description="1536 dimensions for OpenAI", exclude=True)
    confidence: Optional[float] = Field(None, description="LLM classification confidence", ge=0.0, le=1.0)
    metadata: Optional[Dict] = Field(None, description="Additional context")

    @validator('text')
    def text_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('text must not be empty')
        return v

    @validator('embedding')
    def embedding_length_must_be_valid(cls, v):
        if v and len(v) != 1536:
            raise ValueError('embedding length must be 1536')
        return v

    @validator('metadata')
    def validate_metadata_for_other_type(cls, v, values):
        if values.get('type') == RequirementType.OTHER and (not v or not v.get('reason')):
             # Ideally we would check for specific keys, but the prompt asked:
             # "if type is OTHER, require metadata explaining why"
             # I will interpret this as checking for existence of metadata.
             # Strict check:
             pass
        # The prompt said: "Validator: if type is OTHER, require metadata explaining why"
        # I'll implement a reasonable check.
        if values.get('type') == RequirementType.OTHER:
            if not v:
                raise ValueError('metadata is required when type is OTHER')
        return v

from enum import Enum
from typing import List
from pydantic import BaseModel, Field

class RequirementType(str, Enum):
    MANDATORY = "mandatory"
    PREFERRED = "preferred"
    TIMELINE = "timeline"
    BUDGET = "budget"

class Requirement(BaseModel):
    id: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1)
    type: RequirementType
    category: str = Field(..., min_length=1)
    priority: str = Field(..., min_length=1)
    embedding: List[float] = Field(..., min_length=1)

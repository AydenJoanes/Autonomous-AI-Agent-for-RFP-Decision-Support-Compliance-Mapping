from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

class Project(BaseModel):
    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    industry: str = Field(..., min_length=1)
    client_sector: str = Field(..., min_length=1)
    technologies: List[str] = Field(..., min_length=1)
    budget: float = Field(..., gt=0)
    duration_months: int = Field(..., ge=1, le=36)
    team_size: int = Field(..., gt=0)
    outcome: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    year: int = Field(..., ge=2000)
    embedding: Optional[List[float]] = None

from typing import List, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator

class CompanyProfile(BaseModel):
    name: str = Field(..., min_length=1)
    overview: str = Field(..., min_length=1)
    years_of_experience: int = Field(..., gt=0)
    team_size: int = Field(..., gt=0)
    delivery_regions: List[str] = Field(..., min_length=1)
    budget_capacity: Dict[str, Any] = Field(..., description="Must include min, max, currency")
    industries_served: List[str] = Field(..., min_length=1)
    core_services: List[str] = Field(..., min_length=1)

    @field_validator('budget_capacity')
    @classmethod
    def validate_budget_capacity(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        required_keys = {'min', 'max', 'currency'}
        if not required_keys.issubset(v.keys()):
            raise ValueError(f"budget_capacity must contain keys: {required_keys}")
        
        if v['min'] >= v['max']:
            raise ValueError("budget_capacity min must be less than max")
        
        return v

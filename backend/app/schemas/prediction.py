
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AttritionPredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    Age: int = Field(ge=18, le=100)
    Department: str = Field(min_length=1, max_length=100)
    JobRole: str = Field(min_length=1, max_length=100)
    MonthlyIncome: float = Field(ge=0, le=10_000_000)
    YearsAtCompany: int = Field(ge=0, le=80)
    JobSatisfaction: int = Field(ge=1, le=4)
    WorkLifeBalance: int = Field(ge=1, le=4)
    OverTime: Literal["Yes", "No"]


class AttritionPredictionResponse(BaseModel):
    prediction: Literal["Yes", "No"]
    attrition_probability: float = Field(ge=0, le=1)
    risk_level: Literal["LOW", "MODERATE", "HIGH"]
    model: str
    disclaimer: str

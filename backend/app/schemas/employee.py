
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


EmploymentType = Literal[
    "FULL_TIME",
    "PART_TIME",
    "CONTRACT",
    "INTERN",
]


class EmployeeCreate(BaseModel):
    employee_code: str = Field(min_length=2, max_length=30)
    user_id: int = Field(gt=0)
    department: str = Field(min_length=2, max_length=100)
    job_title: str = Field(min_length=2, max_length=100)
    employment_type: EmploymentType = "FULL_TIME"
    date_of_joining: date
    phone: str | None = Field(default=None, max_length=20)
    annual_salary: Decimal = Field(ge=0, max_digits=12, decimal_places=2)


class EmployeeUpdate(BaseModel):
    department: str | None = Field(default=None, min_length=2, max_length=100)
    job_title: str | None = Field(default=None, min_length=2, max_length=100)
    employment_type: EmploymentType | None = None
    date_of_joining: date | None = None
    phone: str | None = Field(default=None, max_length=20)
    annual_salary: Decimal | None = Field(
        default=None, ge=0, max_digits=12, decimal_places=2
    )
    is_active: bool | None = None


class EmployeeResponse(BaseModel):
    id: int
    employee_code: str
    user_id: int
    department: str
    job_title: str
    employment_type: EmploymentType
    date_of_joining: date
    phone: str | None
    annual_salary: Decimal
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

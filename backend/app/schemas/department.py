
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from typing import Annotated


DepartmentName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=2, max_length=100),
]

DepartmentCode = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=2,
        max_length=20,
        pattern=r"^[A-Za-z0-9_-]+$",
    ),
]


class DepartmentCreate(BaseModel):
    name: DepartmentName
    code: DepartmentCode
    description: str | None = Field(default=None, max_length=500)


class DepartmentUpdate(BaseModel):
    name: DepartmentName | None = None
    code: DepartmentCode | None = None
    description: str | None = Field(default=None, max_length=500)


class DepartmentResponse(BaseModel):
    id: int
    name: str
    code: str
    description: str | None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

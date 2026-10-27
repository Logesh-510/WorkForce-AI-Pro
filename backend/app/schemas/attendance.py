
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


AttendanceStatus = Literal[
    "PRESENT",
    "ABSENT",
    "HALF_DAY",
    "ON_LEAVE",
]


class AttendanceCheckIn(BaseModel):
    attendance_date: date | None = None
    shift_name: str | None = Field(default=None, max_length=50)


class AttendanceCheckOut(BaseModel):
    pass


class AttendanceResponse(BaseModel):
    id: int
    employee_id: int
    attendance_date: date
    check_in: datetime | None
    check_out: datetime | None
    working_hours: Decimal | None
    status: AttendanceStatus
    shift_name: str | None
    overtime_hours: Decimal
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)



class AttendanceAdminUpdate(BaseModel):
    status: AttendanceStatus | None = None
    shift_name: str | None = Field(default=None, max_length=50)
    notes: str | None = Field(default=None, max_length=500)
    overtime_hours: Decimal | None = Field(default=None, ge=0, le=999.99)

    @field_validator("status", mode="before")
    @classmethod
    def reject_null_status(cls, value):
        if value is None:
            raise ValueError(
                "status cannot be null; omit the field if no status change is needed"
            )
        return value

    @model_validator(mode="after")
    def validate_update_fields(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        return self


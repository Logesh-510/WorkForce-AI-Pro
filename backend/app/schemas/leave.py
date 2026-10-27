from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


LeaveType = Literal[
    "CASUAL",
    "SICK",
    "ANNUAL",
    "UNPAID",
    "MATERNITY",
    "PATERNITY",
]

LeaveStatus = Literal[
    "PENDING",
    "APPROVED",
    "REJECTED",
    "CANCELLED",
]


class LeaveRequestCreate(BaseModel):
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: str = Field(min_length=5, max_length=2000)

    @model_validator(mode="after")
    def validate_leave_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date cannot be earlier than start_date")

        if self.start_date < date.today():
            raise ValueError("Leave cannot start in the past")

        return self


class LeaveReview(BaseModel):
    status: Literal["APPROVED", "REJECTED"]
    review_comment: str | None = Field(default=None, max_length=2000)


class LeaveResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: str
    status: LeaveStatus
    reviewed_by: int | None
    review_comment: str | None
    reviewed_at: datetime | None
    created_at: datetime


from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.employee import Employee
from app.models.leave import LeaveRequest
from app.models.user import User
from app.schemas.leave import (
    LeaveRequestCreate,
    LeaveResponse,
    LeaveReview,
)

router = APIRouter()


def get_leave_or_404(
    db: Session,
    leave_id: int,
    *,
    for_update: bool = False,
) -> LeaveRequest:
    statement = select(LeaveRequest).where(
        LeaveRequest.id == leave_id
    )

    # MySQL/InnoDB locks the selected leave row until the transaction ends.
    if for_update:
        statement = statement.with_for_update()

    leave = db.scalar(statement)

    if leave is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave request not found",
        )

    return leave


def get_employee_for_user(db: Session, user_id: int) -> Employee:
    employee = db.scalar(
        select(Employee).where(Employee.user_id == user_id)
    )

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee profile not found for this account",
        )

    if not employee.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive employees cannot manage leave requests",
        )

    return employee


@router.post(
    "/",
    response_model=LeaveResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_leave_request(
    data: LeaveRequestCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    employee = get_employee_for_user(db, current_user.id)

    try:
        # Serialize leave creation for this employee.
        # MySQL/InnoDB holds this employee-row lock until commit/rollback.
        locked_employee_id = db.scalar(
            select(Employee.id)
            .where(Employee.id == employee.id)
            .with_for_update()
        )

        if locked_employee_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee profile not found",
            )

        # Run the overlap check only after acquiring the employee lock.
        overlapping_leave = db.scalar(
            select(LeaveRequest.id)
            .where(
                LeaveRequest.employee_id == employee.id,
                LeaveRequest.status.in_(("PENDING", "APPROVED")),
                LeaveRequest.start_date <= data.end_date,
                LeaveRequest.end_date >= data.start_date,
            )
            .limit(1)
        )

        if overlapping_leave is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Leave dates overlap an existing pending "
                    "or approved request"
                ),
            )

        leave = LeaveRequest(
            employee_id=employee.id,
            leave_type=data.leave_type,
            start_date=data.start_date,
            end_date=data.end_date,
            reason=data.reason.strip(),
            status="PENDING",
        )

        db.add(leave)
        db.commit()
        db.refresh(leave)

        return leave

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unable to create the leave request",
        )


@router.get("/", response_model=list[LeaveResponse])
def list_leave_requests(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    leave_status: str | None = Query(
        default=None,
        alias="status",
        pattern="^(PENDING|APPROVED|REJECTED|CANCELLED)$",
    ),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    statement = select(LeaveRequest)

    if current_user.role not in ("ADMIN", "HR"):
        employee = get_employee_for_user(db, current_user.id)
        statement = statement.where(
            LeaveRequest.employee_id == employee.id
        )

    if leave_status:
        statement = statement.where(
            LeaveRequest.status == leave_status
        )

    statement = (
        statement
        .order_by(LeaveRequest.created_at.desc(), LeaveRequest.id.desc())
        .offset(skip)
        .limit(limit)
    )

    return list(db.scalars(statement).all())


@router.get("/{leave_id}", response_model=LeaveResponse)
def get_leave_request(
    leave_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    leave = get_leave_or_404(db, leave_id)

    if current_user.role not in ("ADMIN", "HR"):
        employee = get_employee_for_user(db, current_user.id)

        if leave.employee_id != employee.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot access another employee's leave request",
            )

    return leave


@router.patch(
    "/{leave_id}/review",
    response_model=LeaveResponse,
)
def review_leave_request(
    leave_id: int,
    data: LeaveReview,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles("ADMIN", "HR"))],
):
    try:
        # Lock the leave row before checking its current status.
        leave = get_leave_or_404(db, leave_id, for_update=True)

        if leave.status != "PENDING":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only pending leave requests can be reviewed",
            )

        employee = db.get(Employee, leave.employee_id)

        if employee is not None and employee.user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot review your own leave request",
            )

        leave.status = data.status
        leave.reviewed_by = current_user.id
        leave.review_comment = (
            data.review_comment.strip()
            if data.review_comment and data.review_comment.strip()
            else None
        )
        leave.reviewed_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(leave)

        return leave

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unable to review this leave request",
        )


@router.post(
    "/{leave_id}/cancel",
    response_model=LeaveResponse,
)
def cancel_leave_request(
    leave_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    employee = get_employee_for_user(db, current_user.id)

    try:
        # Lock the leave row to coordinate cancellation with review.
        leave = get_leave_or_404(db, leave_id, for_update=True)

        if leave.employee_id != employee.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot cancel another employee's leave request",
            )

        if leave.status != "PENDING":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only pending leave requests can be cancelled",
            )

        leave.status = "CANCELLED"

        db.commit()
        db.refresh(leave)

        return leave

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unable to cancel this leave request",
        )

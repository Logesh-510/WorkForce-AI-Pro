from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.attendance import Attendance
from app.models.employee import Employee
from app.models.user import User
from app.schemas.attendance import (
    AttendanceAdminUpdate,
    AttendanceCheckIn,
    AttendanceResponse,
)


router = APIRouter()


def get_utc_now_naive() -> datetime:
    """Return current UTC time without timezone information for MySQL DATETIME."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_active_employee(db: Session, user_id: int) -> Employee:
    """Return the active employee profile linked to the authenticated user."""
    employee = db.scalar(
        select(Employee).where(Employee.user_id == user_id)
    )

    if employee is None or not employee.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No active employee profile is linked to this account",
        )

    return employee


@router.post(
    "/check-in",
    response_model=AttendanceResponse,
    status_code=status.HTTP_201_CREATED,
)
def check_in(
    data: AttendanceCheckIn,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    employee = get_active_employee(db, current_user.id)
    today = date.today()
    attendance_date = data.attendance_date or today

    if attendance_date != today:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can only check in for today's date",
        )

    existing_record = db.scalar(
        select(Attendance).where(
            Attendance.employee_id == employee.id,
            Attendance.attendance_date == attendance_date,
        )
    )

    if existing_record is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Attendance has already been recorded for today",
        )

    attendance = Attendance(
        employee_id=employee.id,
        attendance_date=attendance_date,
        check_in=get_utc_now_naive(),
        status="PRESENT",
        shift_name=data.shift_name,
    )

    try:
        db.add(attendance)
        db.commit()
        db.refresh(attendance)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Attendance has already been recorded for today",
        )

    return attendance


@router.post(
    "/check-out",
    response_model=AttendanceResponse,
    status_code=status.HTTP_200_OK,
)
def check_out(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    employee = get_active_employee(db, current_user.id)
    attendance = db.scalar(
        select(Attendance).where(
            Attendance.employee_id == employee.id,
            Attendance.attendance_date == date.today(),
        )
    )

    if attendance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No attendance check-in found for today",
        )

    if attendance.check_in is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Check-in is required before check-out",
        )

    if attendance.check_out is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already checked out for today",
        )

    checkout_time = get_utc_now_naive()

    if checkout_time < attendance.check_in:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Check-out cannot be earlier than check-in",
        )

    elapsed_seconds = (
        checkout_time - attendance.check_in
    ).total_seconds()

    attendance.working_hours = (
        Decimal(str(elapsed_seconds)) / Decimal("3600")
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    attendance.check_out = checkout_time

    try:
        db.commit()
        db.refresh(attendance)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unable to record check-out",
        )

    return attendance


@router.get(
    "/history",
    response_model=list[AttendanceResponse],
)
def attendance_history(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    employee_id: int | None = Query(default=None, ge=1),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date cannot be later than end_date",
        )

    query = select(Attendance)

    if current_user.role in ("ADMIN", "HR"):
        if employee_id is not None:
            query = query.where(
                Attendance.employee_id == employee_id
            )
    else:
        employee = get_active_employee(db, current_user.id)
        query = query.where(
            Attendance.employee_id == employee.id
        )

    if start_date is not None:
        query = query.where(
            Attendance.attendance_date >= start_date
        )

    if end_date is not None:
        query = query.where(
            Attendance.attendance_date <= end_date
        )

    query = (
        query
        .order_by(
            Attendance.attendance_date.desc(),
            Attendance.id.desc(),
        )
        .offset(skip)
        .limit(limit)
    )

    return db.scalars(query).all()


@router.get(
    "/management",
    response_model=list[AttendanceResponse],
)
def attendance_management(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User, Depends(require_roles("ADMIN", "HR"))
    ],
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    employee_id: int | None = Query(default=None, ge=1),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date cannot be later than end_date",
        )

    query = select(Attendance)

    if employee_id is not None:
        query = query.where(
            Attendance.employee_id == employee_id
        )

    if start_date is not None:
        query = query.where(
            Attendance.attendance_date >= start_date
        )

    if end_date is not None:
        query = query.where(
            Attendance.attendance_date <= end_date
        )

    query = (
        query
        .order_by(
            Attendance.attendance_date.desc(),
            Attendance.id.desc(),
        )
        .offset(skip)
        .limit(limit)
    )

    return db.scalars(query).all()


@router.patch(
    "/management/{attendance_id}",
    response_model=AttendanceResponse,
)
def update_attendance(
    attendance_id: int,
    data: AttendanceAdminUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User, Depends(require_roles("ADMIN", "HR"))
    ],
):
    attendance = db.get(Attendance, attendance_id)

    if attendance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found",
        )

    updates = data.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(attendance, field, value)

    try:
        db.commit()
        db.refresh(attendance)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attendance update violates a database constraint",
        )

    return attendance

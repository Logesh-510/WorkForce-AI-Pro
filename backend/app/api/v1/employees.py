
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.employee import Employee
from app.models.user import User
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeResponse,
    EmployeeUpdate,
)

router = APIRouter()


def get_employee_or_404(db: Session, employee_id: int) -> Employee:
    employee = db.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )
    return employee


@router.post(
    "/",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_employee(
    data: EmployeeCreate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_roles("ADMIN", "HR"))],
):
    user = db.get(User, data.user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A valid active user is required",
        )

    if data.date_of_joining > date.today():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Date of joining cannot be in the future",
        )

    employee = Employee(**data.model_dump())

    try:
        db.add(employee)
        db.commit()
        db.refresh(employee)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Employee code or user is already assigned to an employee",
        )

    return employee


@router.get("/", response_model=list[EmployeeResponse])
def list_employees(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    search: str | None = Query(default=None, max_length=100),
    department: str | None = Query(default=None, max_length=100),
    is_active: bool | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    statement = select(Employee)

    if current_user.role == "EMPLOYEE":
        statement = statement.where(Employee.user_id == current_user.id)

    if search:
        term = f"%{search.strip()}%"
        statement = statement.where(
            Employee.employee_code.ilike(term)
            | Employee.department.ilike(term)
            | Employee.job_title.ilike(term)
        )

    if department:
        statement = statement.where(Employee.department == department)

    if is_active is not None:
        statement = statement.where(Employee.is_active == is_active)

    statement = statement.order_by(Employee.id).offset(skip).limit(limit)
    return list(db.scalars(statement).all())


@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(
    employee_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    employee = get_employee_or_404(db, employee_id)

    if (
        current_user.role == "EMPLOYEE"
        and employee.user_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot access another employee's profile",
        )

    return employee


@router.patch("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: int,
    data: EmployeeUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_roles("ADMIN", "HR"))],
):
    employee = get_employee_or_404(db, employee_id)
    updates = data.model_dump(exclude_unset=True)

    if "date_of_joining" in updates and updates["date_of_joining"] is not None:
        if updates["date_of_joining"] > date.today():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Date of joining cannot be in the future",
            )

    for field, value in updates.items():
        setattr(employee, field, value)

    try:
        db.commit()
        db.refresh(employee)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unable to update employee due to a data conflict",
        )

    return employee


@router.delete("/{employee_id}", status_code=status.HTTP_200_OK)
def deactivate_employee(
    employee_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_roles("ADMIN", "HR"))],
):
    employee = get_employee_or_404(db, employee_id)
    employee.is_active = False

    # Also disable login for this employee.
    user = db.get(User, employee.user_id)
    if user is not None:
        user.is_active = False

    db.commit()

    return {
        "message": "Employee deactivated successfully",
        "employee_id": employee.id,
        "is_active": employee.is_active,
    }

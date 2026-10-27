
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.v1.deps import require_roles
from app.db.session import get_db
from app.models.department import Department
from app.models.user import User
from app.schemas.department import (
    DepartmentCreate,
    DepartmentResponse,
    DepartmentUpdate,
)

router = APIRouter()


def get_department_or_404(
    db: Session,
    department_id: int,
) -> Department:
    department = db.get(Department, department_id)

    if department is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found",
        )

    return department


@router.post(
    "/",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_department(
    data: DepartmentCreate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_roles("ADMIN", "HR"))],
):
    department = Department(
        name=data.name.strip(),
        code=data.code.strip().upper(),
        description=data.description.strip() if data.description else None,
    )

    existing = db.scalar(
        select(Department).where(
            (func.lower(Department.name) == department.name.lower())
            | (func.upper(Department.code) == department.code)
        )
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Department name or code already exists",
        )

    try:
        db.add(department)
        db.commit()
        db.refresh(department)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Department name or code already exists",
        )

    return department


@router.get("/", response_model=list[DepartmentResponse])
def list_departments(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_roles("ADMIN", "HR", "MANAGER"))],
    search: str | None = Query(default=None, max_length=100),
    is_active: bool | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    statement = select(Department)

    if search and search.strip():
        term = f"%{search.strip()}%"
        statement = statement.where(
            Department.name.ilike(term)
            | Department.code.ilike(term)
        )

    if is_active is not None:
        statement = statement.where(Department.is_active == is_active)

    statement = statement.order_by(Department.id).offset(skip).limit(limit)
    return list(db.scalars(statement).all())


@router.get("/{department_id}", response_model=DepartmentResponse)
def get_department(
    department_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_roles("ADMIN", "HR", "MANAGER"))],
):
    return get_department_or_404(db, department_id)


@router.patch("/{department_id}", response_model=DepartmentResponse)
def update_department(
    department_id: int,
    data: DepartmentUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_roles("ADMIN", "HR"))],
):
    department = get_department_or_404(db, department_id)
    updates = data.model_dump(exclude_unset=True)

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide at least one field to update",
        )

    if "name" in updates and updates["name"] is not None:
        updates["name"] = updates["name"].strip()

    if "code" in updates and updates["code"] is not None:
        updates["code"] = updates["code"].strip().upper()

    if "description" in updates and updates["description"] is not None:
        updates["description"] = updates["description"].strip() or None

    new_name = updates.get("name", department.name)
    new_code = updates.get("code", department.code)

    duplicate = db.scalar(
        select(Department).where(
            Department.id != department_id,
            (
                (func.lower(Department.name) == new_name.lower())
                | (func.upper(Department.code) == new_code.upper())
            ),
        )
    )

    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Another department already uses this name or code",
        )

    for field, value in updates.items():
        setattr(department, field, value)

    try:
        db.commit()
        db.refresh(department)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Department update conflicts with an existing record",
        )

    return department


@router.delete("/{department_id}")
def deactivate_department(
    department_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_roles("ADMIN", "HR"))],
):
    department = get_department_or_404(db, department_id)

    if not department.is_active:
        return {
            "message": "Department is already inactive",
            "department_id": department.id,
            "is_active": False,
        }

    department.is_active = False
    db.commit()

    return {
        "message": "Department deactivated successfully",
        "department_id": department.id,
        "is_active": False,
    }

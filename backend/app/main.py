from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.auth import router as auth_router
from app.api.v1.employees import router as employees_router
from app.api.v1.departments import router as departments_router
from app.api.v1.attendance import router as attendance_router
from app.api.v1.leaves import router as leaves_router
from app.api.v1.predictions import router as predictions_router

from app.db.session import Base, engine

from app.models.employee import Employee
from app.models.attendance import Attendance
from app.models.user import User
from app.models.department import Department
from app.models.leave import LeaveRequest

app = FastAPI(
    title="WorkForce AI Pro",
    description="HR Attrition Prediction & Workforce Intelligence Platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create missing tables for the currently registered models.
Base.metadata.create_all(bind=engine)

app.include_router(
    auth_router,
    prefix="/api/v1/auth",
    tags=["Authentication"],
)

app.include_router(
    employees_router,
    prefix="/api/v1/employees",
    tags=["Employee Management"],
)

app.include_router(
    departments_router,
    prefix="/api/v1/departments",
    tags=["Department Management"],
)

app.include_router(
    attendance_router,
    prefix="/api/v1/attendance",
    tags=["Attendance Management"],
)

app.include_router(
    leaves_router,
    prefix="/api/v1/leaves",
    tags=["Leave Management"],
)

app.include_router(predictions_router)

@app.get("/", tags=["System"])
def root():
    return {
        "message": "Welcome to WorkForce AI Pro",
        "status": "running",
        "version": "1.0.0",
    }


@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "service": "WorkForce AI Pro API",
    }

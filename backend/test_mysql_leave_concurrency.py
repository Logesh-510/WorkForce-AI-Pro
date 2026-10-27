
import os
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

import httpx
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.core.security import hash_password
from app.db.session import SessionLocal, engine
from app.models.employee import Employee
from app.models.leave import LeaveRequest
from app.models.user import User


API_URL = "http://127.0.0.1:8001"
TEST_MARKER = f"CT{uuid.uuid4().hex[:8]}"
TEST_PASSWORD = f"Temporary-{uuid.uuid4().hex}-A9!"
DEPARTMENT = "Concurrency Test"
JOB_TITLE = "Integration Test Employee"

created_user_id = None
created_employee_id = None
created_leave_ids = []


def create_test_employee():
    global created_user_id, created_employee_id

    with SessionLocal() as db:
        user = User(
            full_name="Temporary Concurrency Test",
            email=f"{TEST_MARKER.lower()}@example.invalid",
            hashed_password=hash_password(TEST_PASSWORD),
            role="EMPLOYEE",
            is_active=True,
        )
        db.add(user)
        db.flush()

        employee = Employee(
            employee_code=TEST_MARKER,
            user_id=user.id,
            department=DEPARTMENT,
            job_title=JOB_TITLE,
            employment_type="FULL_TIME",
            date_of_joining=date.today(),
            annual_salary=0,
            is_active=True,
        )
        db.add(employee)
        db.commit()

        created_user_id = user.id
        created_employee_id = employee.id

    print("Temporary test account created.")


def submit_leave_request(token, start_date, end_date, reason):
    try:
        response = httpx.post(
            f"{API_URL}/api/v1/leaves/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "leave_type": "CASUAL",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "reason": reason,
            },
            timeout=30,
        )
        try:
            body = response.json()
        except ValueError:
            body = response.text

        return response.status_code, body

    except httpx.RequestException as exc:
        return None, str(exc)


def cleanup():
    if created_user_id is None:
        return

    print("Cleaning up temporary test records...")

    try:
        with SessionLocal() as db:
            # Delete only leave records belonging to our temporary employee.
            if created_employee_id is not None:
                db.query(LeaveRequest).filter(
                    LeaveRequest.employee_id == created_employee_id
                ).delete(synchronize_session=False)

                db.query(Employee).filter(
                    Employee.id == created_employee_id,
                    Employee.employee_code == TEST_MARKER,
                    Employee.user_id == created_user_id,
                ).delete(synchronize_session=False)

            db.query(User).filter(
                User.id == created_user_id,
                User.email == f"{TEST_MARKER.lower()}@example.invalid",
            ).delete(synchronize_session=False)

            db.commit()

        print("Temporary test records cleaned up.")

    except SQLAlchemyError as exc:
        print("WARNING: Automatic cleanup failed.")
        print(f"Error type: {type(exc).__name__}")
        print(
            "Please inspect the temporary test account before "
            "running this test again."
        )



def main():
    if engine.dialect.name != "mysql":
        raise RuntimeError(
            "Safety check failed: this integration test requires MySQL."
        )

    health = httpx.get(f"{API_URL}/health", timeout=10)
    health.raise_for_status()
    print("API health check passed.")

    try:
        # Include setup inside the cleanup block.
        create_test_employee()

        with SessionLocal() as db:
            employee = db.scalar(
                select(Employee).where(
                    Employee.id == created_employee_id,
                    Employee.employee_code == TEST_MARKER,
                )
            )
            user = db.get(User, created_user_id)

            if employee is None or user is None:
                raise RuntimeError(
                    "Temporary test account was not found."
                )

            from app.core.security import create_access_token

            token = create_access_token(user.id, user.role)

        start_date = date.today() + timedelta(days=30)
        end_date = start_date + timedelta(days=1)

        barrier = threading.Barrier(2)

        def request_a():
            barrier.wait(timeout=10)
            return submit_leave_request(
                token,
                start_date,
                end_date,
                "Concurrency integration test request A",
            )

        def request_b():
            barrier.wait(timeout=10)
            return submit_leave_request(
                token,
                start_date,
                end_date,
                "Concurrency integration test request B",
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            future_a = pool.submit(request_a)
            future_b = pool.submit(request_b)
            results = [future_a.result(), future_b.result()]

        print("\nConcurrent API responses:")
        for index, (code, body) in enumerate(results, start=1):
            print(f"Request {index}: HTTP {code}")
            print(f"Response: {body}")

        with SessionLocal() as db:
            saved_leaves = list(
                db.scalars(
                    select(LeaveRequest).where(
                        LeaveRequest.employee_id == created_employee_id,
                        LeaveRequest.start_date <= end_date,
                        LeaveRequest.end_date >= start_date,
                    )
                ).all()
            )

        print(f"\nMatching saved leave requests: {len(saved_leaves)}")

        codes = [code for code, _ in results]

        if (
            codes.count(201) == 1
            and codes.count(409) == 1
            and len(saved_leaves) == 1
        ):
            print("PASS: overlapping concurrent requests were serialized.")
        else:
            print(
                "FAIL: expected one HTTP 201, one HTTP 409, "
                "and exactly one saved matching request."
            )
            raise AssertionError(
                "MySQL leave concurrency test did not meet expectations."
            )

    finally:
        cleanup()

if __name__ == "__main__":
    main()
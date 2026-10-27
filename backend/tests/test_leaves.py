from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.models.employee import Employee
from app.models.user import User
from app.core.security import hash_password


@pytest.fixture
def leave_employee(db_session):
    user = User(
        full_name="Leave Employee",
        email="leave.employee@example.com",
        hashed_password=hash_password("Test-Password-123!"),
        role="EMPLOYEE",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    employee = Employee(
        employee_code="LEAVE-001",
        user_id=user.id,
        department="IT",
        job_title="Software Engineer",
        employment_type="FULL_TIME",
        date_of_joining=date.today(),
        annual_salary=Decimal("50000.00"),
        is_active=True,
    )
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture
def second_leave_employee(db_session):
    user = User(
        full_name="Second Leave Employee",
        email="leave.employee2@example.com",
        hashed_password=hash_password("Test-Password-123!"),
        role="EMPLOYEE",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    employee = Employee(
        employee_code="LEAVE-002",
        user_id=user.id,
        department="QA",
        job_title="QA Engineer",
        employment_type="FULL_TIME",
        date_of_joining=date.today(),
        annual_salary=Decimal("45000.00"),
        is_active=True,
    )
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture
def leave_admin(db_session):
    user = User(
        full_name="Leave Admin",
        email="leave.admin@example.com",
        hashed_password=hash_password("Test-Password-123!"),
        role="ADMIN",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


def valid_leave_payload():
    start = date.today() + timedelta(days=5)

    return {
        "leave_type": "CASUAL",
        "start_date": start.isoformat(),
        "end_date": (start + timedelta(days=1)).isoformat(),
        "reason": "Personal work and family commitments",
    }


def submit_leave(client, auth_state, user):
    auth_state["user"] = user

    return client.post(
        "/api/v1/leaves/",
        json=valid_leave_payload(),
    )


def test_employee_can_create_leave_request(
    client, auth_state, leave_employee
):
    response = submit_leave(client, auth_state, leave_employee)

    assert response.status_code == 201
    assert response.json()["status"] == "PENDING"
    assert response.json()["leave_type"] == "CASUAL"
    assert response.json()["employee_id"] > 0
    assert response.json()["reviewed_by"] is None


@pytest.mark.parametrize(
    "date_changes",
    [
        {"start_date": (date.today() - timedelta(days=1)).isoformat()},
        {
            "start_date": (date.today() + timedelta(days=10)).isoformat(),
            "end_date": (date.today() + timedelta(days=9)).isoformat(),
        },
    ],
)
def test_invalid_leave_dates_return_422(
    client, auth_state, leave_employee, date_changes
):
    auth_state["user"] = leave_employee
    payload = valid_leave_payload()
    payload.update(date_changes)

    response = client.post("/api/v1/leaves/", json=payload)

    assert response.status_code == 422


def test_employee_can_list_own_leave_requests(
    client, auth_state, leave_employee
):
    created = submit_leave(client, auth_state, leave_employee)
    assert created.status_code == 201

    response = client.get("/api/v1/leaves/")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["employee_id"] == created.json()["employee_id"]


def test_employee_cannot_view_another_employees_leave(
    client, auth_state, leave_employee, second_leave_employee
):
    created = submit_leave(client, auth_state, leave_employee)
    assert created.status_code == 201

    auth_state["user"] = second_leave_employee

    response = client.get(
        f"/api/v1/leaves/{created.json()['id']}"
    )

    assert response.status_code == 403


def test_employee_cannot_review_leave_request(
    client, auth_state, leave_employee
):
    created = submit_leave(client, auth_state, leave_employee)
    assert created.status_code == 201

    response = client.patch(
        f"/api/v1/leaves/{created.json()['id']}/review",
        json={"status": "APPROVED"},
    )

    assert response.status_code == 403


def test_admin_can_approve_leave_and_repeat_review_is_rejected(
    client, auth_state, leave_employee, leave_admin
):
    created = submit_leave(client, auth_state, leave_employee)
    assert created.status_code == 201

    auth_state["user"] = leave_admin

    review_url = f"/api/v1/leaves/{created.json()['id']}/review"

    response = client.patch(
        review_url,
        json={
            "status": "APPROVED",
            "review_comment": "Approved for the requested dates",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"
    assert response.json()["reviewed_by"] == leave_admin.id

    repeated = client.patch(
        review_url,
        json={"status": "REJECTED"},
    )

    assert repeated.status_code == 409


def test_overlapping_pending_leave_returns_conflict(
    client, auth_state, leave_employee
):
    first = submit_leave(client, auth_state, leave_employee)
    assert first.status_code == 201

    overlapping_payload = valid_leave_payload()
    overlapping_payload["start_date"] = first.json()["start_date"]
    overlapping_payload["end_date"] = first.json()["end_date"]

    second = client.post(
        "/api/v1/leaves/",
        json=overlapping_payload,
    )

    assert second.status_code == 409


def test_employee_can_cancel_own_pending_leave(
    client, auth_state, leave_employee
):
    created = submit_leave(client, auth_state, leave_employee)
    assert created.status_code == 201

    leave_id = created.json()["id"]

    response = client.post(
        f"/api/v1/leaves/{leave_id}/cancel"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"


def test_employee_cannot_cancel_another_employees_leave(
    client, auth_state, leave_employee, second_leave_employee
):
    created = submit_leave(client, auth_state, leave_employee)
    assert created.status_code == 201

    auth_state["user"] = second_leave_employee

    response = client.post(
        f"/api/v1/leaves/{created.json()['id']}/cancel"
    )

    assert response.status_code == 403


def test_employee_cannot_cancel_approved_leave(
    client, auth_state, leave_employee, leave_admin
):
    created = submit_leave(client, auth_state, leave_employee)
    assert created.status_code == 201

    leave_id = created.json()["id"]

    auth_state["user"] = leave_admin

    review_response = client.patch(
        f"/api/v1/leaves/{leave_id}/review",
        json={"status": "APPROVED"},
    )

    assert review_response.status_code == 200

    auth_state["user"] = leave_employee

    cancel_response = client.post(
        f"/api/v1/leaves/{leave_id}/cancel"
    )

    assert cancel_response.status_code == 409
    assert cancel_response.json()["detail"] == (
        "Only pending leave requests can be cancelled"
    )

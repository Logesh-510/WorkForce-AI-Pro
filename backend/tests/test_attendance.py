from datetime import date
from decimal import Decimal

import pytest

from app.models.employee import Employee
from app.models.user import User


@pytest.fixture
def employee_user(db_session):
    user = User(
        full_name="Test Employee",
        email="test.employee@example.com",
        hashed_password="test-only-hash",
        role="EMPLOYEE",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    employee = Employee(
        employee_code="TEST-001",
        user_id=user.id,
        department="IT",
        job_title="QA Engineer",
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
def admin_user(db_session):
    user = User(
        full_name="Test Admin",
        email="test.admin@example.com",
        hashed_password="test-only-hash",
        role="ADMIN",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_check_in_success(client, auth_state, employee_user):
    auth_state["user"] = employee_user

    response = client.post(
        "/api/v1/attendance/check-in",
        json={"shift_name": "General"},
    )

    assert response.status_code == 201
    assert response.json()["status"] == "PRESENT"
    assert response.json()["check_in"] is not None


def test_duplicate_check_in_returns_conflict(
    client, auth_state, employee_user
):
    auth_state["user"] = employee_user

    first = client.post(
        "/api/v1/attendance/check-in",
        json={"shift_name": "General"},
    )
    second = client.post(
        "/api/v1/attendance/check-in",
        json={"shift_name": "General"},
    )

    assert first.status_code == 201
    assert second.status_code == 409


def test_check_out_without_check_in_returns_not_found(
    client, auth_state, employee_user
):
    auth_state["user"] = employee_user

    response = client.post(
        "/api/v1/attendance/check-out",
        json={},
    )

    assert response.status_code == 404


def test_check_out_success(client, auth_state, employee_user):
    auth_state["user"] = employee_user

    check_in_response = client.post(
        "/api/v1/attendance/check-in",
        json={"shift_name": "General"},
    )
    assert check_in_response.status_code == 201

    response = client.post(
        "/api/v1/attendance/check-out",
        json={},
    )

    assert response.status_code == 200
    assert response.json()["check_out"] is not None
    assert Decimal(response.json()["working_hours"]) >= Decimal("0")


def test_duplicate_check_out_returns_conflict(
    client, auth_state, employee_user
):
    auth_state["user"] = employee_user

    check_in_response = client.post(
        "/api/v1/attendance/check-in",
        json={"shift_name": "General"},
    )
    assert check_in_response.status_code == 201

    first = client.post(
        "/api/v1/attendance/check-out",
        json={},
    )
    second = client.post(
        "/api/v1/attendance/check-out",
        json={},
    )

    assert first.status_code == 200
    assert second.status_code == 409


def test_employee_cannot_access_management(
    client, auth_state, employee_user
):
    auth_state["user"] = employee_user

    response = client.get("/api/v1/attendance/management")

    assert response.status_code == 403


def test_admin_can_access_management(
    client, auth_state, admin_user
):
    auth_state["user"] = admin_user

    response = client.get("/api/v1/attendance/management")

    assert response.status_code == 200


def test_admin_can_update_attendance_notes(
    client, auth_state, employee_user, admin_user
):
    auth_state["user"] = employee_user

    check_in_response = client.post(
        "/api/v1/attendance/check-in",
        json={"shift_name": "General"},
    )
    assert check_in_response.status_code == 201
    attendance_id = check_in_response.json()["id"]

    auth_state["user"] = admin_user
    response = client.patch(
        f"/api/v1/attendance/management/{attendance_id}",
        json={"notes": "Automated test correction"},
    )

    assert response.status_code == 200
    assert response.json()["notes"] == "Automated test correction"


def test_admin_cannot_set_invalid_attendance_status(
    client, auth_state, admin_user
):
    auth_state["user"] = admin_user

    response = client.patch(
        "/api/v1/attendance/management/1",
        json={"status": "HOLIDAY"},
    )

    assert response.status_code == 422


def test_admin_cannot_set_null_attendance_status(
    client, auth_state, admin_user
):
    auth_state["user"] = admin_user

    response = client.patch(
        "/api/v1/attendance/management/1",
        json={"status": None},
    )

    assert response.status_code == 422


def test_admin_update_missing_attendance_returns_not_found(
    client, auth_state, admin_user
):
    auth_state["user"] = admin_user

    response = client.patch(
        "/api/v1/attendance/management/999999",
        json={"notes": "Missing record test"},
    )

    assert response.status_code == 404

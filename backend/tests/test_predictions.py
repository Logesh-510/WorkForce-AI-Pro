
from app.models.user import User


VALID_PAYLOAD = {
    "Age": 35,
    "Department": "Research & Development",
    "JobRole": "Research Scientist",
    "MonthlyIncome": 5000,
    "YearsAtCompany": 5,
    "JobSatisfaction": 3,
    "WorkLifeBalance": 3,
    "OverTime": "No",
}


def test_employee_cannot_access_prediction(client, auth_state):
    auth_state["user"] = User(
        id=101,
        full_name="Test Employee",
        email="employee@example.com",
        hashed_password="not-a-real-password-hash",
        role="EMPLOYEE",
        is_active=True,
    )

    response = client.post(
        "/api/v1/predictions/attrition",
        json=VALID_PAYLOAD,
    )

    assert response.status_code == 403


def test_admin_can_request_prediction(client, auth_state):
    auth_state["user"] = User(
        id=102,
        full_name="Test Admin",
        email="admin@example.com",
        hashed_password="not-a-real-password-hash",
        role="ADMIN",
        is_active=True,
    )

    response = client.post(
        "/api/v1/predictions/attrition",
        json=VALID_PAYLOAD,
    )

    assert response.status_code == 200, response.text

    data = response.json()
    assert data["prediction"] in {"Yes", "No"}
    assert 0 <= data["attrition_probability"] <= 1
    assert data["risk_level"] in {"LOW", "MODERATE", "HIGH"}
    assert data["model"] == "LogisticRegression"
    assert "not a validated assessment" in data["disclaimer"]


def test_invalid_prediction_payload_returns_422(client, auth_state):
    auth_state["user"] = User(
        id=103,
        full_name="Test HR",
        email="hr@example.com",
        hashed_password="not-a-real-password-hash",
        role="HR",
        is_active=True,
    )

    invalid_payload = {**VALID_PAYLOAD, "OverTime": "Sometimes"}

    response = client.post(
        "/api/v1/predictions/attrition",
        json=invalid_payload,
    )

    assert response.status_code == 422

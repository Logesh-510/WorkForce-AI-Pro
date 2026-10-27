from datetime import timedelta

import jwt
import pytest

from app.api.v1.deps import get_current_user
from app.core.security import (
    ALGORITHM,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.main import app
from app.models.user import User


def test_password_is_hashed_and_verifies():
    password = "Test-Password-123!"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("Wrong-Password!", hashed)


def test_valid_token_contains_expected_claims():
    token = create_access_token(user_id=123, role="EMPLOYEE")
    payload = decode_access_token(token)

    assert payload["sub"] == "123"
    assert payload["role"] == "EMPLOYEE"
    assert "iat" in payload
    assert "exp" in payload


def test_expired_token_is_rejected():
    token = create_access_token(
        user_id=123,
        role="EMPLOYEE",
        expires_delta=timedelta(seconds=-1),
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)


def test_token_signed_with_wrong_secret_is_rejected():
    wrong_secret = "different-test-secret-key-at-least-32-bytes-long"

    token = jwt.encode(
        {"sub": "123", "role": "EMPLOYEE"},
        wrong_secret,
        algorithm=ALGORITHM,
    )

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(token)


def test_register_success(client, db_session):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Registration Test",
            "email": "registration.test@example.com",
            "password": "Test-Password-123!",
        },
    )

    assert response.status_code == 201

    data = response.json()
    assert data["email"] == "registration.test@example.com"
    assert data["role"] == "EMPLOYEE"
    assert "hashed_password" not in data
    assert "password" not in data

    user = (
        db_session.query(User)
        .filter_by(email="registration.test@example.com")
        .one()
    )

    assert user.hashed_password != "Test-Password-123!"
    assert verify_password(
        "Test-Password-123!",
        user.hashed_password,
    )


def test_register_duplicate_email_returns_conflict(client):
    payload = {
        "full_name": "Duplicate Test",
        "email": "duplicate.test@example.com",
        "password": "Test-Password-123!",
    }

    first = client.post("/api/v1/auth/register", json=payload)
    second = client.post("/api/v1/auth/register", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


@pytest.mark.parametrize(
    "payload",
    [
        {
            "full_name": "A",
            "email": "short.name@example.com",
            "password": "Test-Password-123!",
        },
        {
            "full_name": "Invalid Email",
            "email": "not-an-email",
            "password": "Test-Password-123!",
        },
        {
            "full_name": "Short Password",
            "email": "short.password@example.com",
            "password": "short",
        },
    ],
)
def test_register_invalid_payload_returns_422(client, payload):
    response = client.post(
        "/api/v1/auth/register",
        json=payload,
    )

    assert response.status_code == 422


def test_login_success(client, db_session):
    password = "Test-Password-123!"

    user = User(
        full_name="Login Test",
        email="login.test@example.com",
        hashed_password=hash_password(password),
        role="EMPLOYEE",
        is_active=True,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "login.test@example.com",
            "password": password,
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["token_type"] == "bearer"
    assert decode_access_token(data["access_token"])["sub"] == str(user.id)


def test_login_wrong_password_returns_401(client, db_session):
    user = User(
        full_name="Wrong Password Test",
        email="wrong.password@example.com",
        hashed_password=hash_password("Correct-Password-123!"),
        role="EMPLOYEE",
        is_active=True,
    )

    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "wrong.password@example.com",
            "password": "Wrong-Password-123!",
        },
    )

    assert response.status_code == 401


def test_login_unknown_email_returns_401(client):
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "unknown.user@example.com",
            "password": "Test-Password-123!",
        },
    )

    assert response.status_code == 401


def test_inactive_user_cannot_login(client, db_session):
    user = User(
        full_name="Inactive Test",
        email="inactive.test@example.com",
        hashed_password=hash_password("Test-Password-123!"),
        role="EMPLOYEE",
        is_active=False,
    )

    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "inactive.test@example.com",
            "password": "Test-Password-123!",
        },
    )

    assert response.status_code == 401


def test_me_requires_authentication(client):
    # Remove the shared fixture's mock to test real JWT authentication.
    app.dependency_overrides.pop(get_current_user, None)

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_me_returns_authenticated_user(client, db_session):
    user = User(
        full_name="Current User Test",
        email="current.user@example.com",
        hashed_password=hash_password("Test-Password-123!"),
        role="EMPLOYEE",
        is_active=True,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token(
        user_id=user.id,
        role=user.role,
    )

    # Remove the mock so the endpoint validates the JWT and loads the user.
    app.dependency_overrides.pop(get_current_user, None)

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "current.user@example.com"
    assert "hashed_password" not in response.json()

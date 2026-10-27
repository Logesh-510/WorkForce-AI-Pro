import os

# Set test configuration before importing the application.
os.environ["DATABASE_URL"] = "sqlite:///./workforce_test.db"
os.environ["SECRET_KEY"] = "test-only-secret-key-not-for-production"

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import Base, SessionLocal, engine, get_db
from app.api.v1.deps import get_current_user

if engine.dialect.name != "sqlite":
    raise RuntimeError(
        "Safety check failed: automated tests must use SQLite, not MySQL."
    )

@pytest.fixture(autouse=True)
def reset_test_database():
    """Reset only the separate SQLite test database for each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def auth_state():
    """Allow tests to switch between test users and roles."""
    return {"user": None}


@pytest.fixture
def client(auth_state):
    """Create a test client using test-only database sessions."""

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = (
        lambda: auth_state["user"]
    )

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def db_session():
    """Provide a database session for creating test records."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

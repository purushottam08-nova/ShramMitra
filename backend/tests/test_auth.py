
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.api.auth import get_db as auth_get_db
from app.core.security import verify_password
from app.db.database import Base
from app.main import app
from app.models.user import User


@pytest.fixture
def auth_test_setup():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False,
    )

    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()

    def override_db():
        yield db

    app.dependency_overrides[auth_get_db] = override_db

    try:
        with TestClient(app) as client:
            yield client, db
    finally:
        app.dependency_overrides.clear()
        db.close()
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()


def test_register_creates_worker_with_hashed_password(auth_test_setup):
    client, db = auth_test_setup

    response = client.post(
        "/auth/register",
        json={
            "full_name": "Test Worker",
            "mobile": "9000000101",
            "password": "StrongPass123!",
        },
    )

    assert response.status_code == 200
    assert response.json()["message"] == "User registered successfully"

    user = db.query(User).filter(User.mobile == "9000000101").one()

    assert user.role == "WORKER"
    assert user.password_hash != "StrongPass123!"
    assert verify_password("StrongPass123!", user.password_hash)


def test_register_rejects_admin_role_in_request(auth_test_setup):
    client, db = auth_test_setup

    response = client.post(
        "/auth/register",
        json={
            "full_name": "Test Admin",
            "mobile": "9000000102",
            "password": "StrongPass123!",
            "role": "ADMIN",
        },
    )

    assert response.status_code == 422
    assert db.query(User).filter(User.mobile == "9000000102").count() == 0
    assert db.query(User).count() == 0


from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.core.auth import get_db, get_current_user
from app.core.security import ALGORITHM, SECRET_KEY, create_access_token
from app.db.database import Base
from app.main import app
from app.models.user import User


@pytest.fixture
def jwt_test_setup():
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

    user = User(
        full_name="JWT Test Worker",
        mobile="9000000201",
        password_hash="test-hash",
        role="WORKER",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db

    try:
        with TestClient(app) as client:
            yield client, db, user
    finally:
        app.dependency_overrides.clear()
        db.close()
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()


def test_valid_token_can_access_auth_me(jwt_test_setup):
    client, db, user = jwt_test_setup
    token = create_access_token(user.id)

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == user.id
    assert response.json()["mobile"] == user.mobile


def test_expired_token_is_rejected(jwt_test_setup):
    client, db, user = jwt_test_setup

    token = jwt.encode(
        {
            "sub": str(user.id),
            "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401


def test_tampered_token_is_rejected(jwt_test_setup):
    client, db, user = jwt_test_setup
    token = create_access_token(user.id)

    tampered_token = token[:-1] + ("A" if token[-1] != "A" else "B")

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {tampered_token}"},
    )

    assert response.status_code == 401


def test_malformed_subject_is_rejected(jwt_test_setup):
    client, db, user = jwt_test_setup

    token = jwt.encode(
        {
            "sub": "abc",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401


def test_token_for_nonexistent_user_is_rejected(jwt_test_setup):
    client, db, user = jwt_test_setup
    token = create_access_token(999999)

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401



def test_missing_token_is_rejected(jwt_test_setup):
    client, db, user = jwt_test_setup

    response = client.get("/auth/me")

    assert response.status_code in (401, 403)


def test_worker_token_cannot_access_admin_endpoint(jwt_test_setup):
    client, db, user = jwt_test_setup
    token = create_access_token(user.id)

    response = client.post(
        "/admin/schemes/1/verify",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "source_url": "https://www.india.gov.in/",
            "notes": "Checked against the official government source.",
            "version": "2.0",
        },
    )

    assert response.status_code == 403


from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # Registers all SQLAlchemy models
from app.db.database import Base
from app.main import app
from app.api.auth import get_db as dashboard_get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.scheme import Scheme
from app.models.application import Application
from app.models.grievance import Grievance
from app.models.grievance_status_history import GrievanceStatusHistory 


@pytest.fixture
def dashboard_test_setup():
    # Separate in-memory database for testing.
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
        full_name="Test Worker",
        mobile="9000000001",
        password_hash="test-hash",
    )
    db.add(user)

    scheme = Scheme(
        name="Test Scheme",
        description="Scheme created only for automated testing",
        category="SOCIAL_SECURITY",
        level="CENTRAL",
        source_url="https://example.com/test-scheme",
        verification_status="VERIFIED",
        version="1.0",
        status="ACTIVE",
    )
    db.add(scheme)
    db.commit()
    db.refresh(user)
    db.refresh(scheme)

    def override_dashboard_db():
        yield db

    def override_current_user():
        return user

    app.dependency_overrides[dashboard_get_db] = override_dashboard_db
    app.dependency_overrides[get_current_user] = override_current_user

    try:
        with TestClient(app) as client:
            yield client, db, user, scheme
    finally:
        app.dependency_overrides.clear()
        db.close()
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()


def test_dashboard_returns_empty_counts(dashboard_test_setup):
    client, _, _, _ = dashboard_test_setup

    response = client.get("/dashboard/me")

    assert response.status_code == 200

    data = response.json()
    assert data["applications_count"] == 0
    assert data["active_applications_count"] == 0
    assert data["open_grievances_count"] == 0
    assert data["applications"] == []
    assert data["grievances"] == []


def test_dashboard_counts_applications_and_grievances(
    dashboard_test_setup,
):
    client, db, user, scheme = dashboard_test_setup

    db.add_all([
        Application(
            user_id=user.id,
            scheme_id=scheme.id,
            status="SUBMITTED",
            application_date=datetime.utcnow(),
        ),
        Application(
            user_id=user.id,
            scheme_id=scheme.id,
            status="APPROVED",
            application_date=datetime.utcnow(),
        ),
        Grievance(
            user_id=user.id,
            subject="Application status delayed",
            description="My application status has not changed.",
            status="OPEN",
        ),
        Grievance(
            user_id=user.id,
            subject="Resolved document issue",
            description="The document issue has been resolved.",
            status="RESOLVED",
        ),
    ])
    db.commit()

    response = client.get("/dashboard/me")

    assert response.status_code == 200

    data = response.json()
    assert data["applications_count"] == 2
    assert data["active_applications_count"] == 1
    assert data["open_grievances_count"] == 1
    assert len(data["applications"]) == 2
    assert len(data["grievances"]) == 2

    submitted = next(
        item for item in data["applications"]
        if item["status"] == "SUBMITTED"
    )
    assert submitted["next_action"]
    assert submitted["days_in_current_status"] is not None


def test_dashboard_only_returns_current_users_data(
    dashboard_test_setup,
):
    client, db, _, scheme = dashboard_test_setup

    other_user = User(
        full_name="Another Worker",
        mobile="9000000002",
        password_hash="test-hash",
    )
    db.add(other_user)
    db.commit()
    db.refresh(other_user)

    db.add(
        Application(
            user_id=other_user.id,
            scheme_id=scheme.id,
            status="SUBMITTED",
        )
    )
    db.commit()

    response = client.get("/dashboard/me")

    assert response.status_code == 200
    data = response.json()
    assert data["applications_count"] == 0
    assert data["applications"] == []


def test_dashboard_requires_authentication():
    response = TestClient(app).get("/dashboard/me")

    assert response.status_code == 401



def test_grievance_pending_days_use_latest_status_change(
    dashboard_test_setup,
):
    client, db, user, _ = dashboard_test_setup

    grievance = Grievance(
        user_id=user.id,
        subject="Delayed grievance",
        description="This grievance needs status tracking.",
        status="IN_PROGRESS",
        created_at=datetime.utcnow() - timedelta(days=10),
    )
    db.add(grievance)
    db.flush()

    db.add(
        GrievanceStatusHistory(
            grievance_id=grievance.id,
            status="IN_PROGRESS",
            note="Grievance moved to in progress",
            changed_at=datetime.utcnow() - timedelta(days=2),
        )
    )
    db.commit()

    response = client.get("/dashboard/me")

    assert response.status_code == 200

    grievance_item = response.json()["grievances"][0]

    assert grievance_item["status"] == "IN_PROGRESS"
    assert grievance_item["days_pending"] == 2

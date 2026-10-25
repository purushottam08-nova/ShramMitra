
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.core.auth import get_db
from app.core.auth import get_current_user
from app.db.database import Base
from app.main import app
from app.models.scheme import Scheme
from app.models.scheme_verification_history import SchemeVerificationHistory
from app.models.user import User



@pytest.fixture
def admin_test_setup():
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

    worker = User(
        full_name="Test Worker",
        mobile="9000000011",
        password_hash="test-hash",
        role="WORKER",
    )
    admin_user = User(
        full_name="Test Admin",
        mobile="9000000012",
        password_hash="test-hash",
        role="ADMIN",
    )

    db.add_all([worker, admin_user])
    db.commit()
    db.refresh(worker)
    db.refresh(admin_user)

    scheme = Scheme(
        name="Test Scheme",
        description="Test scheme description",
        category="SOCIAL_SECURITY",
        level="CENTRAL",
        source_url="https://example.gov.in/test-scheme",
        verification_status="PENDING",
        version="1.0",
        status="ACTIVE",
    )
    db.add(scheme)
    db.commit()
    db.refresh(scheme)

    active_user = {"user": worker}

    def override_db():
        yield db

    def override_current_user():
        return active_user["user"]

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_current_user

    try:
        with TestClient(app) as client:
            yield client, db, worker, admin_user, scheme, active_user
    finally:
        app.dependency_overrides.clear()
        db.close()
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()


def verification_payload():
    return {
        "source_url": "https://www.india.gov.in/",
        "notes": "Checked against the official government source.",
        "version": "2.0",
    }


def test_worker_cannot_verify_scheme(admin_test_setup):
    client, db, worker, admin_user, scheme, active_user = admin_test_setup

    response = client.post(
        f"/admin/schemes/{scheme.id}/verify",
        json=verification_payload(),
    )

    assert response.status_code == 403
    assert db.query(SchemeVerificationHistory).count() == 0


def test_admin_can_verify_scheme_and_create_history(admin_test_setup):
    client, db, worker, admin_user, scheme, active_user = admin_test_setup
    active_user["user"] = admin_user

    response = client.post(
        f"/admin/schemes/{scheme.id}/verify",
        json=verification_payload(),
    )

    assert response.status_code == 200
    assert response.json()["verification_status"] == "VERIFIED"
    assert response.json()["version"] == "2.0"

    db.refresh(scheme)
    assert scheme.verification_status == "VERIFIED"
    assert scheme.source_url == "https://www.india.gov.in/"

    history = db.query(SchemeVerificationHistory).one()
    assert history.scheme_id == scheme.id
    assert history.verifier_id == admin_user.id
    assert history.previous_status == "PENDING"
    assert history.new_status == "VERIFIED"
    assert history.notes == verification_payload()["notes"]


def test_admin_verifying_missing_scheme_returns_404(admin_test_setup):
    client, db, worker, admin_user, scheme, active_user = admin_test_setup
    active_user["user"] = admin_user

    response = client.post(
        "/admin/schemes/99999/verify",
        json=verification_payload(),
    )

    assert response.status_code == 404
    assert db.query(SchemeVerificationHistory).count() == 0


@pytest.mark.parametrize(
    "payload",
    [
        {
            "source_url": "not-a-valid-url",
            "notes": "Checked against the official government source.",
            "version": "2.0",
        },
        {
            "source_url": "https://www.india.gov.in/",
            "notes": "short",
            "version": "2.0",
        },
        {
            "source_url": "https://www.india.gov.in/",
            "notes": "Checked against the official government source.",
            "version": "2.0",
            "verification_status": "VERIFIED",
        },
    ],
)
def test_invalid_verification_payload_is_rejected(admin_test_setup, payload):
    client, db, worker, admin_user, scheme, active_user = admin_test_setup
    active_user["user"] = admin_user

    response = client.post(
        f"/admin/schemes/{scheme.id}/verify",
        json=payload,
    )

    assert response.status_code == 422
    assert db.query(SchemeVerificationHistory).count() == 0



def test_failed_commit_rolls_back_scheme_and_history(
    admin_test_setup, monkeypatch
):
    client, db, worker, admin_user, scheme, active_user = admin_test_setup
    active_user["user"] = admin_user

    def fail_commit():
        raise RuntimeError("Simulated database commit failure")

    monkeypatch.setattr(db, "commit", fail_commit)

    response = client.post(
        f"/admin/schemes/{scheme.id}/verify",
        json=verification_payload(),
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Could not save scheme verification"

    db.refresh(scheme)
    assert scheme.verification_status == "PENDING"
    assert scheme.version == "1.0"

    assert db.query(SchemeVerificationHistory).count() == 0



def test_reverification_preserves_previous_history(admin_test_setup):
    client, db, worker, admin_user, scheme, active_user = admin_test_setup
    active_user["user"] = admin_user

    first_payload = verification_payload()

    first_response = client.post(
        f"/admin/schemes/{scheme.id}/verify",
        json=first_payload,
    )
    assert first_response.status_code == 200

    first_history_id = first_response.json()["history_id"]

    second_payload = {
        "source_url": "https://www.myscheme.gov.in/",
        "notes": "Rechecked the scheme against the official source.",
        "version": "3.0",
    }

    second_response = client.post(
        f"/admin/schemes/{scheme.id}/verify",
        json=second_payload,
    )
    assert second_response.status_code == 200
    assert second_response.json()["version"] == "3.0"

    db.refresh(scheme)

    assert scheme.verification_status == "VERIFIED"
    assert scheme.version == "3.0"
    assert scheme.source_url == "https://www.myscheme.gov.in/"

    histories = (
        db.query(SchemeVerificationHistory)
        .filter(SchemeVerificationHistory.scheme_id == scheme.id)
        .order_by(SchemeVerificationHistory.id)
        .all()
    )

    assert len(histories) == 2

    first_history, second_history = histories

    assert first_history.id == first_history_id
    assert first_history.previous_status == "PENDING"
    assert first_history.new_status == "VERIFIED"
    assert second_history.verifier_id == admin_user.id
    assert second_history.previous_status == "VERIFIED"
    assert second_history.new_status == "VERIFIED"
    assert second_history.source_url == second_payload["source_url"]
    assert second_history.notes == second_payload["notes"]





import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.api.auth import get_db
from app.core.auth import get_current_user
from app.db.database import Base
from app.main import app
from app.models.scheme import Scheme
from app.models.scheme_rule import SchemeRule
from app.models.user import User
from app.models.worker_profile import WorkerProfile
from datetime import datetime, timedelta


@pytest.fixture
def benefits_test_setup():
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
    db.flush()

    profile = WorkerProfile(
        user_id=user.id,
        age=30,
        monthly_income=10000,
        epfo_status=False,
        esic_status=False,
        nps_status=False,
        income_tax_payer=False,
        state="Maharashtra",
        district="Pune",
        worker_type="DELIVERY_PARTNER",
        employment_type="FULL_TIME",
    )

    db.add(profile)
    db.commit()
    db.refresh(user)

    def override_db():
        yield db

    def override_current_user():
        return user

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_current_user

    try:
        with TestClient(app) as client:
            yield client, db, user
    finally:
        app.dependency_overrides.clear()
        db.close()
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()


def create_scheme(
    db,
    name="Test Scheme",
    verification_status="VERIFIED",
):
    scheme = Scheme(
        name=name,
        description="Test scheme description",
        category="SOCIAL_SECURITY",
        level="CENTRAL",
        source_url="https://example.gov.in/test-scheme",
        verification_status=verification_status,
        version="1.0",
        status="ACTIVE",
        last_verified_at=datetime.now() - timedelta(days=1),
    )

    db.add(scheme)
    db.commit()
    db.refresh(scheme)

    return scheme


def add_age_rule(db, scheme_id, operator=">=", value="18"):
    rule = SchemeRule(
        scheme_id=scheme_id,
        field="age",
        operator=operator,
        value=value,
        logical_group=1,
        logical_operator="AND",
    )

    db.add(rule)
    db.commit()


def test_unverified_scheme_requires_verification(
    benefits_test_setup,
):
    client, db, _ = benefits_test_setup

    scheme = create_scheme(
        db,
        verification_status="REVIEW_REQUIRED",
    )
    add_age_rule(db, scheme.id)

    response = client.get("/benefits/me")

    assert response.status_code == 200

    benefit = response.json()[0]

    assert benefit["verification_status"] == "REVIEW_REQUIRED"
    assert benefit["status"] == "Additional Verification Required"


def test_unknown_verification_status_is_not_trusted(
    benefits_test_setup,
):
    client, db, _ = benefits_test_setup

    scheme = create_scheme(
        db,
        verification_status="UNKNOWN",
    )
    add_age_rule(db, scheme.id)

    response = client.get("/benefits/me")

    assert response.status_code == 200

    benefit = response.json()[0]

    assert benefit["verification_status"] == "UNKNOWN"
    assert benefit["status"] == "Additional Verification Required"


def test_verified_scheme_without_rules_requires_verification(
    benefits_test_setup,
):
    client, db, _ = benefits_test_setup

    create_scheme(db, verification_status="VERIFIED")

    response = client.get("/benefits/me")

    assert response.status_code == 200

    benefit = response.json()[0]

    assert benefit["verification_status"] == "VERIFIED"
    assert benefit["status"] == "Additional Verification Required"
    assert "rules" in benefit["reasons"][0].lower()


def test_verified_scheme_with_matching_rules_is_potentially_eligible(
    benefits_test_setup,
):
    client, db, _ = benefits_test_setup

    scheme = create_scheme(db)
    add_age_rule(db, scheme.id, operator=">=", value="18")

    response = client.get("/benefits/me")

    assert response.status_code == 200

    benefit = response.json()[0]

    assert benefit["verification_status"] == "VERIFIED"
    assert benefit["status"] == "Potentially Eligible"


def test_verified_scheme_with_non_matching_rules(
    benefits_test_setup,
):
    client, db, _ = benefits_test_setup

    scheme = create_scheme(db)
    add_age_rule(db, scheme.id, operator="<", value="18")

    response = client.get("/benefits/me")

    assert response.status_code == 200

    benefit = response.json()[0]

    assert benefit["verification_status"] == "VERIFIED"
    assert benefit["status"] == "Not Matching"


def test_user_without_profile_receives_empty_list(
    benefits_test_setup,
):
    client, db, user = benefits_test_setup

    db.query(WorkerProfile).filter(
        WorkerProfile.user_id == user.id
    ).delete()
    db.commit()

    response = client.get("/benefits/me")

    assert response.status_code == 200
    assert response.json() == []




def test_stale_verified_scheme_requires_reverification(
    benefits_test_setup,
):
    client, db, _ = benefits_test_setup

    scheme = create_scheme(db, verification_status="VERIFIED")
    scheme.last_verified_at = datetime.now() - timedelta(days=91)
    db.commit()

    # Even a matching rule must not override stale verification.
    add_age_rule(db, scheme.id, operator=">=", value="18")

    response = client.get("/benefits/me")

    assert response.status_code == 200
    benefit = response.json()[0]

    assert benefit["verification_status"] == "STALE"
    assert benefit["status"] == "Additional Verification Required"
    assert any(
        "outdated" in reason.lower()
        for reason in benefit["reasons"]
    )


def test_missing_verification_date_requires_reverification(
    benefits_test_setup,
):
    client, db, _ = benefits_test_setup

    scheme = create_scheme(db, verification_status="VERIFIED")
    scheme.last_verified_at = None
    db.commit()

    add_age_rule(db, scheme.id, operator=">=", value="18")

    response = client.get("/benefits/me")

    assert response.status_code == 200
    benefit = response.json()[0]

    assert benefit["verification_status"] == "STALE"
    assert benefit["status"] == "Additional Verification Required"


def test_fresh_verified_scheme_still_evaluates_rules(
    benefits_test_setup,
):
    client, db, _ = benefits_test_setup

    scheme = create_scheme(db, verification_status="VERIFIED")
    scheme.last_verified_at = datetime.now() - timedelta(days=10)
    db.commit()

    add_age_rule(db, scheme.id, operator=">=", value="18")

    response = client.get("/benefits/me")

    assert response.status_code == 200
    benefit = response.json()[0]

    assert benefit["verification_status"] == "VERIFIED"
    assert benefit["status"] == "Potentially Eligible"

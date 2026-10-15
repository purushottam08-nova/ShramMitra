
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import pytest

from app.db.database import Base
from app.models.scheme import Scheme
from app.models.scheme_rule import SchemeRule
from scripts import seed_database


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    TestingSession = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    db = TestingSession()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


SCHEME_DATA = {
    "name": "Test Scheme",
    "description": "Test scheme description",
    "category": "Social Security",
    "level": "CENTRAL",
    "source_url": "https://example.gov.in/scheme",
    "verification_status": "VERIFIED",
    "last_verified_at": "2026-10-01T00:00:00",
    "version": "1.0",
    "status": "ACTIVE",
}

RULE_DATA = {
    "scheme_name": "Test Scheme",
    "field": "age",
    "operator": ">=",
    "value": "18",
    "logical_group": 1,
    "logical_operator": "AND",
}


def mock_seed_files(monkeypatch):
    files = {
        "schemes.json": [SCHEME_DATA],
        "scheme_rules.json": [RULE_DATA],
    }

    def fake_load_json(filename):
        if filename not in files:
            return []
        return files[filename]

    monkeypatch.setattr(seed_database, "load_json", fake_load_json)


def test_seed_schemes_and_rules(db_session, monkeypatch):
    mock_seed_files(monkeypatch)

    seed_database.seed_schemes(db_session)

    # Required because autoflush is disabled.
    db_session.flush()

    seed_database.seed_scheme_rules(db_session)
    db_session.commit()

    scheme_count = db_session.query(func.count(Scheme.id)).scalar()
    rule_count = db_session.query(func.count(SchemeRule.id)).scalar()

    assert scheme_count == 1
    assert rule_count == 1


def test_seed_schemes_is_idempotent_after_commit(
    db_session,
    monkeypatch,
):
    mock_seed_files(monkeypatch)

    seed_database.seed_schemes(db_session)
    db_session.commit()

    seed_database.seed_schemes(db_session)
    db_session.commit()

    count = db_session.query(func.count(Scheme.id)).scalar()

    assert count == 1


def test_seed_rules_is_idempotent_after_commit(
    db_session,
    monkeypatch,
):
    mock_seed_files(monkeypatch)

    seed_database.seed_schemes(db_session)
    db_session.commit()

    seed_database.seed_scheme_rules(db_session)
    db_session.commit()

    seed_database.seed_scheme_rules(db_session)
    db_session.commit()

    count = db_session.query(func.count(SchemeRule.id)).scalar()

    assert count == 1


def test_missing_scheme_causes_error(db_session, monkeypatch):
    monkeypatch.setattr(
        seed_database,
        "load_json",
        lambda filename: [RULE_DATA]
        if filename == "scheme_rules.json"
        else [],
    )

    with pytest.raises(ValueError, match="Scheme not found"):
        seed_database.seed_scheme_rules(db_session)

    assert db_session.query(SchemeRule).count() == 0



def test_seed_failure_can_be_rolled_back(db_session, monkeypatch):
    mock_seed_files(monkeypatch)

    # Insert the scheme, but don't commit it.
    seed_database.seed_schemes(db_session)
    db_session.flush()

    # Simulate a failure during rule seeding.
    monkeypatch.setattr(
        seed_database,
        "load_json",
        lambda filename: [RULE_DATA]
        if filename == "scheme_rules.json"
        else [],
    )

    with pytest.raises(ValueError, match="Scheme not found"):
        # Force the failure by using a scheme name that doesn't exist.
        invalid_rule = {**RULE_DATA, "scheme_name": "Missing Scheme"}
        monkeypatch.setattr(
            seed_database,
            "load_json",
            lambda filename: [invalid_rule]
            if filename == "scheme_rules.json"
            else [],
        )
        seed_database.seed_scheme_rules(db_session)

    db_session.rollback()

    assert db_session.query(Scheme).count() == 0
    assert db_session.query(SchemeRule).count() == 0

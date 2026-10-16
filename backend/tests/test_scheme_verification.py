from datetime import date, datetime, timedelta

import pytest

from app.services.scheme_verification import is_verification_fresh


def test_recent_verification_is_fresh():
    today = date(2026, 10, 16)
    verified_at = datetime(2026, 10, 10)

    assert is_verification_fresh(
        verified_at,
        today=today,
    ) is True


def test_verification_exactly_90_days_old_is_fresh():
    today = date(2026, 10, 16)
    verified_at = datetime.combine(
        today - timedelta(days=90),
        datetime.min.time(),
    )

    assert is_verification_fresh(
        verified_at,
        today=today,
    ) is True


def test_verification_older_than_90_days_is_stale():
    today = date(2026, 10, 16)
    verified_at = datetime.combine(
        today - timedelta(days=91),
        datetime.min.time(),
    )

    assert is_verification_fresh(
        verified_at,
        today=today,
    ) is False


def test_missing_verification_date_is_stale():
    assert is_verification_fresh(
        None,
        today=date(2026, 10, 16),
    ) is False


def test_future_verification_date_is_stale():
    today = date(2026, 10, 16)
    verified_at = datetime(2026, 10, 17)

    assert is_verification_fresh(
        verified_at,
        today=today,
    ) is False


def test_custom_freshness_limit():
    today = date(2026, 10, 16)
    verified_at = datetime(2026, 10, 1)

    assert is_verification_fresh(
        verified_at,
        today=today,
        max_age_days=30,
    ) is True

    assert is_verification_fresh(
        verified_at,
        today=today,
        max_age_days=7,
    ) is False


def test_negative_freshness_limit_is_rejected():
    with pytest.raises(ValueError):
        is_verification_fresh(
            datetime(2026, 10, 10),
            today=date(2026, 10, 16),
            max_age_days=-1,
        )
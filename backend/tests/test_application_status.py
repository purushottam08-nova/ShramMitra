from datetime import datetime, timedelta
from types import SimpleNamespace

from app.services.application_status import get_application_summary


def make_application(status, changed_at=None):
    now = datetime.utcnow()

    return SimpleNamespace(
        status=status,
        created_at=now - timedelta(days=5),
        status_history=[
            SimpleNamespace(changed_at=changed_at or now - timedelta(days=2))
        ],
    )


def test_pending_duration_uses_latest_status_history():
    application = make_application(
        "UNDER_REVIEW",
        datetime.utcnow() - timedelta(days=3),
    )

    summary = get_application_summary(application)

    assert summary["days_in_current_status"] >= 3


def test_final_status_has_no_pending_duration():
    application = make_application("APPROVED")

    summary = get_application_summary(application)

    assert summary["days_in_current_status"] is None


def test_next_action_is_included():
    application = make_application("DOCUMENT_REQUIRED")

    summary = get_application_summary(application)

    assert summary["next_action"]
    assert "documents" in summary["next_action"].lower()


def test_missing_history_uses_creation_time():
    application = make_application("SUBMITTED")
    application.status_history = []

    summary = get_application_summary(application)

    assert summary["days_in_current_status"] >= 5
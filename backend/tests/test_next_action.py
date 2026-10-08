from app.services.next_action import get_next_action


def test_document_required_action():
    action = get_next_action("DOCUMENT_REQUIRED")
    assert "documents" in action.lower()


def test_approved_action():
    action = get_next_action("APPROVED")
    assert "disbursement" in action.lower()


def test_unknown_status_has_fallback():
    action = get_next_action("SOMETHING_UNKNOWN")
    assert action


def test_each_supported_status_has_an_action():
    statuses = [
        "DRAFT",
        "SUBMITTED",
        "UNDER_REVIEW",
        "DOCUMENT_REQUIRED",
        "APPROVED",
        "REJECTED",
        "WITHDRAWN",
    ]

    for status in statuses:
        assert get_next_action(status)
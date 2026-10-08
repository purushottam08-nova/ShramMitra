from datetime import datetime

from app.models.application import Application
from app.services.next_action import get_next_action


FINAL_STATUSES = {"APPROVED", "REJECTED", "WITHDRAWN"}


def get_application_summary(application: Application) -> dict:
    next_action = get_next_action(application.status)

    if application.status in FINAL_STATUSES:
        days_in_current_status = None
    else:
        history = application.status_history

        if history:
            latest_entry = max(
                history,
                key=lambda entry: entry.changed_at,
            )
            status_started_at = latest_entry.changed_at
        else:
            status_started_at = application.created_at

        now = datetime.utcnow()
        days_in_current_status = max(
            0,
            (now - status_started_at).days,
        )

    return {
        "next_action": next_action,
        "days_in_current_status": days_in_current_status,
    }
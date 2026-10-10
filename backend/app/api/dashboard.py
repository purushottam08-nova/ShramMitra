
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth import get_current_user, get_db
from app.models.application import Application
from app.models.grievance import Grievance
from app.models.user import User
from app.services.application_status import get_application_summary

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/me")
def get_my_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    applications = (
        db.query(Application)
        .filter(Application.user_id == current_user.id)
        .order_by(Application.created_at.desc())
        .all()
    )

    grievances = (
        db.query(Grievance)
        .filter(Grievance.user_id == current_user.id)
        .order_by(Grievance.created_at.desc())
        .all()
    )

    active_applications = [
        application
        for application in applications
        if application.status not in {"APPROVED", "REJECTED", "WITHDRAWN"}
    ]

    open_grievances = [
        grievance
        for grievance in grievances
        if grievance.status not in {"RESOLVED", "CLOSED"}
    ]

    application_items = []
    for application in applications:
        summary = get_application_summary(application)

        application_items.append(
            {
                "id": application.id,
                "scheme_id": application.scheme_id,
                "reference_number": application.reference_number,
                "status": application.status,
                "application_date": application.application_date,
                "next_action": summary["next_action"],
                "days_in_current_status": summary["days_in_current_status"],
            }
        )

    
    now = datetime.utcnow()
    grievance_items = []

    for grievance in grievances:
        if grievance.status in {"RESOLVED", "CLOSED"}:
            days_pending = None
        else:
            history = grievance.status_history

            if history:
                latest_entry = max(
                    history,
                    key=lambda entry: entry.changed_at,
                )
                pending_since = latest_entry.changed_at
            else:
                pending_since = grievance.created_at

            days_pending = max(
                0,
                (now - pending_since).days,
            )

        grievance_items.append(
            {
                "id": grievance.id,
                "subject": grievance.subject,
                "status": grievance.status,
                "created_at": grievance.created_at,
                "days_pending": days_pending,
            }
        )

    return {
        "applications_count": len(applications),
        "active_applications_count": len(active_applications),
        "open_grievances_count": len(open_grievances),
        "applications": application_items,
        "grievances": grievance_items,
    }

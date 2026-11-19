
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, get_db
from app.core.permissions import require_admin
from app.models.application import Application
from app.models.application_status_history import ApplicationStatusHistory
from app.models.scheme import Scheme
from app.models.user import User
from app.schemas.application import (
    ApplicationCreateRequest,
    ApplicationResponse,
    ApplicationStatusUpdateRequest,
)
from app.services.application_status import get_application_summary
from app.services.notifications import create_notification


router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post("/", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_application(
    payload: ApplicationCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    scheme = db.query(Scheme).filter(Scheme.id == payload.scheme_id).first()

    if scheme is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheme not found",
        )

    application = Application(
        user_id=current_user.id,
        scheme_id=payload.scheme_id,
        reference_number=payload.reference_number,
        status="SUBMITTED",
    )

    try:
        db.add(application)
        db.flush()

        history = ApplicationStatusHistory(
            application_id=application.id,
            status="SUBMITTED",
            note="Application submitted",
        )
        db.add(history)

        create_notification(
            db=db,
            user_id=current_user.id,
            title="Application submitted",
            message=f"Your application for {scheme.name} has been submitted successfully.",
            notification_type="APPLICATION",
        )

        db.commit()
        db.refresh(application)

    except Exception:
        db.rollback()
        raise

    return ApplicationResponse.model_validate(application)


@router.get("/", response_model=list[ApplicationResponse])
def get_my_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    applications = (
        db.query(Application)
        .filter(Application.user_id == current_user.id)
        .order_by(Application.application_date.desc())
        .all()
    )

    results = []

    for application in applications:
        item = ApplicationResponse.model_validate(application)
        summary = get_application_summary(application)
        results.append(item.model_copy(update=summary))

    return results


@router.patch(
    "/{application_id}/status",
    response_model=ApplicationResponse,
)
def update_application_status(
    application_id: int,
    payload: ApplicationStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Only administrators can update application status.
    Workers can submit and view their applications, but cannot modify status.
    """

    application = (
        db.query(Application)
        .filter(Application.id == application_id)
        .first()
    )

    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    new_status = payload.status.strip().upper()

    if not new_status:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Application status cannot be empty",
        )

    previous_status = application.status

    if previous_status == new_status:
        return ApplicationResponse.model_validate(application)

    scheme = (
        db.query(Scheme)
        .filter(Scheme.id == application.scheme_id)
        .first()
    )

    try:
        application.status = new_status

        history = ApplicationStatusHistory(
            application_id=application.id,
            status=new_status,
            note=payload.note,
        )
        db.add(history)

        create_notification(
            db=db,
            user_id=application.user_id,
            title="Application status updated",
            message=(
                f"Your application for {scheme.name if scheme else 'the scheme'} "
                f"has changed from {previous_status} to {new_status}."
                + (f" Note: {payload.note}" if payload.note else "")
            ),
            notification_type="APPLICATION",
        )

        db.commit()
        db.refresh(application)

    except Exception:
        db.rollback()
        raise

    return ApplicationResponse.model_validate(application)


@router.get("/{application_id}/history")
def get_application_history(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    application = (
        db.query(Application)
        .filter(
            Application.id == application_id,
            Application.user_id == current_user.id,
        )
        .first()
    )

    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    history = (
        db.query(ApplicationStatusHistory)
        .filter(ApplicationStatusHistory.application_id == application_id)
        .order_by(ApplicationStatusHistory.changed_at.asc())
        .all()
    )

    return [
        {
            "id": item.id,
            "application_id": item.application_id,
            "status": item.status,
            "note": item.note,
            "changed_at": item.changed_at,
        }
        for item in history
    ]

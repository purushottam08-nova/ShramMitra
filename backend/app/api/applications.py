from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.auth import get_current_user, get_db
from app.models.application import Application
from app.models.application_status_history import ApplicationStatusHistory
from app.models.scheme import Scheme
from app.models.user import User
from app.schemas.application import (
    ApplicationCreateRequest,
    ApplicationResponse,
    ApplicationStatusUpdateRequest,
)


router = APIRouter(
    prefix="/applications",
    tags=["Applications"],
)


@router.post(
    "",
    response_model=ApplicationResponse,
    status_code=201,
)
def create_application(
    data: ApplicationCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    scheme = (
        db.query(Scheme)
        .filter(
            Scheme.id == data.scheme_id,
            Scheme.status == "ACTIVE",
        )
        .first()
    )

    if not scheme:
        raise HTTPException(
            status_code=404,
            detail="Scheme not found",
        )

    application = Application(
        user_id=current_user.id,
        scheme_id=scheme.id,
        reference_number=data.reference_number,
        status="SUBMITTED",
        application_date=datetime.utcnow(),
    )

    db.add(application)

    db.flush()

    history = ApplicationStatusHistory(
        application_id=application.id,
        status="SUBMITTED",
        note="Application submitted",
    )

    db.add(history)

    db.commit()
    db.refresh(application)

    return application


@router.get(
    "",
    response_model=list[ApplicationResponse],
)
def get_my_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    applications = (
        db.query(Application)
        .filter(
            Application.user_id == current_user.id
        )
        .order_by(Application.created_at.desc())
        .all()
    )

    return applications


@router.patch(
    "/{application_id}/status",
    response_model=ApplicationResponse,
)
def update_application_status(
    application_id: int,
    data: ApplicationStatusUpdateRequest,
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

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    application.status = data.status

    history = ApplicationStatusHistory(
        application_id=application.id,
        status=data.status,
        note=data.note,
    )

    db.add(history)

    db.commit()
    db.refresh(application)

    return application


@router.get(
    "/{application_id}/history",
)
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

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    history = (
        db.query(ApplicationStatusHistory)
        .filter(
            ApplicationStatusHistory.application_id
            == application.id
        )
        .order_by(
            ApplicationStatusHistory.changed_at.asc()
        )
        .all()
    )

    return history
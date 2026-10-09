
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.auth import get_current_user, get_db
from app.models.application import Application
from app.models.grievance import Grievance
from app.models.grievance_status_history import GrievanceStatusHistory
from app.models.user import User
from app.schemas.grievance import (
    GrievanceCreateRequest,
    GrievanceResponse,
    GrievanceHistoryResponse,
)

router = APIRouter(prefix="/grievances", tags=["Grievances"])


@router.post("", response_model=GrievanceResponse, status_code=201)
def create_grievance(
    data: GrievanceCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if data.application_id is not None:
        application = (
            db.query(Application)
            .filter(
                Application.id == data.application_id,
                Application.user_id == current_user.id,
            )
            .first()
        )
        if not application:
            raise HTTPException(
                status_code=404,
                detail="Application not found",
            )

    grievance = Grievance(
        user_id=current_user.id,
        application_id=data.application_id,
        subject=data.subject,
        description=data.description,
        status="OPEN",
    )

    try:
        db.add(grievance)
        db.flush()

        history = GrievanceStatusHistory(
            grievance_id=grievance.id,
            status="OPEN",
            note="Grievance created",
        )
        db.add(history)
        db.commit()
        db.refresh(grievance)
    except Exception:
        db.rollback()
        raise

    return grievance


@router.get("", response_model=list[GrievanceResponse])
def get_my_grievances(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Grievance)
        .filter(Grievance.user_id == current_user.id)
        .order_by(Grievance.created_at.desc())
        .all()
    )


@router.get(
    "/{grievance_id}/history",
    response_model=list[GrievanceHistoryResponse],
)
def get_grievance_history(
    grievance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    grievance = (
        db.query(Grievance)
        .filter(
            Grievance.id == grievance_id,
            Grievance.user_id == current_user.id,
        )
        .first()
    )

    if not grievance:
        raise HTTPException(
            status_code=404,
            detail="Grievance not found",
        )

    return (
        db.query(GrievanceStatusHistory)
        .filter(
            GrievanceStatusHistory.grievance_id == grievance.id
        )
        .order_by(GrievanceStatusHistory.changed_at.asc())
        .all()
    )
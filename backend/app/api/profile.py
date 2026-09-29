from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.auth import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.worker_profile import WorkerProfile
from app.schemas.profile import WorkerProfileRequest


router = APIRouter(
    prefix="/profile",
    tags=["Worker Profile"],
)


@router.post("")
def create_profile(
    profile_data: WorkerProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = WorkerProfile(
        user_id=current_user.id,
        state=profile_data.state,
        district=profile_data.district,
        worker_type=profile_data.worker_type,
        employment_type=profile_data.employment_type,
        monthly_income_range=profile_data.monthly_income_range,
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return {
        "message": "Worker profile created successfully",
        "profile_id": profile.id,
    }



@router.get("/me")
def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = (
        db.query(WorkerProfile)
        .filter(WorkerProfile.user_id == current_user.id)
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Worker profile not found",
        )

    return {
        "id": profile.id,
        "state": profile.state,
        "district": profile.district,
        "worker_type": profile.worker_type,
        "employment_type": profile.employment_type,
        "monthly_income_range": profile.monthly_income_range,
    }



@router.put("/me")
def update_my_profile(
    profile_data: WorkerProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = (
        db.query(WorkerProfile)
        .filter(WorkerProfile.user_id == current_user.id)
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Worker profile not found",
        )
    
    profile.state = profile_data.state
    profile.district = profile_data.district
    profile.worker_type = profile_data.worker_type
    profile.employment_type = profile_data.employment_type
    profile.monthly_income_range = profile_data.monthly_income_range

    db.commit()
    db.refresh(profile)

    return {
        "message": "Worker profile updated successfully",
    }



@router.post("", status_code=status.HTTP_201_CREATED)
def create_profile(
    profile_data: WorkerProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing_profile = (
        db.query(WorkerProfile)
        .filter(WorkerProfile.user_id == current_user.id)
        .first()
    )

    if existing_profile:
        raise HTTPException(
            status_code=409,
            detail="Worker profile already exists",
        )

    profile = WorkerProfile(
        user_id=current_user.id,
        state=profile_data.state,
        district=profile_data.district,
        worker_type=profile_data.worker_type,
        employment_type=profile_data.employment_type,
        monthly_income_range=profile_data.monthly_income_range,
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return {
        "message": "Worker profile created successfully",
        "profile_id": profile.id,
    }
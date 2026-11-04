from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.user import User
from app.api.auth import get_current_user

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"],
)


@router.get("/me")
def get_my_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns schemes matching the current user's profile.
    """

    from app.models.scheme import Scheme

    schemes = db.query(Scheme).all()

    recommendations = []

    for scheme in schemes:
        reasons = []

        # Basic occupation matching
        occupation = getattr(current_user, "occupation", None)

        if scheme.target_occupation:
            if occupation and occupation.lower() in scheme.target_occupation.lower():
                reasons.append("Your occupation matches this scheme.")

        # State matching
        user_state = getattr(current_user, "state", None)

        if scheme.state:
            if user_state and user_state.lower() == scheme.state.lower():
                reasons.append("This scheme is available in your state.")

        # General schemes
        if not scheme.state and not scheme.target_occupation:
            reasons.append("This is a general scheme.")

        if reasons:
            recommendations.append({
                "scheme_id": scheme.id,
                "scheme_name": scheme.name,
                "description": scheme.description,
                "reasons": reasons,
                "eligibility_status": "POTENTIAL_MATCH",
            })

    return {
        "total": len(recommendations),
        "recommendations": recommendations,
    }
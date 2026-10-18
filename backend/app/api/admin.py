
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_db
from app.core.permissions import require_admin
from app.models.scheme import Scheme
from app.models.scheme_verification_history import SchemeVerificationHistory
from app.models.user import User
from app.schemas.scheme_verification import SchemeVerificationRequest


router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/schemes/{scheme_id}/verify")
def verify_scheme(
    scheme_id: int,
    request: SchemeVerificationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    scheme = db.query(Scheme).filter(Scheme.id == scheme_id).first()

    if scheme is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheme not found",
        )

    previous_status = scheme.verification_status

    scheme.verification_status = "VERIFIED"
    scheme.source_url = str(request.source_url)
    scheme.version = request.version
    scheme.last_verified_at = datetime.now(timezone.utc).replace(tzinfo=None)

    history = SchemeVerificationHistory(
        scheme_id=scheme.id,
        verifier_id=current_user.id,
        previous_status=previous_status,
        new_status="VERIFIED",
        source_url=scheme.source_url,
        notes=request.notes,
        verified_at=scheme.last_verified_at,
    )

    db.add(history)

    try:
        db.commit()
        db.refresh(scheme)
        db.refresh(history)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save scheme verification",
        )

    return {
        "message": "Scheme verified successfully",
        "scheme_id": scheme.id,
        "verification_status": scheme.verification_status,
        "version": scheme.version,
        "verified_at": scheme.last_verified_at,
        "history_id": history.id,
    }

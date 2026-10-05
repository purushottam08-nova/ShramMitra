from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth import get_db
from app.models.scheme import Scheme
from app.schemas.scheme import SchemeResponse


router = APIRouter(
    prefix="/schemes",
    tags=["Schemes"],
)


@router.get("", response_model=list[SchemeResponse])
def get_schemes(
    db: Session = Depends(get_db),
):
    schemes = (
        db.query(Scheme)
        .filter(Scheme.status == "ACTIVE")
        .all()
    )

    return schemes
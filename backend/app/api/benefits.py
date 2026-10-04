from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth import get_current_user, get_db
from app.models.scheme import Scheme
from app.models.scheme_rule import SchemeRule
from app.models.user import User
from app.schemas.benefit import BenefitResponse
from app.rules.evaluator import (
    MATCH,
    MISSING,
    NO_MATCH,
    evaluate_scheme,
    get_missing_fields,
)


router = APIRouter(
    prefix="/benefits",
    tags=["Benefits"],
)


@router.get("/me", response_model=list[BenefitResponse])
def get_my_benefits(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = current_user.worker_profile

    if not profile:
        return []

    profile_data = {
        "age": profile.age,
        "monthly_income": profile.monthly_income,
        "epfo_status": profile.epfo_status,
        "esic_status": profile.esic_status,
        "nps_status": profile.nps_status,
        "income_tax_payer": profile.income_tax_payer,
        "state": profile.state,
        "district": profile.district,
        "worker_type": profile.worker_type,
        "employment_type": profile.employment_type,
    }

    schemes = (
        db.query(Scheme)
        .filter(Scheme.status == "ACTIVE")
        .all()
    )

    benefits = []

    for scheme in schemes:
        rules = (
            db.query(SchemeRule)
            .filter(SchemeRule.scheme_id == scheme.id)
            .all()
        )

        if not rules:
            continue

        result = evaluate_scheme(profile_data, rules)

        if result == MATCH:
            status = "Potentially Eligible"
        elif result == MISSING:
            status = "Missing Information"
        else:
            status = "Not Matching"

        missing_fields = []

        if result == MISSING:
            missing_fields = get_missing_fields(
                profile_data,
                rules,
            )

        benefits.append(
            BenefitResponse(
                scheme_id=scheme.id,
                scheme_name=scheme.name,
                description=scheme.description,
                category=scheme.category,
                source_url=scheme.source_url,
                status=status,
                missing_fields=missing_fields,
            )
        )

    return benefits
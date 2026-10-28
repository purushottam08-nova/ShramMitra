from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.services.scheme_verification import is_verification_fresh
from app.api.auth import get_current_user, get_db

from app.models.scheme import Scheme
from app.models.scheme_rule import SchemeRule
from app.models.scheme_state import SchemeState
from app.models.scheme_worker_type import SchemeWorkerType
from app.models.state import State
from app.models.worker_type import WorkerType
from app.models.user import User

from app.rules.evaluator import (
    MATCH,
    MISSING,
    NO_MATCH,
    evaluate_scheme,
    get_missing_fields,
    get_rule_reasons,
)

from app.schemas.benefit import BenefitResponse


router = APIRouter(
    prefix="/benefits",
    tags=["Benefits"],
)


def normalize(value):
    if value is None:
        return None

    return str(value).strip().lower()


def get_scheme_states(db: Session, scheme_id: int):
    rows = (
        db.query(State.name, State.code)
        .join(SchemeState, SchemeState.state_id == State.id)
        .filter(SchemeState.scheme_id == scheme_id)
        .all()
    )

    return {
        normalize(value)
        for row in rows
        for value in row
        if value
    }


def get_scheme_worker_types(db: Session, scheme_id: int):
    rows = (
        db.query(WorkerType.name, WorkerType.code)
        .join(
            SchemeWorkerType,
            SchemeWorkerType.worker_type_id == WorkerType.id,
        )
        .filter(SchemeWorkerType.scheme_id == scheme_id)
        .all()
    )

    return {
        normalize(value)
        for row in rows
        for value in row
        if value
    }


def check_applicability(db: Session, scheme: Scheme, profile):
    missing_fields = []
    reasons = []

    scheme_states = get_scheme_states(db, scheme.id)
    scheme_worker_types = get_scheme_worker_types(db, scheme.id)

    profile_state = normalize(profile.state)
    profile_worker_type = normalize(profile.worker_type)

    # State applicability
    if scheme_states:
        if not profile_state:
            missing_fields.append("state")
            reasons.append(
                "Your state is required to check this scheme's applicability."
            )
        elif profile_state not in scheme_states:
            reasons.append(
                "This scheme is not listed for your state."
            )

    # Worker-type applicability
    if scheme_worker_types:
        if not profile_worker_type:
            missing_fields.append("worker_type")
            reasons.append(
                "Your worker type is required to check this scheme's applicability."
            )
        elif profile_worker_type not in scheme_worker_types:
            reasons.append(
                "This scheme is not listed for your worker type."
            )

    if missing_fields:
        return MISSING, missing_fields, reasons

    if reasons:
        return NO_MATCH, [], reasons

    return MATCH, [], []


@router.get(
    "/me",
    response_model=list[BenefitResponse],
)
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

        # Scheme information has not been verified.
        if scheme.verification_status != "VERIFIED":
            benefits.append(
                BenefitResponse(
                    scheme_id=scheme.id,
                    scheme_name=scheme.name,
                    description=scheme.description,
                    category=scheme.category,
                    source_url=scheme.source_url,
                    verification_status=scheme.verification_status,
                    status="Additional Verification Required",
                    missing_fields=[],
                    reasons=[
                        "Scheme information requires verification "
                        "before eligibility can be assessed."
                    ],
                )
            )
            continue

        # Verification is missing or outdated.
        if not is_verification_fresh(scheme.last_verified_at):
            benefits.append(
                BenefitResponse(
                    scheme_id=scheme.id,
                    scheme_name=scheme.name,
                    description=scheme.description,
                    category=scheme.category,
                    source_url=scheme.source_url,
                    verification_status="STALE",
                    status="Additional Verification Required",
                    missing_fields=[],
                    reasons=[
                        "Scheme verification is missing or outdated. "
                        "Verify the information using an official source "
                        "before assessing eligibility."
                    ],
                )
            )
            continue

        # Check state and worker-type applicability.
        applicability, applicability_missing, applicability_reasons = (
            check_applicability(db, scheme, profile)
        )

        if applicability == NO_MATCH:
            benefits.append(
                BenefitResponse(
                    scheme_id=scheme.id,
                    scheme_name=scheme.name,
                    description=scheme.description,
                    category=scheme.category,
                    source_url=scheme.source_url,
                    verification_status=scheme.verification_status,
                    status="Not Matching",
                    missing_fields=[],
                    reasons=applicability_reasons,
                )
            )
            continue

        if applicability == MISSING:
            benefits.append(
                BenefitResponse(
                    scheme_id=scheme.id,
                    scheme_name=scheme.name,
                    description=scheme.description,
                    category=scheme.category,
                    source_url=scheme.source_url,
                    verification_status=scheme.verification_status,
                    status="Missing Information",
                    missing_fields=applicability_missing,
                    reasons=applicability_reasons,
                )
            )
            continue

        # No eligibility rules means we cannot assess this scheme.
        if not rules:
            benefits.append(
                BenefitResponse(
                    scheme_id=scheme.id,
                    scheme_name=scheme.name,
                    description=scheme.description,
                    category=scheme.category,
                    source_url=scheme.source_url,
                    verification_status=scheme.verification_status,
                    status="Additional Verification Required",
                    missing_fields=[],
                    reasons=[
                        "Eligibility rules are not yet configured "
                        "for this scheme."
                    ],
                )
            )
            continue

        # Evaluate eligibility rules.
        result = evaluate_scheme(profile_data, rules)

        if result == MATCH:
            status = "Potentially Eligible"
        elif result == MISSING:
            status = "Missing Information"
        elif result == NO_MATCH:
            status = "Not Matching"
        else:
            raise ValueError(
                f"Unexpected evaluator result: {result}"
            )

        missing_fields = get_missing_fields(
            profile_data,
            rules,
        )

        reasons = get_rule_reasons(
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
                verification_status=scheme.verification_status,
                status=status,
                missing_fields=missing_fields,
                reasons=reasons,
            )
        )

    return benefits
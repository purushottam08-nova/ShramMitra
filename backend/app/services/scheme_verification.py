
import os
from datetime import date, datetime


MAX_VERIFICATION_AGE_DAYS = int(
    os.getenv("SCHEME_VERIFICATION_MAX_AGE_DAYS", "90")
)


def is_verification_fresh(
    last_verified_at: datetime | None,
    *,
    today: date | None = None,
    max_age_days: int = MAX_VERIFICATION_AGE_DAYS,
) -> bool:
    """
    Return True only when verification is recent and valid.

    Missing dates, future dates, and dates older than the
    configured maximum age are considered stale.
    """
    if max_age_days < 0:
        raise ValueError("max_age_days cannot be negative")

    if last_verified_at is None:
        return False

    current_date = today or date.today()
    verified_date = last_verified_at.date()

    if verified_date > current_date:
        return False

    age_in_days = (current_date - verified_date).days

    return age_in_days <= max_age_days

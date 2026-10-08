from datetime import datetime

from pydantic import BaseModel, Field


class ApplicationCreateRequest(BaseModel):
    scheme_id: int

    reference_number: str | None = Field(
        default=None,
        max_length=100,
    )


class ApplicationStatusUpdateRequest(BaseModel):
    status: str = Field(
        max_length=50,
    )

    note: str | None = Field(
        default=None,
        max_length=500,
    )


class ApplicationResponse(BaseModel):
    id: int
    scheme_id: int
    reference_number: str | None
    status: str
    application_date: datetime | None
    created_at: datetime
    next_action: str | None = None
    days_in_current_status: int | None = None

    class Config:
        from_attributes = True
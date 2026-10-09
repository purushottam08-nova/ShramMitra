
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class GrievanceCreateRequest(BaseModel):
    subject: str = Field(min_length=5, max_length=200)
    description: str = Field(min_length=10, max_length=3000)
    application_id: int | None = Field(default=None, gt=0)


class GrievanceStatusUpdateRequest(BaseModel):
    status: str
    note: str | None = Field(default=None, max_length=1000)


class GrievanceResponse(BaseModel):
    id: int
    application_id: int | None
    subject: str
    description: str
    status: str
    external_reference: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GrievanceHistoryResponse(BaseModel):
    id: int
    status: str
    note: str | None
    changed_at: datetime

    model_config = ConfigDict(from_attributes=True)
from pydantic import BaseModel, Field


class WorkerProfileRequest(BaseModel):
    state: str | None = Field(default=None, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    worker_type: str | None = Field(default=None, max_length=50)
    employment_type: str | None = Field(default=None, max_length=50)
    monthly_income_range: str | None = Field(default=None, max_length=50)
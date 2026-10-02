from pydantic import BaseModel, Field


class WorkerProfileRequest(BaseModel):
    state: str | None = Field(default=None, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    worker_type: str | None = Field(default=None, max_length=50)
    employment_type: str | None = Field(default=None, max_length=50)
    monthly_income_range: str | None = Field(default=None, max_length=50)
    age: int | None = Field(default=None, ge=18, le=100)

    monthly_income: float | None = Field(
        default=None,
        ge=0,
    )

    epfo_status: bool | None = None
    esic_status: bool | None = None
    nps_status: bool | None = None
    income_tax_payer: bool | None = None
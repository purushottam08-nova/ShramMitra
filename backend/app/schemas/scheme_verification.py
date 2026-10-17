
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class SchemeVerificationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_url: HttpUrl
    notes: str = Field(min_length=10, max_length=2000)
    version: str = Field(min_length=1, max_length=50)

    @field_validator("notes", "version")
    @classmethod
    def validate_non_empty_text(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("This field cannot be empty")

        return value


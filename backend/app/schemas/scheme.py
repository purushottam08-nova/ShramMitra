from datetime import datetime

from pydantic import BaseModel


class SchemeResponse(BaseModel):
    id: int
    name: str
    description: str
    category: str
    level: str
    source_url: str
    verification_status: str
    last_verified_at: datetime | None
    version: str
    status: str

    class Config:
        from_attributes = True
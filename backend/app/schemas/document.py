from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: int
    document_type: str
    original_filename: str
    mime_type: str
    file_size: int
    verification_status: str
    created_at: datetime

    class Config:
        from_attributes = True
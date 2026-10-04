from pydantic import BaseModel


class BenefitResponse(BaseModel):
    scheme_id: int
    scheme_name: str
    description: str
    category: str
    source_url: str
    status: str
    missing_fields: list[str]
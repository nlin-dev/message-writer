from pydantic import BaseModel, Field

from app.schemas.claims import Claim


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1)
    reference_ids: list[int]
    top_k: int = Field(default=5, ge=1)


class GenerateResponse(BaseModel):
    message_id: int | None
    message_text: str
    claims: list[Claim]
    warnings: list[str]

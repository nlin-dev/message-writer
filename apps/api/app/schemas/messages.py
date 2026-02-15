from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.claims import Claim


class MessageVersionSchema(BaseModel):
    id: int
    created_at: datetime
    prompt_or_instruction: str
    message_text: str
    claims: list[Claim]
    dropped_claims: list[Claim]

    model_config = ConfigDict(from_attributes=True)

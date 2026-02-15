from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.claims import Claim


class MessageVersionSchema(BaseModel):
    id: int
    version_number: int
    source: str
    created_at: datetime
    prompt_or_instruction: str
    message_text: str
    claims: list[Claim]
    dropped_claims: list[Claim]

    model_config = ConfigDict(from_attributes=True)


class RefineRequest(BaseModel):
    instruction: str = Field(min_length=1)
    reference_ids: list[int]
    top_k: int = Field(default=5, ge=1)


class EditRequest(BaseModel):
    message_text: str = Field(min_length=1)


class StatusUpdate(BaseModel):
    status: Literal["draft", "finalized"]


class StatusResponse(BaseModel):
    id: int
    status: Literal["draft", "finalized"]


class RefineResponse(BaseModel):
    message_id: int
    version_number: int
    message_text: str
    claims: list[Claim]
    warnings: list[str]


class EditResponse(BaseModel):
    message_id: int
    version_number: int
    message_text: str
    warnings: list[str]


class MessageSummary(BaseModel):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    latest_version: MessageVersionSchema

    model_config = ConfigDict(from_attributes=True)


class MessageDetail(BaseModel):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    versions: list[MessageVersionSchema]

    model_config = ConfigDict(from_attributes=True)

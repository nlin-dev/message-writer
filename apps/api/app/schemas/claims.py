from enum import Enum

from pydantic import BaseModel


class ClaimStatus(str, Enum):
    supported = "supported"
    dropped = "dropped"


class Citation(BaseModel):
    reference_id: int
    chunk_id: int


class Claim(BaseModel):
    text: str
    citations: list[Citation]
    status: ClaimStatus
    warning: str | None = None

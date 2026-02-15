from __future__ import annotations

from pydantic import BaseModel


class PubMedResult(BaseModel):
    pmid: str
    title: str
    authors: list[str]
    abstract: str
    pub_date: str


class SearchResponse(BaseModel):
    results: list[PubMedResult]


class SaveFromPubMedRequest(BaseModel):
    pmid: str


class ReferenceResponse(BaseModel):
    id: int
    pmid: str | None
    title: str
    authors: str | None
    source: str
    chunk_count: int


class ReferenceListResponse(BaseModel):
    references: list[ReferenceResponse]


class UploadResponse(BaseModel):
    reference_id: int
    title: str
    status: str
    char_count: int
    chunk_count: int

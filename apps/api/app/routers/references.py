import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.chunk import Chunk
from app.models.reference import Reference
from app.models.working_set_item import WorkingSetItem
from app.schemas.references import (
    ReferenceListResponse,
    ReferenceResponse,
    SaveFromPubMedRequest,
)
from app.services.chunking import chunk_text
from app.services.pubmed_client import PubMedClient, get_pubmed_client

router = APIRouter(prefix="/references", tags=["references"])


def _to_response(ref: Reference, chunk_count: int) -> ReferenceResponse:
    return ReferenceResponse(
        id=ref.id,
        pmid=ref.pmid,
        title=ref.title,
        authors=ref.authors,
        source=ref.source,
        chunk_count=chunk_count,
    )


@router.post("/from-pubmed", response_model=ReferenceResponse, status_code=201)
async def save_from_pubmed(
    body: SaveFromPubMedRequest,
    db: Session = Depends(get_db),
    pubmed: PubMedClient = Depends(get_pubmed_client),
) -> ReferenceResponse:
    existing = db.query(Reference).filter(Reference.pmid == body.pmid).first()
    if existing:
        ws = db.query(WorkingSetItem).filter(
            WorkingSetItem.reference_id == existing.id
        ).first()
        if not ws:
            db.add(WorkingSetItem(reference_id=existing.id))
            db.commit()
        count = db.query(func.count(Chunk.id)).filter(
            Chunk.reference_id == existing.id
        ).scalar() or 0
        return _to_response(existing, count)

    try:
        article = await pubmed.fetch_by_pmid(body.pmid)
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="PubMed API unavailable")
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found on PubMed")

    ref = Reference(
        pmid=article["pmid"],
        title=article["title"],
        authors=", ".join(article["authors"]) or None,
        abstract=article["abstract"] or None,
        source="pubmed",
    )
    db.add(ref)
    db.flush()

    chunks_text = chunk_text(article["abstract"])
    for i, content in enumerate(chunks_text):
        db.add(Chunk(reference_id=ref.id, content=content, chunk_index=i))

    db.add(WorkingSetItem(reference_id=ref.id))
    db.commit()
    db.refresh(ref)

    return _to_response(ref, len(chunks_text))


@router.get("/", response_model=ReferenceListResponse)
def list_references(db: Session = Depends(get_db)) -> ReferenceListResponse:
    chunk_count_sub = (
        db.query(Chunk.reference_id, func.count(Chunk.id).label("cnt"))
        .group_by(Chunk.reference_id)
        .subquery()
    )

    rows = (
        db.query(Reference, func.coalesce(chunk_count_sub.c.cnt, 0))
        .join(WorkingSetItem, WorkingSetItem.reference_id == Reference.id)
        .outerjoin(chunk_count_sub, chunk_count_sub.c.reference_id == Reference.id)
        .all()
    )

    return ReferenceListResponse(
        references=[_to_response(ref, count) for ref, count in rows]
    )


@router.delete("/{reference_id}", status_code=204)
def delete_reference(
    reference_id: int,
    db: Session = Depends(get_db),
) -> None:
    ref = db.query(Reference).filter(Reference.id == reference_id).first()
    if not ref:
        raise HTTPException(status_code=404, detail="Reference not found")
    db.delete(ref)
    db.commit()

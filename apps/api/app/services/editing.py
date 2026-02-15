import json

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.chunk import Chunk
from app.models.message import Message
from app.models.message_version import MessageVersion
from app.schemas.claims import Claim
from app.schemas.messages import EditResponse, MessageDetail, MessageSummary, MessageVersionSchema, RefineResponse
from app.services.grounding_verifier import verify_claims
from app.services.llm_provider import LLMClaim, LLMProvider
from app.services.retrieval import retrieve

REFINE_SYSTEM_PROMPT = (
    "You are a medical/scientific writing assistant. "
    "You are given a previous message and an instruction to refine it. "
    "Generate updated claims based on the provided evidence chunks. "
    "Each claim must cite specific chunk_ids from the provided evidence. "
    "ONLY cite chunk_ids that appear in the evidence list. "
    "Return structured output with a list of claims, each containing text and citations."
)


def refine_message(
    db: Session,
    message_id: int,
    instruction: str,
    reference_ids: list[int],
    llm: LLMProvider,
    top_k: int = 5,
) -> RefineResponse:
    msg = db.get(Message, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    if msg.status != "draft":
        raise HTTPException(status_code=409, detail="Cannot refine a finalized message")

    latest = (
        db.query(MessageVersion)
        .filter_by(message_id=message_id)
        .order_by(MessageVersion.version_number.desc())
        .first()
    )

    chunks = retrieve(db, instruction, reference_ids, top_k)
    if not chunks:
        return RefineResponse(
            message_id=message_id,
            version_number=(latest.version_number if latest else 0) + 1,
            message_text="",
            claims=[],
            warnings=["Insufficient evidence: no relevant chunks found for the given references."],
        )

    previous_text = latest.message_text if latest else ""
    prompt = f"Previous message:\n{previous_text}\n\nInstruction: {instruction}"

    result = llm.generate_claims(prompt, chunks, REFINE_SYSTEM_PROMPT)
    supported, dropped = verify_claims(result.claims, chunks)

    message_text = " ".join(c.text for c in supported)
    warnings = [f"Dropped claim: '{c.text}' - {c.warning}" for c in dropped]

    version = MessageVersion(
        message_id=message_id,
        version_number=(latest.version_number if latest else 0) + 1,
        source="refined",
        prompt_or_instruction=instruction,
        message_text=message_text,
        claims_json=json.dumps([c.model_dump() for c in supported]),
        dropped_claims_json=json.dumps([c.model_dump() for c in dropped]),
    )
    db.add(version)
    db.flush()

    return RefineResponse(
        message_id=message_id,
        version_number=version.version_number,
        message_text=message_text,
        claims=supported,
        warnings=warnings,
    )


def edit_message(
    db: Session,
    message_id: int,
    message_text: str,
) -> EditResponse:
    msg = db.get(Message, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    previous = (
        db.query(MessageVersion)
        .filter_by(message_id=message_id)
        .order_by(MessageVersion.version_number.desc())
        .first()
    )

    warnings: list[str] = []
    chunk_ids: set[int] = set()

    if previous and previous.claims_json:
        prev_claims = json.loads(previous.claims_json)
        for c in prev_claims:
            for cit in c.get("citations", []):
                chunk_ids.add(cit.get("chunk_id"))

    if chunk_ids:
        chunks_rows = db.query(Chunk).filter(Chunk.id.in_(chunk_ids)).all()
        available_chunks = [{"id": ch.id, "content": ch.content} for ch in chunks_rows]
        claim = LLMClaim(text=message_text, citations=[])
        _, dropped = verify_claims([claim], available_chunks)
        if dropped:
            warnings.append(
                "Edited text could not be grounded against previous version's evidence. Review for accuracy."
            )
    else:
        warnings.append("Direct edit bypasses grounding verification. No previous evidence to check against.")

    max_version = (
        db.query(func.max(MessageVersion.version_number))
        .filter_by(message_id=message_id)
        .scalar()
        or 0
    )

    version = MessageVersion(
        message_id=message_id,
        version_number=max_version + 1,
        source="edited",
        prompt_or_instruction="direct edit",
        message_text=message_text,
        claims_json=json.dumps([{"text": message_text, "citations": [], "status": "supported"}]),
        dropped_claims_json="[]",
    )
    db.add(version)
    db.flush()

    return EditResponse(
        message_id=message_id,
        version_number=version.version_number,
        message_text=message_text,
        warnings=warnings,
    )


def list_messages(db: Session) -> list[MessageSummary]:
    max_version_sq = (
        db.query(
            MessageVersion.message_id,
            func.max(MessageVersion.version_number).label("max_vn"),
        )
        .group_by(MessageVersion.message_id)
        .subquery()
    )

    rows = (
        db.query(Message, MessageVersion)
        .join(max_version_sq, Message.id == max_version_sq.c.message_id)
        .join(
            MessageVersion,
            (MessageVersion.message_id == Message.id)
            & (MessageVersion.version_number == max_version_sq.c.max_vn),
        )
        .all()
    )

    results = []
    for msg, ver in rows:
        results.append(
            MessageSummary(
                id=msg.id,
                status=msg.status,
                created_at=msg.created_at,
                updated_at=msg.updated_at,
                latest_version=MessageVersionSchema.model_validate(ver),
            )
        )
    return results


def get_message(db: Session, message_id: int) -> MessageDetail:
    msg = db.get(Message, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    versions = (
        db.query(MessageVersion)
        .filter_by(message_id=message_id)
        .order_by(MessageVersion.version_number.asc())
        .all()
    )

    return MessageDetail(
        id=msg.id,
        status=msg.status,
        created_at=msg.created_at,
        updated_at=msg.updated_at,
        versions=[MessageVersionSchema.model_validate(v) for v in versions],
    )


def update_status(db: Session, message_id: int, status: str) -> Message:
    msg = db.get(Message, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    msg.status = status
    db.flush()
    return msg

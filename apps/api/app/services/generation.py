import json

from sqlalchemy.orm import Session

from app.models.message import Message
from app.models.message_version import MessageVersion
from app.schemas.generation import GenerateResponse
from app.services.grounding_verifier import verify_claims
from app.services.llm_provider import LLMProvider
from app.services.retrieval import retrieve

SYSTEM_PROMPT = (
    "You are a medical/scientific writing assistant. "
    "Generate claims based on the provided evidence chunks. "
    "Each claim must cite specific chunk_ids from the provided evidence. "
    "ONLY cite chunk_ids that appear in the evidence list. "
    "Return structured output with a list of claims, each containing text and citations."
)


def generate_message(
    db: Session,
    prompt: str,
    reference_ids: list[int],
    llm: LLMProvider,
    top_k: int = 5,
) -> GenerateResponse:
    chunks = retrieve(db, prompt, reference_ids, top_k)
    if not chunks:
        return GenerateResponse(
            message_id=None,
            message_text="",
            claims=[],
            warnings=["Insufficient evidence: no relevant chunks found for the given references."],
        )

    result = llm.generate_claims(prompt, chunks, SYSTEM_PROMPT)

    supported, dropped = verify_claims(result.claims, chunks)

    message_text = " ".join(c.text for c in supported)
    warnings: list[str] = [f"Dropped claim: '{c.text}' - {c.warning}" for c in dropped]

    msg = Message(status="draft")
    db.add(msg)
    db.flush()

    version = MessageVersion(
        message_id=msg.id,
        version_number=1,
        prompt_or_instruction=prompt,
        message_text=message_text,
        claims_json=json.dumps([c.model_dump() for c in supported]),
        dropped_claims_json=json.dumps([c.model_dump() for c in dropped]),
        source="generated",
    )
    db.add(version)
    db.flush()

    return GenerateResponse(
        message_id=msg.id,
        message_text=message_text,
        claims=supported,
        warnings=warnings,
    )

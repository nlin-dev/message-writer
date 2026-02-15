import asyncio
import json
from functools import partial
from typing import AsyncIterator

from sqlalchemy.orm import Session

from app.models.message import Message
from app.models.message_version import MessageVersion
from app.schemas.generation import GenerateResponse
from app.schemas.streaming import DeltaEvent, ErrorEvent, StatusEvent, sse_event
from app.services.generation import SYSTEM_PROMPT
from app.services.grounding_verifier import verify_claims
from app.services.llm_provider import LLMProvider, StreamResult
from app.services.retrieval import retrieve


async def stream_generate_pipeline(
    db: Session,
    prompt: str,
    reference_ids: list[int],
    llm: LLMProvider,
    top_k: int = 5,
) -> AsyncIterator[dict]:
    try:
        yield sse_event("status", StatusEvent(stage="retrieving"))

        loop = asyncio.get_running_loop()
        chunks = await loop.run_in_executor(
            None, partial(retrieve, db, prompt, reference_ids, top_k)
        )

        if not chunks:
            response = GenerateResponse(
                message_id=None,
                message_text="",
                claims=[],
                warnings=["Insufficient evidence: no relevant chunks found for the given references."],
            )
            yield sse_event("final", response)
            yield sse_event("status", StatusEvent(stage="done"))
            return

        yield sse_event("status", StatusEvent(stage="generating"))

        result = StreamResult()
        async for delta in llm.async_stream_claims(prompt, chunks, SYSTEM_PROMPT, result):
            yield sse_event("delta", DeltaEvent(text=delta))

        parsed = result.parsed
        if parsed is None:
            raise ValueError("Stream completed without parsed result")

        yield sse_event("status", StatusEvent(stage="verifying"))

        supported, dropped = await loop.run_in_executor(
            None, partial(verify_claims, parsed.claims, chunks)
        )

        message_text = " ".join(c.text for c in supported)
        warnings: list[str] = [
            f"Dropped claim: '{c.text}' - {c.warning}" for c in dropped
        ]

        yield sse_event("status", StatusEvent(stage="persisting"))

        def _persist():
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
            db.commit()
            return msg.id

        message_id = await loop.run_in_executor(None, _persist)

        response = GenerateResponse(
            message_id=message_id,
            message_text=message_text,
            claims=supported,
            warnings=warnings,
        )
        yield sse_event("final", response)
        yield sse_event("status", StatusEvent(stage="done"))

    except Exception as e:
        yield sse_event("error", ErrorEvent(message=str(e)))

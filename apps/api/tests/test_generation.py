from app.models.chunk import Chunk
from app.models.message import Message
from app.models.message_version import MessageVersion
from app.models.reference import Reference
from app.services.generation import generate_message
from app.services.llm_provider import (
    LLMCitation,
    LLMClaim,
    LLMGenerationResult,
    MockProvider,
)


def _seed_reference_with_chunks(db) -> tuple[int, int]:
    ref = Reference(title="Test", source="pubmed")
    db.add(ref)
    db.flush()
    chunk = Chunk(
        reference_id=ref.id,
        content="diabetes treatment insulin therapy",
        chunk_index=0,
    )
    db.add(chunk)
    db.flush()
    return ref.id, chunk.id


class TestGenerateMessage:
    def test_generate_with_no_evidence_returns_warning(self, db):
        provider = MockProvider(LLMGenerationResult(claims=[]))
        result = generate_message(db, "test prompt", [99999], provider)
        assert result.message_id is None
        assert result.claims == []
        assert any("Insufficient evidence" in w for w in result.warnings)

    def test_generate_with_mock_provider_persists_message(self, db):
        ref_id, chunk_id = _seed_reference_with_chunks(db)
        provider = MockProvider(
            LLMGenerationResult(
                claims=[
                    LLMClaim(
                        text="diabetes treatment uses insulin therapy",
                        citations=[LLMCitation(reference_id=ref_id, chunk_id=chunk_id)],
                    )
                ]
            )
        )
        result = generate_message(db, "diabetes", [ref_id], provider)
        assert result.message_id is not None
        assert result.message_text != ""
        assert len(result.claims) == 1
        msg = db.query(Message).filter_by(id=result.message_id).first()
        assert msg is not None
        version = db.query(MessageVersion).filter_by(message_id=msg.id).first()
        assert version is not None


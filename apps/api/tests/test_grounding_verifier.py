from app.schemas.claims import ClaimStatus
from app.services.grounding_verifier import verify_claims
from app.services.llm_provider import LLMClaim, LLMCitation


def _chunk(id: int, reference_id: int, content: str) -> dict:
    return {"id": id, "reference_id": reference_id, "content": content, "chunk_index": 0}


class TestVerifyClaims:
    def test_claim_with_no_citations_dropped(self):
        chunks = [_chunk(1, 1, "some text")]
        claims = [LLMClaim(text="a claim", citations=[])]
        supported, dropped = verify_claims(claims, chunks)
        assert len(supported) == 0
        assert len(dropped) == 1
        assert dropped[0].status == ClaimStatus.dropped
        assert "No citations provided" in dropped[0].warning

    def test_claim_citing_nonexistent_chunk_dropped(self):
        chunks = [_chunk(1, 1, "some text")]
        claims = [
            LLMClaim(
                text="a claim about something",
                citations=[LLMCitation(reference_id=1, chunk_id=999)],
            )
        ]
        supported, dropped = verify_claims(claims, chunks)
        assert len(supported) == 0
        assert len(dropped) == 1
        assert "invalid" in dropped[0].warning.lower()

    def test_claim_below_overlap_threshold_dropped(self):
        chunks = [_chunk(1, 1, "quantum physics entanglement theory")]
        claims = [
            LLMClaim(
                text="baseball statistics home runs batting average",
                citations=[LLMCitation(reference_id=1, chunk_id=1)],
            )
        ]
        supported, dropped = verify_claims(claims, chunks)
        assert len(supported) == 0
        assert len(dropped) == 1
        assert dropped[0].status == ClaimStatus.dropped


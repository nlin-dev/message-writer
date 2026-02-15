from app.schemas.claims import Citation, Claim, ClaimStatus
from app.services.llm_provider import LLMClaim


def verify_claims(
    claims: list[LLMClaim],
    available_chunks: list[dict],
    overlap_threshold: float = 0.3,
) -> tuple[list[Claim], list[Claim]]:
    chunk_map = {c["id"]: c for c in available_chunks}
    supported: list[Claim] = []
    dropped: list[Claim] = []

    for claim in claims:
        if not claim.citations:
            dropped.append(Claim(text=claim.text, citations=[], status=ClaimStatus.dropped, warning="No citations provided"))
            continue

        valid_citations: list[Citation] = []
        for cit in claim.citations:
            chunk = chunk_map.get(cit.chunk_id)
            if chunk is None:
                continue
            if _overlap_score(claim.text, chunk.get("content", "")) < overlap_threshold:
                continue
            valid_citations.append(Citation(reference_id=cit.reference_id, chunk_id=cit.chunk_id))

        if not valid_citations:
            dropped.append(
                Claim(text=claim.text, citations=[], status=ClaimStatus.dropped, warning="All citations invalid or below overlap threshold")
            )
        else:
            supported.append(Claim(text=claim.text, citations=valid_citations, status=ClaimStatus.supported, warning=None))

    return supported, dropped


def _overlap_score(claim_text: str, chunk_content: str) -> float:
    claim_words = set(claim_text.lower().split())
    if not claim_words:
        return 0.0
    chunk_words = set(chunk_content.lower().split())
    return len(claim_words & chunk_words) / len(claim_words)

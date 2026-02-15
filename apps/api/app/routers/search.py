from fastapi import APIRouter, Depends

from app.schemas.references import PubMedResult, SearchResponse
from app.services.pubmed_client import PubMedClient, get_pubmed_client

router = APIRouter(tags=["search"])


@router.get("/search", response_model=SearchResponse)
async def search(
    query: str = "",
    pubmed: PubMedClient = Depends(get_pubmed_client),
) -> SearchResponse:
    if not query.strip():
        return SearchResponse(results=[])

    raw_results = await pubmed.search(query)
    results = [PubMedResult(**r) for r in raw_results]
    return SearchResponse(results=results)

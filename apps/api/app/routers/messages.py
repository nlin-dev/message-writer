from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.schemas.generation import GenerateRequest, GenerateResponse
from app.services.generation import generate_message
from app.services.llm_provider import (
    LLMGenerationResult,
    LLMProvider,
    MockProvider,
    OpenAIProvider,
)

router = APIRouter(prefix="/messages", tags=["messages"])


def get_llm_provider() -> LLMProvider:
    if settings.openai_api_key:
        return OpenAIProvider(api_key=settings.openai_api_key, model=settings.openai_model)
    return MockProvider(fixed_result=LLMGenerationResult(claims=[]))


@router.post("/generate", response_model=GenerateResponse)
def generate(
    request: GenerateRequest,
    db: Session = Depends(get_db),
    llm: LLMProvider = Depends(get_llm_provider),
) -> GenerateResponse:
    response = generate_message(db, request.prompt, request.reference_ids, llm, request.top_k)
    db.commit()
    return response

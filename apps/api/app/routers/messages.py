from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.schemas.generation import GenerateRequest, GenerateResponse
from app.schemas.messages import (
    EditRequest,
    EditResponse,
    MessageDetail,
    MessageSummary,
    RefineRequest,
    RefineResponse,
    StatusResponse,
    StatusUpdate,
)
from app.services.editing import edit_message, get_message, list_messages, refine_message, update_status
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


@router.get("/", response_model=list[MessageSummary])
def list_all_messages(db: Session = Depends(get_db)) -> list[MessageSummary]:
    return list_messages(db)


@router.get("/{message_id}", response_model=MessageDetail)
def get_message_detail(message_id: int, db: Session = Depends(get_db)) -> MessageDetail:
    return get_message(db, message_id)


@router.post("/{message_id}/refine", response_model=RefineResponse)
def refine(
    message_id: int,
    request: RefineRequest,
    db: Session = Depends(get_db),
    llm: LLMProvider = Depends(get_llm_provider),
) -> RefineResponse:
    response = refine_message(db, message_id, request.instruction, request.reference_ids, llm, request.top_k)
    db.commit()
    return response


@router.put("/{message_id}", response_model=EditResponse)
def edit(
    message_id: int,
    request: EditRequest,
    db: Session = Depends(get_db),
) -> EditResponse:
    response = edit_message(db, message_id, request.message_text)
    db.commit()
    return response


@router.patch("/{message_id}", response_model=StatusResponse)
def patch_status(
    message_id: int,
    request: StatusUpdate,
    db: Session = Depends(get_db),
) -> StatusResponse:
    msg = update_status(db, message_id, request.status)
    db.commit()
    return StatusResponse(id=msg.id, status=msg.status)

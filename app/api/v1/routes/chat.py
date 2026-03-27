from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db_session
from app.schemas.chat import ChatAskRequest, ChatAskResponse
from app.services.chat import ChatService
from app.services.embeddings import EmbeddingService
from app.services.llm import LLMService
from app.services.retrieval import RetrievalService

router = APIRouter(prefix="/chat")


@router.post("/ask", response_model=ChatAskResponse)
async def ask_question(
    payload: ChatAskRequest,
    db_session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> ChatAskResponse:
    service = ChatService(
        settings=settings,
        embedding_service=EmbeddingService(settings=settings),
        retrieval_service=RetrievalService(db_session=db_session),
        llm_service=LLMService(settings=settings),
    )

    answer, citations = service.ask(
        question=payload.question,
        top_k=payload.top_k,
        document_ids=payload.document_ids,
    )

    return ChatAskResponse(answer=answer, citations=citations)

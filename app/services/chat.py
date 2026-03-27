from app.core.config import Settings
from app.schemas.chat import ChatCitation
from app.services.embeddings import EmbeddingService
from app.services.llm import LLMService
from app.services.retrieval import RetrievalService


class ChatService:
    def __init__(
        self,
        settings: Settings,
        embedding_service: EmbeddingService,
        retrieval_service: RetrievalService,
        llm_service: LLMService,
    ) -> None:
        self.settings = settings
        self.embedding_service = embedding_service
        self.retrieval_service = retrieval_service
        self.llm_service = llm_service

    def ask(
        self,
        question: str,
        top_k: int | None,
        document_ids: list[str] | None,
    ) -> tuple[str, list[ChatCitation]]:
        query_embedding = self.embedding_service.embed_text(question)
        retrieved = self.retrieval_service.retrieve(
            query_embedding=query_embedding,
            top_k=top_k or self.settings.retrieval_top_k,
            document_ids=document_ids,
        )
        answer = self.llm_service.answer_question(question=question, chunks=retrieved)

        citations = [
            ChatCitation(
                document_id=item.chunk.document_id,
                chunk_id=item.chunk.id,
                chunk_index=item.chunk.chunk_index,
                score=round(item.score, 4),
                text=item.chunk.content,
            )
            for item in retrieved
        ]

        return answer, citations

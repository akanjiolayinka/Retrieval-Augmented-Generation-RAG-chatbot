import math
from dataclasses import dataclass

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.models.document_chunk import DocumentChunk


@dataclass(slots=True)
class RetrievedChunk:
    chunk: DocumentChunk
    score: float


class RetrievalService:
    def __init__(self, db_session: Session) -> None:
        self.db_session = db_session

    def retrieve(
        self,
        query_embedding: list[float],
        top_k: int,
        document_ids: list[str] | None = None,
    ) -> list[RetrievedChunk]:
        dialect_name = self.db_session.bind.dialect.name if self.db_session.bind is not None else ""

        if dialect_name == "postgresql":
            return self._retrieve_postgres(query_embedding, top_k, document_ids)

        return self._retrieve_fallback(query_embedding, top_k, document_ids)

    def _retrieve_postgres(
        self,
        query_embedding: list[float],
        top_k: int,
        document_ids: list[str] | None,
    ) -> list[RetrievedChunk]:
        score_expr = (1 - DocumentChunk.embedding.cosine_distance(query_embedding)).label("score")
        statement = select(DocumentChunk, score_expr).where(DocumentChunk.embedding.is_not(None))

        if document_ids:
            statement = statement.where(DocumentChunk.document_id.in_(document_ids))

        statement = statement.order_by(desc(score_expr)).limit(top_k)

        rows = self.db_session.execute(statement).all()
        return [RetrievedChunk(chunk=row[0], score=float(row[1])) for row in rows]

    def _retrieve_fallback(
        self,
        query_embedding: list[float],
        top_k: int,
        document_ids: list[str] | None,
    ) -> list[RetrievedChunk]:
        statement = select(DocumentChunk).where(DocumentChunk.embedding.is_not(None))

        if document_ids:
            statement = statement.where(DocumentChunk.document_id.in_(document_ids))

        chunks = self.db_session.scalars(statement).all()

        scored = []
        for chunk in chunks:
            embedding = self._to_float_list(chunk.embedding)
            score = self._cosine_similarity(query_embedding, embedding)
            scored.append(RetrievedChunk(chunk=chunk, score=score))

        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:top_k]

    @staticmethod
    def _to_float_list(value: object) -> list[float]:
        if value is None:
            return []

        if isinstance(value, list):
            return [float(item) for item in value]

        if hasattr(value, "tolist"):
            raw_value = value.tolist()
            if isinstance(raw_value, list):
                return [float(item) for item in raw_value]

        return []

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        if not a or not b:
            return 0.0

        dot = sum(x * y for x, y in zip(a, b, strict=False))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot / (norm_a * norm_b)

from openai import OpenAI

from app.core.config import Settings
from app.services.retrieval import RetrievedChunk


class LLMService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client: OpenAI | None = None

        if settings.openai_api_key and settings.llm_provider == "openai":
            self._client = OpenAI(api_key=settings.openai_api_key)

    def answer_question(self, question: str, chunks: list[RetrievedChunk]) -> str:
        if self._client is None:
            return self._local_answer(question, chunks)

        context = "\n\n".join(
            [f"[source:{chunk.chunk.id}] {chunk.chunk.content}" for chunk in chunks]
        )
        prompt = (
            "You are a grounded assistant. Use only provided context. "
            "If context is insufficient, say you do not have enough information."
        )

        response = self._client.chat.completions.create(
            model=self.settings.llm_model,
            messages=[
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": f"Question: {question}\n\nContext:\n{context}",
                },
            ],
            temperature=0.1,
        )

        return response.choices[0].message.content or "I could not generate an answer."

    @staticmethod
    def _local_answer(question: str, chunks: list[RetrievedChunk]) -> str:
        if not chunks:
            return "I do not have enough information from your uploaded documents to answer that."

        top = chunks[0]
        return (
            f"Based on your documents, the best matching context is: {top.chunk.content[:400]}"
            f"\n\nQuestion asked: {question}"
        )

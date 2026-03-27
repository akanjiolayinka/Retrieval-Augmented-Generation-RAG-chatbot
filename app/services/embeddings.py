import hashlib
import math
from collections.abc import Sequence

from openai import OpenAI

from app.core.config import Settings


class EmbeddingService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client: OpenAI | None = None

        if settings.openai_api_key and settings.embedding_provider == "openai":
            self._client = OpenAI(api_key=settings.openai_api_key)

    def embed_text(self, text: str) -> list[float]:
        if self._client is None:
            return self._local_embedding(text)

        response = self._client.embeddings.create(
            model=self.settings.embedding_model,
            input=text,
            dimensions=self.settings.embedding_dimensions,
        )
        return list(response.data[0].embedding)

    def embed_many(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []

        if self._client is None:
            return [self._local_embedding(value) for value in texts]

        response = self._client.embeddings.create(
            model=self.settings.embedding_model,
            input=list(texts),
            dimensions=self.settings.embedding_dimensions,
        )
        return [list(item.embedding) for item in response.data]

    def _local_embedding(self, text: str) -> list[float]:
        vector = [0.0] * self.settings.embedding_dimensions

        words = text.lower().split()
        if not words:
            return vector

        for word in words:
            digest = hashlib.sha256(word.encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:4], "big") % self.settings.embedding_dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[bucket] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector

        return [value / norm for value in vector]

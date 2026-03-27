from pydantic import BaseModel, Field


class ChatAskRequest(BaseModel):
    question: str = Field(min_length=3)
    top_k: int | None = Field(default=None, ge=1, le=20)
    document_ids: list[str] | None = None


class ChatCitation(BaseModel):
    document_id: str
    chunk_id: int
    chunk_index: int
    score: float
    text: str


class ChatAskResponse(BaseModel):
    answer: str
    citations: list[ChatCitation]

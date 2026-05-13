"""Pydantic schemas for chat messages and citations."""

from pydantic import BaseModel


class QueryRequest(BaseModel):
    session_id: str
    query: str
    include_history: bool = True


class CitationResponse(BaseModel):
    chunk_id: str
    doc_id: str
    filename: str
    page_number: int | None = None
    chunk_index: int
    excerpt: str
    similarity_score: float


class MessageResponse(BaseModel):
    message_id: str
    session_id: str
    role: str
    content: str
    is_refusal: bool
    retrieved_chunks: list[CitationResponse] = []
    created_at: str


class QueryInitResponse(BaseModel):
    message_id: str


class ChatHistoryResponse(BaseModel):
    messages: list[MessageResponse]

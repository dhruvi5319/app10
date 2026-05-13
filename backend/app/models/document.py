"""Pydantic schemas for document request/response."""

from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    doc_id: str
    session_id: str
    filename: str
    status: str


class DocumentStatusResponse(BaseModel):
    doc_id: str
    session_id: str
    filename: str
    file_type: str
    file_size_bytes: int
    status: str
    chunk_count: int | None = None
    page_count: int | None = None
    error_message: str | None = None
    uploaded_at: str
    ready_at: str | None = None
    file_path: str


class DocumentListResponse(BaseModel):
    documents: list[DocumentStatusResponse]

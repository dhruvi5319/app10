"""Pydantic schemas for document request/response."""

from typing import Optional

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
    chunk_count: Optional[int] = None
    page_count: Optional[int] = None
    error_message: Optional[str] = None
    uploaded_at: str
    ready_at: Optional[str] = None
    file_path: str


class DocumentListResponse(BaseModel):
    documents: list[DocumentStatusResponse]

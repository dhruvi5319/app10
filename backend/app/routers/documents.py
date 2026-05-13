"""Document endpoints: upload, status, SSE progress, list, delete."""

import json
import os
import uuid
from pathlib import Path

import aiosqlite
from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.config import Settings, get_settings
from app.database import (
    count_session_documents,
    delete_document,
    get_db,
    get_document,
    insert_document,
    list_documents,
)
from app.models.document import (
    DocumentListResponse,
    DocumentStatusResponse,
    DocumentUploadResponse,
)
from app.models.errors import ErrorCode, ErrorResponse
from app.models.session import sessions
from app.services.ingestion import (
    get_progress_queue,
    ingest_document,
    remove_progress_queue,
)
from app.services.vector_store import delete_doc_chunks
from app.utils.file_validation import validate_upload

router = APIRouter(tags=["documents"])


# ---------------------------------------------------------------------------
# POST /api/documents/upload
# ---------------------------------------------------------------------------

@router.post(
    "/documents/upload",
    response_model=DocumentUploadResponse,
    status_code=202,
    responses={
        404: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
async def upload_document(
    file: UploadFile,
    session_id: str,
    background_tasks: BackgroundTasks,
    settings: Settings = None,
):
    if settings is None:
        settings = get_settings()

    # Validate session
    if session_id not in sessions:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": ErrorCode.SESSION_NOT_FOUND,
                "message": f"Session '{session_id}' not found",
            },
        )

    # Read file bytes
    file_bytes = await file.read()
    file_size = len(file_bytes)
    filename = file.filename or "upload"

    # Validate file (raises HTTPException on failure)
    file_type = validate_upload(filename, file_bytes, file_size, settings)

    # Check document count limit
    db = await get_db()
    try:
        doc_count = await count_session_documents(db, session_id)
        if doc_count >= settings.MAX_DOCS_PER_SESSION:
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": ErrorCode.DOCUMENT_LIMIT_REACHED,
                    "message": (
                        f"Session has reached the maximum of "
                        f"{settings.MAX_DOCS_PER_SESSION} documents"
                    ),
                },
            )

        # Save file to disk
        doc_id = str(uuid.uuid4())
        upload_dir = Path(settings.UPLOADS_DIR) / session_id / doc_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / filename
        file_path.write_bytes(file_bytes)

        # Insert document record
        await insert_document(
            db,
            doc_id=doc_id,
            session_id=session_id,
            filename=filename,
            file_type=file_type,
            file_size_bytes=file_size,
            file_path=str(file_path),
            status="UPLOADING",
        )

        # Add to session registry
        sessions[session_id].document_ids.append(doc_id)

    finally:
        await db.close()

    # Launch ingestion as background task (returns 202 immediately)
    background_tasks.add_task(
        _run_ingestion,
        doc_id=doc_id,
        session_id=session_id,
        filename=filename,
        file_type=file_type,
        file_bytes=file_bytes,
        settings=settings,
    )

    return DocumentUploadResponse(
        doc_id=doc_id,
        session_id=session_id,
        filename=filename,
        status="UPLOADING",
    )


async def _run_ingestion(
    doc_id: str,
    session_id: str,
    filename: str,
    file_type: str,
    file_bytes: bytes,
    settings: Settings,
) -> None:
    """Background task wrapper for ingest_document."""
    db = await get_db()
    try:
        await ingest_document(
            doc_id=doc_id,
            session_id=session_id,
            filename=filename,
            file_type=file_type,
            file_bytes=file_bytes,
            db=db,
            settings=settings,
        )
    finally:
        await db.close()


# ---------------------------------------------------------------------------
# GET /api/documents/{doc_id}/status
# ---------------------------------------------------------------------------

@router.get(
    "/documents/{doc_id}/status",
    response_model=DocumentStatusResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_document_status(doc_id: str):
    db = await get_db()
    try:
        doc = await get_document(db, doc_id)
    finally:
        await db.close()

    if doc is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "DOCUMENT_NOT_FOUND",
                "message": f"Document '{doc_id}' not found",
            },
        )
    return DocumentStatusResponse(**doc)


# ---------------------------------------------------------------------------
# GET /api/documents/upload/stream  (SSE)
# ---------------------------------------------------------------------------

@router.get("/documents/upload/stream")
async def stream_upload_progress(doc_id: str):
    """SSE endpoint streaming ingestion progress events for a given doc_id."""

    async def event_generator():
        queue = get_progress_queue(doc_id)
        try:
            while True:
                event = await queue.get()
                data = json.dumps(event)
                yield f"data: {data}\n\n"
                # Close stream when terminal status reached
                if event.get("status") in ("READY", "FAILED"):
                    break
        finally:
            remove_progress_queue(doc_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# GET /api/documents
# ---------------------------------------------------------------------------

@router.get(
    "/documents",
    response_model=DocumentListResponse,
    responses={404: {"model": ErrorResponse}},
)
async def list_session_documents(session_id: str):
    if session_id not in sessions:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": ErrorCode.SESSION_NOT_FOUND,
                "message": f"Session '{session_id}' not found",
            },
        )
    db = await get_db()
    try:
        docs = await list_documents(db, session_id)
    finally:
        await db.close()

    return DocumentListResponse(documents=[DocumentStatusResponse(**d) for d in docs])


# ---------------------------------------------------------------------------
# DELETE /api/documents/{doc_id}
# ---------------------------------------------------------------------------

@router.delete(
    "/documents/{doc_id}",
    status_code=204,
    responses={404: {"model": ErrorResponse}},
)
async def delete_document_endpoint(doc_id: str):
    db = await get_db()
    try:
        doc = await get_document(db, doc_id)
        if doc is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": "DOCUMENT_NOT_FOUND",
                    "message": f"Document '{doc_id}' not found",
                },
            )

        session_id = doc["session_id"]

        # Remove vector embeddings
        delete_doc_chunks(session_id, doc_id)

        # Delete from DB (cascades to chunks)
        await delete_document(db, doc_id)

        # Remove file from disk
        file_path = Path(doc["file_path"])
        if file_path.exists():
            file_path.unlink()
        # Remove parent dir if empty
        parent = file_path.parent
        try:
            parent.rmdir()
        except OSError:
            pass

        # Remove from session registry
        state = sessions.get(session_id)
        if state and doc_id in state.document_ids:
            state.document_ids.remove(doc_id)

    finally:
        await db.close()

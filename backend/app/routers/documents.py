"""Document endpoints: upload, status, SSE progress, list, delete."""

import json
import shutil
import uuid
from pathlib import Path
from typing import AsyncGenerator

import aiosqlite
from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, UploadFile
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

router = APIRouter(prefix="/documents", tags=["documents"])


async def get_db_dep() -> AsyncGenerator[aiosqlite.Connection, None]:
    """Async generator dependency that yields a DB connection and closes it after."""
    db = await get_db()
    try:
        yield db
    finally:
        await db.close()


async def _run_ingestion(
    doc_id: str,
    session_id: str,
    filename: str,
    file_type: str,
    file_bytes: bytes,
    settings: Settings,
) -> None:
    """Background task wrapper: opens its own DB connection for ingestion.

    The request's Depends-managed DB connection is closed before background
    tasks run, so this helper opens a fresh connection.
    """
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
# GET /api/documents/upload/stream  (SSE)
# IMPORTANT: This route MUST be registered BEFORE /{doc_id}/status to avoid
# path conflicts where "upload" would be treated as a doc_id.
# ---------------------------------------------------------------------------


@router.get("/upload/stream")
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
# POST /api/documents/upload
# ---------------------------------------------------------------------------


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=202,
    responses={
        404: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile,
    session_id: str = Form(...),
    db: aiosqlite.Connection = Depends(get_db_dep),
    settings: Settings = Depends(get_settings),
):
    # Validate session
    if session_id not in sessions:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": ErrorCode.SESSION_NOT_FOUND,
                "message": f"Session '{session_id}' not found",
            },
        )

    # Check document count limit
    doc_count = await count_session_documents(db, session_id)
    if doc_count >= settings.MAX_DOCS_PER_SESSION:
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": ErrorCode.DOCUMENT_LIMIT_REACHED,
                "message": (
                    f"Session has reached the maximum of {settings.MAX_DOCS_PER_SESSION} documents"
                ),
            },
        )

    # Read file bytes
    file_bytes = await file.read()
    file_size = len(file_bytes)
    filename = file.filename or "upload"

    # Validate file (raises HTTPException on failure)
    file_type = validate_upload(filename, file_bytes, file_size, settings)

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

    # Launch ingestion as background task (returns 202 immediately).
    # NOTE: We do NOT pass the request's `db` to the background task because
    # the Depends-managed connection will be closed when the request ends.
    # _run_ingestion opens its own fresh DB connection.
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


# ---------------------------------------------------------------------------
# GET /api/documents/{doc_id}/status
# ---------------------------------------------------------------------------


@router.get(
    "/{doc_id}/status",
    response_model=DocumentStatusResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_document_status(
    doc_id: str,
    db: aiosqlite.Connection = Depends(get_db_dep),
):
    doc = await get_document(db, doc_id)

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
# GET /api/documents
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=DocumentListResponse,
    responses={404: {"model": ErrorResponse}},
)
async def list_session_documents(
    session_id: str,
    db: aiosqlite.Connection = Depends(get_db_dep),
):
    if session_id not in sessions:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": ErrorCode.SESSION_NOT_FOUND,
                "message": f"Session '{session_id}' not found",
            },
        )

    docs = await list_documents(db, session_id)
    return DocumentListResponse(documents=[DocumentStatusResponse(**d) for d in docs])


# ---------------------------------------------------------------------------
# DELETE /api/documents/{doc_id}
# ---------------------------------------------------------------------------


@router.delete(
    "/{doc_id}",
    status_code=204,
    responses={404: {"model": ErrorResponse}},
)
async def delete_document_endpoint(
    doc_id: str,
    db: aiosqlite.Connection = Depends(get_db_dep),
    settings: Settings = Depends(get_settings),
):
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

    # Remove vector embeddings (sync, best-effort)
    delete_doc_chunks(session_id, doc_id)

    # Delete from DB (cascades to chunks)
    await delete_document(db, doc_id)

    # Remove file directory from disk
    shutil.rmtree(
        f"{settings.UPLOADS_DIR}/{session_id}/{doc_id}",
        ignore_errors=True,
    )

    # Remove from session registry
    state = sessions.get(session_id)
    if state and doc_id in state.document_ids:
        state.document_ids.remove(doc_id)

    await db.commit()

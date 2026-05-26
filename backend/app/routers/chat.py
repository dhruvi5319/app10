"""Chat endpoints: query, SSE stream, history, delete history."""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator

import aiosqlite
import openai
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.config import Settings, get_settings
from app.database import (
    count_ready_documents,
    delete_messages,
    get_citations,
    get_db,
    get_messages,
    get_recent_messages,
    insert_citation,
    insert_message,
    update_message,
)
from app.models.chat import (
    ChatHistoryResponse,
    CitationResponse,
    MessageResponse,
    QueryInitResponse,
    QueryRequest,
)
from app.models.errors import ErrorCode, ErrorResponse
from app.models.session import sessions
from app.services.embedder import embed_query
from app.services.vector_store import query_chunks

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# In-memory queues for streaming responses: message_id → asyncio.Queue
_pending_streams: dict[str, asyncio.Queue] = {}

GROUNDING_SYSTEM_PROMPT = """You are a document Q&A assistant. Answer questions ONLY based on the provided document excerpts below.

Rules:
- If the answer is found in the excerpts, answer it accurately and cite the source.
- If the answer is NOT in the excerpts, respond with: "I could not find information about that in the provided documents."
- Do NOT use any external knowledge or make assumptions beyond what is explicitly stated in the excerpts.
- Do NOT hallucinate or fabricate information."""


async def get_db_dep() -> AsyncGenerator[aiosqlite.Connection, None]:
    """Async generator dependency that yields a DB connection and closes it after."""
    db = await get_db()
    try:
        yield db
    finally:
        await db.close()


# ---------------------------------------------------------------------------
# POST /chat/query  →  /api/chat/query
# ---------------------------------------------------------------------------


@router.post(
    "/query",
    response_model=QueryInitResponse,
    responses={
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
async def chat_query(
    request: QueryRequest,
    db: aiosqlite.Connection = Depends(get_db_dep),
    settings: Settings = Depends(get_settings),
):
    # 1. Validate session
    if request.session_id not in sessions:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": ErrorCode.SESSION_NOT_FOUND,
                "message": f"Session '{request.session_id}' not found",
            },
        )

    # 2. Validate query
    query = request.query.strip()
    if not query:
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": ErrorCode.EMPTY_QUERY,
                "message": "Query cannot be empty",
            },
        )
    if len(query) > 2000:
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": ErrorCode.QUERY_TOO_LONG,
                "message": "Query must not exceed 2000 characters",
            },
        )

    # 3. Check READY documents
    ready_count = await count_ready_documents(db, request.session_id)
    if ready_count == 0:
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": ErrorCode.NO_DOCUMENTS_READY,
                "message": "No documents are ready. Upload and process a document first.",
            },
        )

    # 4. Save user message
    user_message_id = str(uuid.uuid4())
    await insert_message(db, user_message_id, request.session_id, "user", query)

    # 5. Create assistant message placeholder
    assistant_message_id = str(uuid.uuid4())
    await insert_message(
        db,
        assistant_message_id,
        request.session_id,
        "assistant",
        "",
        is_refusal=False,
    )

    # 6. Create streaming queue and register it
    _pending_streams[assistant_message_id] = asyncio.Queue()

    # 7. Launch background generation task
    asyncio.create_task(
        _generate_response(
            message_id=assistant_message_id,
            session_id=request.session_id,
            query=query,
            include_history=request.include_history,
            settings=settings,
        )
    )

    # 8. Commit before returning
    await db.commit()

    # 9. Return the assistant message id
    return QueryInitResponse(message_id=assistant_message_id)


# ---------------------------------------------------------------------------
# GET /chat/stream/{message_id}  →  /api/chat/stream/{message_id}  (SSE)
# ---------------------------------------------------------------------------


@router.get("/stream/{message_id}")
async def stream_chat_response(message_id: str):
    """SSE endpoint streaming tokens for a given message_id."""
    if message_id not in _pending_streams:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "STREAM_NOT_FOUND",
                "message": f"No active stream for message_id '{message_id}'",
            },
        )

    async def event_generator():
        queue = _pending_streams.get(message_id)
        if queue is None:
            return
        try:
            while True:
                event = await queue.get()
                data = json.dumps(event)
                yield f"data: {data}\n\n"
                if event.get("type") in ("done", "error"):
                    break
        finally:
            _pending_streams.pop(message_id, None)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# Background: _generate_response
# ---------------------------------------------------------------------------


async def _generate_response(
    message_id: str,
    session_id: str,
    query: str,
    include_history: bool,
    settings: Settings,
) -> None:
    """Background task: embed query, retrieve chunks, call LLM, stream tokens."""
    queue = _pending_streams.get(message_id)
    if queue is None:
        return

    # Open own DB connection (Depends-managed connection is closed after request)
    db = await get_db()
    try:
        # 1. Embed the query
        try:
            query_embedding = await embed_query(query, model=settings.EMBEDDING_MODEL)
        except HTTPException as exc:
            error_code = (
                exc.detail.get("error_code", ErrorCode.LLM_UNAVAILABLE)
                if isinstance(exc.detail, dict)
                else ErrorCode.LLM_UNAVAILABLE
            )
            await queue.put(
                {
                    "type": "error",
                    "error_code": error_code,
                    "message": "Failed to generate query embedding",
                }
            )
            return

        # 2. Retrieve relevant chunks
        try:
            retrieved_chunks = query_chunks(session_id, query_embedding, top_k=settings.TOP_K)
        except HTTPException as exc:
            await queue.put(
                {
                    "type": "error",
                    "error_code": ErrorCode.RETRIEVAL_FAILURE,
                    "message": "Vector retrieval failed",
                }
            )
            return

        # 3. Build context block
        context_parts: list[str] = []
        for chunk in retrieved_chunks:
            page_label = f"Page {chunk['page_number']}" if chunk["page_number"] else "N/A"
            context_parts.append(
                f"[Source: {chunk['filename']}, {page_label}, "
                f"Chunk {chunk['chunk_index'] + 1}]\n{chunk['text']}\n"
            )
        context_block = "\n".join(context_parts)

        # 4. Get recent history if include_history
        history: list[dict] = []
        if include_history:
            history = await get_recent_messages(db, session_id, turns=settings.CHAT_HISTORY_TURNS)

        # 5. Build LLM messages
        messages_for_llm: list[dict] = [
            {"role": "system", "content": GROUNDING_SYSTEM_PROMPT},
        ]

        # Add history (exclude placeholder messages with empty content)
        for msg in history:
            if msg["message_id"] == message_id:
                continue
            if msg["role"] in ("user", "assistant") and msg["content"]:
                messages_for_llm.append({"role": msg["role"], "content": msg["content"]})

        # User message: context block + question
        user_content = context_block + "\n\nQuestion: " + query
        messages_for_llm.append({"role": "user", "content": user_content})

        # 6. Stream from OpenAI
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        full_content = ""

        try:
            stream = await client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=messages_for_llm,
                temperature=settings.LLM_TEMPERATURE,
                stream=True,
            )

            async for chunk in stream:
                delta = chunk.choices[0].delta.content if chunk.choices else None
                if delta:
                    full_content += delta
                    await queue.put({"type": "token", "delta": delta})

        except openai.RateLimitError:
            await queue.put(
                {
                    "type": "error",
                    "error_code": ErrorCode.LLM_RATE_LIMIT,
                    "message": "LLM rate limit reached",
                }
            )
            await update_message(db, message_id, "[Error: LLM rate limit]", is_refusal=False)
            await db.commit()
            return
        except (openai.APIConnectionError, openai.APIStatusError) as exc:
            await queue.put(
                {
                    "type": "error",
                    "error_code": ErrorCode.LLM_UNAVAILABLE,
                    "message": f"LLM unavailable: {exc}",
                }
            )
            await update_message(
                db, message_id, f"[Error: LLM unavailable: {exc}]", is_refusal=False
            )
            await db.commit()
            return

        # 7. Detect refusal
        is_refusal = (not retrieved_chunks) or ("i could not find" in full_content.lower())

        # 8. Update message in DB
        await update_message(db, message_id, full_content, is_refusal)

        # 9. Insert citations (only if not refusal)
        citation_responses: list[CitationResponse] = []
        if not is_refusal:
            for chunk in retrieved_chunks:
                await insert_citation(
                    db,
                    message_id=message_id,
                    chunk_id=chunk["chunk_id"],
                    doc_id=chunk["doc_id"],
                    filename=chunk["filename"],
                    page_number=chunk.get("page_number"),
                    chunk_index=chunk["chunk_index"],
                    excerpt=chunk["text"][:500],
                    similarity_score=chunk.get("similarity_score"),
                )
                citation_responses.append(
                    CitationResponse(
                        chunk_id=chunk["chunk_id"],
                        doc_id=chunk["doc_id"],
                        filename=chunk["filename"],
                        page_number=chunk.get("page_number"),
                        chunk_index=chunk["chunk_index"],
                        excerpt=chunk["text"][:500],
                        similarity_score=chunk.get("similarity_score", 0.0),
                    )
                )

        # 10. Commit
        await db.commit()

        # 11. Build final MessageResponse and emit done event
        # Look up created_at from DB
        msgs = await get_messages(db, session_id)
        created_at = datetime.now(timezone.utc).isoformat()
        for m in msgs:
            if m["message_id"] == message_id:
                created_at = m["created_at"]
                break

        final_message = MessageResponse(
            message_id=message_id,
            session_id=session_id,
            role="assistant",
            content=full_content,
            is_refusal=is_refusal,
            retrieved_chunks=citation_responses,
            created_at=created_at,
        )
        await queue.put({"type": "done", "message": final_message.model_dump()})

    except Exception as exc:
        logger.error(f"Unexpected error in _generate_response: {exc}", exc_info=True)
        if queue is not None:
            await queue.put(
                {
                    "type": "error",
                    "error_code": ErrorCode.LLM_UNAVAILABLE,
                    "message": str(exc),
                }
            )
    finally:
        await db.close()


# ---------------------------------------------------------------------------
# GET /chat/history/{session_id}  →  /api/chat/history/{session_id}
# ---------------------------------------------------------------------------


@router.get(
    "/history/{session_id}",
    response_model=ChatHistoryResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_chat_history(
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

    msgs = await get_messages(db, session_id)
    result: list[MessageResponse] = []
    for msg in msgs:
        citations = await get_citations(db, msg["message_id"])
        citation_responses = [
            CitationResponse(
                chunk_id=c["chunk_id"],
                doc_id=c["doc_id"],
                filename=c["filename"],
                page_number=c.get("page_number"),
                chunk_index=c["chunk_index"],
                excerpt=c["excerpt"],
                similarity_score=c.get("similarity_score", 0.0),
            )
            for c in citations
        ]
        result.append(
            MessageResponse(
                message_id=msg["message_id"],
                session_id=msg["session_id"],
                role=msg["role"],
                content=msg["content"],
                is_refusal=bool(msg["is_refusal"]) if msg["is_refusal"] is not None else False,
                retrieved_chunks=citation_responses,
                created_at=msg["created_at"],
            )
        )

    return ChatHistoryResponse(messages=result)


# ---------------------------------------------------------------------------
# DELETE /chat/history/{session_id}  →  /api/chat/history/{session_id}
# ---------------------------------------------------------------------------


@router.delete(
    "/history/{session_id}",
    status_code=204,
    responses={404: {"model": ErrorResponse}},
)
async def delete_chat_history(
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

    await delete_messages(db, session_id)
    await db.commit()

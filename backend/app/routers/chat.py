"""Chat endpoints: query, SSE stream, history, delete history."""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone

import openai
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.config import Settings, get_settings
from app.database import (
    delete_messages,
    get_citations,
    get_db,
    get_messages,
    get_recent_messages,
    insert_citation,
    insert_message,
    update_message,
    count_ready_documents,
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
router = APIRouter(tags=["chat"])

# In-memory queues for streaming responses: message_id → asyncio.Queue
_pending_streams: dict[str, asyncio.Queue] = {}

REFUSAL_PATTERNS = [
    "i could not find",
    "cannot find",
    "not found in the",
    "not present in",
    "no information",
    "does not contain",
    "unable to find",
    "not mentioned",
    "i don't have information",
]


def _is_refusal(text: str) -> bool:
    lower = text.lower()
    return any(pattern in lower for pattern in REFUSAL_PATTERNS)


# ---------------------------------------------------------------------------
# POST /api/chat/query
# ---------------------------------------------------------------------------

@router.post(
    "/chat/query",
    response_model=QueryInitResponse,
    responses={
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
async def chat_query(request: QueryRequest):
    settings = get_settings()

    # Validate session
    if request.session_id not in sessions:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": ErrorCode.SESSION_NOT_FOUND,
                "message": f"Session '{request.session_id}' not found",
            },
        )

    # Validate query
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

    # Check READY documents
    db = await get_db()
    try:
        ready_count = await count_ready_documents(db, request.session_id)
        if ready_count == 0:
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": ErrorCode.NO_DOCUMENTS_READY,
                    "message": "No documents are ready. Upload and process a document first.",
                },
            )

        # Save user message
        user_message_id = str(uuid.uuid4())
        await insert_message(db, user_message_id, request.session_id, "user", query)

        # Create assistant message placeholder
        assistant_message_id = str(uuid.uuid4())
        await insert_message(
            db,
            assistant_message_id,
            request.session_id,
            "assistant",
            "",
            is_refusal=None,
        )
    finally:
        await db.close()

    # Create streaming queue
    _pending_streams[assistant_message_id] = asyncio.Queue()

    # Launch background generation
    asyncio.create_task(
        _generate_response(
            message_id=assistant_message_id,
            session_id=request.session_id,
            query=query,
            include_history=request.include_history,
            settings=settings,
        )
    )

    return QueryInitResponse(message_id=assistant_message_id)


# ---------------------------------------------------------------------------
# GET /api/chat/stream/{message_id}  (SSE)
# ---------------------------------------------------------------------------

@router.get("/chat/stream/{message_id}")
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
# Background: generate_response
# ---------------------------------------------------------------------------

async def _generate_response(
    message_id: str,
    session_id: str,
    query: str,
    include_history: bool,
    settings: Settings,
) -> None:
    """Background task: embed query, retrieve, call LLM, stream tokens."""
    queue = _pending_streams.get(message_id)
    if queue is None:
        return

    db = await get_db()
    try:
        # 1. Embed the query
        try:
            query_embedding = await embed_query(query, model=settings.EMBEDDING_MODEL)
        except HTTPException as exc:
            await _emit_error(queue, message_id, db, session_id, "LLM_UNAVAILABLE",
                              "Failed to generate query embedding")
            return

        # 2. Retrieve relevant chunks
        try:
            retrieved = query_chunks(session_id, query_embedding, top_k=settings.TOP_K)
        except HTTPException as exc:
            await _emit_error(queue, message_id, db, session_id,
                              ErrorCode.RETRIEVAL_FAILURE, "Vector retrieval failed")
            return

        # 3. Build context block
        context_parts: list[str] = []
        for chunk in retrieved:
            page_label = f"Page {chunk['page_number']}" if chunk['page_number'] else "N/A"
            context_parts.append(
                f"[Source: {chunk['filename']}, {page_label}, "
                f"Chunk {chunk['chunk_index'] + 1}]\n{chunk['text']}"
            )
        context_block = "\n\n---\n\n".join(context_parts)

        # 4. Build message history
        messages_for_llm: list[dict] = [
            {
                "role": "system",
                "content": (
                    "You are a document assistant. Answer the user's question using ONLY "
                    "the provided document excerpts. If the answer is not present in the "
                    "excerpts, respond with: 'I could not find an answer to your question "
                    "in the uploaded documents.' Do NOT use any external knowledge."
                ),
            }
        ]

        if include_history:
            history = await get_recent_messages(db, session_id, turns=settings.CHAT_HISTORY_TURNS)
            for msg in history:
                # Skip the placeholder assistant message we just created
                if msg["message_id"] == message_id:
                    continue
                if msg["role"] in ("user", "assistant") and msg["content"]:
                    messages_for_llm.append(
                        {"role": msg["role"], "content": msg["content"]}
                    )

        # Final user message: context + question
        if context_block:
            user_content = (
                f"Document excerpts:\n\n{context_block}\n\n"
                f"Question: {query}"
            )
        else:
            user_content = f"Question: {query}"

        messages_for_llm.append({"role": "user", "content": user_content})

        # 5. Call OpenAI with streaming
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        full_response = ""

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
                    full_response += delta
                    await queue.put({"type": "token", "delta": delta})

        except openai.RateLimitError:
            await _emit_error(queue, message_id, db, session_id,
                              ErrorCode.LLM_RATE_LIMIT, "LLM rate limit reached")
            return
        except (openai.APIConnectionError, openai.APIStatusError) as exc:
            await _emit_error(queue, message_id, db, session_id,
                              ErrorCode.LLM_UNAVAILABLE, f"LLM unavailable: {exc}")
            return

        if not full_response.strip():
            await _emit_error(queue, message_id, db, session_id,
                              ErrorCode.LLM_EMPTY_RESPONSE, "LLM returned empty response")
            return

        # 6. Determine refusal
        is_refusal = _is_refusal(full_response) or len(retrieved) == 0

        # 7. Persist assistant message
        await update_message(db, message_id, full_response, is_refusal)

        # 8. Persist citations (only if not refusal)
        citation_responses: list[CitationResponse] = []
        if not is_refusal:
            for chunk in retrieved:
                await insert_citation(
                    db,
                    message_id=message_id,
                    chunk_id=chunk["chunk_id"],
                    doc_id=chunk["doc_id"],
                    filename=chunk["filename"],
                    page_number=chunk.get("page_number"),
                    chunk_index=chunk["chunk_index"],
                    excerpt=chunk["text"][:800],
                    similarity_score=chunk.get("similarity_score"),
                )
                citation_responses.append(
                    CitationResponse(
                        chunk_id=chunk["chunk_id"],
                        doc_id=chunk["doc_id"],
                        filename=chunk["filename"],
                        page_number=chunk.get("page_number"),
                        chunk_index=chunk["chunk_index"],
                        excerpt=chunk["text"][:800],
                        similarity_score=chunk.get("similarity_score", 0.0),
                    )
                )
            await db.commit()

        # 9. Get message created_at
        msgs = await get_messages(db, session_id)
        created_at = datetime.now(timezone.utc).isoformat()
        for m in msgs:
            if m["message_id"] == message_id:
                created_at = m["created_at"]
                break

        # 10. Emit done event
        final_message = MessageResponse(
            message_id=message_id,
            session_id=session_id,
            role="assistant",
            content=full_response,
            is_refusal=is_refusal,
            retrieved_chunks=citation_responses,
            created_at=created_at,
        )
        await queue.put({"type": "done", "message": final_message.model_dump()})

    except Exception as exc:
        logger.error(f"Unexpected error in generate_response: {exc}", exc_info=True)
        await _emit_error(queue, message_id, db, session_id,
                          ErrorCode.LLM_UNAVAILABLE, str(exc))
    finally:
        await db.close()


async def _emit_error(
    queue: asyncio.Queue,
    message_id: str,
    db,
    session_id: str,
    error_code: str,
    message: str,
) -> None:
    try:
        await update_message(db, message_id, f"[Error: {message}]", is_refusal=False)
        await db.commit()
    except Exception:
        pass
    await queue.put({"type": "error", "error_code": error_code, "message": message})


# ---------------------------------------------------------------------------
# GET /api/chat/history/{session_id}
# ---------------------------------------------------------------------------

@router.get(
    "/chat/history/{session_id}",
    response_model=ChatHistoryResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_chat_history(session_id: str):
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
    finally:
        await db.close()

    return ChatHistoryResponse(messages=result)


# ---------------------------------------------------------------------------
# DELETE /api/chat/history/{session_id}
# ---------------------------------------------------------------------------

@router.delete(
    "/chat/history/{session_id}",
    status_code=204,
    responses={404: {"model": ErrorResponse}},
)
async def delete_chat_history(session_id: str):
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
        await delete_messages(db, session_id)
    finally:
        await db.close()

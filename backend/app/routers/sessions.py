"""Session management endpoints."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.errors import ErrorCode, ErrorResponse
from app.models.session import SessionState, sessions

router = APIRouter(tags=["sessions"])


class SessionCreateResponse(BaseModel):
    session_id: str
    created_at: str


class SessionGetResponse(BaseModel):
    session_id: str
    created_at: str
    document_count: int


@router.post("/sessions", response_model=SessionCreateResponse, status_code=201)
async def create_session():
    """Create a new session and return its ID."""
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    sessions[session_id] = SessionState(
        session_id=session_id,
        created_at=now,
    )
    return SessionCreateResponse(
        session_id=session_id,
        created_at=now.isoformat(),
    )


@router.get(
    "/sessions/{session_id}",
    response_model=SessionGetResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_session(session_id: str):
    """Get session details and update last_active timestamp."""
    state = sessions.get(session_id)
    if state is None:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                error_code=ErrorCode.SESSION_NOT_FOUND,
                message=f"Session '{session_id}' not found",
            ).model_dump(),
        )
    # Update last_active on access
    state.last_active = datetime.now(timezone.utc)
    return SessionGetResponse(
        session_id=state.session_id,
        created_at=state.created_at.isoformat(),
        document_count=len(state.document_ids),
    )

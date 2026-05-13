"""In-memory session registry."""

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class SessionState:
    session_id: str
    created_at: datetime
    document_ids: list[str] = field(default_factory=list)
    last_active: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# Module-level registry (in-memory)
sessions: dict[str, SessionState] = {}

"""In-memory operator-session store for the single-process local runtime.

Sessions live only while the API process is alive, matching the current local
product boundary. A durable store (Postgres) is a later increment behind the same
``SessionStore`` port.
"""

from __future__ import annotations

from deepwork_api.domain import Session


class InMemorySessionStore:
    """Process-local session storage keyed by opaque token."""

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    async def save(self, session: Session) -> None:
        self._sessions[session.token] = session

    async def get(self, token: str) -> Session | None:
        return self._sessions.get(token)

    async def delete(self, token: str) -> None:
        self._sessions.pop(token, None)

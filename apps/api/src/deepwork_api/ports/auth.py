"""Port for durable operator-session storage."""

from __future__ import annotations

from typing import Protocol

from deepwork_api.domain import Session


class SessionStore(Protocol):
    """Persist and retrieve minted operator sessions by opaque token."""

    async def save(self, session: Session) -> None:
        """Store a session, overwriting any prior entry for its token."""
        ...

    async def get(self, token: str) -> Session | None:
        """Return the stored session for ``token`` or ``None``."""
        ...

    async def delete(self, token: str) -> None:
        """Remove any session stored for ``token``; idempotent."""
        ...

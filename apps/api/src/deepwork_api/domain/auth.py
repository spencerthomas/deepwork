"""Operator session identity for application authentication.

Pure domain values only: no framework, credential source, clock, or storage.
The application layer owns credential comparison, token minting, and expiry.
"""

from __future__ import annotations

from dataclasses import dataclass


class AuthError(Exception):
    """Base error for authentication failures."""


class InvalidCredentialError(AuthError):
    """The supplied access credential did not match the configured key."""


class SessionNotFoundError(AuthError):
    """No live session exists for the presented token."""


class SessionExpiredError(AuthError):
    """The presented session exists but has passed its expiry."""


@dataclass(frozen=True, slots=True)
class Session:
    """A minted operator session. The token is opaque and server-issued."""

    token: str
    actor_id: str
    issued_at: float
    expires_at: float

    def is_expired(self, now: float) -> bool:
        """Return whether the session is expired at ``now`` epoch seconds."""

        return now >= self.expires_at

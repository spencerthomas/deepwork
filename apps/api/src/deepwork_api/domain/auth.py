"""Operator session identity for application authentication.

Pure domain values only: no framework, credential source, clock, or storage.
The application layer owns credential comparison, token minting, and expiry.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

DEFAULT_TENANT_ID = "tenant-local"
DEFAULT_WORKSPACE_ID = "workspace-local"
DEFAULT_ACTOR_ID = "operator"

_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")


def _validate_identifier(field: str, value: str) -> None:
    if not isinstance(value, str) or _IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field} must be a valid non-empty identifier")


class AuthError(Exception):
    """Base error for authentication failures."""


class InvalidCredentialError(AuthError):
    """The supplied access credential did not match the configured key."""


class SessionNotFoundError(AuthError):
    """No live session exists for the presented token."""


class SessionExpiredError(AuthError):
    """The presented session exists but has passed its expiry."""


@dataclass(frozen=True, slots=True)
class SecurityContext:
    """Immutable server-side identity and authorization scope for a session."""

    tenant_id: str = DEFAULT_TENANT_ID
    workspace_id: str = DEFAULT_WORKSPACE_ID
    actor_id: str = DEFAULT_ACTOR_ID

    def __post_init__(self) -> None:
        _validate_identifier("tenant_id", self.tenant_id)
        _validate_identifier("workspace_id", self.workspace_id)
        _validate_identifier("actor_id", self.actor_id)


DEFAULT_SECURITY_CONTEXT = SecurityContext()


@dataclass(frozen=True, slots=True)
class Session:
    """A minted operator session. The token is opaque and server-issued."""

    token: str
    security_context: SecurityContext
    issued_at: float
    expires_at: float

    @property
    def actor_id(self) -> str:
        """Preserve the existing actor projection for session consumers."""

        return self.security_context.actor_id

    def is_expired(self, now: float) -> bool:
        """Return whether the session is expired at ``now`` epoch seconds."""

        return now >= self.expires_at

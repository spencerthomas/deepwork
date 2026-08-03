"""Authentication use cases: login, session validation, and logout.

The v1 baseline is an application session established with a server-held access
key, per the accepted auth decision. Credential comparison is constant-time, the
session token is a cryptographically random opaque string, and the access key
never leaves the server.
"""

from __future__ import annotations

import hmac
import secrets
import time
from collections.abc import Callable

from deepwork_api.domain import (
    InvalidCredentialError,
    Session,
    SessionExpiredError,
    SessionNotFoundError,
)
from deepwork_api.ports import SessionStore

_DEFAULT_TTL_SECONDS = 12 * 60 * 60
_OPERATOR_ACTOR = "operator"


def _default_token() -> str:
    return secrets.token_urlsafe(32)


class AuthService:
    """Issue and validate operator sessions against a server-held access key."""

    def __init__(
        self,
        *,
        store: SessionStore,
        access_key: str,
        now: Callable[[], float] | None = None,
        token_factory: Callable[[], str] | None = None,
        ttl_seconds: int = _DEFAULT_TTL_SECONDS,
        actor_id: str = _OPERATOR_ACTOR,
    ) -> None:
        normalized = access_key.strip() if isinstance(access_key, str) else ""
        if not normalized:
            raise ValueError("access key must be a non-empty string")
        if ttl_seconds <= 0:
            raise ValueError("session ttl must be positive")
        self._store = store
        self._access_key = normalized
        self._now = now if now is not None else time.time
        self._token_factory = token_factory if token_factory is not None else _default_token
        self._ttl = ttl_seconds
        self._actor_id = actor_id

    async def login(self, credential: str) -> Session:
        """Exchange the access key for a fresh session, or fail closed."""

        provided = credential if isinstance(credential, str) else ""
        if not hmac.compare_digest(provided.encode("utf-8"), self._access_key.encode("utf-8")):
            raise InvalidCredentialError
        now = float(self._now())
        session = Session(
            token=self._token_factory(),
            actor_id=self._actor_id,
            issued_at=now,
            expires_at=now + self._ttl,
        )
        await self._store.save(session)
        return session

    async def authenticate(self, token: str) -> Session:
        """Return the live session for ``token`` or fail closed."""

        if not isinstance(token, str) or not token:
            raise SessionNotFoundError
        session = await self._store.get(token)
        if session is None:
            raise SessionNotFoundError
        if session.is_expired(float(self._now())):
            await self._store.delete(token)
            raise SessionExpiredError
        return session

    async def logout(self, token: str) -> None:
        """Revoke the session for ``token``; idempotent and never raises."""

        if isinstance(token, str) and token:
            await self._store.delete(token)

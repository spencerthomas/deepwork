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
from collections.abc import Callable, Mapping

from deepwork_api.domain import (
    DEFAULT_ACTOR_ID,
    DEFAULT_TENANT_ID,
    DEFAULT_WORKSPACE_ID,
    InvalidCredentialError,
    SecurityContext,
    Session,
    SessionExpiredError,
    SessionNotFoundError,
)
from deepwork_api.ports import SessionStore

_DEFAULT_TTL_SECONDS = 12 * 60 * 60


def _default_token() -> str:
    return secrets.token_urlsafe(32)


class AuthService:
    """Issue and validate sessions against server-held access keys."""

    def __init__(
        self,
        *,
        store: SessionStore,
        access_key: str | None = None,
        access_key_contexts: Mapping[str, SecurityContext] | None = None,
        now: Callable[[], float] | None = None,
        token_factory: Callable[[], str] | None = None,
        ttl_seconds: int = _DEFAULT_TTL_SECONDS,
        actor_id: str = DEFAULT_ACTOR_ID,
    ) -> None:
        if (access_key is None) == (access_key_contexts is None):
            raise ValueError("configure exactly one access key mode")
        if ttl_seconds <= 0:
            raise ValueError("session ttl must be positive")

        credentials: tuple[tuple[bytes, SecurityContext], ...]
        if access_key is not None:
            normalized = access_key.strip() if isinstance(access_key, str) else ""
            if not normalized:
                raise ValueError("access key must be a non-empty string")
            context = SecurityContext(
                tenant_id=DEFAULT_TENANT_ID,
                workspace_id=DEFAULT_WORKSPACE_ID,
                actor_id=actor_id,
            )
            credentials = ((normalized.encode("utf-8"), context),)
        else:
            if not isinstance(access_key_contexts, Mapping) or not access_key_contexts:
                raise ValueError("access key mapping must contain at least one entry")
            normalized_keys: set[str] = set()
            configured: list[tuple[bytes, SecurityContext]] = []
            for raw_key, context in access_key_contexts.items():
                normalized = raw_key.strip() if isinstance(raw_key, str) else ""
                if not normalized:
                    raise ValueError("access key mapping keys must be non-empty strings")
                if normalized in normalized_keys:
                    raise ValueError("access key mapping keys must be unique after normalization")
                if not isinstance(context, SecurityContext):
                    raise ValueError("access key mapping values must be SecurityContext instances")
                normalized_keys.add(normalized)
                configured.append((normalized.encode("utf-8"), context))
            credentials = tuple(configured)

        self._store = store
        self._credential_contexts = credentials
        self._now = now if now is not None else time.time
        self._token_factory = token_factory if token_factory is not None else _default_token
        self._ttl = ttl_seconds

    async def login(self, credential: str) -> Session:
        """Exchange a configured access key for a fresh session, or fail closed."""

        provided = (credential if isinstance(credential, str) else "").encode("utf-8")
        matched_context: SecurityContext | None = None
        for configured_key, context in self._credential_contexts:
            if hmac.compare_digest(provided, configured_key):
                matched_context = context
        if matched_context is None:
            raise InvalidCredentialError
        now = float(self._now())
        session = Session(
            token=self._token_factory(),
            security_context=matched_context,
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

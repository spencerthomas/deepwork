"""Unit tests for the operator authentication service."""

from __future__ import annotations

import pytest

from deepwork_api.adapters.auth import InMemorySessionStore
from deepwork_api.application import AuthService
from deepwork_api.domain import (
    InvalidCredentialError,
    SessionExpiredError,
    SessionNotFoundError,
)


def _service(*, now_value: list[float], tokens: list[str], ttl: int = 100) -> AuthService:
    token_iter = iter(tokens)
    return AuthService(
        store=InMemorySessionStore(),
        access_key="s3cret-access-key",
        now=lambda: now_value[0],
        token_factory=lambda: next(token_iter),
        ttl_seconds=ttl,
    )


async def test_login_with_correct_key_issues_session() -> None:
    auth = _service(now_value=[1000.0], tokens=["tok-1"])
    session = await auth.login("s3cret-access-key")
    assert session.token == "tok-1"
    assert session.actor_id == "operator"
    assert session.expires_at == 1100.0


async def test_login_with_wrong_key_fails_closed() -> None:
    auth = _service(now_value=[1000.0], tokens=["tok-1"])
    with pytest.raises(InvalidCredentialError):
        await auth.login("wrong-key")


async def test_authenticate_returns_live_session() -> None:
    now = [1000.0]
    auth = _service(now_value=now, tokens=["tok-1"])
    issued = await auth.login("s3cret-access-key")
    now[0] = 1050.0
    assert (await auth.authenticate(issued.token)).token == "tok-1"


async def test_authenticate_unknown_token_fails() -> None:
    auth = _service(now_value=[1000.0], tokens=["tok-1"])
    with pytest.raises(SessionNotFoundError):
        await auth.authenticate("nope")


async def test_authenticate_expired_session_is_revoked() -> None:
    now = [1000.0]
    auth = _service(now_value=now, tokens=["tok-1"], ttl=100)
    issued = await auth.login("s3cret-access-key")
    now[0] = 1100.0  # exactly at expiry -> expired
    with pytest.raises(SessionExpiredError):
        await auth.authenticate(issued.token)
    # A revoked session is gone, not merely expired-on-read.
    now[0] = 1000.0
    with pytest.raises(SessionNotFoundError):
        await auth.authenticate(issued.token)


async def test_logout_revokes_session() -> None:
    auth = _service(now_value=[1000.0], tokens=["tok-1"])
    issued = await auth.login("s3cret-access-key")
    await auth.logout(issued.token)
    with pytest.raises(SessionNotFoundError):
        await auth.authenticate(issued.token)


async def test_empty_access_key_is_rejected_at_construction() -> None:
    with pytest.raises(ValueError, match="access key"):
        AuthService(store=InMemorySessionStore(), access_key="   ")

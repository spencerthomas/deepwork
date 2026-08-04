"""Unit tests for the operator authentication service."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from deepwork_api.adapters.auth import InMemorySessionStore
from deepwork_api.application import AuthService
from deepwork_api.domain import (
    DEFAULT_ACTOR_ID,
    DEFAULT_TENANT_ID,
    DEFAULT_WORKSPACE_ID,
    InvalidCredentialError,
    SecurityContext,
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
    assert session.actor_id == DEFAULT_ACTOR_ID
    assert session.security_context == SecurityContext(
        tenant_id=DEFAULT_TENANT_ID,
        workspace_id=DEFAULT_WORKSPACE_ID,
        actor_id=DEFAULT_ACTOR_ID,
    )
    assert session.expires_at == 1100.0


def test_security_context_is_validated_and_immutable() -> None:
    context = SecurityContext(tenant_id="tenant-a", workspace_id="workspace-1", actor_id="actor:2")

    with pytest.raises(FrozenInstanceError):
        context.workspace_id = "workspace-2"  # type: ignore[misc]


@pytest.mark.parametrize("field", ["tenant_id", "workspace_id", "actor_id"])
@pytest.mark.parametrize("invalid", ["", "   ", "has spaces", "/root", "x" * 257])
def test_security_context_rejects_invalid_identifiers(field: str, invalid: str) -> None:
    values = {"tenant_id": "tenant-a", "workspace_id": "workspace-a", "actor_id": "actor-a"}
    values[field] = invalid

    with pytest.raises(ValueError, match=field):
        SecurityContext(**values)


async def test_access_key_mapping_issues_sessions_in_the_mapped_context() -> None:
    contexts = {
        "key-a": SecurityContext("tenant-a", "workspace-a", "actor-a"),
        "key-b": SecurityContext("tenant-b", "workspace-b", "actor-b"),
    }
    tokens = iter(["tok-a", "tok-b"])
    auth = AuthService(
        store=InMemorySessionStore(),
        access_key_contexts=contexts,
        now=lambda: 1000.0,
        token_factory=lambda: next(tokens),
    )

    first = await auth.login("key-a")
    second = await auth.login("key-b")

    assert first.security_context == contexts["key-a"]
    assert first.actor_id == "actor-a"
    assert second.security_context == contexts["key-b"]
    assert second.actor_id == "actor-b"


async def test_access_key_mapping_is_copied_and_unknown_keys_fail_closed() -> None:
    contexts = {"known": SecurityContext("tenant-a", "workspace-a", "actor-a")}
    auth = AuthService(store=InMemorySessionStore(), access_key_contexts=contexts)
    contexts["added-later"] = SecurityContext("tenant-b", "workspace-b", "actor-b")

    with pytest.raises(InvalidCredentialError):
        await auth.login("added-later")
    with pytest.raises(InvalidCredentialError):
        await auth.login("unknown")


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


def test_access_key_configuration_requires_exactly_one_mode() -> None:
    context = SecurityContext("tenant-a", "workspace-a", "actor-a")

    with pytest.raises(ValueError, match="exactly one"):
        AuthService(store=InMemorySessionStore())
    with pytest.raises(ValueError, match="exactly one"):
        AuthService(
            store=InMemorySessionStore(),
            access_key="single",
            access_key_contexts={"mapped": context},
        )


def test_access_key_mapping_rejects_empty_or_ambiguous_keys() -> None:
    context = SecurityContext("tenant-a", "workspace-a", "actor-a")

    with pytest.raises(ValueError, match="at least one"):
        AuthService(store=InMemorySessionStore(), access_key_contexts={})
    with pytest.raises(ValueError, match="non-empty"):
        AuthService(store=InMemorySessionStore(), access_key_contexts={"   ": context})
    with pytest.raises(ValueError, match="unique"):
        AuthService(
            store=InMemorySessionStore(),
            access_key_contexts={"same": context, " same ": context},
        )

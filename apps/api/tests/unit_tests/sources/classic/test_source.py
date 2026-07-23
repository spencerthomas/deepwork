"""Offline tests for dormant classic Deployment qualification."""

from __future__ import annotations

import sys
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from types import SimpleNamespace

import pytest

from deepwork_api.adapters.sources.classic import (
    LIVE_CONTRACT_CAPABILITIES,
    ClassicSourceConfigurationError,
    ClassicSourceSettings,
    qualify_classic_sources,
    validate_deployment_endpoint,
)


@dataclass
class FakeAssistants:
    response: object
    error: Exception | None = None
    calls: list[str] = field(default_factory=list)

    async def get(self, assistant_id: str) -> object:
        self.calls.append(assistant_id)
        if self.error is not None:
            raise self.error
        return self.response


@dataclass
class FakeClient:
    assistants: FakeAssistants
    close_error: Exception | None = None
    close_calls: int = 0

    async def aclose(self) -> None:
        self.close_calls += 1
        if self.close_error is not None:
            raise self.close_error


@dataclass
class RecordingFactory:
    clients: list[FakeClient]
    calls: list[dict[str, object]] = field(default_factory=list)

    def __call__(self, **kwargs: object) -> FakeClient:
        self.calls.append(kwargs)
        return self.clients[len(self.calls) - 1]


def _settings(
    source_id: str = "source-one",
    *,
    endpoint: str = "https://example.us.langgraph.app/team/mount/",
    assistant_id: str = "assistant-one",
    auth_ref: str = "vault:classic/source-one",
    enabled: bool = True,
) -> ClassicSourceSettings:
    return ClassicSourceSettings(
        source_id=source_id,
        endpoint=endpoint,
        assistant_id=assistant_id,
        auth_ref=auth_ref,
        enabled=enabled,
    )


def _client(
    *,
    assistant_id: str = "assistant-one",
    graph_id: str = "graph-one",
    error: Exception | None = None,
    close_error: Exception | None = None,
) -> FakeClient:
    return FakeClient(
        assistants=FakeAssistants(
            response={"assistant_id": assistant_id, "graph_id": graph_id, "secret": "ignored"},
            error=error,
        ),
        close_error=close_error,
    )


@pytest.mark.parametrize(
    "value",
    [
        "http://example.langgraph.app",
        "https://127.0.0.1",
        "https://127.1/agent",
        "https://0x7f.0.0.1/agent",
        "https://example.com:0/agent",
        "https://[::1]/agent",
        "https://localhost/agent",
        "https://singlelabel/agent",
        "https://bad_host.example/agent",
        "https://éxample.com/agent",
        "https://user:secret@example.com/agent",
        "https://example.com/agent?token=secret",
        "https://example.com/agent#fragment",
        "https://example.com//evil",
        "https://example.com/a/../admin",
        "https://example.com/./admin",
        "https://example.com/%2f%2fevil",
        "https://example.com/%252f%252fevil",
        "https://example.com/a%2fb",
        "https://example.com/a%5cb",
        "https://example.com/%2e%2e/admin",
        "https://example.com/%252e%252e/admin",
        "https://example.com/%2525252e%2525252e/admin",
        "https://example.com/%2525252f%2525252fevil",
        "https://example.com/a%2525255cb",
        "https://example.com/%25252500admin",
        "https://example.com/%00admin",
        "https://example.com/%7fadmin",
        "https://example.com/%zz",
        "https://example.com/%25zz",
        "https://example.com/%2525zz",
        "https://example.com/\x01admin",
        r"https://example.com/a\evil",
    ],
)
def test_endpoint_rejects_unsafe_shapes(value: str) -> None:
    with pytest.raises(ClassicSourceConfigurationError):
        validate_deployment_endpoint(value)


def test_endpoint_preserves_explicit_https_mount_path() -> None:
    assert (
        validate_deployment_endpoint("https://Example.COM:8443/team/deployment/")
        == "https://example.com:8443/team/deployment"
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_id", ""),
        ("source_id", "x" * 257),
        ("assistant_id", "assistant with spaces"),
        ("auth_ref", ""),
        ("auth_ref", "x" * 513),
        ("auth_ref", "vault:secret?raw=yes"),
    ],
)
def test_settings_enforce_identifier_and_auth_ref_bounds(field: str, value: str) -> None:
    source_id = value if field == "source_id" else "source-one"
    assistant_id = value if field == "assistant_id" else "assistant-one"
    auth_ref = value if field == "auth_ref" else "vault:classic/source-one"
    with pytest.raises(ClassicSourceConfigurationError):
        ClassicSourceSettings(
            source_id=source_id,
            endpoint="https://example.com/mount",
            assistant_id=assistant_id,
            auth_ref=auth_ref,
        )


def test_settings_safe_projection_excludes_auth_ref_and_endpoint() -> None:
    settings = _settings(auth_ref="vault:never-print-this")
    assert "never-print-this" not in repr(settings)
    assert asdict(settings.safe_projection()) == {
        "source_id": "source-one",
        "assistant_id": "assistant-one",
        "enabled": True,
    }


@pytest.mark.asyncio
async def test_default_gate_has_zero_resolver_factory_and_client_calls() -> None:
    calls: list[str] = []

    async def resolver(auth_ref: str) -> str:
        calls.append(auth_ref)
        return "secret"

    factory = RecordingFactory([_client()])
    result = await qualify_classic_sources(
        [_settings()],
        credential_resolver=resolver,
        client_factory=factory,
    )

    assert result[0].state == "gated"
    assert calls == []
    assert factory.calls == []
    assert factory.clients[0].close_calls == 0


@pytest.mark.asyncio
async def test_per_source_gate_skips_all_side_effects() -> None:
    calls: list[str] = []

    async def resolver(auth_ref: str) -> str:
        calls.append(auth_ref)
        return "secret"

    factory = RecordingFactory([_client()])
    result = await qualify_classic_sources(
        [_settings(enabled=False)],
        credential_resolver=resolver,
        enabled=True,
        client_factory=factory,
    )
    assert result[0].state == "gated"
    assert calls == []
    assert factory.calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize("credential", [None, "", "   ", "x" * 8_193])
async def test_unusable_credentials_are_permission_denied_before_factory(
    credential: object,
) -> None:
    resolver_calls: list[str] = []

    async def resolver(auth_ref: str) -> str:
        resolver_calls.append(auth_ref)
        return credential  # type: ignore[return-value]

    client = _client()
    factory = RecordingFactory([client])
    result = await qualify_classic_sources(
        [_settings()],
        credential_resolver=resolver,
        enabled=True,
        client_factory=factory,
    )
    assert result[0].state == "permission-denied"
    assert result[0].reason == "credential-unavailable"
    assert resolver_calls == ["vault:classic/source-one"]
    assert factory.calls == []
    assert client.assistants.calls == []
    assert client.close_calls == 0


@pytest.mark.asyncio
async def test_resolver_exception_is_permission_denied_before_factory() -> None:
    async def resolver(auth_ref: str) -> str:
        raise RuntimeError("secret resolver detail")

    client = _client()
    factory = RecordingFactory([client])
    result = await qualify_classic_sources(
        [_settings()],
        credential_resolver=resolver,
        enabled=True,
        client_factory=factory,
    )
    assert result[0].state == "permission-denied"
    assert result[0].reason == "credential-unavailable"
    assert "resolver detail" not in repr(result)
    assert factory.calls == []
    assert client.assistants.calls == []
    assert client.close_calls == 0


@pytest.mark.asyncio
async def test_factory_value_error_is_not_an_assistant_contract_mismatch() -> None:
    async def resolver(auth_ref: str) -> str:
        return "secret"

    factory_calls: list[dict[str, object]] = []

    def factory(**kwargs: object) -> FakeClient:
        factory_calls.append(kwargs)
        raise ValueError("factory private detail")

    result = await qualify_classic_sources(
        [_settings()],
        credential_resolver=resolver,
        enabled=True,
        client_factory=factory,
    )
    assert result[0].state == "unknown"
    assert result[0].reason == "client-unavailable"
    assert len(factory_calls) == 1
    assert "factory private detail" not in repr(result)


@pytest.mark.asyncio
async def test_duplicate_ids_rejected_before_any_side_effect() -> None:
    calls: list[str] = []

    async def resolver(auth_ref: str) -> str:
        calls.append(auth_ref)
        return "secret"

    with pytest.raises(ClassicSourceConfigurationError, match="duplicate"):
        await qualify_classic_sources(
            [_settings(), _settings()],
            credential_resolver=resolver,
            enabled=True,
            client_factory=RecordingFactory([_client()]),
        )
    assert calls == []


@pytest.mark.asyncio
async def test_official_sdk_kwargs_and_bounded_assistant_projection() -> None:
    resolved: list[str] = []

    async def resolver(auth_ref: str) -> str:
        resolved.append(auth_ref)
        return "resolved-api-key"

    client = _client()
    factory = RecordingFactory([client])
    result = await qualify_classic_sources(
        [_settings()],
        credential_resolver=resolver,
        enabled=True,
        client_factory=factory,
    )

    assert resolved == ["vault:classic/source-one"]
    assert factory.calls == [
        {
            "url": "https://example.us.langgraph.app/team/mount",
            "api_key": "resolved-api-key",
            "headers": {},
            "timeout": (5.0, 20.0, 20.0, 5.0),
        }
    ]
    assert client.assistants.calls == ["assistant-one"]
    assert result[0].assistant is not None
    assert result[0].assistant.source_id == "source-one"
    assert result[0].assistant.assistant_id == "assistant-one"
    assert result[0].assistant.graph_id == "graph-one"
    assert not hasattr(result[0], "auth_ref")
    assert not hasattr(result[0], "endpoint")
    assert client.close_calls == 1


@pytest.mark.asyncio
async def test_dynamic_official_factory_uses_installed_get_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression for langgraph-sdk 0.4.2 ``assistants.get(id)``."""

    async def resolver(auth_ref: str) -> str:
        return "resolved-api-key"

    client = _client()
    factory = RecordingFactory([client])

    monkeypatch.setitem(sys.modules, "langgraph_sdk", SimpleNamespace(get_client=factory))
    result = await qualify_classic_sources(
        [_settings()],
        credential_resolver=resolver,
        enabled=True,
    )

    assert result[0].state == "available"
    assert client.assistants.calls == ["assistant-one"]
    assert factory.calls[0]["headers"] == {}
    assert client.close_calls == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "response",
    [
        {},
        {"assistant_id": "assistant-one"},
        {"assistant_id": "other", "graph_id": "graph-one"},
        {"assistant_id": "assistant-one", "graph_id": "bad graph"},
        [{"assistant_id": "assistant-one", "graph_id": "graph-one"}],
        "not-a-list",
    ],
)
async def test_malformed_assistant_shapes_fail_closed(response: object) -> None:
    async def resolver(auth_ref: str) -> str:
        return "secret"

    client = FakeClient(assistants=FakeAssistants(response=response))
    result = await qualify_classic_sources(
        [_settings()],
        credential_resolver=resolver,
        enabled=True,
        client_factory=RecordingFactory([client]),
    )
    assert result[0].state == "unavailable"
    assert result[0].assistant is None
    assert result[0].reason == "assistant-contract-mismatch"
    assert client.close_calls == 1


@pytest.mark.asyncio
async def test_exception_text_and_auth_class_are_not_forwarded_or_inferred() -> None:
    async def resolver(auth_ref: str) -> str:
        return "secret"

    client = _client(error=RuntimeError("401 invalid token super-secret"))
    result = await qualify_classic_sources(
        [_settings()],
        credential_resolver=resolver,
        enabled=True,
        client_factory=RecordingFactory([client]),
    )
    assert result[0].state == "unknown"
    assert result[0].reason == "qualification-failed"
    assert "401" not in repr(result)
    assert "secret" not in repr(result)
    assert client.close_calls == 1


@pytest.mark.asyncio
async def test_lookup_value_error_is_transport_unknown_not_contract_mismatch() -> None:
    async def resolver(auth_ref: str) -> str:
        return "secret"

    client = _client(error=ValueError("lookup private response text"))
    result = await qualify_classic_sources(
        [_settings()],
        credential_resolver=resolver,
        enabled=True,
        client_factory=RecordingFactory([client]),
    )
    assert result[0].state == "unknown"
    assert result[0].reason == "qualification-failed"
    assert result[0].assistant is None
    assert "lookup private response text" not in repr(result)
    assert client.close_calls == 1


@pytest.mark.asyncio
async def test_missing_assistant_is_sanitized_without_capability_promotion() -> None:
    async def resolver(auth_ref: str) -> str:
        return "secret"

    client = _client(error=KeyError("assistant-one private upstream body"))
    result = await qualify_classic_sources(
        [_settings()],
        credential_resolver=resolver,
        enabled=True,
        client_factory=RecordingFactory([client]),
    )
    assert result[0].state == "unknown"
    assert result[0].reason == "qualification-failed"
    assert result[0].assistant is None
    assert all(capability.state == "gated" for capability in result[0].capabilities)
    assert "private upstream body" not in repr(result)
    assert client.close_calls == 1


@pytest.mark.asyncio
async def test_close_failure_is_fail_closed_and_scrubbed() -> None:
    async def resolver(auth_ref: str) -> str:
        return "secret"

    client = _client(close_error=RuntimeError("close leaked secret"))
    result = await qualify_classic_sources(
        [_settings()],
        credential_resolver=resolver,
        enabled=True,
        client_factory=RecordingFactory([client]),
    )
    assert result[0].state == "unknown"
    assert result[0].assistant is None
    assert result[0].reason == "client-close-failed"
    assert client.close_calls == 1


@pytest.mark.asyncio
async def test_per_source_failures_are_isolated_and_order_is_preserved() -> None:
    async def resolver(auth_ref: str) -> str:
        if auth_ref.endswith("two"):
            raise RuntimeError("resolver private detail")
        return "secret"

    clients = [
        _client(assistant_id="assistant-one", graph_id="graph-one"),
        _client(assistant_id="assistant-three", graph_id="graph-three"),
    ]
    sources = [
        _settings("source-one", assistant_id="assistant-one", auth_ref="vault:one"),
        _settings("source-two", assistant_id="assistant-two", auth_ref="vault:two"),
        _settings("source-three", assistant_id="assistant-three", auth_ref="vault:three"),
    ]
    result = await qualify_classic_sources(
        sources,
        credential_resolver=resolver,
        enabled=True,
        client_factory=RecordingFactory(clients),
    )

    assert [item.source_id for item in result] == ["source-one", "source-two", "source-three"]
    assert [item.state for item in result] == [
        "available",
        "permission-denied",
        "available",
    ]
    assert [client.close_calls for client in clients] == [1, 1]


@pytest.mark.asyncio
async def test_no_live_contract_capability_is_promoted() -> None:
    async def resolver(auth_ref: str) -> str:
        return "secret"

    result = await qualify_classic_sources(
        [_settings()],
        credential_resolver=resolver,
        enabled=True,
        client_factory=RecordingFactory([_client()]),
    )
    observations: Mapping[str, str] = {
        capability.name: capability.state for capability in result[0].capabilities
    }
    assert tuple(observations) == LIVE_CONTRACT_CAPABILITIES
    assert set(observations.values()) == {"gated"}
    assert {capability.reason for capability in result[0].capabilities} == {"blocked-live-evidence"}

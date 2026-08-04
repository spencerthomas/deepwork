"""Contract tests for the authenticated, read-only source qualification API."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx
import pytest

from deepwork_api import SourceProbeConfig, create_app
from deepwork_api.adapters.sources.classic.source import (
    ClassicSourceConfigurationError,
    validate_deployment_endpoint,
)
from deepwork_api.bootstrap.api import create_app as create_bootstrap_app
from deepwork_api.bootstrap.source_probe_config import (
    SourceProbeConfig as BootstrapSourceProbeConfig,
)
from deepwork_api.domain import (
    SecurityContext,
    SourceCapabilityObservation,
    SourceEndpointInvalidError,
    SourceProbeResult,
)


class FakeSourceProbeClient:
    """Deterministic probe seam with no provider or credential side effects."""

    def __init__(self, result: SourceProbeResult) -> None:
        self.result = result
        self.calls: list[tuple[str, str]] = []
        self.closed = False

    async def probe(self, endpoint: str, assistant_id: str) -> SourceProbeResult:
        try:
            normalized = validate_deployment_endpoint(endpoint)
        except ClassicSourceConfigurationError:
            raise SourceEndpointInvalidError from None
        self.calls.append((normalized, assistant_id))
        return self.result

    async def close(self) -> None:
        self.closed = True


@asynccontextmanager
async def _client(**kwargs: Any) -> AsyncIterator[httpx.AsyncClient]:
    if kwargs.get("source_probe_client") is not None and kwargs.get("source_probe_config") is None:
        kwargs["source_probe_config"] = BootstrapSourceProbeConfig(
            credential="test-only-server-key",
            allowed_endpoints=("https://agent.example.test",),
        )
    app = create_bootstrap_app(**kwargs)
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="https://source.test") as client:
            yield client


async def test_available_probe_returns_only_sanitized_read_evidence() -> None:
    probe = FakeSourceProbeClient(
        SourceProbeResult(
            state="available",
            assistant_id="assistant-1",
            graph_id="deep-work",
            reason="assistant-qualified-read-only",
            capabilities=(
                SourceCapabilityObservation(
                    name="assistants-read",
                    state="available",
                    observed_at="2026-08-04T00:00:00.000Z",
                    adapter_version="classic-source-probe-v1",
                    contract_version="langgraph-assistants-get-v1",
                    evidence_class="live-contract",
                ),
                SourceCapabilityObservation(
                    name="runs-create",
                    state="gated",
                    safe_reason="adapter-disabled",
                    observed_at="2026-08-04T00:00:00.000Z",
                    adapter_version="classic-source-probe-v1",
                    contract_version="langgraph-assistants-get-v1",
                    evidence_class="documented",
                ),
            ),
        )
    )
    async with _client(source_probe_client=probe, access_key="workspace-key") as client:
        assert (
            await client.post("/api/v1/auth/login", json={"accessKey": "workspace-key"})
        ).status_code == 200
        response = await client.post(
            "/api/v1/sources/probes",
            json={
                "kind": "langsmith_deployment",
                "sourceTargetId": "classic-default",
                "assistantId": "assistant-1",
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "kind": "langsmith_deployment",
        "state": "available",
        "assistantId": "assistant-1",
        "graphId": "deep-work",
        "reason": "assistant-qualified-read-only",
        "saveAllowed": False,
        "capabilities": [
            {
                "name": "assistants-read",
                "state": "available",
                "observedAt": "2026-08-04T00:00:00.000Z",
                "adapterVersion": "classic-source-probe-v1",
                "contractVersion": "langgraph-assistants-get-v1",
                "evidenceClass": "live-contract",
            },
            {
                "name": "runs-create",
                "state": "gated",
                "safeReason": "adapter-disabled",
                "observedAt": "2026-08-04T00:00:00.000Z",
                "adapterVersion": "classic-source-probe-v1",
                "contractVersion": "langgraph-assistants-get-v1",
                "evidenceClass": "documented",
            },
        ],
    }
    assert probe.calls == [("https://agent.example.test", "assistant-1")]
    serialized = response.text.lower()
    assert "credential" not in serialized
    assert "workspace-key" not in serialized
    assert "agent.example.test" not in serialized
    assert probe.closed is True


async def test_probe_is_guarded_and_unavailable_without_server_credential() -> None:
    async with _client(access_key="workspace-key") as client:
        unauthenticated = await client.post(
            "/api/v1/sources/probes",
            json={
                "kind": "langsmith_deployment",
                "sourceTargetId": "classic-default",
                "assistantId": "assistant-1",
            },
        )
        assert unauthenticated.status_code == 401

        assert (
            await client.post("/api/v1/auth/login", json={"accessKey": "workspace-key"})
        ).status_code == 200
        unavailable = await client.post(
            "/api/v1/sources/probes",
            json={
                "kind": "langsmith_deployment",
                "sourceTargetId": "classic-default",
                "assistantId": "assistant-1",
            },
        )

    assert unavailable.status_code == 503
    assert unavailable.json() == {
        "code": "source_probe_unavailable",
        "message": "No server-held source credential is configured for connection checks.",
    }


async def test_probe_rejects_unknown_target_before_calling_provider() -> None:
    probe = FakeSourceProbeClient(
        SourceProbeResult(
            state="unknown",
            assistant_id=None,
            graph_id=None,
            reason="must-not-run",
        )
    )
    async with _client(source_probe_client=probe, access_key="workspace-key") as client:
        assert (
            await client.post("/api/v1/auth/login", json={"accessKey": "workspace-key"})
        ).status_code == 200
        response = await client.post(
            "/api/v1/sources/probes",
            json={
                "kind": "langsmith_deployment",
                "sourceTargetId": "other-target",
                "assistantId": "assistant-1",
            },
        )

    assert response.status_code == 422
    assert response.json() == {"code": "request_invalid", "message": "Request validation failed."}
    assert probe.calls == []


async def test_probe_request_rejects_unknown_fields_and_source_kinds() -> None:
    async with _client() as client:
        unknown_kind = await client.post(
            "/api/v1/sources/probes",
            json={
                "kind": "mda_beta",
                "sourceTargetId": "classic-default",
                "assistantId": "assistant-1",
            },
        )
        spoofed_credential = await client.post(
            "/api/v1/sources/probes",
            json={
                "kind": "langsmith_deployment",
                "sourceTargetId": "classic-default",
                "assistantId": "assistant-1",
                "credential": "browser-secret",
            },
        )

    assert unknown_kind.status_code == 422
    assert spoofed_credential.status_code == 422


def test_source_capability_state_requires_a_coherent_safe_reason() -> None:
    with pytest.raises(ValueError, match="not coherent"):
        SourceCapabilityObservation(
            name="runs-create",
            state="gated",
            safe_reason="source-unavailable",
            observed_at="2026-08-04T00:00:00.000Z",
            adapter_version="classic-source-probe-v1",
            contract_version="langgraph-assistants-get-v1",
            evidence_class="documented",
        )


def test_server_probe_credential_does_not_enable_a_task_source_or_call_provider() -> None:
    app = create_app(
        source_probe_config=SourceProbeConfig(
            credential="server-only-source-key",
            allowed_endpoints=("https://agent.example.test",),
        ),
        access_key="workspace-key",
    )

    assert app.state.source_service is not None
    assert app.state.task_runner.__class__.__name__ == "DeterministicFixtureRunner"


def test_server_probe_requires_session_authentication_at_startup() -> None:
    with pytest.raises(ValueError, match="requires configured session authentication"):
        create_bootstrap_app(
            source_probe_config=BootstrapSourceProbeConfig(
                credential="server-only-source-key",
                allowed_endpoints=("https://approved.example.test",),
            )
        )


async def test_probe_authority_is_bound_to_tenant_and_workspace() -> None:
    probe = FakeSourceProbeClient(
        SourceProbeResult(
            state="available",
            assistant_id="assistant-1",
            graph_id="deep-work",
            reason="assistant-qualified-read-only",
        )
    )
    contexts = {
        "owner-key": SecurityContext("tenant-a", "workspace-a", "actor-a"),
        "foreign-key": SecurityContext("tenant-b", "workspace-b", "actor-b"),
    }
    config = BootstrapSourceProbeConfig(
        credential="server-only-source-key",
        allowed_endpoints=("https://agent.example.test",),
        tenant_id="tenant-a",
        workspace_id="workspace-a",
    )
    async with _client(
        source_probe_client=probe,
        source_probe_config=config,
        access_key_contexts=contexts,
    ) as client:
        assert (
            await client.post("/api/v1/auth/login", json={"accessKey": "foreign-key"})
        ).status_code == 200
        foreign = await client.post(
            "/api/v1/sources/probes",
            json={
                "kind": "langsmith_deployment",
                "sourceTargetId": "classic-default",
                "assistantId": "assistant-1",
            },
        )
        assert foreign.status_code == 404
        assert foreign.json() == {
            "code": "source_target_unavailable",
            "message": "The source target is not available in this workspace.",
        }
        assert probe.calls == []

        assert (
            await client.post("/api/v1/auth/login", json={"accessKey": "owner-key"})
        ).status_code == 200
        owner = await client.post(
            "/api/v1/sources/probes",
            json={
                "kind": "langsmith_deployment",
                "sourceTargetId": "classic-default",
                "assistantId": "assistant-1",
            },
        )

    assert owner.status_code == 200
    assert probe.calls == [("https://agent.example.test", "assistant-1")]

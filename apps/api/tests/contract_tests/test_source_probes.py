"""Contract tests for the authenticated, read-only source qualification API."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx

from deepwork_api import SourceProbeConfig, create_app
from deepwork_api.adapters.sources.classic.source import (
    ClassicSourceConfigurationError,
    validate_deployment_endpoint,
)
from deepwork_api.bootstrap.api import (
    SourceProbeConfig as BootstrapSourceProbeConfig,
)
from deepwork_api.bootstrap.api import create_app as create_bootstrap_app
from deepwork_api.domain import (
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
                    name="assistants-read", state="available", reason="assistant-qualified"
                ),
                SourceCapabilityObservation(
                    name="runs-create", state="gated", reason="invocation-not-authorized"
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
                "deploymentUrl": "https://Agent.Example.Test/api/",
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
                "reason": "assistant-qualified",
            },
            {
                "name": "runs-create",
                "state": "gated",
                "reason": "invocation-not-authorized",
            },
        ],
    }
    assert probe.calls == [("https://agent.example.test/api", "assistant-1")]
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
                "deploymentUrl": "https://agent.example.test",
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
                "deploymentUrl": "https://agent.example.test",
                "assistantId": "assistant-1",
            },
        )

    assert unavailable.status_code == 503
    assert unavailable.json() == {
        "code": "source_probe_unavailable",
        "message": "No server-held source credential is configured for connection checks.",
    }


async def test_probe_rejects_unsafe_endpoint_before_calling_provider() -> None:
    probe = FakeSourceProbeClient(
        SourceProbeResult(
            state="unknown",
            assistant_id=None,
            graph_id=None,
            reason="must-not-run",
        )
    )
    async with _client(source_probe_client=probe) as client:
        response = await client.post(
            "/api/v1/sources/probes",
            json={
                "kind": "langsmith_deployment",
                "deploymentUrl": "http://127.0.0.1:2024",
                "assistantId": "assistant-1",
            },
        )

    assert response.status_code == 422
    assert response.json() == {
        "code": "source_endpoint_invalid",
        "message": "The deployment URL is not an allowed hosted HTTPS endpoint.",
    }
    assert probe.calls == []


async def test_probe_request_rejects_unknown_fields_and_source_kinds() -> None:
    async with _client() as client:
        unknown_kind = await client.post(
            "/api/v1/sources/probes",
            json={
                "kind": "mda_beta",
                "deploymentUrl": "https://agent.example.test",
                "assistantId": "assistant-1",
            },
        )
        spoofed_credential = await client.post(
            "/api/v1/sources/probes",
            json={
                "kind": "langsmith_deployment",
                "deploymentUrl": "https://agent.example.test",
                "assistantId": "assistant-1",
                "credential": "browser-secret",
            },
        )

    assert unknown_kind.status_code == 422
    assert spoofed_credential.status_code == 422


def test_server_probe_credential_does_not_enable_a_task_source_or_call_provider() -> None:
    app = create_app(
        source_probe_config=SourceProbeConfig(
            credential="server-only-source-key",
            allowed_endpoints=("https://agent.example.test",),
        ),
    )

    assert app.state.source_service is not None
    assert app.state.task_runner.__class__.__name__ == "DeterministicFixtureRunner"


async def test_server_probe_rejects_non_allowlisted_origin_without_network() -> None:
    async with _client(
        source_probe_config=BootstrapSourceProbeConfig(
            credential="server-only-source-key",
            allowed_endpoints=("https://approved.example.test",),
        ),
    ) as client:
        response = await client.post(
            "/api/v1/sources/probes",
            json={
                "kind": "langsmith_deployment",
                "deploymentUrl": "https://attacker.example.test",
                "assistantId": "assistant-1",
            },
        )

    assert response.status_code == 422
    assert response.json() == {
        "code": "source_endpoint_invalid",
        "message": "The deployment URL is not an allowed hosted HTTPS endpoint.",
    }

"""Contract tests for task execution through a hosted classic deployment.

These reuse the deterministic Agent Server double from the loopback contract
tests -- a hosted LangGraph Platform deployment speaks the same official SDK
protocol -- but drive the FastAPI app in classic deployment mode over an HTTPS
endpoint with a server-held credential. They prove the full plan/approve/result
loop works against a hosted deployment and that neither the endpoint nor the
credential ever crosses the wire.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

import httpx
import pytest
from fastapi import FastAPI

import deepwork_api.bootstrap.api as bootstrap_api
from deepwork_api import create_app
from deepwork_api.adapters.sources.classic.runtime import ClassicDeploymentSource
from deepwork_api.application import LocalAgentServerRunner
from test_local_source_execution import (
    INITIAL_PLAN,
    ScriptedAgentServer,
    _create_task,
    _sse_events,
    _wait_for_status,
)

CLASSIC_ENDPOINT = "https://my-deployment.smith.langchain.com"
CLASSIC_ASSISTANT = "deep-work-local-agent"
CLASSIC_CREDENTIAL = "lsv2-SECRET-DEPLOYMENT-KEY"


@dataclass(slots=True)
class _Harness:
    app: FastAPI
    client: httpx.AsyncClient


@asynccontextmanager
async def _classic_app(
    server: ScriptedAgentServer,
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncIterator[_Harness]:
    def _fake_builder(
        *, endpoint: str, assistant_id: str, credential: str
    ) -> ClassicDeploymentSource:
        assert credential == CLASSIC_CREDENTIAL
        return ClassicDeploymentSource(
            client=server,
            endpoint=endpoint,
            assistant_id=assistant_id,
        )

    monkeypatch.setattr(bootstrap_api, "_build_classic_deployment_source", _fake_builder)
    app = create_app(
        classic_deployment_endpoint=CLASSIC_ENDPOINT,
        classic_deployment_assistant=CLASSIC_ASSISTANT,
        classic_deployment_credential=CLASSIC_CREDENTIAL,
        allow_ungated_local_agent_source=True,
    )
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://classic-source.test",
        ) as client:
            yield _Harness(app=app, client=client)


async def test_classic_deployment_runs_plan_approve_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = ScriptedAgentServer()
    async with _classic_app(server, monkeypatch) as harness:
        client = harness.client
        assert isinstance(harness.app.state.task_runner, LocalAgentServerRunner)

        created = await _create_task(client, "Summarize the supplied notes")
        task_id = created["taskId"]
        paused = await _wait_for_status(client, task_id, {"waiting-approval"})
        assert paused["proposedPlan"]["steps"] == list(INITIAL_PLAN)
        interrupt_id = paused["pendingInterrupt"]["interruptId"]

        decided = await client.post(
            f"/api/v1/tasks/{task_id}/decisions",
            json={"interruptId": interrupt_id, "decision": "approve"},
        )
        assert decided.status_code == 202

        completed = await _wait_for_status(client, task_id, {"completed"})
        assert completed["pendingInterrupt"] is None
        assert server.resume_decisions == ["approve"]

        result = await client.get(f"/api/v1/tasks/{task_id}/result")
        assert result.status_code == 200
        assert "Draft the local result." in result.json()["result"]

        # Neither the deployment credential nor the endpoint may cross the wire.
        replay = await client.get(f"/api/v1/tasks/{task_id}/events")
        assert CLASSIC_CREDENTIAL not in replay.text
        assert CLASSIC_ENDPOINT not in replay.text
        assert "my-deployment" not in replay.text


async def test_classic_deployment_rejects_maps_without_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = ScriptedAgentServer()
    async with _classic_app(server, monkeypatch) as harness:
        client = harness.client
        created = await _create_task(client, "Summarize the supplied notes")
        task_id = created["taskId"]
        paused = await _wait_for_status(client, task_id, {"waiting-approval"})

        rejected = await client.post(
            f"/api/v1/tasks/{task_id}/decisions",
            json={
                "interruptId": paused["pendingInterrupt"]["interruptId"],
                "decision": "reject",
            },
        )
        assert rejected.status_code == 202
        final = await _wait_for_status(client, task_id, {"rejected"})
        assert final["result"] is None


async def test_classic_mode_adds_no_new_wire_surface(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = ScriptedAgentServer()

    def _fake_builder(
        *, endpoint: str, assistant_id: str, credential: str
    ) -> ClassicDeploymentSource:
        return ClassicDeploymentSource(
            client=server, endpoint=endpoint, assistant_id=assistant_id
        )

    monkeypatch.setattr(bootstrap_api, "_build_classic_deployment_source", _fake_builder)
    classic = create_app(
        classic_deployment_endpoint=CLASSIC_ENDPOINT,
        classic_deployment_assistant=CLASSIC_ASSISTANT,
        classic_deployment_credential=CLASSIC_CREDENTIAL,
        allow_ungated_local_agent_source=True,
    )
    fixture = create_app()
    classic_schema = classic.openapi()
    assert classic_schema["paths"] == fixture.openapi()["paths"]
    serialized = json.dumps(classic_schema)
    assert CLASSIC_ENDPOINT not in serialized
    assert CLASSIC_CREDENTIAL not in serialized
    assert "my-deployment" not in serialized


async def test_classic_mode_is_gated_off_by_default() -> None:
    with pytest.raises(bootstrap_api.LocalSourceGatedError):
        create_app(
            classic_deployment_endpoint=CLASSIC_ENDPOINT,
            classic_deployment_assistant=CLASSIC_ASSISTANT,
            classic_deployment_credential=CLASSIC_CREDENTIAL,
        )


async def test_classic_and_local_are_mutually_exclusive() -> None:
    with pytest.raises(ValueError, match="not both"):
        create_app(
            classic_deployment_endpoint=CLASSIC_ENDPOINT,
            classic_deployment_assistant=CLASSIC_ASSISTANT,
            classic_deployment_credential=CLASSIC_CREDENTIAL,
            local_agent_server_endpoint="http://127.0.0.1:2024",
            local_agent_server_assistant=CLASSIC_ASSISTANT,
            allow_ungated_local_agent_source=True,
        )

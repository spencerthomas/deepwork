"""Durability contract for real-agent (classic) mode across process restarts.

Completed work must survive an API restart byte-for-byte. An in-flight task keeps
its source-owned thread/run binding so a fresh API process can rejoin the same
upstream work without creating a second run.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI
from test_local_source_execution import (
    ScriptedAgentServer,
    _create_task,
    _sse_events,
    _wait_for_status,
)

import deepwork_api.bootstrap.api as bootstrap_api
from deepwork_api import create_app
from deepwork_api.adapters.sources.classic.runtime import ClassicDeploymentSource

CLASSIC_ENDPOINT = "https://my-deployment.smith.langchain.com"
CLASSIC_ASSISTANT = "deep-work-local-agent"
NAMED_ASSISTANT = "assistant-evidence-reviewer"
CLASSIC_CREDENTIAL = "lsv2-SECRET-DEPLOYMENT-KEY"


@asynccontextmanager
async def _classic_app(
    server: ScriptedAgentServer,
    monkeypatch: pytest.MonkeyPatch,
    database: Path,
) -> AsyncIterator[httpx.AsyncClient]:
    def _fake_builder(
        *, endpoint: str, assistant_id: str, credential: str
    ) -> ClassicDeploymentSource:
        return ClassicDeploymentSource(client=server, endpoint=endpoint, assistant_id=assistant_id)

    monkeypatch.setattr(bootstrap_api, "_build_classic_deployment_source", _fake_builder)
    app: FastAPI = create_app(
        task_database_path=database,
        classic_deployment_endpoint=CLASSIC_ENDPOINT,
        classic_deployment_assistant=CLASSIC_ASSISTANT,
        classic_deployment_credential=CLASSIC_CREDENTIAL,
        allow_ungated_local_agent_source=True,
    )
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="https://durable.test"
        ) as client:
            yield client


async def test_completed_task_survives_restart(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    database = tmp_path / "tasks.db"
    server = ScriptedAgentServer()

    async with _classic_app(server, monkeypatch, database) as client:
        created = await _create_task(client, "Summarize the supplied notes")
        task_id = created["taskId"]
        paused = await _wait_for_status(client, task_id, {"waiting-approval"})
        await client.post(
            f"/api/v1/tasks/{task_id}/decisions",
            json={
                "interruptId": paused["pendingInterrupt"]["interruptId"],
                "decision": "approve",
            },
        )
        completed = await _wait_for_status(client, task_id, {"completed"})
        assert completed["result"]
        first_result = completed["result"]

    # Fresh process: new scripted server (upstream memory is gone too).
    async with _classic_app(ScriptedAgentServer(), monkeypatch, database) as client:
        listing = await client.get("/api/v1/tasks")
        assert listing.status_code == 200
        items = listing.json()["items"]
        assert [item["taskId"] for item in items] == [task_id]
        assert items[0]["status"] == "completed"

        result = await client.get(f"/api/v1/tasks/{task_id}/result")
        assert result.status_code == 200
        assert result.json()["result"] == first_result

        replay = await client.get(f"/api/v1/tasks/{task_id}/events")
        names = [event["event"] for event in _sse_events(replay.text)]
        assert names[0] == "task.created"
        assert names[-1] == "run.completed"


async def test_inflight_task_rejoins_the_same_source_run_after_restart(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    database = tmp_path / "tasks.db"
    server = ScriptedAgentServer()

    async with _classic_app(server, monkeypatch, database) as client:
        created = await _create_task(
            client,
            "Summarize the supplied notes",
            agent_id=NAMED_ASSISTANT,
        )
        task_id = created["taskId"]
        # Leave the task waiting for approval — in flight — and "crash".
        await _wait_for_status(client, task_id, {"waiting-approval"})

    # The classic source is an external service and remains authoritative while
    # the API process restarts. Reuse the same double to model that boundary.
    async with _classic_app(server, monkeypatch, database) as client:
        recovered = await _wait_for_status(client, task_id, {"waiting-approval"})
        assert recovered["agentId"] == NAMED_ASSISTANT
        interrupt_id = recovered["pendingInterrupt"]["interruptId"]
        decision = await client.post(
            f"/api/v1/tasks/{task_id}/decisions",
            json={"interruptId": interrupt_id, "decision": "approve"},
        )
        assert decision.status_code == 202
        completed = await _wait_for_status(client, task_id, {"completed"})
        assert completed["result"]

        replay = await client.get(f"/api/v1/tasks/{task_id}/events")
        events = _sse_events(replay.text)
        names = [event["event"] for event in events]
        progress = [event for event in events if event["event"] == "content.delta"]
        assert names.count("task.created") == 1
        assert names.count("run.started") == 2
        assert names.count("interrupt.requested") == 1
        assert names.count("decision.recorded") == 1
        assert names.count("run.completed") == 1
        assert len(progress) == 4
        assert all(
            event["data"]
            == {
                "text": "Local Agent Server progress received.",
                "evidenceClass": "local-source",
            }
            for event in progress
        )
        assert server._counter == 3
        assert server.join_without_cursor_count == 3
        assert server.run_assistant_ids == [NAMED_ASSISTANT, NAMED_ASSISTANT]

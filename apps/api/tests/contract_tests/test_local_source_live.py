"""Explicitly enabled task-API acceptance against a real loopback Agent Server.

Skipped unless both environment variables below name a running local
``langgraph dev`` server. Because the shared suite denies IP sockets, run this
acceptance explicitly, for example:

    uv run pytest tests/contract_tests/test_local_source_live.py \
        --allow-hosts=127.0.0.1,::1

with ``DEEPWORK_TEST_LOCAL_AGENT_SERVER_URL`` and
``DEEPWORK_TEST_LOCAL_AGENT_SERVER_ASSISTANT`` exported.
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, cast

import httpx
import pytest

from deepwork_api import create_app

_URL_ENV = "DEEPWORK_TEST_LOCAL_AGENT_SERVER_URL"
_ASSISTANT_ENV = "DEEPWORK_TEST_LOCAL_AGENT_SERVER_ASSISTANT"
_POLL_INTERVAL_SECONDS = 0.25
_STAGE_TIMEOUT_SECONDS = 120.0


@asynccontextmanager
async def _live_client(endpoint: str, assistant_id: str) -> AsyncIterator[httpx.AsyncClient]:
    app = create_app(
        local_agent_server_endpoint=endpoint,
        local_agent_server_assistant=assistant_id,
    )
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://local-live.test",
        ) as client:
            yield client


async def _wait_for_status(
    client: httpx.AsyncClient,
    task_id: str,
    expected: set[str],
) -> dict[str, Any]:
    async with asyncio.timeout(_STAGE_TIMEOUT_SECONDS):
        while True:
            response = await client.get(f"/api/v1/tasks/{task_id}")
            assert response.status_code == 200
            payload = response.json()
            if payload["status"] in expected:
                return cast("dict[str, Any]", payload)
            assert payload["status"] != "failed", "task failed before the expected state"
            await asyncio.sleep(_POLL_INTERVAL_SECONDS)


async def test_explicit_loopback_agent_server_completes_a_task_via_the_api() -> None:
    """Prove create, review, approve, and result against the real local source."""

    endpoint = os.environ.get(_URL_ENV)
    assistant_id = os.environ.get(_ASSISTANT_ENV)
    if not endpoint or not assistant_id:
        pytest.skip(f"set {_URL_ENV} and {_ASSISTANT_ENV} to run loopback acceptance")

    async with _live_client(endpoint, assistant_id) as client:
        created = await client.post(
            "/api/v1/tasks",
            json={"prompt": "Prepare a two-step local plan, then wait for review."},
        )
        assert created.status_code == 202
        task_id = created.json()["taskId"]

        paused = await _wait_for_status(client, task_id, {"waiting-approval"})
        pending = paused["pendingInterrupt"]
        assert pending is not None
        assert "approve" in pending["decisions"]
        assert paused["proposedPlan"] is not None
        assert paused["proposedPlan"]["steps"]

        decided = await client.post(
            f"/api/v1/tasks/{task_id}/decisions",
            json={"interruptId": pending["interruptId"], "decision": "approve"},
        )
        assert decided.status_code == 202

        completed = await _wait_for_status(client, task_id, {"completed"})
        assert completed["result"]

        result = await client.get(f"/api/v1/tasks/{task_id}/result")
        assert result.status_code == 200
        assert result.json()["result"] == completed["result"]

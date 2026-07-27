"""Contract tests for the source-backed schedule (recurring run) registry.

Deep Work owns no schedule storage: these tests drive the real FastAPI app
through ``/api/v1/schedules`` against a scripted double standing in for the
official ``langgraph_sdk`` Assistants/Crons clients, and separately prove
fixture mode reports an honest unavailable state instead of a fabricated
registry.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, cast

import httpx
import pytest

import deepwork_api.bootstrap.api as bootstrap_api
from deepwork_api import create_app
from deepwork_api.adapters.sources.local import LocalAgentServerSource
from deepwork_api.adapters.sources.local.source import _AgentServerClient

LOCAL_ENDPOINT = "http://127.0.0.1:2024"
LOCAL_ASSISTANT = "deep-work-local-agent"


@dataclass
class _FakeAssistants:
    default: dict[str, object] = field(
        default_factory=lambda: {"assistant_id": LOCAL_ASSISTANT, "graph_id": LOCAL_ASSISTANT}
    )
    search_response: list[dict[str, object]] = field(
        default_factory=lambda: [
            {
                "assistant_id": LOCAL_ASSISTANT,
                "name": LOCAL_ASSISTANT,
                "description": None,
                "config": {},
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
            }
        ]
    )

    async def get(self, assistant_id: str) -> object:
        assert assistant_id == LOCAL_ASSISTANT
        return self.default

    async def search(
        self, *, graph_id: str | None = None, limit: int = 10, offset: int = 0
    ) -> object:
        assert graph_id == LOCAL_ASSISTANT
        return self.search_response


@dataclass
class _FakeCrons:
    search_response: list[dict[str, object]] = field(default_factory=list)

    async def search(
        self, *, assistant_id: str | None = None, limit: int = 10, offset: int = 0
    ) -> object:
        return self.search_response


@dataclass
class _FakeClient:
    assistants: _FakeAssistants
    crons: _FakeCrons
    threads: object = None
    runs: object = None
    closed: bool = False

    async def aclose(self) -> None:
        self.closed = True


@asynccontextmanager
async def _real_agent_app(
    assistants: _FakeAssistants,
    crons: _FakeCrons,
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncIterator[httpx.AsyncClient]:
    def _fake_builder(*, endpoint: str, assistant_id: str) -> LocalAgentServerSource:
        return LocalAgentServerSource(
            client=cast("_AgentServerClient", _FakeClient(assistants=assistants, crons=crons)),
            endpoint=endpoint,
            assistant_id=assistant_id,
        )

    monkeypatch.setattr(bootstrap_api, "_build_local_agent_server_source", _fake_builder)
    app = create_app(
        local_agent_server_endpoint=LOCAL_ENDPOINT,
        local_agent_server_assistant=LOCAL_ASSISTANT,
        allow_ungated_local_agent_source=True,
    )
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="https://schedules.test"
        ) as client:
            yield client


@asynccontextmanager
async def _fixture_app(**kwargs: Any) -> AsyncIterator[httpx.AsyncClient]:
    app = create_app(**kwargs)
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="https://schedules.test"
        ) as client:
            yield client


async def test_fixture_mode_reports_an_honest_unavailable_registry() -> None:
    async with _fixture_app() as client:
        response = await client.get("/api/v1/schedules")
        assert response.status_code == 200
        assert response.json() == {"available": False, "items": []}


async def test_real_agent_mode_lists_schedules_scoped_to_our_graph(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    crons = _FakeCrons(
        search_response=[
            {
                "cron_id": "cron-1",
                "assistant_id": LOCAL_ASSISTANT,
                "schedule": "0 9 * * *",
                "timezone": "America/New_York",
                "end_time": None,
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
            },
            {
                "cron_id": "cron-2",
                "assistant_id": "unrelated-graph-assistant",
                "schedule": "0 10 * * *",
                "timezone": None,
                "end_time": None,
                "created_at": "2026-01-02T00:00:00Z",
                "updated_at": "2026-01-02T00:00:00Z",
            },
        ]
    )
    async with _real_agent_app(_FakeAssistants(), crons, monkeypatch) as client:
        response = await client.get("/api/v1/schedules")
        assert response.status_code == 200
        body = response.json()
        assert body["available"] is True
        assert [item["scheduleId"] for item in body["items"]] == ["cron-1"]
        assert body["items"][0]["agentId"] == LOCAL_ASSISTANT
        assert body["items"][0]["cronExpression"] == "0 9 * * *"
        assert body["items"][0]["timezone"] == "America/New_York"


async def test_real_agent_mode_reports_no_schedules_as_an_empty_available_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async with _real_agent_app(_FakeAssistants(), _FakeCrons(), monkeypatch) as client:
        response = await client.get("/api/v1/schedules")
        assert response.status_code == 200
        assert response.json() == {"available": True, "items": []}


async def test_schedules_are_session_guarded_when_access_key_is_set() -> None:
    async with _fixture_app(access_key="secret-key") as client:
        response = await client.get("/api/v1/schedules")
        assert response.status_code == 401

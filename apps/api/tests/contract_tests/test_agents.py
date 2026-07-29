"""Contract tests for the source-backed agent registry API.

Deep Work owns no agent storage: these tests drive the real FastAPI app
through ``/api/v1/agents`` against a scripted double standing in for the
official ``langgraph_sdk`` Assistants client, and separately prove fixture
mode reports an honest unavailable state instead of a fabricated registry.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
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
    search_response: list[dict[str, object]] = field(default_factory=list)
    create_response: dict[str, object] | None = None
    update_response: dict[str, object] | None = None
    deleted: list[str] = field(default_factory=list)

    async def get(self, assistant_id: str) -> object:
        assert assistant_id == LOCAL_ASSISTANT
        return self.default

    async def search(
        self, *, graph_id: str | None = None, limit: int = 10, offset: int = 0
    ) -> object:
        assert graph_id == LOCAL_ASSISTANT
        return self.search_response

    async def create(
        self,
        graph_id: str | None,
        config: Mapping[str, object] | None = None,
        *,
        metadata: Mapping[str, object] | None = None,
        assistant_id: str | None = None,
        if_exists: str | None = None,
        name: str | None = None,
        description: str | None = None,
    ) -> object:
        assert graph_id == LOCAL_ASSISTANT
        assert self.create_response is not None
        return self.create_response

    async def update(
        self,
        assistant_id: str,
        *,
        config: Mapping[str, object] | None = None,
        name: str | None = None,
        description: str | None = None,
    ) -> object:
        assert self.update_response is not None
        return self.update_response

    async def delete(self, assistant_id: str) -> None:
        self.deleted.append(assistant_id)


@dataclass
class _FakeClient:
    """Minimal double satisfying ``_AgentServerClient``; only ``assistants`` is exercised."""

    assistants: _FakeAssistants
    threads: object = None
    runs: object = None
    closed: bool = False

    async def aclose(self) -> None:
        self.closed = True


@asynccontextmanager
async def _real_agent_app(
    assistants: _FakeAssistants,
    monkeypatch: pytest.MonkeyPatch,
    **kwargs: Any,
) -> AsyncIterator[httpx.AsyncClient]:
    def _fake_builder(*, endpoint: str, assistant_id: str) -> LocalAgentServerSource:
        return LocalAgentServerSource(
            client=cast("_AgentServerClient", _FakeClient(assistants=assistants)),
            endpoint=endpoint,
            assistant_id=assistant_id,
        )

    monkeypatch.setattr(bootstrap_api, "_build_local_agent_server_source", _fake_builder)
    app = create_app(
        local_agent_server_endpoint=LOCAL_ENDPOINT,
        local_agent_server_assistant=LOCAL_ASSISTANT,
        allow_ungated_local_agent_source=True,
        **kwargs,
    )
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="https://agents.test") as client:
            yield client


@asynccontextmanager
async def _fixture_app(**kwargs: Any) -> AsyncIterator[httpx.AsyncClient]:
    app = create_app(**kwargs)
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="https://agents.test") as client:
            yield client


async def test_fixture_mode_reports_an_honest_unavailable_registry() -> None:
    async with _fixture_app() as client:
        response = await client.get("/api/v1/agents")
        assert response.status_code == 200
        assert response.json() == {"available": False, "items": []}


async def test_fixture_mode_refuses_agent_mutations() -> None:
    async with _fixture_app() as client:
        create = await client.post("/api/v1/agents", json={"name": "Reviewer"})
        assert create.status_code == 409
        assert create.json()["code"] == "agent_registry_unavailable"

        update = await client.put(
            "/api/v1/agents/assistant-2", json={"name": "Reviewer", "systemPrompt": None}
        )
        assert update.status_code == 409

        delete = await client.delete("/api/v1/agents/assistant-2")
        assert delete.status_code == 409


async def test_fixture_mode_task_creation_ignores_a_supplied_agent_id() -> None:
    async with _fixture_app() as client:
        response = await client.post(
            "/api/v1/tasks", json={"prompt": "Write a brief.", "agentId": "assistant-2"}
        )
        assert response.status_code == 202


async def test_real_agent_mode_lists_the_default_and_registered_agents(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assistants = _FakeAssistants(
        search_response=[
            {
                "assistant_id": LOCAL_ASSISTANT,
                "name": LOCAL_ASSISTANT,
                "description": None,
                "config": {},
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
            },
            {
                "assistant_id": "assistant-2",
                "name": "Terse reviewer",
                "description": "Short reviews.",
                "config": {"configurable": {"system_prompt": "Always be terse."}},
                "created_at": "2026-01-02T00:00:00Z",
                "updated_at": "2026-01-02T00:00:00Z",
            },
        ]
    )
    async with _real_agent_app(assistants, monkeypatch) as client:
        response = await client.get("/api/v1/agents")
        assert response.status_code == 200
        body = response.json()
        assert body["available"] is True
        assert [item["agentId"] for item in body["items"]] == [LOCAL_ASSISTANT, "assistant-2"]
        assert body["items"][0]["isDefault"] is True
        assert body["items"][1]["isDefault"] is False
        assert body["items"][1]["systemPrompt"] == "Always be terse."


async def test_real_agent_mode_creates_updates_and_deletes_a_named_agent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assistants = _FakeAssistants(
        create_response={
            "assistant_id": "assistant-3",
            "name": "Release reviewer",
            "description": "Reviews release notes.",
            "config": {"configurable": {"system_prompt": "Be precise."}},
            "created_at": "2026-01-03T00:00:00Z",
            "updated_at": "2026-01-03T00:00:00Z",
        }
    )
    async with _real_agent_app(assistants, monkeypatch) as client:
        created = await client.post(
            "/api/v1/agents",
            json={
                "name": "Release reviewer",
                "description": "Reviews release notes.",
                "systemPrompt": "Be precise.",
            },
        )
        assert created.status_code == 201
        assert created.json()["agentId"] == "assistant-3"

        assistants.update_response = {
            "assistant_id": "assistant-3",
            "name": "Renamed reviewer",
            "description": None,
            "config": {},
            "created_at": "2026-01-03T00:00:00Z",
            "updated_at": "2026-01-04T00:00:00Z",
        }
        updated = await client.put(
            "/api/v1/agents/assistant-3",
            json={"name": "Renamed reviewer", "description": None, "systemPrompt": None},
        )
        assert updated.status_code == 200
        assert updated.json()["name"] == "Renamed reviewer"
        assert updated.json()["systemPrompt"] is None

        deleted = await client.delete("/api/v1/agents/assistant-3")
        assert deleted.status_code == 204
        assert assistants.deleted == ["assistant-3"]


async def test_real_agent_mode_refuses_to_edit_or_delete_the_default_agent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assistants = _FakeAssistants()
    async with _real_agent_app(assistants, monkeypatch) as client:
        update = await client.put(
            f"/api/v1/agents/{LOCAL_ASSISTANT}", json={"name": "x", "systemPrompt": None}
        )
        assert update.status_code == 409
        assert update.json()["code"] == "default_agent_immutable"

        delete = await client.delete(f"/api/v1/agents/{LOCAL_ASSISTANT}")
        assert delete.status_code == 409
        assert delete.json()["code"] == "default_agent_immutable"


async def test_agents_are_session_guarded_when_access_key_is_set() -> None:
    async with _fixture_app(access_key="secret-key") as client:
        response = await client.get("/api/v1/agents")
        assert response.status_code == 401

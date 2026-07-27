"""Contract tests for the task trace-link endpoint."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx
import pytest

import deepwork_api.bootstrap.api as bootstrap_api
from deepwork_api import create_app


class _FakeLocator:
    """Deterministic trace locator double."""

    def __init__(self, mapping: dict[str, str]) -> None:
        self.mapping = mapping
        self.calls: list[str] = []
        self.closed = False

    async def locate(self, run_id: str) -> str | None:
        self.calls.append(run_id)
        return self.mapping.get(run_id)

    async def close(self) -> None:
        self.closed = True


@asynccontextmanager
async def _app(**kwargs: Any) -> AsyncIterator[httpx.AsyncClient]:
    app = create_app(**kwargs)
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="https://trace.test"
        ) as client:
            yield client


async def _create_and_finish_fixture_task(client: httpx.AsyncClient) -> tuple[str, str]:
    created = (await client.post("/api/v1/tasks", json={"prompt": "Trace me"})).json()
    return created["taskId"], created["runId"]


async def test_trace_available_when_locator_resolves(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _FakeLocator({})

    def _fake_builder(*, api_key: str) -> _FakeLocator:
        assert api_key == "ls-key"
        return fake

    monkeypatch.setattr(bootstrap_api, "_build_trace_locator", _fake_builder)
    async with _app(trace_api_key="ls-key") as client:
        task_id, run_id = await _create_and_finish_fixture_task(client)
        fake.mapping[run_id] = f"https://smith.langchain.com/o/org/r/{run_id}"

        response = await client.get(f"/api/v1/tasks/{task_id}/trace")
        assert response.status_code == 200
        assert response.json() == {
            "taskId": task_id,
            "traceUrl": f"https://smith.langchain.com/o/org/r/{run_id}",
            "state": "available",
        }
        assert fake.calls == [run_id]
    assert fake.closed is True


async def test_trace_unavailable_without_configuration() -> None:
    async with _app() as client:
        task_id, _ = await _create_and_finish_fixture_task(client)
        response = await client.get(f"/api/v1/tasks/{task_id}/trace")
        assert response.status_code == 200
        body = response.json()
        assert body["state"] == "unavailable"
        assert body["traceUrl"] is None


async def test_trace_unknown_task_is_404(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        bootstrap_api, "_build_trace_locator", lambda *, api_key: _FakeLocator({})
    )
    async with _app(trace_api_key="ls-key") as client:
        response = await client.get("/api/v1/tasks/task_99999999/trace")
        assert response.status_code == 404


async def test_trace_requires_session_when_auth_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        bootstrap_api, "_build_trace_locator", lambda *, api_key: _FakeLocator({})
    )
    async with _app(trace_api_key="ls-key", access_key="operator-key") as client:
        unauth = await client.get("/api/v1/tasks/task_00000001/trace")
        assert unauth.status_code == 401

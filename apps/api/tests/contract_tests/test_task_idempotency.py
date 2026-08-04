"""Authenticated task creation is scoped and durably idempotent."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI

from deepwork_api import create_app
from deepwork_api.application import DeterministicFixtureRunner
from deepwork_api.domain import SecurityContext, TaskSnapshot

CONTEXT_A = SecurityContext("tenant-a", "workspace-a", "actor-a")
ACCESS_KEY_CONTEXTS = {"access-key-a": CONTEXT_A}


@asynccontextmanager
async def _client(
    *,
    task_database_path: Path | None = None,
    contexts: Mapping[str, SecurityContext] = ACCESS_KEY_CONTEXTS,
    access_key: str = "access-key-a",
) -> AsyncIterator[tuple[httpx.AsyncClient, FastAPI]]:
    app: FastAPI = create_app(
        task_database_path=task_database_path,
        access_key_contexts=contexts,
    )
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="https://idempotency.test",
        ) as client:
            login = await client.post(
                "/api/v1/auth/login",
                json={"accessKey": access_key},
            )
            assert login.status_code == 200
            yield client, app


def _headers(key: str) -> dict[str, str]:
    return {"Idempotency-Key": key}


async def test_authenticated_task_creation_requires_idempotency_key() -> None:
    async with _client() as (client, _app):
        response = await client.post(
            "/api/v1/tasks",
            json={"prompt": "Prepare one bounded task."},
        )

    assert response.status_code == 400
    assert response.json() == {
        "code": "idempotency_key_required",
        "message": "Idempotency-Key is required for task creation.",
    }


async def test_identical_retry_returns_original_task_without_restarting_runner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    starts: list[str] = []
    original_start = DeterministicFixtureRunner.start

    def counting_start(self: DeterministicFixtureRunner, task: TaskSnapshot) -> None:
        starts.append(task.task_id)
        original_start(self, task)

    monkeypatch.setattr(DeterministicFixtureRunner, "start", counting_start)
    payload = {
        "prompt": "Prepare one bounded task.",
        "agentId": "deepwork-fixture-planner",
    }
    async with _client() as (client, _app):
        first = await client.post(
            "/api/v1/tasks",
            headers=_headers("task-create-retry"),
            json=payload,
        )
        retried = await client.post(
            "/api/v1/tasks",
            headers=_headers("task-create-retry"),
            json=payload,
        )
        listing = await client.get("/api/v1/tasks")

    assert first.status_code == retried.status_code == 202
    assert first.json()["duplicate"] is False
    assert retried.json() == {**first.json(), "duplicate": True}
    assert [item["taskId"] for item in listing.json()["items"]] == [first.json()["taskId"]]
    assert starts == [first.json()["taskId"]]


@pytest.mark.parametrize(
    ("first_payload", "changed_payload"),
    (
        (
            {"prompt": "Prepare the original task."},
            {"prompt": "Prepare a changed task."},
        ),
        (
            {
                "prompt": "Prepare the same task.",
                "agentId": "deepwork-fixture-planner",
            },
            {"prompt": "Prepare the same task."},
        ),
        (
            {
                "prompt": "Prepare the same task.",
                "journey": "coding",
                "repositoryId": "fixture_repo_deepwork",
            },
            {"prompt": "Prepare the same task."},
        ),
    ),
)
async def test_same_scoped_key_with_changed_request_is_rejected(
    first_payload: dict[str, str],
    changed_payload: dict[str, str],
) -> None:
    async with _client() as (client, _app):
        first = await client.post(
            "/api/v1/tasks",
            headers=_headers("task-create-conflict"),
            json=first_payload,
        )
        conflict = await client.post(
            "/api/v1/tasks",
            headers=_headers("task-create-conflict"),
            json=changed_payload,
        )
        listing = await client.get("/api/v1/tasks")

    assert first.status_code == 202
    assert conflict.status_code == 409
    assert conflict.json() == {
        "code": "task_idempotency_conflict",
        "message": "Idempotency-Key was already used for a different task request.",
    }
    assert len(listing.json()["items"]) == 1


async def test_actor_and_workspace_scopes_may_reuse_the_same_key(tmp_path: Path) -> None:
    contexts = {
        "access-key-a": CONTEXT_A,
        "access-key-actor": SecurityContext("tenant-a", "workspace-a", "actor-b"),
        "access-key-workspace": SecurityContext("tenant-a", "workspace-b", "actor-a"),
    }
    database = tmp_path / "scoped-idempotency.sqlite"
    created: list[str] = []
    for access_key in contexts:
        async with _client(
            task_database_path=database,
            contexts=contexts,
            access_key=access_key,
        ) as (client, _app):
            response = await client.post(
                "/api/v1/tasks",
                headers=_headers("shared-task-key"),
                json={"prompt": "Prepare scoped work."},
            )
            assert response.status_code == 202
            assert response.json()["duplicate"] is False
            created.append(response.json()["taskId"])

    assert len(set(created)) == 3


async def test_concurrent_same_key_requests_converge_on_one_task(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    starts: list[str] = []
    original_start = DeterministicFixtureRunner.start

    def counting_start(self: DeterministicFixtureRunner, task: TaskSnapshot) -> None:
        starts.append(task.task_id)
        original_start(self, task)

    monkeypatch.setattr(DeterministicFixtureRunner, "start", counting_start)
    async with _client() as (client, _app):
        responses = await asyncio.gather(
            *(
                client.post(
                    "/api/v1/tasks",
                    headers=_headers("concurrent-task-key"),
                    json={"prompt": "Create this task once."},
                )
                for _ in range(8)
            )
        )
        listing = await client.get("/api/v1/tasks")

    assert {response.status_code for response in responses} == {202}
    assert len({response.json()["taskId"] for response in responses}) == 1
    assert sum(response.json()["duplicate"] is False for response in responses) == 1
    assert sum(response.json()["duplicate"] is True for response in responses) == 7
    assert len(listing.json()["items"]) == 1
    assert len(starts) == 1


async def test_sqlite_restart_replays_the_original_task_without_rerun(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    starts: list[str] = []
    original_start = DeterministicFixtureRunner.start

    def counting_start(self: DeterministicFixtureRunner, task: TaskSnapshot) -> None:
        starts.append(task.task_id)
        original_start(self, task)

    monkeypatch.setattr(DeterministicFixtureRunner, "start", counting_start)
    database = tmp_path / "idempotent-tasks.sqlite"
    payload = {"prompt": "Retain this task across restart."}

    async with _client(task_database_path=database) as (client, _app):
        first = await client.post(
            "/api/v1/tasks",
            headers=_headers("restart-task-key"),
            json=payload,
        )
        assert first.status_code == 202
        assert first.json()["duplicate"] is False

    async with _client(task_database_path=database) as (client, _app):
        retried = await client.post(
            "/api/v1/tasks",
            headers=_headers("restart-task-key"),
            json=payload,
        )
        listing = await client.get("/api/v1/tasks")

    assert retried.status_code == 202
    assert retried.json() == {**first.json(), "duplicate": True}
    assert [item["taskId"] for item in listing.json()["items"]] == [first.json()["taskId"]]
    assert starts == [first.json()["taskId"]]

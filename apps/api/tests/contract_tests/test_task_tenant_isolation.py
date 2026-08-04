"""Task ownership remains tenant and workspace scoped across every HTTP path."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
from pathlib import Path
from typing import cast

import httpx
from fastapi import FastAPI

from deepwork_api import create_app
from deepwork_api.domain import SecurityContext

CONTEXT_A = SecurityContext("tenant-a", "workspace-a", "actor-a")
CONTEXT_B = SecurityContext("tenant-b", "workspace-b", "actor-b")
ACCESS_KEY_CONTEXTS = {"access-key-a": CONTEXT_A, "access-key-b": CONTEXT_B}


@asynccontextmanager
async def _clients(
    *,
    task_database_path: Path | None = None,
    contexts: Mapping[str, SecurityContext] = ACCESS_KEY_CONTEXTS,
) -> AsyncIterator[tuple[httpx.AsyncClient, httpx.AsyncClient]]:
    app: FastAPI = create_app(
        task_database_path=task_database_path,
        access_key_contexts=contexts,
    )
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with (
            httpx.AsyncClient(transport=transport, base_url="https://tenant.test") as client_a,
            httpx.AsyncClient(transport=transport, base_url="https://tenant.test") as client_b,
        ):
            assert (
                await client_a.post("/api/v1/auth/login", json={"accessKey": "access-key-a"})
            ).status_code == 200
            assert (
                await client_b.post("/api/v1/auth/login", json={"accessKey": "access-key-b"})
            ).status_code == 200
            yield client_a, client_b


async def _create_waiting_task(client: httpx.AsyncClient) -> dict[str, object]:
    created = await client.post(
        "/api/v1/tasks",
        headers={"Idempotency-Key": "tenant-isolation-task"},
        json={"prompt": "Keep this task inside workspace A"},
    )
    assert created.status_code == 202
    task_id = created.json()["taskId"]
    for _ in range(100):
        detail = await client.get(f"/api/v1/tasks/{task_id}")
        assert detail.status_code == 200
        body = cast("dict[str, object]", detail.json())
        if body["status"] == "waiting-approval":
            return body
        await asyncio.sleep(0.01)
    raise AssertionError("fixture task did not reach its approval boundary")


async def _wait_for_completion(client: httpx.AsyncClient, task_id: str) -> dict[str, object]:
    for _ in range(300):
        detail = await client.get(f"/api/v1/tasks/{task_id}")
        assert detail.status_code == 200
        body = cast("dict[str, object]", detail.json())
        if body["status"] == "completed":
            return body
        await asyncio.sleep(0.01)
    raise AssertionError("fixture task did not complete")


async def test_foreign_workspace_cannot_observe_or_mutate_waiting_task() -> None:
    async with _clients() as (client_a, client_b):
        waiting = await _create_waiting_task(client_a)
        task_id = str(waiting["taskId"])
        pending = waiting["pendingInterrupt"]
        assert isinstance(pending, dict)
        interrupt_id = str(pending["interruptId"])
        version = str(pending["version"])
        plan = waiting["proposedPlan"]
        assert isinstance(plan, dict)

        listing = await client_b.get("/api/v1/tasks")
        assert listing.status_code == 200
        assert listing.json()["items"] == []

        requests = (
            await client_b.get(f"/api/v1/tasks/{task_id}"),
            await client_b.get(f"/api/v1/tasks/{task_id}/result"),
            await client_b.get(f"/api/v1/tasks/{task_id}/trace"),
            await client_b.get(f"/api/v1/tasks/{task_id}/events"),
            await client_b.post(f"/api/v1/tasks/{task_id}/cancel"),
            await client_b.post(
                f"/api/v1/tasks/{task_id}/decisions",
                json={"interruptId": interrupt_id, "decision": "approve"},
            ),
            await client_b.post(
                f"/api/v1/tasks/{task_id}/decision-batch",
                json={
                    "interruptId": interrupt_id,
                    "expectedVersion": version,
                    "idempotencyKey": "foreign-workspace-batch",
                    "decisions": [{"type": "approve"}] * len(plan["steps"]),
                },
            ),
            await client_b.patch(
                f"/api/v1/tasks/{task_id}/plan",
                json={
                    "interruptId": interrupt_id,
                    "expectedRevision": plan["revision"],
                    "steps": ["Foreign edit must not be applied."],
                },
            ),
        )
        for response in requests:
            assert response.status_code == 404
            assert response.json() == {
                "code": "task_not_found",
                "message": "Task was not found.",
            }

        unchanged = await client_a.get(f"/api/v1/tasks/{task_id}")
        assert unchanged.status_code == 200
        assert unchanged.json()["status"] == "waiting-approval"
        assert unchanged.json()["pendingInterrupt"]["interruptId"] == interrupt_id
        assert unchanged.json()["proposedPlan"] == plan


async def test_owner_survives_sqlite_restart_without_public_identity_fields(
    tmp_path: Path,
) -> None:
    database = tmp_path / "tenant-owned-tasks.sqlite"
    task_id = ""
    completed_before: dict[str, object]

    async with _clients(task_database_path=database) as (client_a, client_b):
        waiting = await _create_waiting_task(client_a)
        task_id = str(waiting["taskId"])
        pending = waiting["pendingInterrupt"]
        assert isinstance(pending, dict)
        approved = await client_a.post(
            f"/api/v1/tasks/{task_id}/decisions",
            json={"interruptId": pending["interruptId"], "decision": "approve"},
        )
        assert approved.status_code == 202
        completed_before = await _wait_for_completion(client_a, task_id)
        assert (await client_b.get(f"/api/v1/tasks/{task_id}")).status_code == 404

    async with _clients(task_database_path=database) as (client_a, client_b):
        owner_listing = await client_a.get("/api/v1/tasks")
        foreign_listing = await client_b.get("/api/v1/tasks")
        reopened = await client_a.get(f"/api/v1/tasks/{task_id}")
        foreign = await client_b.get(f"/api/v1/tasks/{task_id}")

        assert [item["taskId"] for item in owner_listing.json()["items"]] == [task_id]
        assert foreign_listing.json()["items"] == []
        assert reopened.status_code == 200
        assert reopened.json() == completed_before
        assert foreign.status_code == 404

        owner_events = await client_a.get(f"/api/v1/tasks/{task_id}/events")
        serialized = " ".join((owner_listing.text, reopened.text, owner_events.text))
        for hidden in ("tenant-a", "workspace-a", "actor-a"):
            assert hidden not in serialized

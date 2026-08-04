"""Application-level proof for the explicit local SQLite backup bundle."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, cast

import httpx

from deepwork_api import create_app
from deepwork_api.adapters.recovery import create_backup_bundle, restore_backup_bundle


async def _terminal_detail(client: httpx.AsyncClient, task_id: str) -> dict[str, Any]:
    for _ in range(200):
        response = await client.get(f"/api/v1/tasks/{task_id}")
        assert response.status_code == 200
        detail = cast(dict[str, Any], response.json())
        if detail["status"] in {"waiting-approval", "completed"}:
            return detail
        await asyncio.sleep(0.01)
    raise AssertionError("local task did not reach its next durable state")


async def test_stopped_application_backup_restores_task_result_stream_and_prompt(
    tmp_path: Path,
) -> None:
    tasks = tmp_path / "tasks.sqlite"
    settings = tmp_path / "settings.sqlite"
    app = create_app(task_database_path=tasks, settings_database_path=settings)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://backup.test",
        ) as client:
            assert (
                await client.put(
                    "/api/v1/settings/prompt",
                    json={"systemPrompt": "Retain the verified recovery context."},
                )
            ).status_code == 200
            created = (
                await client.post(
                    "/api/v1/tasks",
                    json={"prompt": "Prepare a useful local recovery result"},
                )
            ).json()
            paused = await _terminal_detail(client, created["taskId"])
            assert paused["status"] == "waiting-approval"
            assert (
                await client.post(
                    f"/api/v1/tasks/{created['taskId']}/decisions",
                    json={
                        "interruptId": paused["pendingInterrupt"]["interruptId"],
                        "decision": "approve",
                    },
                )
            ).status_code == 202
            detail = await _terminal_detail(client, created["taskId"])
            assert detail["status"] == "completed"
            before = {
                "detail": detail,
                "events": (await client.get(f"/api/v1/tasks/{created['taskId']}/events")).text,
                "listing": (await client.get("/api/v1/tasks")).json(),
                "prompt": (await client.get("/api/v1/settings/prompt")).json(),
                "result": (await client.get(f"/api/v1/tasks/{created['taskId']}/result")).json(),
            }

    bundle = tmp_path / "bundle"
    create_backup_bundle(
        task_database=tasks,
        settings_database=settings,
        output_directory=bundle.resolve(),
    )
    restored = tmp_path / "restored"
    report = restore_backup_bundle(
        bundle_directory=bundle,
        output_directory=restored.resolve(),
    )
    assert report["status"] == "verified"

    recovered_app = create_app(
        task_database_path=restored / "tasks.sqlite3",
        settings_database_path=restored / "settings.sqlite3",
    )
    async with recovered_app.router.lifespan_context(recovered_app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=recovered_app),
            base_url="http://restored.test",
        ) as client:
            after = {
                "detail": (await client.get(f"/api/v1/tasks/{created['taskId']}")).json(),
                "events": (await client.get(f"/api/v1/tasks/{created['taskId']}/events")).text,
                "listing": (await client.get("/api/v1/tasks")).json(),
                "prompt": (await client.get("/api/v1/settings/prompt")).json(),
                "result": (await client.get(f"/api/v1/tasks/{created['taskId']}/result")).json(),
            }

    assert after == before

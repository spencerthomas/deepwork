"""End-to-end ASGI lifespan recovery contract for explicit local SQLite."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, cast

import httpx

from deepwork_api import create_app


async def _wait_for_status(
    client: httpx.AsyncClient,
    task_id: str,
    expected: str,
) -> dict[str, Any]:
    for _ in range(100):
        response = await client.get(f"/api/v1/tasks/{task_id}")
        assert response.status_code == 200
        payload = cast(dict[str, Any], response.json())
        if payload["status"] == expected:
            return payload
        await asyncio.sleep(0)
    raise AssertionError(f"task did not reach {expected}")


def _events(body: str) -> list[dict[str, Any]]:
    parsed: list[dict[str, Any]] = []
    for block in body.strip().split("\n\n"):
        fields = dict(line.split(": ", maxsplit=1) for line in block.splitlines())
        parsed.append(
            {
                "id": int(fields["id"]),
                "event": fields["event"],
                "data": json.loads(fields["data"]),
            }
        )
    return parsed


async def test_completed_task_recovers_identically_across_app_lifespans(tmp_path: Path) -> None:
    database = (tmp_path / "tasks.sqlite").resolve()
    app_one = create_app(task_database_path=database)
    transport_one = httpx.ASGITransport(app=app_one)

    async with app_one.router.lifespan_context(app_one):
        async with httpx.AsyncClient(
            transport=transport_one,
            base_url="http://fixture.test",
        ) as client:
            created_response = await client.post(
                "/api/v1/tasks",
                json={"prompt": "Prepare a safe persisted launch plan"},
            )
            assert created_response.status_code == 202
            created = cast(dict[str, Any], created_response.json())
            paused = await _wait_for_status(client, created["taskId"], "waiting-approval")
            interrupt_id = paused["pendingInterrupt"]["interruptId"]

            edited_response = await client.patch(
                f"/api/v1/tasks/{created['taskId']}/plan",
                json={
                    "interruptId": interrupt_id,
                    "expectedRevision": paused["proposedPlan"]["revision"],
                    "steps": [
                        "Inspect the persisted fixture state.",
                        "Approve the current revision.",
                        "Verify restart recovery.",
                    ],
                },
            )
            assert edited_response.status_code == 200
            edited_plan = edited_response.json()["plan"]

            decision = await client.post(
                f"/api/v1/tasks/{created['taskId']}/decisions",
                json={"interruptId": interrupt_id, "decision": "approve"},
            )
            assert decision.status_code == 202
            detail = await _wait_for_status(client, created["taskId"], "completed")
            assert detail["proposedPlan"] == edited_plan

            result_response = await client.get(f"/api/v1/tasks/{created['taskId']}/result")
            assert result_response.status_code == 200
            result = result_response.json()
            stream = await client.get(f"/api/v1/tasks/{created['taskId']}/events")
            assert stream.status_code == 200
            transcript = _events(stream.text)
            assert [event["id"] for event in transcript] == list(
                range(1, detail["lastEventId"] + 1)
            )
            tail_response = await client.get(
                f"/api/v1/tasks/{created['taskId']}/events",
                headers={"Last-Event-ID": "6"},
            )
            replay_tail = _events(tail_response.text)

    app_two = create_app(task_database_path=database)
    transport_two = httpx.ASGITransport(app=app_two)
    async with app_two.router.lifespan_context(app_two):
        async with httpx.AsyncClient(
            transport=transport_two,
            base_url="http://fixture.test",
        ) as client:
            recovered_detail = await client.get(f"/api/v1/tasks/{created['taskId']}")
            recovered_result = await client.get(f"/api/v1/tasks/{created['taskId']}/result")
            recovered_stream = await client.get(f"/api/v1/tasks/{created['taskId']}/events")
            recovered_tail = await client.get(
                f"/api/v1/tasks/{created['taskId']}/events",
                headers={"Last-Event-ID": "6"},
            )
            listing = await client.get("/api/v1/tasks")

    assert recovered_detail.status_code == 200
    assert recovered_detail.json() == detail
    assert recovered_result.status_code == 200
    assert recovered_result.json() == result
    assert _events(recovered_stream.text) == transcript
    assert _events(recovered_tail.text) == replay_tail
    assert listing.json()["items"] == [
        {
            "taskId": created["taskId"],
            "runId": created["runId"],
            "title": detail["title"],
            "objective": detail["objective"],
            "status": "completed",
            "lastEventId": detail["lastEventId"],
        }
    ]
    assert len({event["id"] for event in transcript}) == len(transcript)

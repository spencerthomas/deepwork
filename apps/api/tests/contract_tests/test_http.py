"""Contract tests for fixture-only HTTP behavior."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, cast

import httpx

from deepwork_api import create_app


@asynccontextmanager
async def _client() -> AsyncIterator[httpx.AsyncClient]:
    app = create_app()
    transport = httpx.ASGITransport(app=app)
    try:
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://fixture.test",
        ) as client:
            yield client
    finally:
        await app.state.task_runner.close()


async def test_health_is_process_only() -> None:
    async with _client() as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "alive",
        "scope": "process",
        "evidence_class": "fixture",
        "dependencies_checked": [],
    }


async def test_demo_status_cannot_imply_live_capability() -> None:
    async with _client() as client:
        response = await client.get("/api/v1/demo/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "fixture"
    assert payload["evidence_class"] == "fixture"
    states = {item["name"]: item["state"] for item in payload["capabilities"]}
    assert states["local_task_loop"] == "available"
    assert states["task_stream"] == "available"
    assert states["external_providers"] == "unavailable"
    assert "unavailable" in payload["safe_reason"]


def _field_names(value: Any) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(_field_names(item) for item in value.values()), set())
    if isinstance(value, list):
        return set().union(*(_field_names(item) for item in value), set())
    return set()


def test_openapi_has_no_secret_or_proxy_shape() -> None:
    schema = create_app().openapi()
    field_names = {name.casefold() for name in _field_names(schema)}
    forbidden_fields = {
        "authref",
        "authorization",
        "credential",
        "endpoint",
        "forwarded",
        "provider_cursor",
        "token",
    }
    assert field_names.isdisjoint(forbidden_fields)
    serialized = json.dumps(schema)
    assert "/v1/deepagents" not in serialized


async def _create_task(
    client: httpx.AsyncClient, prompt: str = "Prepare a safe plan"
) -> dict[str, Any]:
    response = await client.post("/api/v1/tasks", json={"prompt": prompt})
    assert response.status_code == 202
    assert response.json()["status"] == "queued"
    return cast(dict[str, Any], response.json())


async def _wait_for_status(
    client: httpx.AsyncClient,
    task_id: str,
    expected: set[str],
) -> dict[str, Any]:
    for _ in range(100):
        response = await client.get(f"/api/v1/tasks/{task_id}")
        assert response.status_code == 200
        payload = response.json()
        if payload["status"] in expected:
            return cast(dict[str, Any], payload)
        await asyncio.sleep(0)
    raise AssertionError(f"task did not reach one of {sorted(expected)}")


def _sse_events(body: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for block in body.strip().split("\n\n"):
        fields = dict(line.split(": ", maxsplit=1) for line in block.splitlines())
        events.append(
            {
                "id": int(fields["id"]),
                "event": fields["event"],
                "data": json.loads(fields["data"]),
            }
        )
    return events


async def test_create_list_detail_and_real_pause() -> None:
    async with _client() as client:
        objective = "Prepare a safe launch plan"
        created = await _create_task(client, objective)
        assert created == {
            "taskId": "task_00000001",
            "runId": "run_00000001",
            "status": "queued",
        }

        paused = await _wait_for_status(
            client,
            created["taskId"],
            {"waiting-approval"},
        )
        assert paused["lastEventId"] == 5
        assert paused["objective"] == objective
        assert paused["result"] is None
        assert paused["pendingInterrupt"] == {
            "interruptId": "interrupt_00000001",
            "decisions": ["approve", "reject"],
        }

        listing = await client.get("/api/v1/tasks")
        assert listing.status_code == 200
        assert listing.json()["items"] == [
            {
                "taskId": "task_00000001",
                "runId": "run_00000001",
                "title": objective,
                "objective": objective,
                "status": "waiting-approval",
                "lastEventId": 5,
            }
        ]

        await asyncio.sleep(0)
        still_paused = await client.get(f"/api/v1/tasks/{created['taskId']}")
        assert still_paused.json()["status"] == "waiting-approval"
        assert still_paused.json()["lastEventId"] == 5


async def test_approve_completes_and_sse_replays_after_cursor() -> None:
    async with _client() as client:
        created = await _create_task(client, "Do not echo sk-example-secret-shaped-input")
        paused = await _wait_for_status(client, created["taskId"], {"waiting-approval"})
        interrupt_id = paused["pendingInterrupt"]["interruptId"]

        decision = await client.post(
            f"/api/v1/tasks/{created['taskId']}/decisions",
            json={
                "interruptId": interrupt_id,
                "decision": "approve",
                "comment": "Proceed without echoing this comment.",
            },
        )
        assert decision.status_code == 202
        assert decision.json() == {
            "taskId": created["taskId"],
            "runId": created["runId"],
            "interruptId": interrupt_id,
            "decision": "approve",
            "status": "accepted",
            "duplicate": False,
        }

        completed = await _wait_for_status(client, created["taskId"], {"completed"})
        assert completed["pendingInterrupt"] is None
        assert completed["lastEventId"] == 8
        assert completed["objective"] == "Do not echo [redacted]"
        assert completed["result"] is not None
        assert "Objective: Do not echo [redacted]" in completed["result"]
        assert all(
            section in completed["result"] for section in ("Plan:", "Risks:", "Next actions:")
        )

        full_stream = await asyncio.wait_for(
            client.get(f"/api/v1/tasks/{created['taskId']}/events"),
            timeout=1,
        )
        assert full_stream.status_code == 200
        assert full_stream.headers["content-type"].startswith("text/event-stream")
        events = _sse_events(full_stream.text)
        assert [event["id"] for event in events] == list(range(1, 9))
        assert [event["event"] for event in events] == [
            "task.created",
            "run.started",
            "content.delta",
            "plan.proposed",
            "interrupt.requested",
            "decision.recorded",
            "content.delta",
            "run.completed",
        ]
        assert events[-1]["data"]["status"] == "completed"
        assert events[-1]["data"]["resultAvailable"] is True
        assert events[-1]["event"] == "run.completed"
        assert full_stream.text.endswith("\n\n")
        assert "sk-example-secret-shaped-input" not in full_stream.text
        assert "[redacted]" in full_stream.text
        assert "Proceed without echoing" not in full_stream.text

        replay = await client.get(
            f"/api/v1/tasks/{created['taskId']}/events",
            headers={"Last-Event-ID": "5"},
        )
        replayed = _sse_events(replay.text)
        assert [event["id"] for event in replayed] == [6, 7, 8]
        assert replayed[0]["event"] == "decision.recorded"

        reopened = await client.get(f"/api/v1/tasks/{created['taskId']}")
        assert reopened.status_code == 200
        assert reopened.json()["result"] == completed["result"]
        listing = await client.get("/api/v1/tasks")
        assert listing.json()["items"][0]["objective"] == "Do not echo [redacted]"
        result = await client.get(f"/api/v1/tasks/{created['taskId']}/result")
        assert result.status_code == 200
        assert result.json() == {
            "taskId": created["taskId"],
            "runId": created["runId"],
            "status": "completed",
            "result": completed["result"],
        }


async def test_reject_ends_truthfully_rejected() -> None:
    async with _client() as client:
        created = await _create_task(client)
        paused = await _wait_for_status(client, created["taskId"], {"waiting-approval"})

        response = await client.post(
            f"/api/v1/tasks/{created['taskId']}/decisions",
            json={
                "interruptId": paused["pendingInterrupt"]["interruptId"],
                "decision": "reject",
            },
        )
        assert response.status_code == 202

        rejected = await _wait_for_status(client, created["taskId"], {"rejected"})
        assert rejected["lastEventId"] == 7
        assert rejected["result"] is None
        unavailable = await client.get(f"/api/v1/tasks/{created['taskId']}/result")
        assert unavailable.status_code == 409
        assert unavailable.json()["code"] == "task_result_unavailable"
        stream = await client.get(f"/api/v1/tasks/{created['taskId']}/events")
        events = _sse_events(stream.text)
        assert events[-1]["event"] == "run.completed"
        assert events[-1]["data"] == {
            "runId": created["runId"],
            "status": "rejected",
            "safeReason": "The pending local fixture plan was rejected.",
            "resultAvailable": False,
        }


async def test_wrong_stale_and_duplicate_decisions_are_safe() -> None:
    async with _client() as client:
        created = await _create_task(client)
        paused = await _wait_for_status(client, created["taskId"], {"waiting-approval"})
        interrupt_id = paused["pendingInterrupt"]["interruptId"]

        wrong = await client.post(
            f"/api/v1/tasks/{created['taskId']}/decisions",
            json={"interruptId": "interrupt_99999999", "decision": "approve"},
        )
        assert wrong.status_code == 409
        assert wrong.json()["code"] == "interrupt_mismatch"

        first = await client.post(
            f"/api/v1/tasks/{created['taskId']}/decisions",
            json={"interruptId": interrupt_id, "decision": "approve"},
        )
        assert first.status_code == 202
        assert first.json()["duplicate"] is False

        duplicate = await client.post(
            f"/api/v1/tasks/{created['taskId']}/decisions",
            json={"interruptId": interrupt_id, "decision": "approve"},
        )
        assert duplicate.status_code == 202
        assert duplicate.json()["duplicate"] is True

        conflicting = await client.post(
            f"/api/v1/tasks/{created['taskId']}/decisions",
            json={"interruptId": interrupt_id, "decision": "reject"},
        )
        assert conflicting.status_code == 409
        assert conflicting.json()["code"] == "decision_conflict"

        await _wait_for_status(client, created["taskId"], {"completed"})
        stale = await client.post(
            f"/api/v1/tasks/{created['taskId']}/decisions",
            json={"interruptId": "interrupt_99999999", "decision": "approve"},
        )
        assert stale.status_code == 409
        assert stale.json()["code"] == "interrupt_stale"

        events = _sse_events((await client.get(f"/api/v1/tasks/{created['taskId']}/events")).text)
        assert sum(event["event"] == "decision.recorded" for event in events) == 1


async def test_invalid_event_cursor_and_input_bounds() -> None:
    async with _client() as client:
        blank = await client.post("/api/v1/tasks", json={"prompt": " \n "})
        assert blank.status_code == 422
        accepted_bound = await client.post(
            "/api/v1/tasks",
            json={"prompt": "x" * 8_000},
        )
        assert accepted_bound.status_code == 202
        bounded_detail = await client.get(f"/api/v1/tasks/{accepted_bound.json()['taskId']}")
        assert bounded_detail.status_code == 200
        assert bounded_detail.json()["objective"] == "x" * 8_000
        assert len(bounded_detail.json()["title"]) == 80
        assert bounded_detail.json()["title"].endswith("…")
        too_long = await client.post("/api/v1/tasks", json={"prompt": "x" * 8_001})
        assert too_long.status_code == 422

        created = await _create_task(client)
        invalid = await client.get(
            f"/api/v1/tasks/{created['taskId']}/events",
            headers={"Last-Event-ID": "not-an-id"},
        )
        assert invalid.status_code == 409
        assert invalid.json()["code"] == "event_cursor_invalid"


async def test_materially_different_prompts_produce_different_useful_results() -> None:
    async with _client() as client:
        results: list[str] = []
        for prompt in (
            "Research coastal wetland restoration evidence",
            "Prepare a production customer migration launch",
        ):
            created = await _create_task(client, prompt)
            paused = await _wait_for_status(
                client,
                created["taskId"],
                {"waiting-approval"},
            )
            decision = await client.post(
                f"/api/v1/tasks/{created['taskId']}/decisions",
                json={
                    "interruptId": paused["pendingInterrupt"]["interruptId"],
                    "decision": "approve",
                },
            )
            assert decision.status_code == 202
            await _wait_for_status(client, created["taskId"], {"completed"})
            result = await client.get(f"/api/v1/tasks/{created['taskId']}/result")
            assert result.status_code == 200
            results.append(cast(str, result.json()["result"]))

    research_result, launch_result = results
    assert research_result != launch_result
    assert "Gather source-qualified findings" in research_result
    assert "rollback and communication steps" in launch_result
    assert all(
        all(section in result for section in ("Objective:", "Plan:", "Risks:", "Next actions:"))
        for result in results
    )


async def test_cors_allows_only_local_next_origins() -> None:
    async with _client() as client:
        allowed = await client.options(
            "/api/v1/tasks",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert allowed.status_code == 200
        assert allowed.headers["access-control-allow-origin"] == "http://localhost:3000"
        assert "POST" in allowed.headers["access-control-allow-methods"]

        loopback = await client.options(
            "/api/v1/tasks/task_00000001/events",
            headers={
                "Origin": "http://127.0.0.1:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "last-event-id",
            },
        )
        assert loopback.status_code == 200
        assert loopback.headers["access-control-allow-origin"] == "http://127.0.0.1:3000"

        denied = await client.options(
            "/api/v1/tasks",
            headers={
                "Origin": "https://example.test",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert denied.status_code == 400
        assert "access-control-allow-origin" not in denied.headers

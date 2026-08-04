"""Contract tests for ordered, positional plan decision batches."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any, cast

import httpx

from deepwork_api import create_app


@asynccontextmanager
async def _client() -> AsyncIterator[httpx.AsyncClient]:
    app = create_app(clock=lambda: datetime(2026, 1, 1, tzinfo=UTC))
    transport = httpx.ASGITransport(app=app)
    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://fixture.test") as client:
            yield client
    finally:
        await app.state.task_runner.close()


async def _paused_task(client: httpx.AsyncClient) -> dict[str, Any]:
    created = await client.post("/api/v1/tasks", json={"prompt": "Prepare a safe plan"})
    assert created.status_code == 202
    task_id = created.json()["taskId"]
    for _ in range(200):
        detail = await client.get(f"/api/v1/tasks/{task_id}")
        if detail.json()["status"] == "waiting-approval":
            return cast(dict[str, Any], detail.json())
        await asyncio.sleep(0.01)
    raise AssertionError("task did not pause")


def _approve_all(pending: dict[str, Any]) -> list[dict[str, Any]]:
    return [{"type": "approve"} for _ in pending["actionRequests"]]


def test_openapi_publishes_the_ordered_batch_contract() -> None:
    schema = create_app().openapi()
    operation = schema["paths"]["/api/v1/tasks/{task_id}/decision-batch"]["post"]
    assert operation["requestBody"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/DecisionBatchRequest"
    }
    assert operation["responses"]["202"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/DecisionBatchAcceptedResponse"
    }
    components = schema["components"]["schemas"]
    assert set(components["DecisionBatchRequest"]["required"]) == {
        "interruptId",
        "expectedVersion",
        "idempotencyKey",
        "decisions",
    }
    assert {
        "version",
        "actionRequests",
        "reviewConfigs",
    }.issubset(components["PendingInterruptResponse"]["properties"])


async def test_pending_interrupt_preserves_repeated_names_and_aligned_configs() -> None:
    async with _client() as client:
        paused = await _paused_task(client)

    pending = paused["pendingInterrupt"]
    assert pending["version"] == "1"
    assert [item["name"] for item in pending["actionRequests"]] == [
        "execute_plan_step",
        "execute_plan_step",
        "execute_plan_step",
    ]
    assert [item["args"]["position"] for item in pending["actionRequests"]] == [1, 2, 3]
    assert [item["args"]["text"] for item in pending["actionRequests"]] == paused["proposedPlan"][
        "steps"
    ]
    assert pending["reviewConfigs"] == [
        {
            "actionName": "execute_plan_step",
            "allowedDecisions": ["approve", "edit", "reject"],
        },
        {
            "actionName": "execute_plan_step",
            "allowedDecisions": ["approve", "edit", "reject"],
        },
        {
            "actionName": "execute_plan_step",
            "allowedDecisions": ["approve", "edit", "reject"],
        },
    ]
    assert pending["decisions"] == ["approve", "reject", "respond"]


async def test_batch_approve_and_edit_are_positional_atomic_and_idempotent() -> None:
    async with _client() as client:
        paused = await _paused_task(client)
        pending = paused["pendingInterrupt"]
        decisions = _approve_all(pending)
        decisions[1] = {
            "type": "edit",
            "editedAction": {
                "name": "execute_plan_step",
                "args": {"position": 2, "text": "Review the bounded result."},
            },
        }
        request = {
            "interruptId": pending["interruptId"],
            "expectedVersion": pending["version"],
            "idempotencyKey": "decision-batch-0001",
            "decisions": decisions,
        }

        first = await client.post(f"/api/v1/tasks/{paused['taskId']}/decision-batch", json=request)
        duplicate = await client.post(
            f"/api/v1/tasks/{paused['taskId']}/decision-batch", json=request
        )
        changed_version_replay = await client.post(
            f"/api/v1/tasks/{paused['taskId']}/decision-batch",
            json={**request, "expectedVersion": "2"},
        )
        detail = await client.get(f"/api/v1/tasks/{paused['taskId']}")
        events = await client.get(f"/api/v1/tasks/{paused['taskId']}/events")

    assert first.status_code == 202
    assert first.json() == {
        "taskId": paused["taskId"],
        "runId": paused["runId"],
        "interruptId": pending["interruptId"],
        "version": "1",
        "decisionTypes": ["approve", "edit", "approve"],
        "status": "accepted",
        "duplicate": False,
    }
    assert duplicate.status_code == 202
    assert duplicate.json()["duplicate"] is True
    assert changed_version_replay.status_code == 409
    assert changed_version_replay.json()["code"] == "decision_conflict"
    assert detail.json()["proposedPlan"]["steps"][1] == "Review the bounded result."
    decision_event = next(
        block for block in events.text.split("\n\n") if "event: decision.recorded" in block
    )
    assert '"decisionTypes":["approve","edit","approve"]' in decision_event
    assert "event: plan.updated" in events.text
    assert events.text.index("event: plan.updated") < events.text.index("event: decision.recorded")
    assert "Review the bounded result." not in decision_event
    assert "editedAction" not in decision_event


async def test_batch_rejects_malformed_disallowed_stale_and_conflicting_vectors() -> None:
    async with _client() as client:
        paused = await _paused_task(client)
        pending = paused["pendingInterrupt"]
        base = {
            "interruptId": pending["interruptId"],
            "expectedVersion": pending["version"],
            "idempotencyKey": "decision-batch-invalid",
        }

        malformed = await client.post(
            f"/api/v1/tasks/{paused['taskId']}/decision-batch",
            json={**base, "decisions": [{"type": "approve"}]},
        )
        disallowed = await client.post(
            f"/api/v1/tasks/{paused['taskId']}/decision-batch",
            json={**base, "decisions": [{"type": "respond", "message": "No"}] * 3},
        )
        stale = await client.post(
            f"/api/v1/tasks/{paused['taskId']}/decision-batch",
            json={**base, "expectedVersion": "0", "decisions": _approve_all(pending)},
        )
        accepted = await client.post(
            f"/api/v1/tasks/{paused['taskId']}/decision-batch",
            json={**base, "decisions": _approve_all(pending)},
        )
        conflicting_reuse = await client.post(
            f"/api/v1/tasks/{paused['taskId']}/decision-batch",
            json={
                **base,
                "decisions": [
                    {"type": "reject", "message": "Stop"},
                    *_approve_all(pending)[1:],
                ],
            },
        )
        different_key = await client.post(
            f"/api/v1/tasks/{paused['taskId']}/decision-batch",
            json={
                **base,
                "idempotencyKey": "decision-batch-different-key",
                "decisions": _approve_all(pending),
            },
        )

    assert malformed.status_code == 422
    assert disallowed.status_code == 422
    assert stale.status_code == 409
    assert stale.json()["code"] == "decision_batch_version_stale"
    assert accepted.status_code == 202
    assert conflicting_reuse.status_code == 409
    assert conflicting_reuse.json()["code"] == "decision_conflict"
    assert different_key.status_code == 409
    assert different_key.json()["code"] == "decision_conflict"


async def test_edit_must_keep_action_name_and_position_aligned() -> None:
    async with _client() as client:
        paused = await _paused_task(client)
        pending = paused["pendingInterrupt"]
        base = {
            "interruptId": pending["interruptId"],
            "expectedVersion": pending["version"],
            "idempotencyKey": "decision-batch-edit-invalid",
        }
        wrong_name = _approve_all(pending)
        wrong_name[0] = {
            "type": "edit",
            "editedAction": {
                "name": "different_action",
                "args": {"position": 1, "text": "Valid text"},
            },
        }
        wrong_position = _approve_all(pending)
        wrong_position[0] = {
            "type": "edit",
            "editedAction": {
                "name": "execute_plan_step",
                "args": {"position": 2, "text": "Valid text"},
            },
        }
        name_response = await client.post(
            f"/api/v1/tasks/{paused['taskId']}/decision-batch",
            json={**base, "decisions": wrong_name},
        )
        position_response = await client.post(
            f"/api/v1/tasks/{paused['taskId']}/decision-batch",
            json={**base, "decisions": wrong_position},
        )

    assert name_response.status_code == 422
    assert position_response.status_code == 422

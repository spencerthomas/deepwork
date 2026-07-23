"""Contract tests for task execution through the configured loopback source.

The scripted server below stands in for one ``langgraph dev`` Agent Server
behind the official SDK client shape; no socket is opened. Every test drives
the real FastAPI app built by ``create_app`` in explicit local source mode,
through the unchanged ``LocalAgentServerSource`` adapter.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Mapping, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, cast

import httpx
import pytest
from fastapi import FastAPI

import deepwork_api.bootstrap.api as bootstrap_api
from deepwork_api import create_app
from deepwork_api.adapters.sources.local import LocalAgentServerSource
from deepwork_api.application import LocalAgentServerRunner

UPSTREAM_MARKER = "SECRET-UPSTREAM-DETAIL"
LOCAL_ENDPOINT = "http://127.0.0.1:2024"
LOCAL_ASSISTANT = "deep-work-local-agent"
INITIAL_PLAN = ("Draft the local result.", "Review the local result.")


@dataclass(slots=True)
class _ServerState:
    task: str = ""
    plan: tuple[str, ...] = ()
    plan_revision: int = 0
    status: str = "planned"
    final_answer: str | None = None
    interrupt_id: str | None = None


class ScriptedAgentServer:
    """Deterministic loopback Agent Server double with failure injection."""

    def __init__(self) -> None:
        self.state = _ServerState()
        self.failures: set[str] = set()
        self.omit_final_answer = False
        self.closed = False
        self.resume_decisions: list[str] = []
        self.resume_comments: list[str | None] = []
        self.update_state_calls: list[Mapping[str, object]] = []
        self.run_events: dict[str, list[object]] = {}
        self._counter = 0
        self.threads = _FakeThreads(self)
        self.runs = _FakeRuns(self)
        self.assistants = _FakeAssistants(self)

    async def aclose(self) -> None:
        self.closed = True

    def fail(self, operation: str) -> None:
        if operation in self.failures:
            raise RuntimeError(UPSTREAM_MARKER)

    def next_id(self, prefix: str) -> str:
        self._counter += 1
        return f"{prefix}-{self._counter}"

    def new_interrupt(self) -> str:
        self.state.interrupt_id = self.next_id("srcint")
        return self.state.interrupt_id

    def interrupt_payload(self) -> dict[str, object]:
        return {
            "id": self.state.interrupt_id,
            "value": {
                "kind": "deepwork-plan-approval",
                "action": "execute_plan",
                "task": self.state.task,
                "plan": list(self.state.plan),
                "plan_revision": self.state.plan_revision,
                "plan_trust": "untrusted",
                "allowed_decisions": ["approve", "reject", "respond"],
            },
        }

    def snapshot(self) -> dict[str, object]:
        values: dict[str, object] = {
            "task": self.state.task,
            "plan": list(self.state.plan),
            "plan_revision": self.state.plan_revision,
            "status": self.state.status,
        }
        if self.state.final_answer is not None:
            values["final_answer"] = self.state.final_answer
        has_interrupt = self.state.interrupt_id is not None
        return {
            "values": values,
            "next": ["approve"] if has_interrupt else [],
            "interrupts": [self.interrupt_payload()] if has_interrupt else [],
        }

    def record_run(self, run_id: str, nodes: Sequence[str]) -> None:
        events: list[object] = [
            {"event": "metadata", "data": {"run_id": run_id}, "id": f"{run_id}-e0"},
        ]
        for index, node in enumerate(nodes, start=1):
            events.append(
                {
                    "event": "updates",
                    "data": {node: {"status": self.state.status}},
                    "id": f"{run_id}-e{index}",
                }
            )
        self.run_events[run_id] = events


@dataclass(slots=True)
class _FakeThreads:
    server: ScriptedAgentServer

    async def create(
        self,
        *,
        metadata: Mapping[str, object] | None = None,
    ) -> object:
        self.server.fail("threads.create")
        assert metadata == {"deepwork_source": "local-agent-server"}
        return {"thread_id": "thread-local-1"}

    async def get_state(self, thread_id: str) -> object:
        self.server.fail("threads.get_state")
        assert thread_id == "thread-local-1"
        return self.server.snapshot()

    async def update_state(
        self,
        thread_id: str,
        values: Mapping[str, object] | None,
        *,
        as_node: str | None = None,
    ) -> object:
        self.server.fail("threads.update_state")
        if as_node != "plan" or values is None:
            raise RuntimeError(UPSTREAM_MARKER)
        self.server.update_state_calls.append(values)
        plan = values["plan"]
        revision = values["plan_revision"]
        assert isinstance(plan, list)
        assert isinstance(revision, int)
        self.server.state.plan = tuple(cast("list[str]", plan))
        self.server.state.plan_revision = revision
        self.server.state.status = "planned"
        self.server.state.interrupt_id = None
        return {"checkpoint": {"checkpoint_id": self.server.next_id("ckpt")}}


@dataclass(slots=True)
class _FakeRuns:
    server: ScriptedAgentServer

    async def create(
        self,
        thread_id: str | None,
        assistant_id: str,
        *,
        input: Mapping[str, object] | None = None,
        command: Mapping[str, object] | None = None,
        stream_mode: str | Sequence[str] = "values",
        stream_resumable: bool = False,
        multitask_strategy: str | None = None,
        durability: str | None = None,
    ) -> object:
        server = self.server
        server.fail("runs.create")
        assert assistant_id == LOCAL_ASSISTANT
        assert stream_resumable is True
        assert multitask_strategy == "reject"
        run_id = server.next_id("run-local")
        if input is not None:
            task = input["task"]
            assert isinstance(task, str)
            server.state = _ServerState(
                task=task,
                plan=INITIAL_PLAN,
                plan_revision=1,
                status="planned",
            )
            server.new_interrupt()
            server.record_run(run_id, ("plan", "approve"))
        elif command is not None:
            resume = command["resume"]
            assert isinstance(resume, Mapping)
            payloads = cast("Mapping[str, Mapping[str, object]]", resume)
            current_interrupt = server.state.interrupt_id
            if current_interrupt is None or current_interrupt not in payloads:
                raise RuntimeError(UPSTREAM_MARKER)
            payload = payloads[current_interrupt]
            decision = payload["decision"]
            assert isinstance(decision, str)
            server.resume_decisions.append(decision)
            comment = payload.get("comment")
            server.resume_comments.append(comment if isinstance(comment, str) else None)
            if decision == "approve":
                server.state.status = "completed"
                server.state.interrupt_id = None
                if not server.omit_final_answer:
                    joined = " | ".join(server.state.plan)
                    server.state.final_answer = (
                        f"Local agent completed '{server.state.task}' with plan: {joined}"
                    )
                server.record_run(run_id, ("approve", "execute"))
            elif decision == "reject":
                server.state.status = "rejected"
                server.state.final_answer = "Execution was not approved."
                server.state.interrupt_id = None
                server.record_run(run_id, ("approve", "reject"))
            else:
                server.state.plan = (
                    *server.state.plan,
                    "Incorporate reviewer guidance.",
                )
                server.state.plan_revision += 1
                server.state.status = "planned"
                server.new_interrupt()
                server.record_run(run_id, ("approve", "revise", "approve"))
        else:
            if server.state.status != "planned":
                raise RuntimeError(UPSTREAM_MARKER)
            server.new_interrupt()
            server.record_run(run_id, ("approve",))
        return {"run_id": run_id}

    def join_stream(
        self,
        thread_id: str,
        run_id: str,
        *,
        cancel_on_disconnect: bool = False,
        stream_mode: str | Sequence[str] | None = None,
        last_event_id: str | None = None,
    ) -> AsyncIterator[object]:
        assert cancel_on_disconnect is False
        return self._replay(run_id)

    async def _replay(self, run_id: str) -> AsyncIterator[object]:
        self.server.fail("runs.join_stream")
        for event in self.server.run_events.pop(run_id, []):
            yield event


@dataclass(slots=True)
class _FakeAssistants:
    server: ScriptedAgentServer

    async def get(self, assistant_id: str) -> object:
        self.server.fail("assistants.get")
        return {"assistant_id": assistant_id}


@dataclass(slots=True)
class _Harness:
    app: FastAPI
    client: httpx.AsyncClient


@asynccontextmanager
async def _local_app(
    server: ScriptedAgentServer,
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncIterator[_Harness]:
    def _fake_builder(*, endpoint: str, assistant_id: str) -> LocalAgentServerSource:
        return LocalAgentServerSource(
            client=server,
            endpoint=endpoint,
            assistant_id=assistant_id,
        )

    monkeypatch.setattr(bootstrap_api, "_build_local_agent_server_source", _fake_builder)
    app = create_app(
        local_agent_server_endpoint=LOCAL_ENDPOINT,
        local_agent_server_assistant=LOCAL_ASSISTANT,
    )
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://local-source.test",
        ) as client:
            yield _Harness(app=app, client=client)


async def _create_task(client: httpx.AsyncClient, prompt: str) -> dict[str, Any]:
    response = await client.post("/api/v1/tasks", json={"prompt": prompt})
    assert response.status_code == 202
    return cast("dict[str, Any]", response.json())


async def _wait_for_status(
    client: httpx.AsyncClient,
    task_id: str,
    expected: set[str],
) -> dict[str, Any]:
    for _ in range(500):
        response = await client.get(f"/api/v1/tasks/{task_id}")
        assert response.status_code == 200
        payload = response.json()
        if payload["status"] in expected:
            return cast("dict[str, Any]", payload)
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


async def test_start_creates_authoritative_thread_run_and_pauses_for_review(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = ScriptedAgentServer()
    async with _local_app(server, monkeypatch) as harness:
        client = harness.client
        created = await _create_task(client, "Summarize the supplied notes")
        assert created["taskId"] == "task_00000001"
        assert created["runId"] == "run-local-1"
        assert created["status"] == "queued"
        assert server.state.task == "Summarize the supplied notes"
        source_interrupt = server.state.interrupt_id
        assert source_interrupt is not None

        paused = await _wait_for_status(client, created["taskId"], {"waiting-approval"})
        assert paused["pendingInterrupt"] == {
            "interruptId": source_interrupt,
            "decisions": ["approve", "reject", "respond"],
            "planRevision": 1,
        }
        assert paused["proposedPlan"] == {
            "revision": 1,
            "title": "Local Agent Server plan",
            "steps": list(INITIAL_PLAN),
            "evidenceRefs": [],
        }
        assert paused["result"] is None
        assert "thread-local-1" not in json.dumps(paused)


async def test_approval_executes_and_maps_result_into_task_api(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = ScriptedAgentServer()
    async with _local_app(server, monkeypatch) as harness:
        client = harness.client
        created = await _create_task(client, "Summarize the supplied notes")
        task_id = created["taskId"]
        paused = await _wait_for_status(client, task_id, {"waiting-approval"})
        interrupt_id = paused["pendingInterrupt"]["interruptId"]

        decided = await client.post(
            f"/api/v1/tasks/{task_id}/decisions",
            json={"interruptId": interrupt_id, "decision": "approve"},
        )
        assert decided.status_code == 202
        assert decided.json()["duplicate"] is False

        completed = await _wait_for_status(client, task_id, {"completed"})
        assert completed["pendingInterrupt"] is None
        assert server.resume_decisions == ["approve"]

        result = await client.get(f"/api/v1/tasks/{task_id}/result")
        assert result.status_code == 200
        assert result.json()["result"] == server.state.final_answer
        assert "Draft the local result." in result.json()["result"]

        replay = await client.get(f"/api/v1/tasks/{task_id}/events")
        events = _sse_events(replay.text)
        names = [event["event"] for event in events]
        assert names[0] == "task.created"
        assert "run.started" in names
        assert "plan.proposed" in names
        assert "interrupt.requested" in names
        assert "decision.recorded" in names
        assert names[-1] == "run.completed"
        assert events[-1]["data"]["status"] == "completed"
        assert events[-1]["data"]["resultAvailable"] is True
        plan_events = [event for event in events if event["event"] == "plan.proposed"]
        assert plan_events
        assert all(event["data"]["evidenceClass"] == "local-source" for event in plan_events)
        deltas = [event for event in events if event["event"] == "content.delta"]
        assert deltas
        assert all(delta["data"]["evidenceClass"] == "local-source" for delta in deltas)
        assert UPSTREAM_MARKER not in replay.text
        assert "thread-local-1" not in replay.text


async def test_plan_edit_binds_to_source_revision_and_reaches_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = ScriptedAgentServer()
    async with _local_app(server, monkeypatch) as harness:
        client = harness.client
        created = await _create_task(client, "Summarize the supplied notes")
        task_id = created["taskId"]
        paused = await _wait_for_status(client, task_id, {"waiting-approval"})
        first_interrupt = paused["pendingInterrupt"]["interruptId"]

        edited_steps = ["Only inspect supplied input.", "Return a concise local result."]
        edited = await client.patch(
            f"/api/v1/tasks/{task_id}/plan",
            json={
                "interruptId": first_interrupt,
                "expectedRevision": 1,
                "steps": edited_steps,
            },
        )
        assert edited.status_code == 200
        fresh_interrupt = edited.json()["interruptId"]
        assert fresh_interrupt != first_interrupt
        assert edited.json()["plan"]["revision"] == 2
        assert edited.json()["plan"]["steps"] == edited_steps
        assert len(server.update_state_calls) == 1
        assert server.state.plan == tuple(edited_steps)
        assert server.state.plan_revision == 2

        stale_edit = await client.patch(
            f"/api/v1/tasks/{task_id}/plan",
            json={
                "interruptId": first_interrupt,
                "expectedRevision": 1,
                "steps": ["Stale revision must not pass."],
            },
        )
        assert stale_edit.status_code == 409
        assert stale_edit.json()["code"] == "interrupt_mismatch"
        assert len(server.update_state_calls) == 1

        stale_decision = await client.post(
            f"/api/v1/tasks/{task_id}/decisions",
            json={"interruptId": first_interrupt, "decision": "approve"},
        )
        assert stale_decision.status_code == 409
        assert stale_decision.json()["code"] == "interrupt_mismatch"
        assert server.resume_decisions == []

        paused = await _wait_for_status(client, task_id, {"waiting-approval"})
        assert paused["pendingInterrupt"]["interruptId"] == fresh_interrupt
        decided = await client.post(
            f"/api/v1/tasks/{task_id}/decisions",
            json={"interruptId": fresh_interrupt, "decision": "approve"},
        )
        assert decided.status_code == 202
        completed = await _wait_for_status(client, task_id, {"completed"})
        assert "Only inspect supplied input." in completed["result"]

        replay = await client.get(f"/api/v1/tasks/{task_id}/events")
        updates = [event for event in _sse_events(replay.text) if event["event"] == "plan.updated"]
        assert len(updates) == 1
        assert updates[0]["data"]["revision"] == 2
        assert updates[0]["data"]["evidenceClass"] == "local-source"


async def test_respond_guidance_produces_fresh_interrupt_and_revision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = ScriptedAgentServer()
    async with _local_app(server, monkeypatch) as harness:
        client = harness.client
        created = await _create_task(client, "Summarize the supplied notes")
        task_id = created["taskId"]
        paused = await _wait_for_status(client, task_id, {"waiting-approval"})
        first_interrupt = paused["pendingInterrupt"]["interruptId"]

        responded = await client.post(
            f"/api/v1/tasks/{task_id}/decisions",
            json={
                "interruptId": first_interrupt,
                "decision": "respond",
                "comment": "Keep the result under one page.",
            },
        )
        assert responded.status_code == 202

        paused = await _wait_for_status(client, task_id, {"waiting-approval"})
        fresh_interrupt = paused["pendingInterrupt"]["interruptId"]
        assert fresh_interrupt != first_interrupt
        assert paused["pendingInterrupt"]["planRevision"] == 2
        assert paused["proposedPlan"]["steps"][-1] == "Incorporate reviewer guidance."
        assert server.resume_comments == ["Keep the result under one page."]

        approved = await client.post(
            f"/api/v1/tasks/{task_id}/decisions",
            json={"interruptId": fresh_interrupt, "decision": "approve"},
        )
        assert approved.status_code == 202
        completed = await _wait_for_status(client, task_id, {"completed"})
        assert "Incorporate reviewer guidance." in completed["result"]

        replay = await client.get(f"/api/v1/tasks/{task_id}/events")
        assert "Keep the result under one page." not in replay.text


async def test_reject_maps_to_rejected_without_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = ScriptedAgentServer()
    async with _local_app(server, monkeypatch) as harness:
        client = harness.client
        created = await _create_task(client, "Summarize the supplied notes")
        task_id = created["taskId"]
        paused = await _wait_for_status(client, task_id, {"waiting-approval"})
        interrupt_id = paused["pendingInterrupt"]["interruptId"]

        rejected = await client.post(
            f"/api/v1/tasks/{task_id}/decisions",
            json={"interruptId": interrupt_id, "decision": "reject"},
        )
        assert rejected.status_code == 202
        final = await _wait_for_status(client, task_id, {"rejected"})
        assert final["result"] is None

        replay = await client.get(f"/api/v1/tasks/{task_id}/events")
        completed_event = _sse_events(replay.text)[-1]
        assert completed_event["event"] == "run.completed"
        assert completed_event["data"]["resultAvailable"] is False

        result = await client.get(f"/api/v1/tasks/{task_id}/result")
        assert result.status_code == 409
        assert result.json()["code"] == "task_result_unavailable"


async def test_identical_decision_replays_idempotently(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = ScriptedAgentServer()
    async with _local_app(server, monkeypatch) as harness:
        client = harness.client
        created = await _create_task(client, "Summarize the supplied notes")
        task_id = created["taskId"]
        paused = await _wait_for_status(client, task_id, {"waiting-approval"})
        interrupt_id = paused["pendingInterrupt"]["interruptId"]

        first = await client.post(
            f"/api/v1/tasks/{task_id}/decisions",
            json={"interruptId": interrupt_id, "decision": "approve"},
        )
        assert first.status_code == 202
        assert first.json()["duplicate"] is False
        await _wait_for_status(client, task_id, {"completed"})

        replay = await client.post(
            f"/api/v1/tasks/{task_id}/decisions",
            json={"interruptId": interrupt_id, "decision": "approve"},
        )
        assert replay.status_code == 202
        assert replay.json()["duplicate"] is True
        assert server.resume_decisions == ["approve"]

        conflicting = await client.post(
            f"/api/v1/tasks/{task_id}/decisions",
            json={"interruptId": interrupt_id, "decision": "reject"},
        )
        assert conflicting.status_code == 409
        assert conflicting.json()["code"] == "decision_conflict"


async def test_decision_with_unknown_interrupt_is_rejected_without_source_io(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = ScriptedAgentServer()
    async with _local_app(server, monkeypatch) as harness:
        client = harness.client
        created = await _create_task(client, "Summarize the supplied notes")
        task_id = created["taskId"]
        paused = await _wait_for_status(client, task_id, {"waiting-approval"})

        mismatch = await client.post(
            f"/api/v1/tasks/{task_id}/decisions",
            json={"interruptId": "srcint-unknown", "decision": "approve"},
        )
        assert mismatch.status_code == 409
        assert mismatch.json()["code"] == "interrupt_mismatch"
        assert server.resume_decisions == []

        still_paused = await _wait_for_status(client, task_id, {"waiting-approval"})
        assert still_paused["pendingInterrupt"] == paused["pendingInterrupt"]


async def test_unreachable_source_rejects_creation_without_a_ghost_task(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = ScriptedAgentServer()
    server.failures.add("threads.create")
    async with _local_app(server, monkeypatch) as harness:
        client = harness.client
        refused = await client.post(
            "/api/v1/tasks",
            json={"prompt": "Summarize the supplied notes"},
        )
        assert refused.status_code == 503
        assert refused.json() == {
            "code": "local_source_unavailable",
            "message": "The configured local task source is unavailable.",
        }
        assert UPSTREAM_MARKER not in refused.text

        listing = await client.get("/api/v1/tasks")
        assert listing.status_code == 200
        assert listing.json() == {"items": []}


async def test_source_outage_after_decision_fails_the_task_safely(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = ScriptedAgentServer()
    async with _local_app(server, monkeypatch) as harness:
        client = harness.client
        created = await _create_task(client, "Summarize the supplied notes")
        task_id = created["taskId"]
        paused = await _wait_for_status(client, task_id, {"waiting-approval"})
        interrupt_id = paused["pendingInterrupt"]["interruptId"]

        server.failures.add("runs.create")
        decided = await client.post(
            f"/api/v1/tasks/{task_id}/decisions",
            json={"interruptId": interrupt_id, "decision": "approve"},
        )
        assert decided.status_code == 202

        failed = await _wait_for_status(client, task_id, {"failed"})
        assert failed["result"] is None
        replay = await client.get(f"/api/v1/tasks/{task_id}/events")
        events = _sse_events(replay.text)
        assert events[-1]["data"] == {
            "runId": created["runId"],
            "status": "failed",
            "safeReason": "The local agent source became unavailable.",
            "resultAvailable": False,
        }
        assert UPSTREAM_MARKER not in replay.text


async def test_externally_advanced_interrupt_fails_source_scoped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = ScriptedAgentServer()
    async with _local_app(server, monkeypatch) as harness:
        client = harness.client
        created = await _create_task(client, "Summarize the supplied notes")
        task_id = created["taskId"]
        paused = await _wait_for_status(client, task_id, {"waiting-approval"})
        interrupt_id = paused["pendingInterrupt"]["interruptId"]

        # The source moved to a different interrupt outside this application.
        server.new_interrupt()
        decided = await client.post(
            f"/api/v1/tasks/{task_id}/decisions",
            json={"interruptId": interrupt_id, "decision": "approve"},
        )
        assert decided.status_code == 202

        failed = await _wait_for_status(client, task_id, {"failed"})
        replay = await client.get(f"/api/v1/tasks/{task_id}/events")
        assert _sse_events(replay.text)[-1]["data"]["safeReason"] == (
            "The local agent source broke its supported contract."
        )
        assert server.resume_decisions == []
        assert failed["result"] is None


async def test_completed_run_without_result_is_a_contract_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = ScriptedAgentServer()
    server.omit_final_answer = True
    async with _local_app(server, monkeypatch) as harness:
        client = harness.client
        created = await _create_task(client, "Summarize the supplied notes")
        task_id = created["taskId"]
        paused = await _wait_for_status(client, task_id, {"waiting-approval"})

        decided = await client.post(
            f"/api/v1/tasks/{task_id}/decisions",
            json={
                "interruptId": paused["pendingInterrupt"]["interruptId"],
                "decision": "approve",
            },
        )
        assert decided.status_code == 202

        failed = await _wait_for_status(client, task_id, {"failed"})
        assert failed["result"] is None
        replay = await client.get(f"/api/v1/tasks/{task_id}/events")
        assert _sse_events(replay.text)[-1]["data"]["safeReason"] == (
            "The local agent source broke its supported contract."
        )
        assert UPSTREAM_MARKER not in replay.text


async def test_stream_disconnect_never_cancels_the_task(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = ScriptedAgentServer()
    async with _local_app(server, monkeypatch) as harness:
        client = harness.client
        created = await _create_task(client, "Summarize the supplied notes")
        task_id = created["taskId"]
        paused = await _wait_for_status(client, task_id, {"waiting-approval"})
        interrupt_id = paused["pendingInterrupt"]["interruptId"]

        service = harness.app.state.task_service
        received: list[object] = []

        async def _follow_stream() -> None:
            async for event in service.stream_events(task_id, 0):
                received.append(event)

        follower = asyncio.create_task(_follow_stream())
        for _ in range(50):
            await asyncio.sleep(0)
        assert received
        follower.cancel()
        with pytest.raises(asyncio.CancelledError):
            await follower

        still_paused = await _wait_for_status(client, task_id, {"waiting-approval"})
        assert still_paused["pendingInterrupt"]["interruptId"] == interrupt_id
        decided = await client.post(
            f"/api/v1/tasks/{task_id}/decisions",
            json={"interruptId": interrupt_id, "decision": "approve"},
        )
        assert decided.status_code == 202
        await _wait_for_status(client, task_id, {"completed"})


async def test_shutdown_closes_runner_and_source_without_failing_tasks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = ScriptedAgentServer()
    task_id = ""
    async with _local_app(server, monkeypatch) as harness:
        assert isinstance(harness.app.state.task_runner, LocalAgentServerRunner)
        created = await _create_task(harness.client, "Summarize the supplied notes")
        task_id = created["taskId"]
        await _wait_for_status(harness.client, task_id, {"waiting-approval"})
        repository = harness.app.state.task_repository

    assert server.closed is True
    final = await repository.get_task(task_id)
    assert final.status.value == "waiting_approval"
    assert final.pending_interrupt_id is not None


async def test_local_mode_adds_no_new_wire_surface(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = ScriptedAgentServer()

    def _fake_builder(*, endpoint: str, assistant_id: str) -> LocalAgentServerSource:
        return LocalAgentServerSource(
            client=server,
            endpoint=endpoint,
            assistant_id=assistant_id,
        )

    monkeypatch.setattr(bootstrap_api, "_build_local_agent_server_source", _fake_builder)
    local_app = create_app(
        local_agent_server_endpoint=LOCAL_ENDPOINT,
        local_agent_server_assistant=LOCAL_ASSISTANT,
    )
    fixture_app = create_app()

    local_schema = local_app.openapi()
    fixture_schema = fixture_app.openapi()
    assert local_schema["paths"] == fixture_schema["paths"]
    assert local_schema["components"] == fixture_schema["components"]
    serialized = json.dumps(local_schema)
    assert LOCAL_ENDPOINT not in serialized
    assert LOCAL_ASSISTANT not in serialized
    assert "classic" not in serialized.casefold()

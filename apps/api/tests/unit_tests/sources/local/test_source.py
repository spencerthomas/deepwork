"""Network-denied tests for the official local Agent Server adapter boundary."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Mapping, Sequence
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import cast

import httpx
import pytest

from deepwork_api.adapters.sources.local import (
    LocalAgentServerSource,
    LocalRunReference,
    LocalSourceConfigurationError,
    LocalSourceContractError,
    LocalSourceStaleInterruptError,
    LocalSourceUnavailableError,
    create_official_client,
    validate_loopback_url,
)
from deepwork_api.adapters.sources.local.source import Decision

OFFICIAL_INTERRUPT_ID = "bb51bb4b9474b86e0c58ac08fa85d3fa"
NEXT_OFFICIAL_INTERRUPT_ID = "cc51bb4b9474b86e0c58ac08fa85d3fc"


def _interrupt(
    *,
    interrupt_id: str = OFFICIAL_INTERRUPT_ID,
    revision: object = 1,
    plan: list[str] | None = None,
    allowed_decisions: list[str] | None = None,
    action: str = "execute_plan",
    plan_trust: str = "untrusted",
) -> dict[str, object]:
    decisions = ["approve", "reject", "respond"] if allowed_decisions is None else allowed_decisions
    steps = ["Inspect inputs", "Produce result"] if plan is None else plan
    return {
        "id": interrupt_id,
        "value": {
            "kind": "deepwork-plan-approval",
            "action": action,
            "task": "private task text is ignored by the adapter",
            "plan": steps,
            "plan_revision": revision,
            "plan_trust": plan_trust,
            "allowed_decisions": decisions,
        },
    }


def _state(
    *,
    interrupt_id: str = OFFICIAL_INTERRUPT_ID,
    revision: object = 1,
    plan: list[str] | None = None,
    final_answer: str | None = None,
    allowed_decisions: list[str] | None = None,
    action: str = "execute_plan",
    plan_trust: str = "untrusted",
) -> dict[str, object]:
    steps = ["Inspect inputs", "Produce result"] if plan is None else plan
    values: dict[str, object] = {
        "task": "private task text is ignored by the adapter",
        "plan": steps,
        "plan_revision": revision,
        "status": "planned" if final_answer is None else "completed",
        "reviewer_comment": "private review note is ignored by the adapter",
    }
    if final_answer is not None:
        values["final_answer"] = final_answer
    return {
        "values": values,
        "next": ["approve"] if final_answer is None else [],
        "checkpoint": {"checkpoint_id": f"checkpoint-official-{revision}"},
        "interrupts": (
            [
                _interrupt(
                    interrupt_id=interrupt_id,
                    revision=revision,
                    plan=steps,
                    allowed_decisions=allowed_decisions,
                    action=action,
                    plan_trust=plan_trust,
                )
            ]
            if final_answer is None
            else []
        ),
    }


@dataclass
class FakeThreads:
    state: object = field(default_factory=_state)
    create_calls: list[dict[str, object]] = field(default_factory=list)
    update_calls: list[dict[str, object]] = field(default_factory=list)
    advance_after_update: bool = True
    state_after_update: object | None = None

    async def create(
        self,
        *,
        metadata: Mapping[str, object] | None = None,
    ) -> object:
        self.create_calls.append({"metadata": metadata})
        return {"thread_id": "thread-official-1"}

    async def get_state(self, thread_id: str) -> object:
        assert thread_id == "thread-official-1"
        return self.state

    async def update_state(
        self,
        thread_id: str,
        values: Mapping[str, object] | None,
        *,
        as_node: str | None = None,
    ) -> object:
        self.update_calls.append(
            {
                "thread_id": thread_id,
                "values": values,
                "as_node": as_node,
            }
        )
        await asyncio.sleep(0)
        if self.advance_after_update:
            assert values is not None
            plan = values["plan"]
            revision = values["plan_revision"]
            assert isinstance(plan, list)
            assert all(isinstance(step, str) for step in plan)
            assert isinstance(revision, int)
            self.state = (
                self.state_after_update
                if self.state_after_update is not None
                else _state(
                    interrupt_id=NEXT_OFFICIAL_INTERRUPT_ID,
                    revision=revision,
                    plan=cast("list[str]", plan),
                )
            )
        return {"checkpoint": {"checkpoint_id": "checkpoint-official-2"}}


@dataclass
class BlockingGetStateThreads(FakeThreads):
    entered: asyncio.Event = field(default_factory=asyncio.Event)
    release: asyncio.Event = field(default_factory=asyncio.Event)
    get_state_calls: int = 0

    async def get_state(self, thread_id: str) -> object:
        self.get_state_calls += 1
        if self.get_state_calls == 1:
            self.entered.set()
            await self.release.wait()
        return await super().get_state(thread_id)


@dataclass
class FakeRuns:
    create_calls: list[dict[str, object]] = field(default_factory=list)
    stream_calls: list[dict[str, object]] = field(default_factory=list)
    stream_events: list[object] = field(default_factory=list)
    create_error: Exception | None = None

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
        if self.create_error is not None:
            raise self.create_error
        self.create_calls.append(
            {
                "thread_id": thread_id,
                "assistant_id": assistant_id,
                "input": input,
                "command": command,
                "stream_mode": stream_mode,
                "stream_resumable": stream_resumable,
                "multitask_strategy": multitask_strategy,
                "durability": durability,
            }
        )
        return {"run_id": f"run-official-{len(self.create_calls)}"}

    def join_stream(
        self,
        thread_id: str,
        run_id: str,
        *,
        cancel_on_disconnect: bool = False,
        stream_mode: str | Sequence[str] | None = None,
        last_event_id: str | None = None,
    ) -> AsyncIterator[object]:
        self.stream_calls.append(
            {
                "thread_id": thread_id,
                "run_id": run_id,
                "cancel_on_disconnect": cancel_on_disconnect,
                "stream_mode": stream_mode,
                "last_event_id": last_event_id,
            }
        )

        async def events() -> AsyncIterator[object]:
            for event in self.stream_events:
                yield event

        return events()


@dataclass
class FakeAssistants:
    response: object = field(default_factory=lambda: {"assistant_id": "deep-work-local-agent"})
    error: Exception | None = None

    async def get(self, assistant_id: str) -> object:
        assert assistant_id == "deep-work-local-agent"
        if self.error is not None:
            raise self.error
        return self.response


@dataclass
class FakeClient:
    threads: FakeThreads = field(default_factory=FakeThreads)
    runs: FakeRuns = field(default_factory=FakeRuns)
    assistants: FakeAssistants = field(default_factory=FakeAssistants)
    closed: bool = False

    async def aclose(self) -> None:
        self.closed = True


def _source(client: FakeClient | None = None) -> tuple[LocalAgentServerSource, FakeClient]:
    fake = client or FakeClient()
    return LocalAgentServerSource(client=fake), fake


@pytest.mark.parametrize(
    "value",
    [
        "https://127.0.0.1:2024",
        "http://localhost:2024",
        "http://127.0.0.2:2024",
        "http://127.0.0.1",
        "http://user:secret@127.0.0.1:2024",
        "http://127.0.0.1:2024/path",
        "http://127.0.0.1:2024?token=secret",
        "http://127.0.0.1:2024#fragment",
    ],
)
def test_source_rejects_every_non_fixed_loopback_origin(value: str) -> None:
    with pytest.raises(LocalSourceConfigurationError):
        validate_loopback_url(value)


def test_source_normalizes_supported_ipv4_and_ipv6_loopback() -> None:
    assert validate_loopback_url("http://127.0.0.1:2024/") == "http://127.0.0.1:2024"
    assert validate_loopback_url("http://[::1]:2024") == "http://[::1]:2024"


def test_official_client_explicitly_suppresses_ambient_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private_values = {
        "LANGGRAPH_API_KEY": "secret-langgraph-key",
        "LANGSMITH_API_KEY": "secret-langsmith-key",
        "LANGCHAIN_API_KEY": "secret-langchain-key",
    }
    for name, value in private_values.items():
        monkeypatch.setenv(name, value)
    captured: dict[str, object] = {}
    client = object()

    def get_client(**kwargs: object) -> object:
        captured.update(kwargs)
        return client

    monkeypatch.setattr(
        "deepwork_api.adapters.sources.local.source.importlib.import_module",
        lambda _: SimpleNamespace(get_client=get_client),
    )

    assert create_official_client() is client
    assert captured == {
        "url": "http://127.0.0.1:2024",
        "api_key": None,
        "headers": {},
        "timeout": (5.0, 300.0, 30.0, 5.0),
    }
    assert all(secret not in repr(captured) for secret in private_values.values())


async def test_start_uses_official_thread_and_resumable_run_calls() -> None:
    source, client = _source()

    run = await source.start("Prepare a release brief")

    assert run == LocalRunReference(
        thread_id="thread-official-1",
        run_id="run-official-1",
    )
    assert client.threads.create_calls == [
        {
            "metadata": {"deepwork_source": "local-agent-server"},
        }
    ]
    assert client.runs.create_calls == [
        {
            "thread_id": "thread-official-1",
            "assistant_id": "deep-work-local-agent",
            "input": {"task": "Prepare a release brief"},
            "command": None,
            "stream_mode": ("values", "updates"),
            "stream_resumable": True,
            "multitask_strategy": "reject",
            "durability": "sync",
        }
    ]


async def test_close_releases_official_client_transport() -> None:
    source, client = _source()

    await source.close()

    assert client.closed is True


async def test_status_is_sanitized_and_makes_no_provider_claim() -> None:
    source, _ = _source()

    status = await source.status()
    assert status.available is True
    assert status.code == "ready"
    capabilities = source.capabilities()
    assert capabilities.transport == "langgraph-sdk"
    assert capabilities.loopback_only is True
    assert capabilities.accepts_credentials is False
    assert not hasattr(capabilities, "external_providers")

    failing, _ = _source(
        FakeClient(
            assistants=FakeAssistants(error=RuntimeError("private upstream token=do-not-disclose"))
        )
    )
    unavailable = await failing.status()
    assert unavailable.code == "unavailable"
    assert "private" not in repr(unavailable)


async def test_state_uses_official_interrupt_id_and_omits_private_fields() -> None:
    source, _ = _source()

    snapshot = await source.get_state("thread-official-1")

    assert snapshot.plan == ("Inspect inputs", "Produce result")
    assert snapshot.plan_revision == 1
    assert snapshot.interrupt is not None
    assert snapshot.interrupt.interrupt_id == OFFICIAL_INTERRUPT_ID
    assert snapshot.interrupt.allowed_decisions == ("approve", "reject", "respond")
    assert "private task" not in repr(snapshot)
    assert "private review" not in repr(snapshot)


@pytest.mark.parametrize(
    ("state", "message"),
    [
        (_state(action="delete_repository"), "action"),
        (_state(plan_trust="trusted"), "trust marker"),
    ],
)
async def test_state_rejects_wrong_interrupt_action_or_trust(
    state: dict[str, object],
    message: str,
) -> None:
    source, _ = _source(FakeClient(threads=FakeThreads(state=state)))

    with pytest.raises(LocalSourceContractError, match=message):
        await source.get_state("thread-official-1")


async def test_stream_reconnects_with_official_cursor_and_sanitizes_payload() -> None:
    source, client = _source()
    client.runs.stream_events = [
        {
            "event": "metadata",
            "data": {"run_id": "run-official-1", "secret": "not-exposed"},
            "id": "next/cursor==",
        },
        {
            "event": "updates",
            "data": {"plan": {"reviewer_comment": "not-exposed"}},
            "id": "cursor:2",
        },
        {
            "event": "error",
            "data": {"message": "private upstream failure"},
            "id": "cursor:3",
        },
    ]

    events = [
        event
        async for event in source.stream(
            LocalRunReference("thread-official-1", "run-official-1"),
            after_cursor="opaque/cursor==",
        )
    ]

    assert client.runs.stream_calls == [
        {
            "thread_id": "thread-official-1",
            "run_id": "run-official-1",
            "cancel_on_disconnect": False,
            "stream_mode": ("values", "updates"),
            "last_event_id": "opaque/cursor==",
        }
    ]
    assert [event.cursor for event in events] == ["next/cursor==", "cursor:2", "cursor:3"]
    assert events[0].run_id == "run-official-1"
    assert events[1].updated_nodes == ("plan",)
    assert events[2].summary == "The local Agent Server reported a run error."
    assert "not-exposed" not in repr(events)
    assert "private upstream" not in repr(events)


@pytest.mark.parametrize("decision", ["approve", "reject", "respond"])
async def test_resume_uses_public_command_for_exact_current_interrupt(
    decision: str,
) -> None:
    source, client = _source()
    comment = "Please tighten the evidence." if decision == "respond" else None

    run = await source.resume(
        "thread-official-1",
        interrupt_id=OFFICIAL_INTERRUPT_ID,
        decision=cast("Decision", decision),
        comment=comment,
    )

    assert run.run_id == "run-official-1"
    resume_value = {"decision": decision}
    if comment is not None:
        resume_value["comment"] = comment
    assert client.runs.create_calls[0]["command"] == {
        "resume": {OFFICIAL_INTERRUPT_ID: resume_value}
    }
    assert source._thread_locks == {}


async def test_resume_rejects_stale_interrupt_and_bounded_response_before_command() -> None:
    source, client = _source()

    with pytest.raises(LocalSourceStaleInterruptError, match="no longer current"):
        await source.resume(
            "thread-official-1",
            interrupt_id="interrupt-other",
            decision="approve",
        )
    with pytest.raises(LocalSourceContractError, match="requires"):
        await source.resume(
            "thread-official-1",
            interrupt_id=OFFICIAL_INTERRUPT_ID,
            decision="respond",
        )
    private_note = "private-" + "x" * 1_001
    with pytest.raises(LocalSourceContractError) as error:
        await source.resume(
            "thread-official-1",
            interrupt_id=OFFICIAL_INTERRUPT_ID,
            decision="respond",
            comment=private_note,
        )
    assert private_note not in str(error.value)
    assert client.runs.create_calls == []
    assert source._thread_locks == {}


@pytest.mark.parametrize(
    "decisions",
    [
        ["approve", "reject"],
        ["respond", "reject", "approve"],
        ["approve", "approve", "reject", "respond"],
        [],
    ],
)
async def test_interrupt_requires_exact_canonical_decisions(
    decisions: list[str],
) -> None:
    source, _ = _source(
        FakeClient(
            threads=FakeThreads(
                state=_state(allowed_decisions=decisions),
            )
        )
    )

    with pytest.raises(LocalSourceContractError, match="decisions"):
        await source.get_state("thread-official-1")


async def test_interrupt_rejects_missing_decisions() -> None:
    state = _state()
    interrupts = cast("list[dict[str, object]]", state["interrupts"])
    payload = cast("dict[str, object]", interrupts[0]["value"])
    del payload["allowed_decisions"]
    source, _ = _source(FakeClient(threads=FakeThreads(state=state)))

    with pytest.raises(LocalSourceContractError, match="decisions"):
        await source.get_state("thread-official-1")


@pytest.mark.parametrize("status_code", [404, 409])
async def test_resume_keeps_ambiguous_source_errors_generic(status_code: int) -> None:
    request = httpx.Request("POST", "http://127.0.0.1:2024/threads/thread/runs")
    response = httpx.Response(status_code, request=request)
    upstream = httpx.HTTPStatusError(
        "private upstream conflict detail",
        request=request,
        response=response,
    )
    client = FakeClient(runs=FakeRuns(create_error=upstream))
    source, _ = _source(client)

    with pytest.raises(LocalSourceUnavailableError) as error:
        await source.resume(
            "thread-official-1",
            interrupt_id=OFFICIAL_INTERRUPT_ID,
            decision="approve",
        )

    assert "private upstream" not in str(error.value)
    assert source._thread_locks == {}


async def test_plan_edit_uses_official_plan_node_and_reinvokes_for_new_interrupt() -> None:
    source, client = _source()

    update = await source.update_plan(
        "thread-official-1",
        interrupt_id=OFFICIAL_INTERRUPT_ID,
        expected_revision=1,
        steps=["Inspect exact inputs", "Produce evidenced result"],
    )

    assert update.plan_revision == 2
    assert update.run_id == "run-official-1"
    assert update.interrupt_id == NEXT_OFFICIAL_INTERRUPT_ID
    assert client.threads.update_calls == [
        {
            "thread_id": "thread-official-1",
            "values": {
                "plan": ["Inspect exact inputs", "Produce evidenced result"],
                "plan_revision": 2,
                "plan_trust": "untrusted",
                "approval": "pending",
                "status": "planned",
            },
            "as_node": "plan",
        }
    ]
    assert client.runs.create_calls[0]["input"] is None
    assert client.runs.create_calls[0]["command"] is None
    assert client.runs.stream_calls == [
        {
            "thread_id": "thread-official-1",
            "run_id": "run-official-1",
            "cancel_on_disconnect": False,
            "stream_mode": ("values", "updates"),
            "last_event_id": None,
        }
    ]
    with pytest.raises(LocalSourceStaleInterruptError):
        await source.resume(
            "thread-official-1",
            interrupt_id=OFFICIAL_INTERRUPT_ID,
            decision="approve",
        )
    resumed = await source.resume(
        "thread-official-1",
        interrupt_id=update.interrupt_id,
        decision="approve",
    )
    assert resumed.run_id == "run-official-2"


async def test_plan_edit_preserves_exact_valid_step_whitespace() -> None:
    source, client = _source()
    steps = ["  Preserve exact spacing.  ", "\tPreserve tabs too.\t"]

    update = await source.update_plan(
        "thread-official-1",
        interrupt_id=OFFICIAL_INTERRUPT_ID,
        expected_revision=1,
        steps=steps,
    )
    state = await source.get_state("thread-official-1")
    update_values = cast(
        "Mapping[str, object]",
        client.threads.update_calls[0]["values"],
    )

    assert update_values["plan"] == steps
    assert state.plan == tuple(steps)
    assert state.interrupt is not None
    assert state.interrupt.interrupt_id == update.interrupt_id
    assert state.interrupt.plan == tuple(steps)


async def test_plan_edits_are_serialized_per_thread_before_current_head_check() -> None:
    client = FakeClient()
    source, _ = _source(client)

    results = await asyncio.gather(
        source.update_plan(
            "thread-official-1",
            interrupt_id=OFFICIAL_INTERRUPT_ID,
            expected_revision=1,
            steps=["First edit"],
        ),
        source.update_plan(
            "thread-official-1",
            interrupt_id=OFFICIAL_INTERRUPT_ID,
            expected_revision=1,
            steps=["Concurrent stale edit"],
        ),
        return_exceptions=True,
    )

    assert sum(isinstance(result, LocalSourceStaleInterruptError) for result in results) == 1
    assert len(client.threads.update_calls) == 1
    assert len(client.runs.create_calls) == 1
    assert source._thread_locks == {}


@pytest.mark.parametrize(
    "confirmed_state",
    [
        _state(
            interrupt_id=OFFICIAL_INTERRUPT_ID,
            revision=2,
            plan=["Edited step"],
        ),
        _state(
            interrupt_id=NEXT_OFFICIAL_INTERRUPT_ID,
            revision=2,
            plan=["Different step"],
        ),
        _state(
            interrupt_id=NEXT_OFFICIAL_INTERRUPT_ID,
            revision=3,
            plan=["Edited step"],
        ),
        _state(
            interrupt_id=NEXT_OFFICIAL_INTERRUPT_ID,
            revision=2,
            plan=["Edited step"],
            action="delete_repository",
        ),
        _state(
            interrupt_id=NEXT_OFFICIAL_INTERRUPT_ID,
            revision=2,
            plan=["Edited step"],
            plan_trust="trusted",
        ),
        _state(
            interrupt_id=NEXT_OFFICIAL_INTERRUPT_ID,
            revision=2,
            plan=["Edited step"],
            allowed_decisions=["approve", "reject"],
        ),
    ],
)
async def test_plan_edit_requires_fresh_canonical_interrupt(
    confirmed_state: dict[str, object],
) -> None:
    client = FakeClient(
        threads=FakeThreads(state_after_update=confirmed_state),
    )
    source, _ = _source(client)

    with pytest.raises(LocalSourceContractError):
        await source.update_plan(
            "thread-official-1",
            interrupt_id=OFFICIAL_INTERRUPT_ID,
            expected_revision=1,
            steps=["Edited step"],
        )

    assert len(client.threads.update_calls) == 1
    assert len(client.runs.create_calls) == 1
    assert len(client.runs.stream_calls) == 1
    assert source._thread_locks == {}


@pytest.mark.parametrize("revision", [False, 0, -1, "1"])
async def test_state_rejects_invalid_plan_revision(revision: object) -> None:
    source, _ = _source(
        FakeClient(
            threads=FakeThreads(
                state=_state(revision=revision),
            )
        )
    )

    with pytest.raises(LocalSourceContractError, match="revision"):
        await source.get_state("thread-official-1")


@pytest.mark.parametrize("revision", [False, 0, -1])
async def test_plan_edit_rejects_invalid_expected_revision_before_mutation(
    revision: int,
) -> None:
    source, client = _source()

    with pytest.raises(LocalSourceContractError, match="revision"):
        await source.update_plan(
            "thread-official-1",
            interrupt_id=OFFICIAL_INTERRUPT_ID,
            expected_revision=revision,
            steps=["Edited step"],
        )

    assert client.threads.update_calls == []
    assert client.runs.create_calls == []
    assert source._thread_locks == {}


async def test_plan_revision_preserves_and_increments_very_large_valid_integer() -> None:
    revision = 10**100
    source, client = _source(
        FakeClient(
            threads=FakeThreads(
                state=_state(revision=revision),
            )
        )
    )

    update = await source.update_plan(
        "thread-official-1",
        interrupt_id=OFFICIAL_INTERRUPT_ID,
        expected_revision=revision,
        steps=["Edited step"],
    )
    state = await source.get_state("thread-official-1")
    update_values = cast(
        "Mapping[str, object]",
        client.threads.update_calls[0]["values"],
    )

    assert update.plan_revision == revision + 1
    assert update.interrupt_id == NEXT_OFFICIAL_INTERRUPT_ID
    assert update_values["plan_revision"] == revision + 1
    assert state.plan_revision == revision + 1


async def test_thread_lock_registry_evicts_cancelled_waiter_and_final_holder() -> None:
    threads = BlockingGetStateThreads()
    source, _ = _source(FakeClient(threads=threads))
    holder = asyncio.create_task(
        source.resume(
            "thread-official-1",
            interrupt_id=OFFICIAL_INTERRUPT_ID,
            decision="approve",
        )
    )
    await threads.entered.wait()
    waiter = asyncio.create_task(
        source.resume(
            "thread-official-1",
            interrupt_id=OFFICIAL_INTERRUPT_ID,
            decision="approve",
        )
    )
    for _ in range(10):
        entry = source._thread_locks.get("thread-official-1")
        if entry is not None and entry.users == 2:
            break
        await asyncio.sleep(0)
    assert entry is not None
    assert entry.users == 2

    waiter.cancel()
    with pytest.raises(asyncio.CancelledError):
        await waiter
    assert source._thread_locks["thread-official-1"].users == 1

    threads.release.set()
    await holder
    assert source._thread_locks == {}


async def test_thread_lock_registry_evicts_cancelled_holder() -> None:
    threads = BlockingGetStateThreads()
    source, _ = _source(FakeClient(threads=threads))
    holder = asyncio.create_task(
        source.resume(
            "thread-official-1",
            interrupt_id=OFFICIAL_INTERRUPT_ID,
            decision="approve",
        )
    )
    await threads.entered.wait()

    holder.cancel()
    with pytest.raises(asyncio.CancelledError):
        await holder

    assert source._thread_locks == {}


async def test_plan_edit_fails_closed_for_revision_and_mixed_steps() -> None:
    source, client = _source()

    with pytest.raises(LocalSourceStaleInterruptError, match="revision"):
        await source.update_plan(
            "thread-official-1",
            interrupt_id=OFFICIAL_INTERRUPT_ID,
            expected_revision=2,
            steps=["Inspect exact inputs"],
        )
    with pytest.raises(LocalSourceContractError, match="text"):
        await source.update_plan(
            "thread-official-1",
            interrupt_id=OFFICIAL_INTERRUPT_ID,
            expected_revision=1,
            steps=["Inspect exact inputs", 42],  # type: ignore[list-item]
        )
    with pytest.raises(LocalSourceContractError, match="supported bound"):
        await source.update_plan(
            "thread-official-1",
            interrupt_id=OFFICIAL_INTERRUPT_ID,
            expected_revision=1,
            steps=[" \t "],
        )
    assert client.threads.update_calls == []
    assert client.runs.create_calls == []

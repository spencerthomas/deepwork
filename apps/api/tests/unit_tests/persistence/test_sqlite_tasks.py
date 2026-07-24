"""Local SQLite TaskRepository durability and safety tests."""

from __future__ import annotations

import asyncio
import hashlib
import json
import sqlite3
import threading
from pathlib import Path

import pytest

import deepwork_api.adapters.persistence.sqlite as sqlite_adapter
from deepwork_api.adapters.persistence import (
    SQLiteTaskRepository,
    SQLiteTaskRepositoryClosedError,
    SQLiteTaskRepositoryDataError,
    SQLiteTaskRepositoryPathError,
    SQLiteTaskRepositorySchemaError,
)
from deepwork_api.domain import (
    MAX_PLAN_REVISION,
    MAX_PLAN_STEP_LENGTH,
    MAX_PLAN_STEPS,
    MAX_TASK_OBJECTIVE_LENGTH,
    MAX_TASK_RESULT_LENGTH,
    DecisionConflictError,
    DecisionRecord,
    DecisionValue,
    EvidenceKind,
    EvidenceRecord,
    EvidenceSource,
    InterruptMismatchError,
    InvalidEventCursorError,
    PlanRevisionConflictError,
    PlanUpdateRecord,
    ProposedPlan,
    StaleInterruptError,
    TaskAlreadyResolvedError,
    TaskEvent,
    TaskEventName,
    TaskStatus,
)


async def _waiting_task(
    repository: SQLiteTaskRepository,
    *,
    objective: str = "Prepare a durable local result",
) -> tuple[str, str, str, ProposedPlan]:
    task = await repository.create_task(title=objective[:80], objective=objective)
    await repository.append_event(
        task.task_id,
        name=TaskEventName.RUN_STARTED,
        data=(("runId", task.run_id), ("status", TaskStatus.RUNNING.value)),
        status=TaskStatus.RUNNING,
    )
    evidence = EvidenceRecord(
        evidence_id=task.task_id.replace("task_", "evidence_", 1),
        kind=EvidenceKind.FIXTURE,
        summary="The local runner prepared a bounded durable plan.",
        source=EvidenceSource.LOCAL_RUNNER,
        verified=False,
    )
    await repository.record_evidence(task.task_id, evidence)
    plan = ProposedPlan(
        revision=1,
        title="Durable local plan",
        steps=("Inspect the bounded input.", "Produce and verify a useful result."),
        evidence_refs=(evidence.evidence_id,),
    )
    await repository.set_plan(
        task.task_id,
        plan=plan,
        event_name=TaskEventName.PLAN_PROPOSED,
    )
    interrupt_id = "interrupt_00000001"
    await repository.append_event(
        task.task_id,
        name=TaskEventName.INTERRUPT_REQUESTED,
        data=(
            ("interruptId", interrupt_id),
            ("question", "Approve or provide guidance?"),
            ("decisions", ("approve", "reject", "respond")),
            ("planRevision", plan.revision),
        ),
        status=TaskStatus.WAITING_APPROVAL,
        pending_interrupt_id=interrupt_id,
    )
    return task.task_id, task.run_id, interrupt_id, plan


async def test_cancellation_is_durable_idempotent_and_wakes_waiters(tmp_path: Path) -> None:
    database = tmp_path / "tasks.sqlite"
    first = SQLiteTaskRepository(database)
    task_id, run_id, interrupt_id, _ = await _waiting_task(first)
    before = await first.get_task(task_id)

    # A pending decision waiter must be released the moment cancellation lands.
    decision_waiter = asyncio.create_task(first.wait_for_decision(task_id, interrupt_id))
    await asyncio.sleep(0)
    record = await first.cancel_task(task_id)
    assert record.task_id == task_id
    assert record.run_id == run_id
    assert record.duplicate is False
    with pytest.raises(StaleInterruptError):
        await asyncio.wait_for(decision_waiter, timeout=1)

    cancelled = await first.get_task(task_id)
    assert cancelled.status is TaskStatus.CANCELLED
    assert cancelled.pending_interrupt_id is None
    assert cancelled.result is None
    assert cancelled.last_event_id == before.last_event_id + 1
    completion = (await first.events_after(task_id, before.last_event_id))[0]
    assert completion.name is TaskEventName.RUN_COMPLETED
    assert dict(completion.data)["status"] == TaskStatus.CANCELLED.value

    # Idempotent replay returns a duplicate receipt without a second event.
    duplicate = await first.cancel_task(task_id)
    assert duplicate.duplicate is True
    assert (await first.get_task(task_id)).last_event_id == cancelled.last_event_id
    await first.close()

    # The cancelled terminal state survives a reopen.
    reopened = SQLiteTaskRepository(database)
    recovered = await reopened.get_task(task_id)
    assert recovered == cancelled
    assert (await reopened.cancel_task(task_id)).duplicate is True
    await reopened.close()


async def test_cancellation_refuses_a_completed_task(tmp_path: Path) -> None:
    repository = SQLiteTaskRepository(tmp_path / "tasks.sqlite")
    task_id, _, interrupt_id, _ = await _waiting_task(repository)
    await repository.record_decision(
        task_id,
        interrupt_id=interrupt_id,
        decision=DecisionValue.APPROVE,
        comment_provided=False,
        response_digest=None,
    )
    await repository.append_event(
        task_id,
        name=TaskEventName.RUN_COMPLETED,
        data=(
            ("runId", "run_00000001"),
            ("status", TaskStatus.COMPLETED.value),
            ("safeReason", "Completed by the local runner."),
            ("resultAvailable", True),
        ),
        status=TaskStatus.COMPLETED,
        clear_pending_interrupt=True,
        result="A useful durable result.",
    )
    with pytest.raises(TaskAlreadyResolvedError):
        await repository.cancel_task(task_id)
    assert (await repository.get_task(task_id)).status is TaskStatus.COMPLETED
    await repository.close()


def _repository_is_closed(repository: SQLiteTaskRepository) -> bool:
    return repository._closed


def _repository_has_process_state(repository: SQLiteTaskRepository) -> bool:
    return repository._process_state is not None


def _unchecked_plan_with_revision(revision: int) -> ProposedPlan:
    """Build corrupt input solely to prove the adapter's defense-in-depth guard."""

    plan = object.__new__(ProposedPlan)
    object.__setattr__(plan, "revision", revision)
    object.__setattr__(plan, "title", "Invalid revision")
    object.__setattr__(plan, "steps", ("Never reach SQLite.",))
    object.__setattr__(plan, "evidence_refs", ())
    return plan


async def test_create_list_and_detail_survive_repository_reopen(tmp_path: Path) -> None:
    database = tmp_path / "tasks.sqlite"
    first = SQLiteTaskRepository(database)
    task_a = await first.create_task(title="First", objective="First durable objective")
    task_b = await first.create_task(title="Second", objective="Second durable objective")
    await first.close()

    second = SQLiteTaskRepository(database)
    listing = await second.list_tasks()
    detail = await second.get_task(task_a.task_id)

    assert [task.task_id for task in listing] == [task_a.task_id, task_b.task_id]
    assert detail == task_a
    assert detail.last_event_id == 1
    assert (await second.events_after(task_a.task_id, 0))[0].name is TaskEventName.TASK_CREATED
    await second.close()


async def test_waiting_approval_snapshot_and_waiters_survive_reopen(tmp_path: Path) -> None:
    database = tmp_path / "tasks.sqlite"
    first = SQLiteTaskRepository(database)
    task_id, _, interrupt_id, plan = await _waiting_task(first)
    expected = await first.get_task(task_id)
    await first.close()

    reopened = SQLiteTaskRepository(database)
    recovered = await reopened.get_task(task_id)
    assert recovered == expected
    assert recovered.status is TaskStatus.WAITING_APPROVAL
    assert recovered.pending_interrupt_id == interrupt_id
    assert recovered.proposed_plan == plan
    assert recovered.evidence[0].evidence_id == "evidence_00000001"

    decision_waiter = asyncio.create_task(reopened.wait_for_decision(task_id, interrupt_id))
    event_waiter = asyncio.create_task(reopened.wait_for_events(task_id, recovered.last_event_id))
    writer = SQLiteTaskRepository(database)
    await writer.record_decision(
        task_id,
        interrupt_id=interrupt_id,
        decision=DecisionValue.APPROVE,
        comment_provided=False,
        response_digest=None,
    )

    assert await asyncio.wait_for(decision_waiter, timeout=1) is DecisionValue.APPROVE
    await asyncio.wait_for(event_waiter, timeout=1)
    await writer.close()
    await reopened.close()


async def test_full_plan_response_approval_evidence_and_result_survive_reopen(
    tmp_path: Path,
) -> None:
    database = tmp_path / "tasks.sqlite"
    repository = SQLiteTaskRepository(database)
    task_id, run_id, first_interrupt, original_plan = await _waiting_task(repository)

    edited = await repository.update_plan(
        task_id,
        interrupt_id=first_interrupt,
        expected_revision=1,
        steps=("Inspect persisted state.", "Verify exact event ordering."),
    )
    note = "Keep the durable result local."
    note_digest = hashlib.sha256(note.encode()).hexdigest()
    response = await repository.record_decision(
        task_id,
        interrupt_id=first_interrupt,
        decision=DecisionValue.RESPOND,
        comment_provided=True,
        response_digest=note_digest,
    )
    response_evidence = EvidenceRecord(
        evidence_id="evidence_00000001_01",
        kind=EvidenceKind.FIXTURE,
        summary="Reviewer guidance was recorded without retaining its raw text.",
        source=EvidenceSource.REVIEWER_RESPONSE,
        verified=False,
    )
    await repository.record_evidence(task_id, response_evidence)
    revised_plan = ProposedPlan(
        revision=edited.plan.revision + 1,
        title="Durable local plan (guidance recorded)",
        steps=edited.plan.steps,
        evidence_refs=(*original_plan.evidence_refs, response_evidence.evidence_id),
    )
    await repository.set_plan(
        task_id,
        plan=revised_plan,
        event_name=TaskEventName.PLAN_PROPOSED,
    )
    second_interrupt = "interrupt_10000001"
    await repository.append_event(
        task_id,
        name=TaskEventName.INTERRUPT_REQUESTED,
        data=(
            ("interruptId", second_interrupt),
            ("question", "Approve the revised plan?"),
            ("decisions", ("approve", "reject", "respond")),
            ("planRevision", revised_plan.revision),
        ),
        status=TaskStatus.WAITING_APPROVAL,
        pending_interrupt_id=second_interrupt,
    )
    approval = await repository.record_decision(
        task_id,
        interrupt_id=second_interrupt,
        decision=DecisionValue.APPROVE,
        comment_provided=False,
        response_digest=None,
    )
    result = "Durable local result with exact evidence and event history."
    await repository.append_event(
        task_id,
        name=TaskEventName.CONTENT_DELTA,
        data=(("text", result), ("evidenceClass", "fixture")),
    )
    await repository.append_event(
        task_id,
        name=TaskEventName.RUN_COMPLETED,
        data=(
            ("runId", run_id),
            ("status", TaskStatus.COMPLETED.value),
            ("safeReason", "Completed by the deterministic local runner."),
            ("resultAvailable", True),
        ),
        status=TaskStatus.COMPLETED,
        clear_pending_interrupt=True,
        result=result,
    )
    events_before = await repository.events_after(task_id, 0)
    await repository.close()

    reopened = SQLiteTaskRepository(database)
    detail = await reopened.get_task(task_id)
    events_after = await reopened.events_after(task_id, 0)

    assert response.duplicate is False
    assert approval.duplicate is False
    assert detail.status is TaskStatus.COMPLETED
    assert detail.pending_interrupt_id is None
    assert detail.proposed_plan == revised_plan
    assert detail.evidence == (
        EvidenceRecord(
            evidence_id="evidence_00000001",
            kind=EvidenceKind.FIXTURE,
            summary="The local runner prepared a bounded durable plan.",
            source=EvidenceSource.LOCAL_RUNNER,
            verified=False,
        ),
        response_evidence,
    )
    assert detail.result == result
    assert detail.last_event_id == len(events_before)
    assert events_after == events_before
    assert [event.event_id for event in events_after] == list(range(1, len(events_after) + 1))
    await reopened.close()


async def test_decision_conflicts_interrupt_errors_and_plan_revision_match_fixture(
    tmp_path: Path,
) -> None:
    repository = SQLiteTaskRepository(tmp_path / "tasks.sqlite")
    task_id, _, interrupt_id, _ = await _waiting_task(repository)

    with pytest.raises(InterruptMismatchError):
        await repository.update_plan(
            task_id,
            interrupt_id="interrupt_00000002",
            expected_revision=1,
            steps=("Keep the current plan.",),
        )
    with pytest.raises(PlanRevisionConflictError):
        await repository.update_plan(
            task_id,
            interrupt_id=interrupt_id,
            expected_revision=99,
            steps=("Keep the current plan.",),
        )

    digest = hashlib.sha256(b"bounded response").hexdigest()
    first = await repository.record_decision(
        task_id,
        interrupt_id=interrupt_id,
        decision=DecisionValue.RESPOND,
        comment_provided=True,
        response_digest=digest,
    )
    duplicate = await repository.record_decision(
        task_id,
        interrupt_id=interrupt_id,
        decision=DecisionValue.RESPOND,
        comment_provided=False,
        response_digest=digest,
    )

    assert first.duplicate is False
    assert duplicate.duplicate is True
    with pytest.raises(DecisionConflictError):
        await repository.record_decision(
            task_id,
            interrupt_id=interrupt_id,
            decision=DecisionValue.REJECT,
            comment_provided=False,
            response_digest=None,
        )
    with pytest.raises(StaleInterruptError):
        await repository.update_plan(
            task_id,
            interrupt_id=interrupt_id,
            expected_revision=1,
            steps=("No longer actionable.",),
        )
    await repository.close()


async def test_set_plan_revisions_are_monotonic_across_concurrency_and_reopen(
    tmp_path: Path,
) -> None:
    database = tmp_path / "tasks.sqlite"
    first = SQLiteTaskRepository(database)
    task = await first.create_task(title="Plan", objective="Monotonic plan revisions")
    revision_two = ProposedPlan(
        revision=2,
        title="Revision two",
        steps=("Persist revision two.",),
        evidence_refs=(),
    )
    await first.set_plan(
        task.task_id,
        plan=revision_two,
        event_name=TaskEventName.PLAN_PROPOSED,
    )
    await first.close()

    second = SQLiteTaskRepository(database)
    with pytest.raises(PlanRevisionConflictError):
        await second.set_plan(
            task.task_id,
            plan=ProposedPlan(
                revision=1,
                title="Regressed revision",
                steps=("Never overwrite revision two.",),
                evidence_refs=(),
            ),
            event_name=TaskEventName.PLAN_PROPOSED,
        )

    third = SQLiteTaskRepository(database)
    revision_three = ProposedPlan(
        revision=3,
        title="Revision three",
        steps=("Persist exactly once.",),
        evidence_refs=(),
    )
    outcomes = await asyncio.gather(
        second.set_plan(
            task.task_id,
            plan=revision_three,
            event_name=TaskEventName.PLAN_PROPOSED,
        ),
        third.set_plan(
            task.task_id,
            plan=revision_three,
            event_name=TaskEventName.PLAN_PROPOSED,
        ),
        return_exceptions=True,
    )
    assert sum(isinstance(outcome, TaskEvent) for outcome in outcomes) == 1
    assert sum(isinstance(outcome, PlanRevisionConflictError) for outcome in outcomes) == 1
    await second.close()
    await third.close()

    reopened = SQLiteTaskRepository(database)
    assert (await reopened.get_task(task.task_id)).proposed_plan == revision_three
    with pytest.raises(PlanRevisionConflictError):
        await reopened.set_plan(
            task.task_id,
            plan=revision_three,
            event_name=TaskEventName.PLAN_PROPOSED,
        )
    await reopened.close()


async def test_plan_revision_bounds_fail_safely_before_sqlite_and_on_decode(
    tmp_path: Path,
) -> None:
    database = tmp_path / "tasks.sqlite"
    repository = SQLiteTaskRepository(database)
    task = await repository.create_task(title="Bound", objective="Revision bound")
    maximum_revision = MAX_PLAN_REVISION
    maximum_plan = ProposedPlan(
        revision=maximum_revision,
        title="Maximum revision",
        steps=("Remain inside the shared signed-32 bound.",),
        evidence_refs=(),
    )
    await repository.set_plan(
        task.task_id,
        plan=maximum_plan,
        event_name=TaskEventName.PLAN_PROPOSED,
    )
    event_count = (await repository.get_task(task.task_id)).last_event_id

    for invalid_revision in (maximum_revision + 1, 10**100):
        with pytest.raises(PlanRevisionConflictError) as error:
            await repository.set_plan(
                "task_99999999",
                plan=_unchecked_plan_with_revision(invalid_revision),
                event_name=TaskEventName.PLAN_PROPOSED,
            )
        assert str(error.value) == ""
        with pytest.raises(PlanRevisionConflictError):
            await repository.update_plan(
                "task_99999999",
                interrupt_id="interrupt_99999999",
                expected_revision=invalid_revision,
                steps=("Never reach SQLite.",),
            )
    assert (await repository.get_task(task.task_id)).last_event_id == event_count

    await repository.append_event(
        task.task_id,
        name=TaskEventName.INTERRUPT_REQUESTED,
        data=(
            ("interruptId", "interrupt_00000001"),
            ("question", "Revise the maximum plan?"),
            ("decisions", ("approve", "reject", "respond")),
            ("planRevision", maximum_revision),
        ),
        status=TaskStatus.WAITING_APPROVAL,
        pending_interrupt_id="interrupt_00000001",
    )
    before_increment = (await repository.get_task(task.task_id)).last_event_id
    with pytest.raises(PlanRevisionConflictError):
        await repository.update_plan(
            task.task_id,
            interrupt_id="interrupt_00000001",
            expected_revision=maximum_revision,
            steps=("An increment would overflow the shared bound.",),
        )
    assert (await repository.get_task(task.task_id)).last_event_id == before_increment
    await repository.close()

    with sqlite3.connect(database) as connection:
        connection.execute(
            "UPDATE tasks SET plan_revision = ? WHERE task_id = ?",
            (maximum_revision + 1, task.task_id),
        )
    corrupt = SQLiteTaskRepository(database)
    with pytest.raises(SQLiteTaskRepositoryDataError) as corrupt_error:
        await corrupt.get_task(task.task_id)
    assert str(corrupt_error.value) == "stored plan revision is invalid"
    assert str(maximum_revision + 1) not in str(corrupt_error.value)


async def test_concurrent_decisions_are_atomic_and_survive_reopen(tmp_path: Path) -> None:
    database = tmp_path / "tasks.sqlite"
    first = SQLiteTaskRepository(database)
    task_id, _, interrupt_id, _ = await _waiting_task(first)
    second = SQLiteTaskRepository(database)
    same_decision = await asyncio.gather(
        first.record_decision(
            task_id,
            interrupt_id=interrupt_id,
            decision=DecisionValue.APPROVE,
            comment_provided=False,
            response_digest=None,
        ),
        second.record_decision(
            task_id,
            interrupt_id=interrupt_id,
            decision=DecisionValue.APPROVE,
            comment_provided=True,
            response_digest=None,
        ),
    )
    assert {record.duplicate for record in same_decision} == {False, True}
    assert (
        sum(
            event.name is TaskEventName.DECISION_RECORDED
            for event in await first.events_after(task_id, 0)
        )
        == 1
    )
    await first.close()
    await second.close()

    reopened = SQLiteTaskRepository(database)
    assert await reopened.wait_for_decision(task_id, interrupt_id) is DecisionValue.APPROVE
    replay = await reopened.record_decision(
        task_id,
        interrupt_id=interrupt_id,
        decision=DecisionValue.APPROVE,
        comment_provided=False,
        response_digest=None,
    )
    assert replay.duplicate is True
    with pytest.raises(DecisionConflictError):
        await reopened.record_decision(
            task_id,
            interrupt_id=interrupt_id,
            decision=DecisionValue.REJECT,
            comment_provided=False,
            response_digest=None,
        )

    conflict_task_id, _, conflict_interrupt, _ = await _waiting_task(
        reopened,
        objective="Concurrent conflicting decision",
    )
    other = SQLiteTaskRepository(database)
    conflict_outcomes = await asyncio.gather(
        reopened.record_decision(
            conflict_task_id,
            interrupt_id=conflict_interrupt,
            decision=DecisionValue.APPROVE,
            comment_provided=False,
            response_digest=None,
        ),
        other.record_decision(
            conflict_task_id,
            interrupt_id=conflict_interrupt,
            decision=DecisionValue.REJECT,
            comment_provided=False,
            response_digest=None,
        ),
        return_exceptions=True,
    )
    assert sum(isinstance(outcome, DecisionRecord) for outcome in conflict_outcomes) == 1
    assert sum(isinstance(outcome, DecisionConflictError) for outcome in conflict_outcomes) == 1
    assert (
        sum(
            event.name is TaskEventName.DECISION_RECORDED
            for event in await reopened.events_after(conflict_task_id, 0)
        )
        == 1
    )
    await other.close()
    await reopened.close()


async def test_concurrent_same_revision_plan_updates_are_atomic(tmp_path: Path) -> None:
    database = tmp_path / "tasks.sqlite"
    first = SQLiteTaskRepository(database)
    task_id, _, interrupt_id, _ = await _waiting_task(first)
    second = SQLiteTaskRepository(database)
    outcomes = await asyncio.gather(
        first.update_plan(
            task_id,
            interrupt_id=interrupt_id,
            expected_revision=1,
            steps=("First concurrent edit.",),
        ),
        second.update_plan(
            task_id,
            interrupt_id=interrupt_id,
            expected_revision=1,
            steps=("Second concurrent edit.",),
        ),
        return_exceptions=True,
    )

    assert sum(isinstance(outcome, PlanUpdateRecord) for outcome in outcomes) == 1
    assert sum(isinstance(outcome, PlanRevisionConflictError) for outcome in outcomes) == 1
    assert (
        sum(
            event.name is TaskEventName.PLAN_UPDATED
            for event in await first.events_after(task_id, 0)
        )
        == 1
    )
    current_plan = (await second.get_task(task_id)).proposed_plan
    assert current_plan is not None
    assert current_plan.revision == 2
    await first.close()
    await second.close()


async def test_maximum_bounds_cursor_validation_and_terminal_immutability(
    tmp_path: Path,
) -> None:
    repository = SQLiteTaskRepository(tmp_path / "tasks.sqlite")
    objective = "x" * MAX_TASK_OBJECTIVE_LENGTH
    task = await repository.create_task(title="x" * 80, objective=objective)
    plan = ProposedPlan(
        revision=1,
        title="p" * 100,
        steps=tuple(
            f"{index}" + "s" * (MAX_PLAN_STEP_LENGTH - len(str(index)))
            for index in range(MAX_PLAN_STEPS)
        ),
        evidence_refs=(),
    )
    await repository.set_plan(
        task.task_id,
        plan=plan,
        event_name=TaskEventName.PLAN_PROPOSED,
    )
    result = "r" * MAX_TASK_RESULT_LENGTH
    await repository.append_event(
        task.task_id,
        name=TaskEventName.RUN_COMPLETED,
        data=(
            ("runId", task.run_id),
            ("status", TaskStatus.COMPLETED.value),
            ("safeReason", "Completed within the maximum bound."),
            ("resultAvailable", True),
        ),
        status=TaskStatus.COMPLETED,
        result=result,
    )

    reopened = SQLiteTaskRepository(tmp_path / "tasks.sqlite")
    assert (await reopened.get_task(task.task_id)).result == result
    with pytest.raises(InvalidEventCursorError):
        await reopened.events_after(task.task_id, -1)
    with pytest.raises(InvalidEventCursorError):
        await reopened.events_after(task.task_id, 99)
    with pytest.raises(StaleInterruptError):
        await reopened.append_event(
            task.task_id,
            name=TaskEventName.CONTENT_DELTA,
            data=(("text", "late"),),
        )
    with pytest.raises(StaleInterruptError):
        await reopened.record_evidence(
            task.task_id,
            EvidenceRecord(
                evidence_id="evidence_00000001",
                kind=EvidenceKind.FIXTURE,
                summary="Late evidence",
                source=EvidenceSource.LOCAL_RUNNER,
                verified=False,
            ),
        )
    with pytest.raises(ValueError, match="objective"):
        await reopened.create_task(
            title="too large",
            objective="x" * (MAX_TASK_OBJECTIVE_LENGTH + 1),
        )
    with pytest.raises(ValueError, match="result"):
        await reopened.append_event(
            "missing",
            name=TaskEventName.CONTENT_DELTA,
            data=(("text", "bounded"),),
            result="r" * (MAX_TASK_RESULT_LENGTH + 1),
        )
    await repository.close()
    await reopened.close()


async def test_concurrent_adapter_mutations_preserve_event_ids_and_wake_waiters(
    tmp_path: Path,
) -> None:
    database = tmp_path / "tasks.sqlite"
    first = SQLiteTaskRepository(database)
    task = await first.create_task(title="Concurrent", objective="Concurrent local task")
    second = SQLiteTaskRepository(database)
    waiter = asyncio.create_task(first.wait_for_events(task.task_id, 1))
    await asyncio.sleep(0)

    events = await asyncio.gather(
        *(
            (first if index % 2 == 0 else second).append_event(
                task.task_id,
                name=TaskEventName.CONTENT_DELTA,
                data=(("text", f"event {index}"),),
            )
            for index in range(20)
        )
    )
    await asyncio.wait_for(waiter, timeout=1)

    assert sorted(event.event_id for event in events) == list(range(2, 22))
    history = await first.events_after(task.task_id, 0)
    assert [event.event_id for event in history] == list(range(1, 22))
    assert (await second.get_task(task.task_id)).last_event_id == 21
    await first.close()
    await second.close()


async def test_cancelled_mutation_finishes_and_notifies_waiters(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = SQLiteTaskRepository(tmp_path / "tasks.sqlite")
    task = await repository.create_task(title="Cancellation", objective="Cancellation safety")
    started = threading.Event()
    release = threading.Event()
    original = SQLiteTaskRepository._append_event_sync

    def slow_append(
        self: SQLiteTaskRepository,
        task_id: str,
        name: TaskEventName,
        encoded_data: str,
        status: TaskStatus | None,
        pending_interrupt_id: str | None,
        clear_pending_interrupt: bool,
        result: str | None,
    ) -> TaskEvent:
        started.set()
        if not release.wait(timeout=1):
            raise RuntimeError("test did not release the bounded mutation")
        return original(
            self,
            task_id,
            name,
            encoded_data,
            status,
            pending_interrupt_id,
            clear_pending_interrupt,
            result,
        )

    monkeypatch.setattr(SQLiteTaskRepository, "_append_event_sync", slow_append)
    waiter = asyncio.create_task(repository.wait_for_events(task.task_id, 1))
    mutation = asyncio.create_task(
        repository.append_event(
            task.task_id,
            name=TaskEventName.CONTENT_DELTA,
            data=(("text", "committed after cancellation"),),
        )
    )
    assert await asyncio.to_thread(started.wait, 1)

    mutation.cancel()
    release.set()
    with pytest.raises(asyncio.CancelledError):
        await mutation
    await asyncio.wait_for(waiter, timeout=1)

    assert (await repository.get_task(task.task_id)).last_event_id == 2
    await repository.close()


async def test_decision_waiter_is_signalled_by_second_adapter(tmp_path: Path) -> None:
    database = tmp_path / "tasks.sqlite"
    first = SQLiteTaskRepository(database)
    task_id, _, interrupt_id, _ = await _waiting_task(first)
    second = SQLiteTaskRepository(database)
    waiter = asyncio.create_task(first.wait_for_decision(task_id, interrupt_id))
    await asyncio.sleep(0)

    await second.record_decision(
        task_id,
        interrupt_id=interrupt_id,
        decision=DecisionValue.APPROVE,
        comment_provided=False,
        response_digest=None,
    )

    assert await asyncio.wait_for(waiter, timeout=1) is DecisionValue.APPROVE
    await first.close()
    await second.close()


def test_process_state_registry_is_shared_and_released_across_event_loops(
    tmp_path: Path,
) -> None:
    database = tmp_path / "registry.sqlite"
    baseline = len(sqlite_adapter._PROCESS_STATES)

    for index in range(10):
        loop = asyncio.new_event_loop()

        async def exercise_loop(
            cycle_index: int = index,
            owner_loop: asyncio.AbstractEventLoop = loop,
        ) -> None:
            first = SQLiteTaskRepository(database)
            task = await first.create_task(
                title=f"Registry {cycle_index}",
                objective=f"Registry lifecycle {cycle_index}",
            )
            second = SQLiteTaskRepository(database)
            await second.append_event(
                task.task_id,
                name=TaskEventName.CONTENT_DELTA,
                data=(("text", "second adapter"),),
            )
            assert first._process_state is second._process_state
            await first.close()
            assert owner_loop in sqlite_adapter._PROCESS_STATES

            waiter = asyncio.create_task(second.wait_for_events(task.task_id, 2))
            third = SQLiteTaskRepository(database)
            await third.append_event(
                task.task_id,
                name=TaskEventName.CONTENT_DELTA,
                data=(("text", "third adapter"),),
            )
            await asyncio.wait_for(waiter, timeout=1)
            await third.close()
            await second.close()
            assert owner_loop not in sqlite_adapter._PROCESS_STATES

        try:
            loop.run_until_complete(exercise_loop())
        finally:
            loop.close()

    assert len(sqlite_adapter._PROCESS_STATES) == baseline


def test_wrong_loop_close_is_retryable_on_owner_loop(tmp_path: Path) -> None:
    database = tmp_path / "wrong-loop.sqlite"
    owner_loop = asyncio.new_event_loop()
    wrong_loop = asyncio.new_event_loop()
    repository = SQLiteTaskRepository(database)
    try:
        owner_loop.run_until_complete(
            repository.create_task(title="Owner", objective="Owner-loop close")
        )
        with pytest.raises(SQLiteTaskRepositoryClosedError, match="owning event loop"):
            wrong_loop.run_until_complete(repository.close())
        assert _repository_is_closed(repository) is False
        assert _repository_has_process_state(repository)

        owner_loop.run_until_complete(repository.close())
        assert _repository_is_closed(repository) is True
        assert not _repository_has_process_state(repository)
        assert owner_loop not in sqlite_adapter._PROCESS_STATES
    finally:
        wrong_loop.close()
        owner_loop.close()


async def test_cancelled_close_is_retryable_without_leaking_state(tmp_path: Path) -> None:
    repository = SQLiteTaskRepository(tmp_path / "cancelled-close.sqlite")
    await repository.create_task(title="Close", objective="Cancellation-safe close")
    state = repository._process_state
    assert state is not None

    async with state.condition:
        closing = asyncio.create_task(repository.close())
        await asyncio.sleep(0)
        closing.cancel()
        with pytest.raises(asyncio.CancelledError):
            await closing

    assert _repository_is_closed(repository) is False
    assert repository._process_state is state
    await repository.close()
    assert _repository_is_closed(repository) is True
    assert not _repository_has_process_state(repository)
    assert asyncio.get_running_loop() not in sqlite_adapter._PROCESS_STATES


async def test_composite_reads_return_one_transactional_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = tmp_path / "tasks.sqlite"
    reader = SQLiteTaskRepository(database)
    task = await reader.create_task(title="Snapshot", objective="Snapshot consistency")
    writer = SQLiteTaskRepository(database)
    count_started = threading.Event()
    release_count = threading.Event()
    original_count = reader._event_count_for_existing_task_sync

    def paused_count(connection: sqlite3.Connection, task_id: str) -> int:
        count_started.set()
        if not release_count.wait(timeout=1):
            raise RuntimeError("test did not release the bounded read")
        return original_count(connection, task_id)

    monkeypatch.setattr(reader, "_event_count_for_existing_task_sync", paused_count)
    reading = asyncio.create_task(reader.get_task(task.task_id))
    assert await asyncio.to_thread(count_started.wait, 1)
    result = "Committed only after the old snapshot finishes."
    writing = asyncio.create_task(
        writer.append_event(
            task.task_id,
            name=TaskEventName.RUN_COMPLETED,
            data=(
                ("runId", task.run_id),
                ("status", TaskStatus.COMPLETED.value),
                ("safeReason", "Completed after the read snapshot."),
                ("resultAvailable", True),
            ),
            status=TaskStatus.COMPLETED,
            result=result,
        )
    )
    await asyncio.sleep(0.05)
    assert not writing.done()

    release_count.set()
    old_snapshot = await reading
    await writing
    await reader.close()
    await writer.close()

    reopened = SQLiteTaskRepository(database)
    new_snapshot = await reopened.get_task(task.task_id)
    assert (
        old_snapshot.status,
        old_snapshot.last_event_id,
        old_snapshot.result,
    ) == (TaskStatus.QUEUED, 1, None)
    assert (
        new_snapshot.status,
        new_snapshot.last_event_id,
        new_snapshot.result,
    ) == (TaskStatus.COMPLETED, 2, result)
    await reopened.close()


async def test_unknown_schema_and_corrupt_values_fail_closed(tmp_path: Path) -> None:
    unsupported_database = tmp_path / "unsupported.sqlite"
    repository = SQLiteTaskRepository(unsupported_database)
    await repository.create_task(title="Safe", objective="Safe objective")
    await repository.close()
    with sqlite3.connect(unsupported_database) as connection:
        connection.execute("PRAGMA user_version = 999")

    unsupported = SQLiteTaskRepository(unsupported_database)
    with pytest.raises(SQLiteTaskRepositorySchemaError, match="unsupported"):
        await unsupported.list_tasks()

    corrupt_database = tmp_path / "corrupt.sqlite"
    corrupt = SQLiteTaskRepository(corrupt_database)
    task = await corrupt.create_task(title="Safe", objective="Safe objective")
    await corrupt.close()
    with sqlite3.connect(corrupt_database) as connection:
        connection.execute(
            "UPDATE events SET name = 'unknown.event' WHERE task_id = ? AND event_id = 1",
            (task.task_id,),
        )

    unreadable = SQLiteTaskRepository(corrupt_database)
    with pytest.raises(SQLiteTaskRepositoryDataError, match="event name"):
        await unreadable.get_task(task.task_id)


@pytest.mark.parametrize(
    "corrupt_references",
    [
        json.dumps([""], ensure_ascii=False, separators=(",", ":"), sort_keys=True),
        json.dumps(["x" * 101], ensure_ascii=False, separators=(",", ":"), sort_keys=True),
        json.dumps(
            ["x" * 100] * 700,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ),
    ],
)
async def test_corrupt_plan_evidence_references_fail_safely_without_echo(
    tmp_path: Path,
    corrupt_references: str,
) -> None:
    database = tmp_path / "corrupt-references.sqlite"
    repository = SQLiteTaskRepository(database)
    task = await repository.create_task(title="Plan", objective="Reference bounds")
    await repository.set_plan(
        task.task_id,
        plan=ProposedPlan(
            revision=1,
            title="Bounded references",
            steps=("Keep references bounded.",),
            evidence_refs=("evidence_00000001",),
        ),
        event_name=TaskEventName.PLAN_PROPOSED,
    )
    await repository.close()
    with sqlite3.connect(database) as connection:
        connection.execute(
            "UPDATE tasks SET plan_evidence_refs = ? WHERE task_id = ?",
            (corrupt_references, task.task_id),
        )

    reopened = SQLiteTaskRepository(database)
    with pytest.raises(SQLiteTaskRepositoryDataError) as error:
        await reopened.get_task(task.task_id)
    assert len(str(error.value)) < 100
    assert corrupt_references not in str(error.value)


async def test_same_version_schema_without_constraints_is_rejected(tmp_path: Path) -> None:
    database = tmp_path / "forged.sqlite"
    with sqlite3.connect(database) as connection:
        connection.executescript(
            """
            CREATE TABLE tasks (
                task_number INTEGER,
                task_id TEXT,
                run_id TEXT,
                title TEXT,
                objective TEXT,
                status TEXT,
                pending_interrupt_id TEXT,
                plan_revision INTEGER,
                plan_title TEXT,
                plan_steps TEXT,
                plan_evidence_refs TEXT,
                result TEXT,
                created_at TEXT
            );
            CREATE TABLE events (
                task_id TEXT, event_id INTEGER, name TEXT, data TEXT
            );
            CREATE TABLE evidence (
                task_id TEXT, position INTEGER, evidence_id TEXT, kind TEXT,
                summary TEXT, source TEXT, verified INTEGER
            );
            CREATE TABLE decisions (
                task_id TEXT, interrupt_id TEXT, decision TEXT, response_digest TEXT
            );
            CREATE INDEX events_task_order ON events(task_id, event_id);
            CREATE INDEX evidence_task_order ON evidence(task_id, position);
            PRAGMA application_id = 1146572849;
            PRAGMA user_version = 2;
            """
        )

    repository = SQLiteTaskRepository(database)
    with pytest.raises(SQLiteTaskRepositorySchemaError, match="schema shape"):
        await repository.initialize()


def _seed_v1_database(database: Path) -> None:
    """Create a pre-timestamp (schema v1) database holding one queued task."""

    created_event = sqlite_adapter._encode_event_data(
        (
            ("taskId", "task_00000001"),
            ("runId", "run_00000001"),
            ("status", TaskStatus.QUEUED.value),
        )
    )
    with sqlite3.connect(database) as connection:
        connection.executescript(
            """
            CREATE TABLE tasks (
                task_number INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL UNIQUE,
                run_id TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                objective TEXT NOT NULL,
                status TEXT NOT NULL,
                pending_interrupt_id TEXT,
                plan_revision INTEGER,
                plan_title TEXT,
                plan_steps TEXT,
                plan_evidence_refs TEXT,
                result TEXT
            );
            CREATE TABLE events (
                task_id TEXT NOT NULL,
                event_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                data TEXT NOT NULL,
                PRIMARY KEY (task_id, event_id),
                FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE RESTRICT
            );
            CREATE TABLE evidence (
                task_id TEXT NOT NULL,
                position INTEGER NOT NULL,
                evidence_id TEXT NOT NULL,
                kind TEXT NOT NULL,
                summary TEXT NOT NULL,
                source TEXT NOT NULL,
                verified INTEGER NOT NULL,
                PRIMARY KEY (task_id, position),
                UNIQUE (task_id, evidence_id),
                FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE RESTRICT
            );
            CREATE TABLE decisions (
                task_id TEXT NOT NULL,
                interrupt_id TEXT NOT NULL,
                decision TEXT NOT NULL,
                response_digest TEXT,
                PRIMARY KEY (task_id, interrupt_id),
                FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE RESTRICT
            );
            CREATE INDEX events_task_order ON events(task_id, event_id);
            CREATE INDEX evidence_task_order ON evidence(task_id, position);
            """
        )
        connection.execute(
            """
            INSERT INTO tasks (task_id, run_id, title, objective, status)
            VALUES ('task_00000001', 'run_00000001', ?, ?, ?)
            """,
            ("Legacy task", "Legacy durable objective", TaskStatus.QUEUED.value),
        )
        connection.execute(
            "INSERT INTO events (task_id, event_id, name, data) VALUES (?, 1, ?, ?)",
            ("task_00000001", TaskEventName.TASK_CREATED.value, created_event),
        )
        connection.execute(f"PRAGMA application_id = {sqlite_adapter._APPLICATION_ID}")
        connection.execute("PRAGMA user_version = 1")


async def test_v1_database_migrates_preserving_tasks_without_fabricating_time(
    tmp_path: Path,
) -> None:
    database = tmp_path / "legacy.sqlite"
    _seed_v1_database(database)

    repository = SQLiteTaskRepository(database)
    recovered = await repository.get_task("task_00000001")
    # The pre-timestamp task survives the schema bump; its unknown creation
    # instant stays null rather than being invented.
    assert recovered.created_at is None
    assert recovered.title == "Legacy task"
    assert recovered.status is TaskStatus.QUEUED
    assert recovered.last_event_id == 1

    # Tasks created after the migration still record a real timestamp and
    # continue the identifier sequence past the migrated row.
    fresh = await repository.create_task(title="After", objective="Post-migration objective")
    assert fresh.task_id == "task_00000002"
    assert fresh.created_at is not None
    await repository.close()

    # The migration is durable: the database now reports schema v2 with the
    # appended nullable column, and reopening validates without re-migrating.
    with sqlite3.connect(database) as connection:
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        columns = [str(row[1]) for row in connection.execute("PRAGMA table_info(tasks)")]
    assert version == 2
    assert columns[-1] == "created_at"

    reopened = SQLiteTaskRepository(database)
    listing = await reopened.list_tasks()
    assert [task.task_id for task in listing] == ["task_00000001", "task_00000002"]
    assert listing[0].created_at is None
    assert listing[1].created_at is not None
    await reopened.close()


async def test_raw_response_note_is_never_stored_or_returned(tmp_path: Path) -> None:
    database = tmp_path / "tasks.sqlite"
    repository = SQLiteTaskRepository(database)
    task_id, _, interrupt_id, _ = await _waiting_task(repository)
    raw_note = "raw reviewer note that must never persist"
    digest = hashlib.sha256(raw_note.encode()).hexdigest()

    await repository.record_decision(
        task_id,
        interrupt_id=interrupt_id,
        decision=DecisionValue.RESPOND,
        comment_provided=True,
        response_digest=digest,
    )
    events = await repository.events_after(task_id, 0)
    await repository.close()

    assert raw_note.encode() not in database.read_bytes()
    assert raw_note not in repr(await SQLiteTaskRepository(database).get_task(task_id))
    assert raw_note not in repr(events)
    with sqlite3.connect(database) as connection:
        row = connection.execute(
            "SELECT decision, response_digest FROM decisions WHERE task_id = ?",
            (task_id,),
        ).fetchone()
        columns = {
            item[1] for item in connection.execute("PRAGMA table_info(decisions)").fetchall()
        }
    assert row == (DecisionValue.RESPOND.value, digest)
    assert columns == {"task_id", "interrupt_id", "decision", "response_digest"}


async def test_closed_repository_and_unsafe_paths_fail_safely(tmp_path: Path) -> None:
    with pytest.raises(SQLiteTaskRepositoryPathError, match="absolute"):
        SQLiteTaskRepository(Path("relative.sqlite"))

    target = tmp_path / "target.sqlite"
    target.touch()
    link = tmp_path / "linked.sqlite"
    link.symlink_to(target)
    with pytest.raises(SQLiteTaskRepositoryPathError, match="unsafe"):
        SQLiteTaskRepository(link)

    repository = SQLiteTaskRepository(tmp_path / "tasks.sqlite")
    await repository.initialize()
    await repository.close()
    with pytest.raises(SQLiteTaskRepositoryClosedError, match="closed"):
        await repository.list_tasks()

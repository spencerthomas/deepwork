"""Repository parity for atomic ordered plan decisions."""

from __future__ import annotations

import hashlib
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import pytest

from deepwork_api.adapters.fixture import InMemoryTaskRepository
from deepwork_api.adapters.persistence import SQLiteTaskRepository
from deepwork_api.application import DeterministicFixtureRunner, LocalAgentServerRunner, TaskService
from deepwork_api.domain import (
    DecisionBatchUnsupportedError,
    DecisionBatchVersionStaleError,
    DecisionConflictError,
    DecisionType,
    OrderedDecision,
    ProposedPlan,
    TaskEventName,
    TaskStatus,
)
from deepwork_api.ports import TaskRepository


@asynccontextmanager
async def _repository(kind: str, tmp_path: Path) -> AsyncIterator[TaskRepository]:
    repository: TaskRepository
    if kind == "memory":
        repository = InMemoryTaskRepository()
    else:
        repository = SQLiteTaskRepository(tmp_path / "batch.sqlite")
    try:
        yield repository
    finally:
        if isinstance(repository, SQLiteTaskRepository):
            await repository.close()


async def _waiting(repository: TaskRepository) -> tuple[str, str]:
    task = await repository.create_task(title="Atomic batch", objective="Atomic batch")
    interrupt_id = "interrupt_00000001"
    await repository.set_plan(
        task.task_id,
        plan=ProposedPlan(
            revision=1,
            title="Bounded plan",
            steps=("First step", "Second step"),
            evidence_refs=(),
        ),
        event_name=TaskEventName.PLAN_PROPOSED,
    )
    await repository.append_event(
        task.task_id,
        name=TaskEventName.INTERRUPT_REQUESTED,
        data=(
            ("interruptId", interrupt_id),
            ("question", "Approve?"),
            ("decisions", ("approve", "reject")),
            ("planRevision", 1),
        ),
        status=TaskStatus.WAITING_APPROVAL,
        pending_interrupt_id=interrupt_id,
    )
    return task.task_id, interrupt_id


@pytest.mark.parametrize("kind", ["memory", "sqlite"])
async def test_batch_edit_and_decision_commit_or_fail_together(kind: str, tmp_path: Path) -> None:
    async with _repository(kind, tmp_path) as repository:
        task_id, interrupt_id = await _waiting(repository)
        before = await repository.get_task(task_id)
        events_before = await repository.events_after(task_id, 0)

        with pytest.raises(DecisionBatchVersionStaleError):
            await repository.record_decision_batch(
                task_id,
                interrupt_id=interrupt_id,
                expected_revision=2,
                decision_types=(DecisionType.APPROVE, DecisionType.EDIT),
                request_fingerprint=hashlib.sha256(b"stale").hexdigest(),
                edited_steps=("First step", "Must not partially land"),
            )

        assert await repository.get_task(task_id) == before
        assert await repository.events_after(task_id, 0) == events_before

        digest = hashlib.sha256(b"accepted vector").hexdigest()
        first = await repository.record_decision_batch(
            task_id,
            interrupt_id=interrupt_id,
            expected_revision=1,
            decision_types=(DecisionType.APPROVE, DecisionType.EDIT),
            request_fingerprint=digest,
            edited_steps=("First step", "Edited second step"),
        )
        duplicate = await repository.record_decision_batch(
            task_id,
            interrupt_id=interrupt_id,
            expected_revision=1,
            decision_types=(DecisionType.APPROVE, DecisionType.EDIT),
            request_fingerprint=digest,
            edited_steps=("First step", "Edited second step"),
        )
        with pytest.raises(DecisionConflictError):
            await repository.record_decision_batch(
                task_id,
                interrupt_id=interrupt_id,
                expected_revision=1,
                decision_types=(DecisionType.REJECT, DecisionType.APPROVE),
                request_fingerprint=hashlib.sha256(b"conflict").hexdigest(),
                edited_steps=("First step", "Edited second step"),
            )

        accepted = await repository.get_task(task_id)
        events = await repository.events_after(task_id, 0)
        assert first.duplicate is False
        assert duplicate.duplicate is True
        assert accepted.proposed_plan is not None
        assert accepted.proposed_plan.revision == 2
        assert accepted.proposed_plan.steps == ("First step", "Edited second step")
        assert [event.name for event in events].count(TaskEventName.DECISION_RECORDED) == 1


async def test_sqlite_batch_request_fingerprint_survives_reopen(tmp_path: Path) -> None:
    database_path = tmp_path / "batch-replay.sqlite"
    fingerprint = hashlib.sha256(b"same idempotency key and vector").hexdigest()
    conflicting_fingerprint = hashlib.sha256(b"same key, different vector").hexdigest()
    repository = SQLiteTaskRepository(database_path)
    task_id, interrupt_id = await _waiting(repository)
    await repository.record_decision_batch(
        task_id,
        interrupt_id=interrupt_id,
        expected_revision=1,
        decision_types=(DecisionType.APPROVE, DecisionType.APPROVE),
        request_fingerprint=fingerprint,
        edited_steps=("First step", "Second step"),
    )
    await repository.close()

    reopened = SQLiteTaskRepository(database_path)
    try:
        duplicate = await reopened.record_decision_batch(
            task_id,
            interrupt_id=interrupt_id,
            expected_revision=1,
            decision_types=(DecisionType.APPROVE, DecisionType.APPROVE),
            request_fingerprint=fingerprint,
            edited_steps=("First step", "Second step"),
        )
        assert duplicate.duplicate is True
        with pytest.raises(DecisionConflictError):
            await reopened.record_decision_batch(
                task_id,
                interrupt_id=interrupt_id,
                expected_revision=1,
                decision_types=(DecisionType.REJECT, DecisionType.APPROVE),
                request_fingerprint=conflicting_fingerprint,
                edited_steps=("First step", "Second step"),
            )
    finally:
        await reopened.close()


async def test_sqlite_service_rejects_changed_version_replay_after_reopen(tmp_path: Path) -> None:
    database_path = tmp_path / "batch-version-replay.sqlite"
    repository = SQLiteTaskRepository(database_path)
    task_id, interrupt_id = await _waiting(repository)
    service = TaskService(repository, DeterministicFixtureRunner(repository))
    await service.record_decision_batch(
        task_id,
        interrupt_id=interrupt_id,
        expected_version="1",
        idempotency_key="same-replay-key",
        decisions=(OrderedDecision(DecisionType.APPROVE), OrderedDecision(DecisionType.APPROVE)),
    )
    await repository.close()

    reopened = SQLiteTaskRepository(database_path)
    reopened_service = TaskService(reopened, DeterministicFixtureRunner(reopened))
    try:
        with pytest.raises(DecisionConflictError):
            await reopened_service.record_decision_batch(
                task_id,
                interrupt_id=interrupt_id,
                expected_version="2",
                idempotency_key="same-replay-key",
                decisions=(
                    OrderedDecision(DecisionType.APPROVE),
                    OrderedDecision(DecisionType.APPROVE),
                ),
            )
    finally:
        await reopened.close()


async def test_local_runner_rejects_batch_endpoint_and_preserves_legacy_decisions() -> None:
    repository = InMemoryTaskRepository()
    task = await repository.create_task(title="Local singleton", objective="Local singleton")
    interrupt_id = "interrupt_00000001"
    await repository.set_plan(
        task.task_id,
        plan=ProposedPlan(
            revision=1,
            title="One step",
            steps=("Only step",),
            evidence_refs=(),
        ),
        event_name=TaskEventName.PLAN_PROPOSED,
    )
    await repository.append_event(
        task.task_id,
        name=TaskEventName.INTERRUPT_REQUESTED,
        data=(
            ("interruptId", interrupt_id),
            ("question", "Approve?"),
            ("decisions", ("approve", "reject")),
            ("planRevision", 1),
        ),
        status=TaskStatus.WAITING_APPROVAL,
        pending_interrupt_id=interrupt_id,
    )
    runner = LocalAgentServerRunner(repository, source=None)  # type: ignore[arg-type]
    service = TaskService(repository, runner)
    for decision in (
        OrderedDecision(DecisionType.APPROVE),
        OrderedDecision(DecisionType.RESPOND, message="Clarification"),
        OrderedDecision(
            DecisionType.EDIT,
            edited_action_name="execute_plan_step",
            edited_position=1,
            edited_text="Edited step",
        ),
    ):
        with pytest.raises(DecisionBatchUnsupportedError):
            await service.record_decision_batch(
                task.task_id,
                interrupt_id=interrupt_id,
                expected_version="1",
                idempotency_key="local-singleton-unsupported",
                decisions=(decision,),
            )

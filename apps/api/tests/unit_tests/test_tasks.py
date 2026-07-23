"""Unit tests for safe local task semantics."""

import asyncio

import pytest

from deepwork_api.adapters.fixture import InMemoryTaskRepository
from deepwork_api.application.tasks import sanitize_objective
from deepwork_api.domain import (
    DecisionConflictError,
    DecisionValue,
    TaskEventName,
    TaskStatus,
)


def test_objective_is_preserved_bounded_and_secret_redacted() -> None:
    prompt = "Deploy\nwith token=fixture-secret-value and sk-example-secret-shaped-input"

    objective = sanitize_objective(prompt)

    assert objective == "Deploy\nwith [redacted] and [redacted]"
    assert (
        sanitize_objective(
            "Inspect -----BEGIN PRIVATE KEY-----\nraw-private-material\n"
            "-----END PRIVATE KEY----- safely"
        )
        == "Inspect [redacted] safely"
    )
    assert sanitize_objective("x" * 8_000) == "x" * 8_000
    with pytest.raises(ValueError, match="shared request bound"):
        sanitize_objective("x" * 8_001)


async def test_repository_preserves_order_and_monotonic_events() -> None:
    repository = InMemoryTaskRepository()
    first = await repository.create_task(
        title="First safe objective",
        objective="First safe objective",
    )
    second = await repository.create_task(
        title="Second safe objective",
        objective="Second safe objective",
    )

    event = await repository.append_event(
        first.task_id,
        name=TaskEventName.RUN_STARTED,
        data=(("runId", first.run_id), ("status", TaskStatus.RUNNING.value)),
        status=TaskStatus.RUNNING,
    )

    assert event.event_id == 2
    assert [task.task_id for task in await repository.list_tasks()] == [
        first.task_id,
        second.task_id,
    ]
    assert (await repository.events_after(first.task_id, 1)) == (event,)


async def test_repository_decision_wait_and_idempotency() -> None:
    repository = InMemoryTaskRepository()
    task = await repository.create_task(
        title="Safe objective",
        objective="Safe objective",
    )
    interrupt_id = "interrupt_00000001"
    await repository.append_event(
        task.task_id,
        name=TaskEventName.INTERRUPT_REQUESTED,
        data=(
            ("interruptId", interrupt_id),
            ("question", "Approve?"),
            ("decisions", ("approve", "reject")),
        ),
        status=TaskStatus.WAITING_APPROVAL,
        pending_interrupt_id=interrupt_id,
    )
    waiter = asyncio.create_task(repository.wait_for_decision(task.task_id, interrupt_id))

    first = await repository.record_decision(
        task.task_id,
        interrupt_id=interrupt_id,
        decision=DecisionValue.APPROVE,
        comment_provided=False,
        response_digest=None,
    )
    duplicate = await repository.record_decision(
        task.task_id,
        interrupt_id=interrupt_id,
        decision=DecisionValue.APPROVE,
        comment_provided=True,
        response_digest=None,
    )

    assert await waiter is DecisionValue.APPROVE
    assert first.duplicate is False
    assert duplicate.duplicate is True
    assert (await repository.get_task(task.task_id)).last_event_id == 3
    with pytest.raises(DecisionConflictError):
        await repository.record_decision(
            task.task_id,
            interrupt_id=interrupt_id,
            decision=DecisionValue.REJECT,
            comment_provided=False,
            response_digest=None,
        )

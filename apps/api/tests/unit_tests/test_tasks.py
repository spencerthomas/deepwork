"""Unit tests for safe local task semantics."""

import asyncio
from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

from deepwork_api.adapters.fixture import InMemoryTaskRepository
from deepwork_api.application.tasks import sanitize_objective
from deepwork_api.contracts.tasks import (
    InterruptRequestedEventData,
    PendingInterruptResponse,
    PlanProposedEventData,
    PlanUpdateRequest,
    ProposedPlanResponse,
    TaskCreateRequest,
    TaskResultResponse,
)
from deepwork_api.domain import (
    MAX_PLAN_REVISION,
    MAX_PLAN_STEPS,
    DecisionConflictError,
    DecisionValue,
    PlanRevisionConflictError,
    ProposedPlan,
    TaskAlreadyResolvedError,
    TaskEventName,
    TaskSnapshot,
    TaskStatus,
)


def _plan_proposed_payload(step_count: int) -> dict[str, Any]:
    return {
        "title": "Bounded plan",
        "steps": [f"Step {index}" for index in range(step_count)],
        "revision": 1,
        "evidenceRefs": [],
        "evidenceClass": "fixture",
    }


def test_plan_proposed_event_steps_use_the_shared_max_plan_steps_bound() -> None:
    # The proposed-plan event contract must bound steps by the shared
    # MAX_PLAN_STEPS constant, not a hardcoded literal that could silently
    # drift from the domain and the other wire models.
    at_bound = PlanProposedEventData.model_validate(_plan_proposed_payload(MAX_PLAN_STEPS))
    assert len(at_bound.steps) == MAX_PLAN_STEPS
    with pytest.raises(ValidationError):
        PlanProposedEventData.model_validate(_plan_proposed_payload(MAX_PLAN_STEPS + 1))


def _completed_snapshot(result: str | None) -> TaskSnapshot:
    return TaskSnapshot(
        task_id="task_00000001",
        run_id="run_00000001",
        created_at="2026-01-01T00:00:00+00:00",
        title="Completed task",
        objective="Completed task",
        status=TaskStatus.COMPLETED,
        last_event_id=1,
        pending_interrupt_id=None,
        proposed_plan=None,
        evidence=(),
        result=result,
    )


def test_task_result_response_rejects_empty_result_as_unavailable() -> None:
    # An empty (not just None) completed result must raise the sanitized
    # domain error, not a Pydantic min_length ValidationError (→ 500).
    for empty in (None, ""):
        with pytest.raises(ValueError, match="task result is unavailable"):
            TaskResultResponse.from_domain(_completed_snapshot(empty))


def test_task_result_response_maps_a_present_result() -> None:
    response = TaskResultResponse.from_domain(_completed_snapshot("A useful brief."))
    assert response.result == "A useful brief."
    assert response.status == "completed"


@pytest.mark.parametrize("bad", ["a\x7fb", "a\x80b", "a\x85b", "a\x9fb", "a\x00b", "a\x1fb"])
def test_task_prompt_rejects_c0_del_and_c1_controls(bad: str) -> None:
    with pytest.raises(ValidationError):
        TaskCreateRequest.model_validate({"prompt": bad})


def test_task_prompt_accepts_tab_newline_carriage_return_and_emoji() -> None:
    request = TaskCreateRequest.model_validate({"prompt": "line1\r\n\tline2 🧭 café"})
    assert request.prompt == "line1\r\n\tline2 🧭 café"


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


def _revision_wire_cases(revision: object) -> tuple[tuple[type[BaseModel], dict[str, Any]], ...]:
    return (
        (
            PendingInterruptResponse,
            {
                "interruptId": "interrupt_00000001",
                "planRevision": revision,
            },
        ),
        (
            ProposedPlanResponse,
            {
                "revision": revision,
                "title": "Bounded plan",
                "steps": ["Inspect input"],
                "evidenceRefs": [],
            },
        ),
        (
            PlanUpdateRequest,
            {
                "interruptId": "interrupt_00000001",
                "expectedRevision": revision,
                "steps": ["Inspect input"],
            },
        ),
        (
            PlanProposedEventData,
            {
                "title": "Bounded plan",
                "steps": ["Inspect input"],
                "revision": revision,
                "evidenceRefs": [],
                "evidenceClass": "fixture",
            },
        ),
        (
            InterruptRequestedEventData,
            {
                "interruptId": "interrupt_00000001",
                "question": "Approve?",
                "decisions": ["approve", "reject", "respond"],
                "planRevision": revision,
            },
        ),
    )


def test_plan_revision_shared_bound_accepts_exact_maximum_everywhere() -> None:
    assert MAX_PLAN_REVISION == 2_147_483_647
    plan = ProposedPlan(
        revision=MAX_PLAN_REVISION,
        title="Bounded plan",
        steps=("Inspect input",),
        evidence_refs=(),
    )

    assert plan.revision == MAX_PLAN_REVISION
    for model, payload in _revision_wire_cases(MAX_PLAN_REVISION):
        validated = model.model_validate(payload)
        assert MAX_PLAN_REVISION in (
            getattr(validated, "revision", None),
            getattr(validated, "plan_revision", None),
            getattr(validated, "expected_revision", None),
        )


@pytest.mark.parametrize(
    "revision",
    [MAX_PLAN_REVISION + 1, 0, -1, True, "1", 1.0],
)
def test_plan_revision_shared_bound_rejects_invalid_domain_and_wire_types(
    revision: object,
) -> None:
    with pytest.raises(ValueError, match="shared bound"):
        ProposedPlan(
            revision=revision,  # type: ignore[arg-type]
            title="Bounded plan",
            steps=("Inspect input",),
            evidence_refs=(),
        )

    for model, payload in _revision_wire_cases(revision):
        with pytest.raises(ValidationError):
            model.model_validate(payload)


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


async def test_in_memory_cancel_terminates_a_running_task_and_wakes_waiters() -> None:
    repository = InMemoryTaskRepository()
    task = await repository.create_task(title="Stop me", objective="Stop me")
    await repository.append_event(
        task.task_id,
        name=TaskEventName.RUN_STARTED,
        data=(("runId", task.run_id), ("status", TaskStatus.RUNNING.value)),
        status=TaskStatus.RUNNING,
    )
    event_waiter = asyncio.create_task(repository.wait_for_events(task.task_id, 2))
    await asyncio.sleep(0)

    record = await repository.cancel_task(task.task_id)
    assert record.duplicate is False
    await asyncio.wait_for(event_waiter, timeout=1)

    cancelled = await repository.get_task(task.task_id)
    assert cancelled.status is TaskStatus.CANCELLED
    assert cancelled.status.is_terminal
    assert cancelled.result is None
    completion = (await repository.events_after(task.task_id, 2))[0]
    assert completion.name is TaskEventName.RUN_COMPLETED
    assert dict(completion.data)["status"] == TaskStatus.CANCELLED.value
    assert dict(completion.data)["resultAvailable"] is False

    # Cancelling again is an idempotent no-op; a resolved task is refused.
    assert (await repository.cancel_task(task.task_id)).duplicate is True


async def test_in_memory_cancel_refuses_a_rejected_task() -> None:
    repository = InMemoryTaskRepository()
    task = await repository.create_task(title="Already rejected", objective="Already rejected")
    await repository.append_event(
        task.task_id,
        name=TaskEventName.RUN_COMPLETED,
        data=(
            ("runId", task.run_id),
            ("status", TaskStatus.REJECTED.value),
            ("safeReason", "The plan was rejected."),
            ("resultAvailable", False),
        ),
        status=TaskStatus.REJECTED,
        clear_pending_interrupt=True,
    )
    with pytest.raises(TaskAlreadyResolvedError):
        await repository.cancel_task(task.task_id)


async def test_repository_rejects_plan_revision_max_without_mutation() -> None:
    repository = InMemoryTaskRepository()
    task = await repository.create_task(
        title="Maximum plan revision",
        objective="Maximum plan revision",
    )
    interrupt_id = "interrupt_00000001"
    plan = ProposedPlan(
        revision=MAX_PLAN_REVISION,
        title="Bounded plan",
        steps=("Inspect input",),
        evidence_refs=(),
    )
    await repository.set_plan(
        task.task_id,
        plan=plan,
        event_name=TaskEventName.PLAN_PROPOSED,
    )
    await repository.append_event(
        task.task_id,
        name=TaskEventName.INTERRUPT_REQUESTED,
        data=(
            ("interruptId", interrupt_id),
            ("question", "Approve?"),
            ("decisions", ("approve", "reject", "respond")),
            ("planRevision", MAX_PLAN_REVISION),
        ),
        status=TaskStatus.WAITING_APPROVAL,
        pending_interrupt_id=interrupt_id,
    )
    before = await repository.get_task(task.task_id)
    events_before = await repository.events_after(task.task_id, 0)

    with pytest.raises(PlanRevisionConflictError):
        await repository.update_plan(
            task.task_id,
            interrupt_id=interrupt_id,
            expected_revision=MAX_PLAN_REVISION,
            steps=("Mutated step",),
        )

    assert await repository.get_task(task.task_id) == before
    assert await repository.events_after(task.task_id, 0) == events_before


@pytest.mark.parametrize(
    "expected_revision",
    [True, 1.0, "1", 0, -1, MAX_PLAN_REVISION + 1],
)
async def test_repository_rejects_invalid_revision_type_without_mutation(
    expected_revision: object,
) -> None:
    repository = InMemoryTaskRepository()
    task = await repository.create_task(
        title="Strict revision",
        objective="Strict revision",
    )
    interrupt_id = "interrupt_00000001"
    await repository.set_plan(
        task.task_id,
        plan=ProposedPlan(
            revision=1,
            title="Bounded plan",
            steps=("Inspect input",),
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
            ("decisions", ("approve", "reject", "respond")),
            ("planRevision", 1),
        ),
        status=TaskStatus.WAITING_APPROVAL,
        pending_interrupt_id=interrupt_id,
    )
    before = await repository.get_task(task.task_id)
    events_before = await repository.events_after(task.task_id, 0)

    with pytest.raises(PlanRevisionConflictError):
        await repository.update_plan(
            task.task_id,
            interrupt_id=interrupt_id,
            expected_revision=expected_revision,  # type: ignore[arg-type]
            steps=("Must not mutate",),
        )

    assert await repository.get_task(task.task_id) == before
    assert await repository.events_after(task.task_id, 0) == events_before


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

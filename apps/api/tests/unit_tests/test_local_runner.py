"""Regression coverage for local Agent Server runner failure boundaries."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass, replace
from types import SimpleNamespace

import pytest

from deepwork_api.adapters.fixture.tasks import InMemoryTaskRepository
from deepwork_api.application.local_runner import LocalAgentServerRunner, LocalRun
from deepwork_api.application.tasks import TaskService
from deepwork_api.domain import (
    DecisionValue,
    ProposedPlan,
    TaskEventName,
    TaskSnapshot,
    TaskStatus,
)


@dataclass(frozen=True)
class _Run:
    thread_id: str = "thread_1"
    run_id: str = "run_1"


@dataclass(frozen=True)
class _PlanUpdate(_Run):
    interrupt_id: str = "interrupt_2"
    plan_revision: int = 2


@dataclass(frozen=True)
class _Interrupt:
    interrupt_id: str = "interrupt_1"
    plan: tuple[str, ...] = ("First step",)
    plan_revision: int = 1


@dataclass(frozen=True)
class _State:
    status: str | None = "planned"
    plan: tuple[str, ...] = ("First step",)
    plan_revision: int | None = 1
    final_answer: str | None = None
    interrupt: _Interrupt | None = _Interrupt()


class _Source:
    def __init__(self, *, events: tuple[object, ...] = ()) -> None:
        self.events = events
        self.resume_comment: str | None = None
        self.state_reads = 0

    async def start(self, objective: str) -> _Run:
        return _Run()

    async def get_state(self, thread_id: str) -> _State:
        self.state_reads += 1
        return _State()

    async def update_plan(
        self,
        thread_id: str,
        *,
        interrupt_id: str,
        expected_revision: int,
        steps: Sequence[str],
    ) -> _PlanUpdate:
        return _PlanUpdate()

    async def resume(
        self,
        thread_id: str,
        *,
        interrupt_id: str,
        decision: str,
        comment: str | None = None,
    ) -> _Run:
        if comment is not None:
            self.resume_comment = comment
        return _Run(run_id="run_2")

    async def stream(self, run: LocalRun) -> AsyncIterator[object]:
        for event in self.events:
            yield event


async def _paused_task(repository: InMemoryTaskRepository) -> TaskSnapshot:
    task = await repository.create_task(title="Task", objective="Objective")
    await repository.set_plan(
        task.task_id,
        plan=ProposedPlan(1, "Plan", ("First step",), ()),
        event_name=TaskEventName.PLAN_PROPOSED,
    )
    await repository.append_event(
        task.task_id,
        name=TaskEventName.INTERRUPT_REQUESTED,
        data=(("interruptId", "interrupt_1"),),
        status=TaskStatus.WAITING_APPROVAL,
        pending_interrupt_id="interrupt_1",
    )
    return await repository.get_task(task.task_id)


@pytest.mark.asyncio
async def test_confirmed_plan_update_reconciles_without_second_state_read() -> None:
    repository = InMemoryTaskRepository()
    source = _Source()
    runner = LocalAgentServerRunner(repository, source)
    task = await _paused_task(repository)
    runner._threads[task.task_id] = "thread_1"

    update = await runner.update_plan(
        task,
        interrupt_id="interrupt_1",
        expected_revision=1,
        steps=("Updated step",),
    )

    current = await repository.get_task(task.task_id)
    assert source.state_reads == 0
    assert update.interrupt_id == "interrupt_2"
    assert current.pending_interrupt_id == "interrupt_2"
    assert current.proposed_plan is not None and current.proposed_plan.revision == 2
    await runner.close()


@pytest.mark.asyncio
async def test_error_stream_event_fails_instead_of_completing() -> None:
    repository = InMemoryTaskRepository()
    runner = LocalAgentServerRunner(repository, _Source(events=(SimpleNamespace(kind="error"),)))
    task = await repository.create_task(title="Task", objective="Objective", run_id="run_1")

    await runner._follow(task, _Run())

    assert (await repository.get_task(task.task_id)).status is TaskStatus.FAILED


@pytest.mark.asyncio
async def test_nonterminal_source_state_fails_instead_of_completing() -> None:
    repository = InMemoryTaskRepository()
    source = _Source()

    async def nonterminal_state(thread_id: str) -> _State:
        source.state_reads += 1
        return replace(_State(), interrupt=None)

    source.get_state = nonterminal_state  # type: ignore[method-assign]
    runner = LocalAgentServerRunner(repository, source)
    task = await repository.create_task(title="Task", objective="Objective", run_id="run_1")

    await runner._follow(task, _Run())

    assert (await repository.get_task(task.task_id)).status is TaskStatus.FAILED


@pytest.mark.asyncio
async def test_response_comment_is_forwarded_to_source_resume() -> None:
    repository = InMemoryTaskRepository()
    source = _Source()
    runner = LocalAgentServerRunner(repository, source)
    service = TaskService(repository, runner)
    task = await _paused_task(repository)

    follower = asyncio.create_task(runner._follow(task, _Run()))
    for _ in range(20):
        if (await repository.get_task(task.task_id)).status is TaskStatus.WAITING_APPROVAL:
            break
        await asyncio.sleep(0)
    await service.record_decision(
        task.task_id,
        interrupt_id="interrupt_1",
        decision=DecisionValue.RESPOND,
        comment="Please make the plan more concise.",
    )
    await follower

    assert source.resume_comment == "Please make the plan more concise."
    await runner.close()

"""Application mapping for the explicitly configured loopback source."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass, field
from typing import Protocol

from deepwork_api.domain import (
    DecisionRecord,
    DecisionValue,
class LocalPlanUpdate(LocalRun, Protocol):
    """Confirmed source checkpoint after an accepted plan edit."""

    interrupt_id: str
    plan_revision: int


    ) -> LocalPlanUpdate: ...
    _review_comments: dict[tuple[str, str], str] = field(default_factory=dict, init=False)
        if updated.interrupt_id == interrupt_id or updated.plan_revision != expected_revision + 1:
        # The source has confirmed the edit at this point.  Reconcile the known
        # checkpoint before doing any further source I/O, so the old interrupt is
        # never advertised after the source has advanced it.
        if record.plan.revision != updated.plan_revision:
            raise RuntimeError("local source plan revision does not match the task")
                ("interruptId", updated.interrupt_id),
                ("planRevision", updated.plan_revision),
            pending_interrupt_id=updated.interrupt_id,
        active = self._tasks.pop(task.task_id, None)
        if active is not None:
            active.cancel()
            await asyncio.gather(active, return_exceptions=True)
        return PlanUpdateRecord(task.task_id, updated.run_id, updated.interrupt_id, record.plan)

    async def record_decision(
        self,
        task_id: str,
        *,
        interrupt_id: str,
        decision: DecisionValue,
        comment: str | None,
        comment_provided: bool,
        response_digest: str | None,
    ) -> DecisionRecord:
        """Retain a response comment only until its source resume is sent."""

        key = (task_id, interrupt_id)
        if decision is DecisionValue.RESPOND and comment is not None:
            self._review_comments[key] = comment
        try:
            record = await self.repository.record_decision(
                task_id,
                interrupt_id=interrupt_id,
                decision=decision,
                comment_provided=comment_provided,
                response_digest=response_digest,
            )
        except Exception:
            self._review_comments.pop(key, None)
            raise
        return record
            async for event in self.source.stream(run):
                if getattr(event, "kind", None) == "error":
                    raise RuntimeError("local source reported a run error")
                key = (task.task_id, state.interrupt.interrupt_id)
                    comment=self._review_comments.pop(key, None),
        if state.status not in {"completed", "rejected"}:
            raise RuntimeError("local source did not report a terminal status")
    """The narrow source-owned identity required by the application."""

    thread_id: str
    run_id: str


class LocalPlanUpdate(LocalRun, Protocol):
    """Confirmed source checkpoint after an accepted plan edit."""

    interrupt_id: str
    plan_revision: int


class LocalInterruptValue(Protocol):
    interrupt_id: str
    plan: tuple[str, ...]
    plan_revision: int


class LocalState(Protocol):
    status: str | None
    plan: tuple[str, ...]
    plan_revision: int | None
    final_answer: str | None
    interrupt: LocalInterruptValue | None


class LocalSource(Protocol):
    async def start(self, objective: str) -> LocalRun: ...
    async def get_state(self, thread_id: str) -> LocalState: ...
    async def resume(
        self, thread_id: str, *, interrupt_id: str, decision: str, comment: str | None = None
    ) -> LocalRun: ...
    async def update_plan(
        self, thread_id: str, *, interrupt_id: str, expected_revision: int, steps: Sequence[str]
    ) -> LocalPlanUpdate: ...
    async def stream(self, run: LocalRun) -> AsyncIterator[object]: ...


@dataclass(slots=True)
class LocalAgentServerRunner:
    """Project source-authoritative state into the existing normalized task API."""

    repository: TaskRepository
    source: LocalSource
    _threads: dict[str, str] = field(default_factory=dict, init=False)
    _tasks: dict[str, asyncio.Task[None]] = field(default_factory=dict, init=False)
    _review_comments: dict[tuple[str, str], str] = field(default_factory=dict, init=False)

    async def create(self, *, title: str, objective: str) -> TaskSnapshot:
        try:
            run = await self.source.start(objective)
        except Exception:
            raise TaskSourceUnavailableError from None
        task = await self.repository.create_task(
            title=title, objective=objective, run_id=run.run_id
        )
        self._threads[task.task_id] = run.thread_id
        self.start(task, run)
        return task

    def start(self, task: TaskSnapshot, run: LocalRun) -> None:
        if task.task_id in self._tasks:
            return
        background = asyncio.create_task(
            self._follow(task, run), name=f"deepwork-local-{task.task_id}"
        )
        self._tasks[task.task_id] = background
        background.add_done_callback(lambda _: self._tasks.pop(task.task_id, None))

    async def close(self) -> None:
        active = tuple(self._tasks.values())
        for task in active:
            task.cancel()
        if active:
            await asyncio.gather(*active, return_exceptions=True)
        self._tasks.clear()

    async def update_plan(
        self,
        task: TaskSnapshot,
        *,
        interrupt_id: str,
        expected_revision: int,
        steps: tuple[str, ...],
    ) -> PlanUpdateRecord:
        thread_id = self._threads.get(task.task_id)
        if thread_id is None:
            raise RuntimeError("local source thread is unavailable")
        try:
            updated = await self.source.update_plan(
                thread_id,
                interrupt_id=interrupt_id,
                expected_revision=expected_revision,
                steps=steps,
            )
        except Exception:
            raise TaskSourceUnavailableError from None
        if updated.interrupt_id == interrupt_id or updated.plan_revision != expected_revision + 1:
            raise RuntimeError("local source did not provide a fresh plan interrupt")
        # The source has confirmed the edit at this point.  Reconcile the known
        # checkpoint before doing any further source I/O, so the old interrupt is
        # never advertised after the source has advanced it.
        record = await self.repository.update_plan(
            task.task_id,
            interrupt_id=interrupt_id,
            expected_revision=expected_revision,
            steps=steps,
        )
        if record.plan.revision != updated.plan_revision:
            raise RuntimeError("local source plan revision does not match the task")
        await self.repository.append_event(
            task.task_id,
            name=TaskEventName.INTERRUPT_REQUESTED,
            data=(
                ("interruptId", updated.interrupt_id),
                ("question", "Approve the updated plan?"),
                ("decisions", ("approve", "reject", "respond")),
                ("planRevision", updated.plan_revision),
            ),
            status=TaskStatus.WAITING_APPROVAL,
            pending_interrupt_id=updated.interrupt_id,
        )
        active = self._tasks.pop(task.task_id, None)
        if active is not None:
            active.cancel()
            await asyncio.gather(active, return_exceptions=True)
        self.start(await self.repository.get_task(task.task_id), updated)
        return PlanUpdateRecord(task.task_id, updated.run_id, updated.interrupt_id, record.plan)

    async def record_decision(
        self,
        task_id: str,
        *,
        interrupt_id: str,
        decision: DecisionValue,
        comment: str | None,
        comment_provided: bool,
        response_digest: str | None,
    ) -> DecisionRecord:
        """Retain a response comment only until its source resume is sent."""

        key = (task_id, interrupt_id)
        if decision is DecisionValue.RESPOND and comment is not None:
            self._review_comments[key] = comment
        try:
            record = await self.repository.record_decision(
                task_id,
                interrupt_id=interrupt_id,
                decision=decision,
                comment_provided=comment_provided,
                response_digest=response_digest,
            )
        except Exception:
            self._review_comments.pop(key, None)
            raise
        return record

    async def _follow(self, task: TaskSnapshot, run: LocalRun) -> None:
        try:
            await self.repository.append_event(
                task.task_id,
                name=TaskEventName.RUN_STARTED,
                data=(("runId", run.run_id), ("status", "running")),
                status=TaskStatus.RUNNING,
            )
            async for event in self.source.stream(run):
                if getattr(event, "kind", None) == "error":
                    raise RuntimeError("local source reported a run error")
                await self.repository.append_event(
                    task.task_id,
                    name=TaskEventName.CONTENT_DELTA,
                    data=(
                        ("text", "Local Agent Server progress received."),
                        ("evidenceClass", "fixture"),
                    ),
                )
            state = await self.source.get_state(run.thread_id)
            if state.interrupt is not None:
                await self._pause(task, state)
                decision = await self.repository.wait_for_decision(
                    task.task_id, state.interrupt.interrupt_id
                )
                key = (task.task_id, state.interrupt.interrupt_id)
                next_run = await self.source.resume(
                    run.thread_id,
                    interrupt_id=state.interrupt.interrupt_id,
                    decision=decision.value,
                    comment=self._review_comments.pop(key, None),
                )
                self._tasks.pop(task.task_id, None)
                self.start(await self.repository.get_task(task.task_id), next_run)
                return
            await self._complete(task, state)
        except asyncio.CancelledError:
            raise
        except Exception:
            await self._fail(task)

    async def _pause(self, task: TaskSnapshot, state: LocalState) -> None:
        assert state.interrupt is not None
        interrupt = state.interrupt
        plan = ProposedPlan(interrupt.plan_revision, "Local Agent Server plan", interrupt.plan, ())
        await self.repository.set_plan(
            task.task_id, plan=plan, event_name=TaskEventName.PLAN_PROPOSED
        )
        await self.repository.append_event(
            task.task_id,
            name=TaskEventName.INTERRUPT_REQUESTED,
            data=(
                ("interruptId", interrupt.interrupt_id),
                ("question", "Approve this local plan?"),
                ("decisions", ("approve", "reject", "respond")),
                ("planRevision", interrupt.plan_revision),
            ),
            status=TaskStatus.WAITING_APPROVAL,
            pending_interrupt_id=interrupt.interrupt_id,
        )

    async def _complete(self, task: TaskSnapshot, state: LocalState) -> None:
        if state.status not in {"completed", "rejected"}:
            raise RuntimeError("local source did not report a terminal status")
        status = TaskStatus.REJECTED if state.status == "rejected" else TaskStatus.COMPLETED
        await self.repository.append_event(
            task.task_id,
            name=TaskEventName.RUN_COMPLETED,
            data=(
                ("runId", task.run_id),
                ("status", status.value),
                ("safeReason", "Local Agent Server run reached a terminal state."),
                ("resultAvailable", state.final_answer is not None),
            ),
            status=status,
            clear_pending_interrupt=True,
            result=state.final_answer,
        )

    async def _fail(self, task: TaskSnapshot) -> None:
        try:
            await self.repository.append_event(
                task.task_id,
                name=TaskEventName.RUN_COMPLETED,
                data=(
                    ("runId", task.run_id),
                    ("status", "failed"),
                    ("safeReason", "The local Agent Server source failed safely."),
                    ("resultAvailable", False),
                ),
                status=TaskStatus.FAILED,
                clear_pending_interrupt=True,
            )
        except Exception:
            return

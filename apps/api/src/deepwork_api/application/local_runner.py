"""Application mapping for the explicitly configured loopback source."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass, field
from typing import Protocol

from deepwork_api.domain import (
    DecisionRecord,
    DecisionValue,
    EvidenceClass,
    InterruptMismatchError,
    PlanRevisionConflictError,
    PlanUnavailableError,
    PlanUpdateRecord,
    ProposedPlan,
    StaleInterruptError,
    TaskEventName,
    TaskSnapshot,
    TaskSourceContractError,
    TaskSourceUnavailableError,
    TaskStatus,
)
from deepwork_api.ports import TaskRepository

_SOURCE_UNAVAILABLE_REASON = "The local agent source became unavailable."
_SOURCE_CONTRACT_REASON = "The local agent source broke its supported contract."
_RUNNER_FAILURE_REASON = "The local source task runner failed safely."
_TERMINAL_REASON = "Local Agent Server run reached a terminal state."


class LocalRun(Protocol):
    """The narrow source-owned identity required by the application."""

    @property
    def thread_id(self) -> str: ...

    @property
    def run_id(self) -> str: ...


class LocalPlanUpdate(LocalRun, Protocol):
    """Confirmed source checkpoint after an accepted plan edit."""

    @property
    def interrupt_id(self) -> str: ...

    @property
    def plan_revision(self) -> int: ...


class LocalInterruptValue(Protocol):
    @property
    def interrupt_id(self) -> str: ...

    @property
    def plan(self) -> tuple[str, ...]: ...

    @property
    def plan_revision(self) -> int: ...


class LocalState(Protocol):
    @property
    def status(self) -> str | None: ...

    @property
    def plan(self) -> tuple[str, ...]: ...

    @property
    def plan_revision(self) -> int | None: ...

    @property
    def final_answer(self) -> str | None: ...

    @property
    def interrupt(self) -> LocalInterruptValue | None: ...


class LocalSource(Protocol):
    async def start(self, objective: str) -> LocalRun: ...
    async def get_state(self, thread_id: str) -> LocalState: ...
    async def resume(
        self, thread_id: str, *, interrupt_id: str, decision: str, comment: str | None = None
    ) -> LocalRun: ...
    async def update_plan(
        self, thread_id: str, *, interrupt_id: str, expected_revision: int, steps: Sequence[str]
    ) -> LocalPlanUpdate: ...
    def stream(self, run: LocalRun) -> AsyncIterator[object]: ...


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
        except TaskSourceContractError:
            raise
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
        background.add_done_callback(lambda finished: self._discard(task.task_id, finished))

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
        # Validate the exact pending interrupt and revision before any source
        # I/O, so a mismatched request never reaches the loopback server.
        current = await self.repository.get_task(task.task_id)
        if current.status.is_terminal or current.pending_interrupt_id is None:
            raise StaleInterruptError
        if current.pending_interrupt_id != interrupt_id:
            raise InterruptMismatchError
        if current.proposed_plan is None:
            raise PlanUnavailableError
        if current.proposed_plan.revision != expected_revision:
            raise PlanRevisionConflictError
        thread_id = self._threads.get(task.task_id)
        if thread_id is None:
            raise TaskSourceContractError
        try:
            updated = await self.source.update_plan(
                thread_id,
                interrupt_id=interrupt_id,
                expected_revision=expected_revision,
                steps=steps,
            )
        except (StaleInterruptError, TaskSourceContractError):
            raise
        except Exception:
            raise TaskSourceUnavailableError from None
        if updated.interrupt_id == interrupt_id or updated.plan_revision != expected_revision + 1:
            raise TaskSourceContractError
        # The source has confirmed the edit at this point.  Reconcile the known
        # checkpoint before doing any further source I/O, so the old interrupt is
        # never advertised after the source has advanced it.
        record = await self.repository.update_plan(
            task.task_id,
            interrupt_id=interrupt_id,
            expected_revision=expected_revision,
            steps=steps,
            evidence_class=EvidenceClass.LOCAL_SOURCE,
        )
        if record.plan.revision != updated.plan_revision:
            raise TaskSourceContractError
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

    def _discard(self, task_id: str, background: asyncio.Task[None]) -> None:
        """Drop only this exact follower so a restarted follower stays tracked."""

        if self._tasks.get(task_id) is background:
            del self._tasks[task_id]

    async def _follow(self, task: TaskSnapshot, run: LocalRun) -> None:
        try:
            await self.repository.append_event(
                task.task_id,
                name=TaskEventName.RUN_STARTED,
                data=(("runId", run.run_id), ("status", "running")),
                status=TaskStatus.RUNNING,
            )
            async for event in self.source.stream(run):
                kind = getattr(event, "kind", None)
                if kind == "error":
                    raise TaskSourceContractError
                if kind != "progress":
                    continue
                await self.repository.append_event(
                    task.task_id,
                    name=TaskEventName.CONTENT_DELTA,
                    data=(
                        ("text", "Local Agent Server progress received."),
                        ("evidenceClass", EvidenceClass.LOCAL_SOURCE.value),
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
        except (StaleInterruptError, TaskSourceContractError):
            # The source advanced or broke its contract underneath an accepted
            # decision; the task must end honestly instead of claiming success.
            await self._fail(task, _SOURCE_CONTRACT_REASON)
        except TaskSourceUnavailableError:
            await self._fail(task, _SOURCE_UNAVAILABLE_REASON)
        except Exception:
            await self._fail(task, _RUNNER_FAILURE_REASON)

    async def _pause(self, task: TaskSnapshot, state: LocalState) -> None:
        interrupt = state.interrupt
        if interrupt is None:
            raise TaskSourceContractError
        plan = ProposedPlan(interrupt.plan_revision, "Local Agent Server plan", interrupt.plan, ())
        await self.repository.set_plan(
            task.task_id,
            plan=plan,
            event_name=TaskEventName.PLAN_PROPOSED,
            evidence_class=EvidenceClass.LOCAL_SOURCE,
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
        if state.status == "rejected":
            await self.repository.append_event(
                task.task_id,
                name=TaskEventName.RUN_COMPLETED,
                data=(
                    ("runId", task.run_id),
                    ("status", TaskStatus.REJECTED.value),
                    ("safeReason", _TERMINAL_REASON),
                    ("resultAvailable", False),
                ),
                status=TaskStatus.REJECTED,
                clear_pending_interrupt=True,
            )
            return
        if state.status != "completed" or state.final_answer is None:
            # A run that pauses no interrupt must end honestly terminal, and a
            # completed run without a result would be a false Done.
            raise TaskSourceContractError
        await self.repository.append_event(
            task.task_id,
            name=TaskEventName.RUN_COMPLETED,
            data=(
                ("runId", task.run_id),
                ("status", TaskStatus.COMPLETED.value),
                ("safeReason", _TERMINAL_REASON),
                ("resultAvailable", True),
            ),
            status=TaskStatus.COMPLETED,
            clear_pending_interrupt=True,
            result=state.final_answer,
        )

    async def _fail(self, task: TaskSnapshot, reason: str) -> None:
        try:
            await self.repository.append_event(
                task.task_id,
                name=TaskEventName.RUN_COMPLETED,
                data=(
                    ("runId", task.run_id),
                    ("status", "failed"),
                    ("safeReason", reason),
                    ("resultAvailable", False),
                ),
                status=TaskStatus.FAILED,
                clear_pending_interrupt=True,
            )
        except Exception:
            return

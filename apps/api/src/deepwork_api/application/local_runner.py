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
_RESUME_SHUTDOWN_GRACE_SECONDS = 1.0


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
    _resume_acknowledgements: dict[tuple[str, str], asyncio.Future[None]] = field(
        default_factory=dict, init=False
    )
    _command_locks: dict[str, asyncio.Lock] = field(default_factory=dict, init=False)
    _resumes_in_flight: set[tuple[str, str]] = field(default_factory=set, init=False)
    _closing: bool = field(default=False, init=False)

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
        if self._closing or task.task_id in self._tasks:
            return
        if task.pending_interrupt_id is not None:
            self._register_resume_acknowledgement((task.task_id, task.pending_interrupt_id))
        background = asyncio.create_task(
            self._follow(task, run), name=f"deepwork-local-{task.task_id}"
        )
        self._tasks[task.task_id] = background
        background.add_done_callback(lambda finished: self._discard(task.task_id, finished))

    async def close(self) -> None:
        self._closing = True
        active = dict(self._tasks)
        resuming_task_ids = {task_id for task_id, _ in self._resumes_in_flight}
        draining = tuple(
            background for task_id, background in active.items() if task_id in resuming_task_ids
        )
        for task_id, task in active.items():
            if task_id not in resuming_task_ids:
                task.cancel()
        if draining:
            _, unfinished = await asyncio.wait(draining, timeout=_RESUME_SHUTDOWN_GRACE_SECONDS)
            for task in unfinished:
                task.cancel()
        remaining = tuple(
            task for task in set(active.values()) | set(self._tasks.values()) if not task.done()
        )
        for task in remaining:
            task.cancel()
        tracked = tuple(set(active.values()) | set(self._tasks.values()))
        if tracked:
            await asyncio.gather(*tracked, return_exceptions=True)
        for acknowledgement in self._resume_acknowledgements.values():
            if not acknowledgement.done():
                acknowledgement.set_exception(TaskSourceUnavailableError())
        self._tasks.clear()

    async def update_plan(
        self,
        task: TaskSnapshot,
        *,
        interrupt_id: str,
        expected_revision: int,
        steps: tuple[str, ...],
    ) -> PlanUpdateRecord:
        async with self._command_lock(task.task_id):
            if self._closing:
                raise TaskSourceUnavailableError
            return await self._update_plan(
                task,
                interrupt_id=interrupt_id,
                expected_revision=expected_revision,
                steps=steps,
            )

    async def _update_plan(
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
        acknowledgement = self._resume_acknowledgements.pop((task.task_id, interrupt_id), None)
        if acknowledgement is not None and not acknowledgement.done():
            acknowledgement.set_exception(StaleInterruptError())
        if record.plan.revision != updated.plan_revision:
            raise TaskSourceContractError
        self._register_resume_acknowledgement((task.task_id, updated.interrupt_id))
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
        """Return only after the source accepts the exact resume command."""

        async with self._command_lock(task_id):
            if self._closing:
                raise TaskSourceUnavailableError
            return await self._record_decision(
                task_id,
                interrupt_id=interrupt_id,
                decision=decision,
                comment=comment,
                comment_provided=comment_provided,
                response_digest=response_digest,
            )

    async def _record_decision(
        self,
        task_id: str,
        *,
        interrupt_id: str,
        decision: DecisionValue,
        comment: str | None,
        comment_provided: bool,
        response_digest: str | None,
    ) -> DecisionRecord:
        key = (task_id, interrupt_id)
        stored_comment = self._review_comments.get(key)
        inserted_comment = (
            decision is DecisionValue.RESPOND and comment is not None and stored_comment is None
        )
        if inserted_comment:
            assert comment is not None
            self._review_comments[key] = comment
        try:
            record = await self.repository.record_decision(
                task_id,
                interrupt_id=interrupt_id,
                decision=decision,
                comment_provided=comment_provided,
                response_digest=response_digest,
            )
            acknowledgement = self._resume_acknowledgements.get(key)
            if acknowledgement is None:
                raise TaskSourceContractError
            await asyncio.shield(acknowledgement)
        except Exception:
            if inserted_comment and self._review_comments.get(key) == comment:
                self._review_comments.pop(key, None)
            raise
        if record.duplicate and inserted_comment and self._review_comments.get(key) == comment:
            self._review_comments.pop(key, None)
        return record

    def _discard(self, task_id: str, background: asyncio.Task[None]) -> None:
        """Drop only this exact follower so a restarted follower stays tracked."""

        if self._tasks.get(task_id) is background:
            del self._tasks[task_id]

    async def _follow(self, task: TaskSnapshot, run: LocalRun) -> None:
        resume_key: tuple[str, str] | None = None
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
                resume_key = (task.task_id, state.interrupt.interrupt_id)
                self._register_resume_acknowledgement(resume_key)
                if task.pending_interrupt_id is None:
                    await self._pause(task, state)
                elif task.pending_interrupt_id != state.interrupt.interrupt_id:
                    raise TaskSourceContractError
                decision = await self.repository.wait_for_decision(
                    task.task_id, state.interrupt.interrupt_id
                )
                key = (task.task_id, state.interrupt.interrupt_id)
                self._resumes_in_flight.add(key)
                try:
                    next_run = await self.source.resume(
                        run.thread_id,
                        interrupt_id=state.interrupt.interrupt_id,
                        decision=decision.value,
                        comment=self._review_comments.pop(key, None),
                    )
                finally:
                    self._resumes_in_flight.discard(key)
                self._accept_resume(resume_key)
                self._tasks.pop(task.task_id, None)
                self.start(await self.repository.get_task(task.task_id), next_run)
                return
            await self._complete(task, state)
        except asyncio.CancelledError:
            self._reject_resume(resume_key, TaskSourceUnavailableError())
            raise
        except (StaleInterruptError, TaskSourceContractError) as error:
            self._reject_resume(resume_key, error)
            # The source advanced or broke its contract underneath an accepted
            # decision; the task must end honestly instead of claiming success.
            await self._fail(task, _SOURCE_CONTRACT_REASON)
        except TaskSourceUnavailableError as error:
            self._reject_resume(resume_key, error)
            await self._fail(task, _SOURCE_UNAVAILABLE_REASON)
        except Exception:
            self._reject_resume(resume_key, TaskSourceUnavailableError())
            await self._fail(task, _RUNNER_FAILURE_REASON)

    def _register_resume_acknowledgement(self, key: tuple[str, str]) -> None:
        existing = self._resume_acknowledgements.get(key)
        if existing is not None:
            if existing.done():
                raise TaskSourceContractError
            return
        acknowledgement = asyncio.get_running_loop().create_future()
        acknowledgement.add_done_callback(self._consume_acknowledgement_error)
        self._resume_acknowledgements[key] = acknowledgement

    def _command_lock(self, task_id: str) -> asyncio.Lock:
        return self._command_locks.setdefault(task_id, asyncio.Lock())

    def _accept_resume(self, key: tuple[str, str]) -> None:
        acknowledgement = self._resume_acknowledgements.get(key)
        if acknowledgement is None:
            raise TaskSourceContractError
        if not acknowledgement.done():
            acknowledgement.set_result(None)

    def _reject_resume(
        self,
        key: tuple[str, str] | None,
        error: TaskSourceContractError | TaskSourceUnavailableError | StaleInterruptError,
    ) -> None:
        if key is None:
            return
        acknowledgement = self._resume_acknowledgements.get(key)
        if acknowledgement is not None and not acknowledgement.done():
            acknowledgement.set_exception(error)

    @staticmethod
    def _consume_acknowledgement_error(acknowledgement: asyncio.Future[None]) -> None:
        if not acknowledgement.cancelled():
            acknowledgement.exception()

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

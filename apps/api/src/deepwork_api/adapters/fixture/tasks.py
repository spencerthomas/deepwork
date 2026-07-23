"""Concurrency-safe in-memory task repository for the local fixture loop."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from deepwork_api.domain import (
    MAX_PLAN_REVISION,
    DecisionConflictError,
    DecisionRecord,
    DecisionValue,
    EventData,
    EvidenceClass,
    EvidenceRecord,
    InterruptMismatchError,
    InvalidEventCursorError,
    PlanRevisionConflictError,
    PlanUnavailableError,
    PlanUpdateRecord,
    ProposedPlan,
    StaleInterruptError,
    TaskEvent,
    TaskEventName,
    TaskNotFoundError,
    TaskSnapshot,
    TaskStatus,
)


@dataclass(slots=True)
class _StoredTask:
    task_id: str
    run_id: str
    title: str
    objective: str
    status: TaskStatus
    events: list[TaskEvent] = field(default_factory=list)
    pending_interrupt_id: str | None = None
    decisions: dict[str, tuple[DecisionValue, str | None]] = field(default_factory=dict)
    proposed_plan: ProposedPlan | None = None
    evidence: list[EvidenceRecord] = field(default_factory=list)
    result: str | None = None

    def snapshot(self) -> TaskSnapshot:
        return TaskSnapshot(
            task_id=self.task_id,
            run_id=self.run_id,
            title=self.title,
            objective=self.objective,
            status=self.status,
            last_event_id=len(self.events),
            pending_interrupt_id=self.pending_interrupt_id,
            proposed_plan=self.proposed_plan,
            evidence=tuple(self.evidence),
            result=self.result,
        )


class InMemoryTaskRepository:
    """Store bounded local task state and notify stream/runner waiters."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._condition = asyncio.Condition(self._lock)
        self._tasks: dict[str, _StoredTask] = {}
        self._next_task_number = 1

    async def create_task(
        self, *, title: str, objective: str, run_id: str | None = None
    ) -> TaskSnapshot:
        """Create a queued task containing only its sanitized objective."""

        async with self._condition:
            number = self._next_task_number
            self._next_task_number += 1
            suffix = f"{number:08d}"
            task = _StoredTask(
                task_id=f"task_{suffix}",
                run_id=run_id or f"run_{suffix}",
                title=title,
                objective=objective,
                status=TaskStatus.QUEUED,
            )
            task.events.append(
                TaskEvent(
                    event_id=1,
                    name=TaskEventName.TASK_CREATED,
                    data=(
                        ("taskId", task.task_id),
                        ("runId", task.run_id),
                        ("status", TaskStatus.QUEUED.value),
                    ),
                )
            )
            self._tasks[task.task_id] = task
            self._condition.notify_all()
            return task.snapshot()

    async def list_tasks(self) -> tuple[TaskSnapshot, ...]:
        """List tasks in deterministic creation order."""

        async with self._lock:
            return tuple(task.snapshot() for task in self._tasks.values())

    async def get_task(self, task_id: str) -> TaskSnapshot:
        """Read one task without leaking other task identities."""

        async with self._lock:
            return self._get(task_id).snapshot()

    async def append_event(
        self,
        task_id: str,
        *,
        name: TaskEventName,
        data: EventData,
        status: TaskStatus | None = None,
        pending_interrupt_id: str | None = None,
        clear_pending_interrupt: bool = False,
        result: str | None = None,
    ) -> TaskEvent:
        """Append one monotonic event and signal all task waiters."""

        async with self._condition:
            task = self._get(task_id)
            if task.status.is_terminal:
                raise StaleInterruptError
            event = TaskEvent(
                event_id=len(task.events) + 1,
                name=name,
                data=data,
            )
            task.events.append(event)
            if status is not None:
                task.status = status
            if pending_interrupt_id is not None:
                task.pending_interrupt_id = pending_interrupt_id
            elif clear_pending_interrupt:
                task.pending_interrupt_id = None
            if result is not None:
                task.result = result
            self._condition.notify_all()
            return event

    async def record_evidence(
        self,
        task_id: str,
        evidence: EvidenceRecord,
    ) -> TaskEvent:
        """Store and replay one truthful local evidence record."""

        async with self._condition:
            task = self._get(task_id)
            if task.status.is_terminal:
                raise StaleInterruptError
            task.evidence.append(evidence)
            event = TaskEvent(
                event_id=len(task.events) + 1,
                name=TaskEventName.EVIDENCE_RECORDED,
                data=(
                    ("evidenceId", evidence.evidence_id),
                    ("kind", evidence.kind),
                    ("summary", evidence.summary),
                    ("source", evidence.source),
                    ("verified", evidence.verified),
                ),
            )
            task.events.append(event)
            self._condition.notify_all()
            return event

    async def set_plan(
        self,
        task_id: str,
        *,
        plan: ProposedPlan,
        event_name: TaskEventName,
        evidence_class: EvidenceClass = EvidenceClass.FIXTURE,
    ) -> TaskEvent:
        """Store and replay a runner-owned proposed or revised plan."""

        async with self._condition:
            task = self._get(task_id)
            if task.status.is_terminal:
                raise StaleInterruptError
            task.proposed_plan = plan
            event = TaskEvent(
                event_id=len(task.events) + 1,
                name=event_name,
                data=(
                    ("title", plan.title),
                    ("steps", plan.steps),
                    ("revision", plan.revision),
                    ("evidenceRefs", plan.evidence_refs),
                    ("evidenceClass", evidence_class.value),
                ),
            )
            task.events.append(event)
            self._condition.notify_all()
            return event

    async def update_plan(
        self,
        task_id: str,
        *,
        interrupt_id: str,
        expected_revision: int,
        steps: tuple[str, ...],
        evidence_class: EvidenceClass = EvidenceClass.FIXTURE,
    ) -> PlanUpdateRecord:
        """Edit only the current plan for the exact pending interrupt and revision."""

        async with self._condition:
            task = self._get(task_id)
            if task.status.is_terminal or task.pending_interrupt_id is None:
                raise StaleInterruptError
            if task.pending_interrupt_id != interrupt_id:
                raise InterruptMismatchError
            current = task.proposed_plan
            if current is None:
                raise PlanUnavailableError
            if (
                not isinstance(expected_revision, int)
                or isinstance(expected_revision, bool)
                or not 1 <= expected_revision <= MAX_PLAN_REVISION
            ):
                raise PlanRevisionConflictError
            if current.revision != expected_revision:
                raise PlanRevisionConflictError
            if current.revision >= MAX_PLAN_REVISION:
                raise PlanRevisionConflictError
            updated = ProposedPlan(
                revision=current.revision + 1,
                title=current.title,
                steps=steps,
                evidence_refs=current.evidence_refs,
            )
            task.proposed_plan = updated
            task.events.append(
                TaskEvent(
                    event_id=len(task.events) + 1,
                    name=TaskEventName.PLAN_UPDATED,
                    data=(
                        ("title", updated.title),
                        ("steps", updated.steps),
                        ("revision", updated.revision),
                        ("evidenceRefs", updated.evidence_refs),
                        ("evidenceClass", evidence_class.value),
                    ),
                )
            )
            self._condition.notify_all()
            return PlanUpdateRecord(
                task_id=task.task_id,
                run_id=task.run_id,
                interrupt_id=interrupt_id,
                plan=updated,
            )

    async def events_after(self, task_id: str, event_id: int) -> tuple[TaskEvent, ...]:
        """Return replay events after a cursor validated against current history."""

        async with self._lock:
            task = self._get(task_id)
            self._validate_cursor(task, event_id)
            return tuple(task.events[event_id:])

    async def wait_for_events(self, task_id: str, event_id: int) -> None:
        """Wait without polling for a later event or a terminal state."""

        async with self._condition:
            while True:
                task = self._get(task_id)
                self._validate_cursor(task, event_id)
                if len(task.events) > event_id or task.status.is_terminal:
                    return
                await self._condition.wait()

    async def record_decision(
        self,
        task_id: str,
        *,
        interrupt_id: str,
        decision: DecisionValue,
        comment_provided: bool,
        response_digest: str | None,
    ) -> DecisionRecord:
        """Record one decision atomically and replay identical duplicates."""

        async with self._condition:
            task = self._get(task_id)
            signature = (decision, response_digest)
            existing = task.decisions.get(interrupt_id)
            if existing is not None:
                if existing != signature:
                    raise DecisionConflictError
                return DecisionRecord(
                    task_id=task.task_id,
                    run_id=task.run_id,
                    interrupt_id=interrupt_id,
                    decision=decision,
                    duplicate=True,
                )
            if task.status.is_terminal or task.pending_interrupt_id is None:
                raise StaleInterruptError
            if task.pending_interrupt_id != interrupt_id:
                raise InterruptMismatchError

            task.decisions[interrupt_id] = signature
            task.pending_interrupt_id = None
            task.status = TaskStatus.RUNNING
            task.events.append(
                TaskEvent(
                    event_id=len(task.events) + 1,
                    name=TaskEventName.DECISION_RECORDED,
                    data=(
                        ("interruptId", interrupt_id),
                        ("decision", decision.value),
                        ("commentProvided", comment_provided),
                        ("responseProvided", response_digest is not None),
                    ),
                )
            )
            self._condition.notify_all()
            return DecisionRecord(
                task_id=task.task_id,
                run_id=task.run_id,
                interrupt_id=interrupt_id,
                decision=decision,
                duplicate=False,
            )

    async def wait_for_decision(
        self,
        task_id: str,
        interrupt_id: str,
    ) -> DecisionValue:
        """Wait for exactly the requested interrupt decision."""

        async with self._condition:
            while True:
                task = self._get(task_id)
                signature = task.decisions.get(interrupt_id)
                if signature is not None:
                    return signature[0]
                if task.status.is_terminal:
                    raise StaleInterruptError
                await self._condition.wait()

    def _get(self, task_id: str) -> _StoredTask:
        try:
            return self._tasks[task_id]
        except KeyError as error:
            raise TaskNotFoundError from error

    @staticmethod
    def _validate_cursor(task: _StoredTask, event_id: int) -> None:
        if event_id < 0 or event_id > len(task.events):
            raise InvalidEventCursorError

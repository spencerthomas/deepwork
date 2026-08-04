"""Concurrency-safe in-memory task repository for the local fixture loop."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from deepwork_api.domain import (
    CANCELLATION_SAFE_REASON,
    DEFAULT_SECURITY_CONTEXT,
    MAX_PLAN_REVISION,
    MAX_PLAN_STEP_LENGTH,
    MAX_PLAN_STEPS,
    CancellationRecord,
    DecisionBatchRecord,
    DecisionBatchVersionStaleError,
    DecisionConflictError,
    DecisionRecord,
    DecisionType,
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
    SecurityContext,
    StaleInterruptError,
    TaskAlreadyResolvedError,
    TaskCreation,
    TaskEvent,
    TaskEventName,
    TaskIdempotencyConflictError,
    TaskJourney,
    TaskNotFoundError,
    TaskSnapshot,
    TaskStatus,
    aggregate_batch_decision,
    coding_outcome_from_event_data,
)
from deepwork_api.ports import Clock, system_clock


@dataclass(slots=True)
class _StoredTask:
    task_id: str
    run_id: str
    created_at: str
    title: str
    objective: str
    agent_id: str | None
    journey: TaskJourney | None
    repository_id: str | None
    tenant_id: str
    workspace_id: str
    created_by_actor_id: str
    status: TaskStatus
    events: list[TaskEvent] = field(default_factory=list)
    pending_interrupt_id: str | None = None
    decisions: dict[str, tuple[DecisionValue, str | None]] = field(default_factory=dict)
    proposed_plan: ProposedPlan | None = None
    evidence: list[EvidenceRecord] = field(default_factory=list)
    result: str | None = None

    def snapshot(self) -> TaskSnapshot:
        coding_event = (
            next(
                (
                    event
                    for event in reversed(self.events)
                    if event.name is TaskEventName.CODING_COMPLETED
                ),
                None,
            )
            if self.status is TaskStatus.COMPLETED and self.result is not None
            else None
        )
        return TaskSnapshot(
            task_id=self.task_id,
            run_id=self.run_id,
            created_at=self.created_at,
            title=self.title,
            objective=self.objective,
            status=self.status,
            last_event_id=len(self.events),
            pending_interrupt_id=self.pending_interrupt_id,
            proposed_plan=self.proposed_plan,
            evidence=tuple(self.evidence),
            result=self.result,
            tenant_id=self.tenant_id,
            workspace_id=self.workspace_id,
            created_by_actor_id=self.created_by_actor_id,
            agent_id=self.agent_id,
            journey=self.journey,
            repository_id=self.repository_id,
            coding=(
                coding_outcome_from_event_data(dict(coding_event.data))
                if coding_event is not None
                else None
            ),
        )


class InMemoryTaskRepository:
    """Store bounded local task state and notify stream/runner waiters."""

    def __init__(self, *, clock: Clock = system_clock) -> None:
        self._lock = asyncio.Lock()
        self._condition = asyncio.Condition(self._lock)
        self._tasks: dict[str, _StoredTask] = {}
        self._idempotency: dict[tuple[str, str, str, str], tuple[str, str]] = {}
        self._next_task_number = 1
        self._clock = clock

    async def create_task(
        self,
        *,
        title: str,
        objective: str,
        run_id: str | None = None,
        agent_id: str | None = None,
        journey: TaskJourney | None = None,
        repository_id: str | None = None,
        security_context: SecurityContext = DEFAULT_SECURITY_CONTEXT,
    ) -> TaskSnapshot:
        """Create a queued task containing only its sanitized objective."""

        async with self._condition:
            task = self._create_task_locked(
                title=title,
                objective=objective,
                run_id=run_id,
                agent_id=agent_id,
                journey=journey,
                repository_id=repository_id,
                security_context=security_context,
            )
            self._condition.notify_all()
            return task.snapshot()

    async def create_task_idempotently(
        self,
        *,
        title: str,
        objective: str,
        idempotency_key: str,
        request_fingerprint: str,
        run_id: str | None = None,
        agent_id: str | None = None,
        journey: TaskJourney | None = None,
        repository_id: str | None = None,
        security_context: SecurityContext = DEFAULT_SECURITY_CONTEXT,
    ) -> TaskCreation:
        """Atomically create or replay one actor-scoped task request."""

        scope = self._idempotency_scope(security_context, idempotency_key)
        async with self._condition:
            existing = self._idempotency.get(scope)
            if existing is not None:
                fingerprint, task_id = existing
                if fingerprint != request_fingerprint:
                    raise TaskIdempotencyConflictError
                return TaskCreation(task=self._get(task_id).snapshot(), created=False)
            task = self._create_task_locked(
                title=title,
                objective=objective,
                run_id=run_id,
                agent_id=agent_id,
                journey=journey,
                repository_id=repository_id,
                security_context=security_context,
            )
            self._idempotency[scope] = (request_fingerprint, task.task_id)
            self._condition.notify_all()
            return TaskCreation(task=task.snapshot(), created=True)

    async def find_task_by_idempotency(
        self,
        *,
        idempotency_key: str,
        request_fingerprint: str,
        security_context: SecurityContext = DEFAULT_SECURITY_CONTEXT,
    ) -> TaskSnapshot | None:
        """Resolve one scoped creation request without exposing other scopes."""

        scope = self._idempotency_scope(security_context, idempotency_key)
        async with self._lock:
            existing = self._idempotency.get(scope)
            if existing is None:
                return None
            fingerprint, task_id = existing
            if fingerprint != request_fingerprint:
                raise TaskIdempotencyConflictError
            return self._get(task_id).snapshot()

    @staticmethod
    def _idempotency_scope(
        security_context: SecurityContext,
        idempotency_key: str,
    ) -> tuple[str, str, str, str]:
        return (
            security_context.tenant_id,
            security_context.workspace_id,
            security_context.actor_id,
            idempotency_key,
        )

    def _create_task_locked(
        self,
        *,
        title: str,
        objective: str,
        run_id: str | None,
        agent_id: str | None,
        journey: TaskJourney | None,
        repository_id: str | None,
        security_context: SecurityContext,
    ) -> _StoredTask:
        number = self._next_task_number
        self._next_task_number += 1
        suffix = f"{number:08d}"
        task = _StoredTask(
            task_id=f"task_{suffix}",
            run_id=run_id or f"run_{suffix}",
            created_at=self._clock().isoformat(),
            title=title,
            objective=objective,
            agent_id=agent_id,
            journey=journey,
            repository_id=repository_id,
            tenant_id=security_context.tenant_id,
            workspace_id=security_context.workspace_id,
            created_by_actor_id=security_context.actor_id,
            status=TaskStatus.QUEUED,
        )
        created_data: EventData = (
            ("taskId", task.task_id),
            ("runId", task.run_id),
            ("status", TaskStatus.QUEUED.value),
        )
        if journey is not None:
            created_data = (*created_data, ("journey", journey.value))
        if repository_id is not None:
            created_data = (*created_data, ("repositoryId", repository_id))
        if agent_id is not None:
            created_data = (*created_data, ("agentId", agent_id))
        task.events.append(
            TaskEvent(
                event_id=1,
                name=TaskEventName.TASK_CREATED,
                data=created_data,
            )
        )
        self._tasks[task.task_id] = task
        return task

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
            if evidence.task_id != task_id or evidence.run_id != task.run_id:
                raise ValueError("evidence identity does not match its owning task and run")
            task.evidence.append(evidence)
            event = TaskEvent(
                event_id=len(task.events) + 1,
                name=TaskEventName.EVIDENCE_RECORDED,
                data=(
                    ("evidenceId", evidence.evidence_id),
                    ("taskId", evidence.task_id),
                    ("runId", evidence.run_id),
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

    async def record_decision_batch(
        self,
        task_id: str,
        *,
        interrupt_id: str,
        expected_revision: int,
        decision_types: tuple[DecisionType, ...],
        request_fingerprint: str,
        edited_steps: tuple[str, ...],
    ) -> DecisionBatchRecord:
        """Apply edits and record the vector under one repository lock."""

        if len(request_fingerprint) != 64:
            raise ValueError("request fingerprint must be a SHA-256 value")
        if not 1 <= len(edited_steps) <= MAX_PLAN_STEPS or any(
            not step.strip() or len(step) > MAX_PLAN_STEP_LENGTH for step in edited_steps
        ):
            raise ValueError("edited steps are outside the shared plan bounds")
        async with self._condition:
            task = self._get(task_id)
            aggregate = aggregate_batch_decision(decision_types)
            existing = task.decisions.get(interrupt_id)
            if existing is not None:
                if existing != (aggregate, request_fingerprint):
                    raise DecisionConflictError
                return DecisionBatchRecord(
                    task_id=task.task_id,
                    run_id=task.run_id,
                    interrupt_id=interrupt_id,
                    version=str(expected_revision),
                    decision_types=decision_types,
                    duplicate=True,
                )
            if task.status.is_terminal or task.pending_interrupt_id is None:
                raise StaleInterruptError
            if task.pending_interrupt_id != interrupt_id:
                raise InterruptMismatchError
            plan = task.proposed_plan
            if plan is None:
                raise PlanUnavailableError
            if plan.revision != expected_revision:
                raise DecisionBatchVersionStaleError
            if len(decision_types) != len(plan.steps) or len(edited_steps) != len(plan.steps):
                raise ValueError("decision vector must align with the current plan")

            if edited_steps != plan.steps:
                if plan.revision >= MAX_PLAN_REVISION:
                    raise PlanRevisionConflictError
                task.proposed_plan = ProposedPlan(
                    revision=plan.revision + 1,
                    title=plan.title,
                    steps=edited_steps,
                    evidence_refs=plan.evidence_refs,
                )
                task.events.append(
                    TaskEvent(
                        event_id=len(task.events) + 1,
                        name=TaskEventName.PLAN_UPDATED,
                        data=(
                            ("title", task.proposed_plan.title),
                            ("steps", task.proposed_plan.steps),
                            ("revision", task.proposed_plan.revision),
                            ("evidenceRefs", task.proposed_plan.evidence_refs),
                            ("evidenceClass", EvidenceClass.FIXTURE.value),
                        ),
                    )
                )
            task.decisions[interrupt_id] = (aggregate, request_fingerprint)
            task.pending_interrupt_id = None
            task.status = TaskStatus.RUNNING
            task.events.append(
                TaskEvent(
                    event_id=len(task.events) + 1,
                    name=TaskEventName.DECISION_RECORDED,
                    data=(
                        ("interruptId", interrupt_id),
                        ("decision", aggregate.value),
                        ("commentProvided", False),
                        ("responseProvided", False),
                        ("decisionTypes", tuple(item.value for item in decision_types)),
                    ),
                )
            )
            self._condition.notify_all()
            return DecisionBatchRecord(
                task_id=task.task_id,
                run_id=task.run_id,
                interrupt_id=interrupt_id,
                version=str(expected_revision),
                decision_types=decision_types,
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

    async def cancel_task(self, task_id: str) -> CancellationRecord:
        """Move a live task to a terminal cancelled state and wake its waiters."""

        async with self._condition:
            task = self._get(task_id)
            if task.status is TaskStatus.CANCELLED:
                return CancellationRecord(
                    task_id=task.task_id,
                    run_id=task.run_id,
                    duplicate=True,
                )
            if task.status.is_terminal:
                raise TaskAlreadyResolvedError
            task.events.append(
                TaskEvent(
                    event_id=len(task.events) + 1,
                    name=TaskEventName.RUN_COMPLETED,
                    data=(
                        ("runId", task.run_id),
                        ("status", TaskStatus.CANCELLED.value),
                        ("safeReason", CANCELLATION_SAFE_REASON),
                        ("resultAvailable", False),
                    ),
                )
            )
            task.status = TaskStatus.CANCELLED
            task.pending_interrupt_id = None
            self._condition.notify_all()
            return CancellationRecord(
                task_id=task.task_id,
                run_id=task.run_id,
                duplicate=False,
            )

    def _get(self, task_id: str) -> _StoredTask:
        try:
            return self._tasks[task_id]
        except KeyError as error:
            raise TaskNotFoundError from error

    @staticmethod
    def _validate_cursor(task: _StoredTask, event_id: int) -> None:
        if event_id < 0 or event_id > len(task.events):
            raise InvalidEventCursorError

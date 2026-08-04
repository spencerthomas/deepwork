"""Application-owned task repository port."""

from __future__ import annotations

from typing import Protocol

from deepwork_api.domain import (
    DEFAULT_SECURITY_CONTEXT,
    CancellationRecord,
    DecisionBatchRecord,
    DecisionRecord,
    DecisionType,
    DecisionValue,
    EventData,
    EvidenceClass,
    EvidenceRecord,
    PlanUpdateRecord,
    ProposedPlan,
    SecurityContext,
    TaskCreation,
    TaskEvent,
    TaskEventName,
    TaskJourney,
    TaskSnapshot,
    TaskSourceBinding,
    TaskSourceLease,
    TaskSourcePlanTransition,
    TaskStatus,
)


class TaskRepository(Protocol):
    """Persist and signal local task state behind application semantics."""

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
        """Create a queued task and its initial replayable event."""

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
        """Atomically create or replay one scoped immutable request."""

    async def find_task_by_idempotency(
        self,
        *,
        idempotency_key: str,
        request_fingerprint: str,
        security_context: SecurityContext = DEFAULT_SECURITY_CONTEXT,
    ) -> TaskSnapshot | None:
        """Resolve an existing scoped request or reject a changed replay."""

    async def acquire_source_lease(
        self,
        task_id: str,
        *,
        owner_id: str,
        lease_seconds: int,
    ) -> TaskSourceLease | None:
        """Acquire expired/unowned source work for one non-terminal task."""

    async def renew_source_lease(
        self,
        task_id: str,
        *,
        lease_token: str,
        lease_seconds: int,
    ) -> TaskSourceLease | None:
        """Extend only the caller's current, unexpired source lease."""

    async def release_source_lease(self, task_id: str, *, lease_token: str) -> bool:
        """Release only the caller's current source lease."""

    async def bind_source_run(
        self,
        task_id: str,
        *,
        lease_token: str,
        thread_id: str,
        run_id: str,
    ) -> TaskSourceBinding:
        """Persist the opaque source identity used to rejoin accepted work."""

    async def mark_source_transition_pending(
        self,
        task_id: str,
        *,
        lease_token: str,
        thread_id: str,
        run_id: str,
        interrupt_id: str,
        transition_id: str,
    ) -> TaskSourceBinding:
        """Durably claim one interrupt transition before source I/O."""

    async def accept_source_transition(
        self,
        task_id: str,
        *,
        lease_token: str,
        thread_id: str,
        previous_run_id: str,
        run_id: str,
        transition_id: str,
    ) -> TaskSourceBinding:
        """Atomically replace a source run and acknowledge its transition."""

    async def mark_source_plan_transition_pending(
        self,
        task_id: str,
        *,
        thread_id: str,
        run_id: str,
        interrupt_id: str,
        transition_id: str,
        expected_revision: int,
        steps: tuple[str, ...],
    ) -> TaskSourcePlanTransition:
        """Durably retain one exact plan edit before source I/O."""

    async def get_source_plan_transition(
        self,
        task_id: str,
    ) -> TaskSourcePlanTransition | None:
        """Return the pending plan edit payload required for recovery."""

    async def accept_source_plan_transition(
        self,
        task_id: str,
        *,
        lease_token: str,
        thread_id: str,
        previous_run_id: str,
        run_id: str,
        transition_id: str,
        new_interrupt_id: str,
        plan_revision: int,
    ) -> TaskSourceBinding:
        """Atomically commit an accepted source plan checkpoint and binding."""

    async def get_source_binding(self, task_id: str) -> TaskSourceBinding | None:
        """Return the server-only source identity for a task when one exists."""

    async def append_source_progress(
        self,
        task_id: str,
        *,
        lease_token: str,
        thread_id: str,
        run_id: str,
        source_event_key: str,
        data: EventData,
    ) -> TaskEvent | None:
        """Atomically retain one application-receipted source progress event."""

    async def list_tasks(self) -> tuple[TaskSnapshot, ...]:
        """List tasks in deterministic creation order."""

    async def get_task(self, task_id: str) -> TaskSnapshot:
        """Read one task or raise a safe not-found error."""

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
        """Append one event and atomically update its related task state."""

    async def record_evidence(
        self,
        task_id: str,
        evidence: EvidenceRecord,
    ) -> TaskEvent:
        """Store and replay one evidence record."""

    async def set_plan(
        self,
        task_id: str,
        *,
        plan: ProposedPlan,
        event_name: TaskEventName,
        evidence_class: EvidenceClass = EvidenceClass.FIXTURE,
    ) -> TaskEvent:
        """Store and replay a runner-owned proposed or revised plan."""

    async def update_plan(
        self,
        task_id: str,
        *,
        interrupt_id: str,
        expected_revision: int,
        steps: tuple[str, ...],
        evidence_class: EvidenceClass = EvidenceClass.FIXTURE,
    ) -> PlanUpdateRecord:
        """Edit the current plan for an exact pending interrupt/revision."""

    async def events_after(self, task_id: str, event_id: int) -> tuple[TaskEvent, ...]:
        """Return replay events strictly after a validated cursor."""

    async def wait_for_events(self, task_id: str, event_id: int) -> None:
        """Wait until an event exists after the cursor or the task is terminal."""

    async def record_decision(
        self,
        task_id: str,
        *,
        interrupt_id: str,
        decision: DecisionValue,
        comment_provided: bool,
        response_digest: str | None,
    ) -> DecisionRecord:
        """Atomically record or idempotently replay one interrupt decision."""

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
        """Atomically apply plan edits and record one complete decision vector."""

    async def wait_for_decision(
        self,
        task_id: str,
        interrupt_id: str,
    ) -> DecisionValue:
        """Wait for the exact interrupt decision."""

    async def cancel_task(self, task_id: str) -> CancellationRecord:
        """Atomically move a live task to a terminal cancelled state.

        Cancellation is idempotent for an already-cancelled task and refuses a
        task that already reached another terminal state.
        """

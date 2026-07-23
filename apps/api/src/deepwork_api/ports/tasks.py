"""Application-owned task repository port."""

from __future__ import annotations

from typing import Protocol

from deepwork_api.domain import (
    DecisionRecord,
    DecisionValue,
    EventData,
    EvidenceRecord,
    PlanUpdateRecord,
    ProposedPlan,
    TaskEvent,
    TaskEventName,
    TaskSnapshot,
    TaskStatus,
)


class TaskRepository(Protocol):
    """Persist and signal local task state behind application semantics."""

    async def create_task(
        self, *, title: str, objective: str, run_id: str | None = None
    ) -> TaskSnapshot:
        """Create a queued task and its initial replayable event."""

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
    ) -> TaskEvent:
        """Store and replay a runner-owned proposed or revised plan."""

    async def update_plan(
        self,
        task_id: str,
        *,
        interrupt_id: str,
        expected_revision: int,
        steps: tuple[str, ...],
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

    async def wait_for_decision(
        self,
        task_id: str,
        interrupt_id: str,
    ) -> DecisionValue:
        """Wait for the exact interrupt decision."""

"""Task use cases and deterministic asynchronous fixture execution."""

from __future__ import annotations

import asyncio
import hashlib
import re
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

from deepwork_api.application.local_runner import LocalAgentServerRunner
from deepwork_api.domain import (
    MAX_TASK_OBJECTIVE_LENGTH,
    DecisionRecord,
    DecisionValue,
    EvidenceKind,
    EvidenceRecord,
    EvidenceSource,
    PlanUpdateRecord,
    ProposedPlan,
    TaskEvent,
    TaskEventName,
    TaskSnapshot,
    TaskStatus,
)
from deepwork_api.ports import TaskRepository

_SECRET_PATTERNS = (
    re.compile(
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b", re.IGNORECASE),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{12,}\b", re.IGNORECASE),
    re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{8,}\b", re.IGNORECASE),
    re.compile(r"\bBasic\s+[A-Za-z0-9+/=]{8,}\b", re.IGNORECASE),
    re.compile(
        r"\b(?:api[_-]?key|aws_secret_access_key|password|secret|token)"
        r"\s*[:=]\s*[^\s,;]{4,}",
        re.IGNORECASE,
    ),
)
_MAX_TASK_TITLE_LENGTH = 80


def sanitize_objective(prompt: str) -> str:
    """Redact an already-bounded prompt without silently truncating it."""

    objective = prompt
    for pattern in _SECRET_PATTERNS:
        objective = pattern.sub("[redacted]", objective)
    if len(objective) > MAX_TASK_OBJECTIVE_LENGTH:
        message = "task objective exceeds the shared request bound"
        raise ValueError(message)
    return objective


def _build_task_title(objective: str) -> str:
    """Derive a bounded display title without altering the objective."""

    title = " ".join(objective.split())
    if len(title) <= _MAX_TASK_TITLE_LENGTH:
        return title
    return f"{title[: _MAX_TASK_TITLE_LENGTH - 1].rstrip()}…"


def _build_task_brief(objective: str, plan: ProposedPlan) -> str:
    risk = _risk_for(objective)
    return "\n".join(
        (
            "Task brief",
            f"Objective: {objective}",
            "Plan:",
            *(f"{index}. {step}" for index, step in enumerate(plan.steps, start=1)),
            "Risks:",
            f"- {risk}",
            "Next actions:",
            "1. Confirm any missing scope or acceptance detail.",
            "2. Execute the approved plan without external side effects.",
            "3. Review the result against the stated objective.",
        )
    )


def _plan_for(objective: str) -> tuple[str, str, str]:
    normalized = objective.casefold()
    if any(word in normalized for word in ("research", "investigate", "compare", "study")):
        return (
            "Frame the research question and evidence threshold.",
            "Gather source-qualified findings and record uncertainty.",
            "Synthesize conclusions with traceable evidence and open questions.",
        )
    if any(
        word in normalized for word in ("launch", "deploy", "migration", "release", "production")
    ):
        return (
            "Confirm readiness gates, owners, and dependencies.",
            "Sequence the change with explicit rollback and communication steps.",
            "Validate launch health and record any unresolved release risk.",
        )
    if any(word in normalized for word in ("write", "report", "brief", "document")):
        return (
            "Confirm audience, purpose, and required evidence.",
            "Draft a structured narrative grounded in the available inputs.",
            "Review for accuracy, clarity, and unresolved claims.",
        )
    if any(word in normalized for word in ("code", "fix", "implement", "refactor", "test")):
        return (
            "Reproduce the requested behavior and define the smallest change.",
            "Implement within the governed boundary with explicit evidence.",
            "Run focused validation and report remaining integration risk.",
        )
    return (
        "Confirm the requested outcome and bounded inputs.",
        "Produce the smallest useful result with explicit evidence.",
        "Validate the result and record unresolved assumptions.",
    )


def _risk_for(objective: str) -> str:
    normalized = objective.casefold()
    if any(
        word in normalized
        for word in ("deploy", "delete", "production", "publish", "send", "merge")
    ):
        return "External-state changes require separate authority and verification."
    if any(
        word in normalized
        for word in ("credential", "password", "secret", "token", "api key", "[redacted]")
    ):
        return "Sensitive inputs must remain redacted and outside fixture evidence."
    return "The local fixture has no provider access, so external facts remain unverified."


@dataclass(slots=True)
class DeterministicFixtureRunner:
    """Run one safe local task until its real approval decision arrives."""

    repository: TaskRepository
    _tasks: dict[str, asyncio.Task[None]] = field(default_factory=dict, init=False)

    def start(self, task: TaskSnapshot) -> None:
        """Start actual asynchronous application work exactly once."""

        if task.task_id in self._tasks:
            return
        background = asyncio.create_task(
            self._run(task),
            name=f"deepwork-fixture-{task.task_id}",
        )
        self._tasks[task.task_id] = background
        background.add_done_callback(lambda _: self._tasks.pop(task.task_id, None))

    async def close(self) -> None:
        """Cancel only runner-owned unfinished tasks."""

        active = tuple(self._tasks.values())
        for task in active:
            task.cancel()
        if active:
            await asyncio.gather(*active, return_exceptions=True)
        self._tasks.clear()

    async def _run(self, task: TaskSnapshot) -> None:
        try:
            await self.repository.append_event(
                task.task_id,
                name=TaskEventName.RUN_STARTED,
                data=(("runId", task.run_id), ("status", TaskStatus.RUNNING.value)),
                status=TaskStatus.RUNNING,
            )
            await asyncio.sleep(0)
            await self.repository.append_event(
                task.task_id,
                name=TaskEventName.CONTENT_DELTA,
                data=(
                    (
                        "text",
                        f"I prepared a local task brief for: {task.objective}",
                    ),
                    ("evidenceClass", "fixture"),
                ),
            )
            await asyncio.sleep(0)
            evidence = EvidenceRecord(
                evidence_id=task.task_id.replace("task_", "evidence_", 1),
                kind=EvidenceKind.FIXTURE,
                summary=(
                    "The deterministic local runner classified the objective and "
                    "prepared a bounded plan; no external source was consulted."
                ),
                source=EvidenceSource.LOCAL_RUNNER,
                verified=False,
            )
            await self.repository.record_evidence(task.task_id, evidence)
            plan = ProposedPlan(
                revision=1,
                title="Safe local fixture plan",
                steps=_plan_for(task.objective),
                evidence_refs=(evidence.evidence_id,),
            )
            await self.repository.set_plan(
                task.task_id,
                plan=plan,
                event_name=TaskEventName.PLAN_PROPOSED,
            )
            await self._run_interrupt_loop(task, plan)
        except asyncio.CancelledError:
            raise
        except Exception:
            await self._record_safe_failure(task)

    async def _run_interrupt_loop(self, task: TaskSnapshot, plan: ProposedPlan) -> None:
        generation = 0
        while True:
            interrupt_id = _interrupt_id(task.task_id, generation)
            await self.repository.append_event(
                task.task_id,
                name=TaskEventName.INTERRUPT_REQUESTED,
                data=(
                    ("interruptId", interrupt_id),
                    ("question", "Approve this local fixture plan or provide guidance?"),
                    ("decisions", ("approve", "reject", "respond")),
                    ("planRevision", plan.revision),
                ),
                status=TaskStatus.WAITING_APPROVAL,
                pending_interrupt_id=interrupt_id,
            )
            decision = await self.repository.wait_for_decision(task.task_id, interrupt_id)
            if decision is DecisionValue.REJECT:
                await self._complete_rejected(task)
                return
            if decision is DecisionValue.APPROVE:
                current = await self.repository.get_task(task.task_id)
                approved_plan = current.proposed_plan
                if approved_plan is None:
                    raise RuntimeError("approved task has no proposed plan")
                await self._complete_approved(task, approved_plan)
                return

            generation += 1
            current = await self.repository.get_task(task.task_id)
            current_plan = current.proposed_plan
            if current_plan is None:
                raise RuntimeError("responded task has no proposed plan")
            response_evidence = EvidenceRecord(
                evidence_id=f"{task.task_id.replace('task_', 'evidence_', 1)}_{generation:02d}",
                kind=EvidenceKind.FIXTURE,
                summary=(
                    "Additional reviewer guidance was recorded locally. Its text is "
                    "intentionally excluded from replayable evidence."
                ),
                source=EvidenceSource.REVIEWER_RESPONSE,
                verified=False,
            )
            await self.repository.record_evidence(task.task_id, response_evidence)
            plan = ProposedPlan(
                revision=current_plan.revision + 1,
                title="Safe local fixture plan (guidance recorded)",
                steps=current_plan.steps,
                evidence_refs=(*current_plan.evidence_refs, response_evidence.evidence_id),
            )
            await self.repository.set_plan(
                task.task_id,
                plan=plan,
                event_name=TaskEventName.PLAN_PROPOSED,
            )

    async def _complete_approved(self, task: TaskSnapshot, plan: ProposedPlan) -> None:
        result = _build_task_brief(task.objective, plan)
        await self.repository.append_event(
            task.task_id,
            name=TaskEventName.CONTENT_DELTA,
            data=(("text", result), ("evidenceClass", "fixture")),
        )
        await self.repository.append_event(
            task.task_id,
            name=TaskEventName.RUN_COMPLETED,
            data=(
                ("runId", task.run_id),
                ("status", TaskStatus.COMPLETED.value),
                ("safeReason", "Completed by the deterministic local fixture runner."),
                ("resultAvailable", True),
            ),
            status=TaskStatus.COMPLETED,
            clear_pending_interrupt=True,
            result=result,
        )

    async def _complete_rejected(self, task: TaskSnapshot) -> None:
        await self.repository.append_event(
            task.task_id,
            name=TaskEventName.RUN_COMPLETED,
            data=(
                ("runId", task.run_id),
                ("status", TaskStatus.REJECTED.value),
                ("safeReason", "The pending local fixture plan was rejected."),
                ("resultAvailable", False),
            ),
            status=TaskStatus.REJECTED,
            clear_pending_interrupt=True,
        )

    async def _record_safe_failure(self, task: TaskSnapshot) -> None:
        try:
            await self.repository.append_event(
                task.task_id,
                name=TaskEventName.RUN_COMPLETED,
                data=(
                    ("runId", task.run_id),
                    ("status", TaskStatus.FAILED.value),
                    ("safeReason", "The local fixture runner failed safely."),
                    ("resultAvailable", False),
                ),
                status=TaskStatus.FAILED,
                clear_pending_interrupt=True,
            )
        except Exception:
            # A terminal/concurrent transition already owns the truthful state.
            return


@dataclass(frozen=True, slots=True)
class TaskService:
    """Coordinate task commands, queries, decisions, and event replay."""

    repository: TaskRepository
    runner: DeterministicFixtureRunner | LocalAgentServerRunner

    async def create_task(self, prompt: str) -> TaskSnapshot:
        """Create a queued task and start its deterministic runner."""

        objective = sanitize_objective(prompt)
        title = _build_task_title(objective)
        if isinstance(self.runner, LocalAgentServerRunner):
            return await self.runner.create(title=title, objective=objective)
        task = await self.repository.create_task(title=title, objective=objective)
        self.runner.start(task)
        return task

    async def list_tasks(self) -> tuple[TaskSnapshot, ...]:
        """List local task summaries."""

        return await self.repository.list_tasks()

    async def get_task(self, task_id: str) -> TaskSnapshot:
        """Read one local task."""

        return await self.repository.get_task(task_id)

    async def record_decision(
        self,
        task_id: str,
        *,
        interrupt_id: str,
        decision: DecisionValue,
        comment: str | None,
    ) -> DecisionRecord:
        """Record one bounded interrupt decision without replaying comment text."""

        response_digest = (
            hashlib.sha256(comment.encode()).hexdigest()
            if decision is DecisionValue.RESPOND and comment is not None
            else None
        )
        if isinstance(self.runner, LocalAgentServerRunner):
            return await self.runner.record_decision(
                task_id,
                interrupt_id=interrupt_id,
                decision=decision,
                comment=comment,
                comment_provided=bool(comment),
                response_digest=response_digest,
            )
        if isinstance(self.runner, LocalAgentServerRunner):
            return await self.runner.record_decision(
                task_id,
                interrupt_id=interrupt_id,
                decision=decision,
                comment=comment,
                comment_provided=bool(comment),
                response_digest=response_digest,
            )
        return await self.repository.record_decision(
            task_id,
            interrupt_id=interrupt_id,
            decision=decision,
            comment_provided=bool(comment),
            response_digest=response_digest,
        )

    async def update_plan(
        self,
        task_id: str,
        *,
        interrupt_id: str,
        expected_revision: int,
        steps: tuple[str, ...],
    ) -> PlanUpdateRecord:
        """Edit the current plan before resuming its exact interrupt."""

        sanitized_steps = tuple(sanitize_objective(step) for step in steps)
        if isinstance(self.runner, LocalAgentServerRunner):
            task = await self.repository.get_task(task_id)
            return await self.runner.update_plan(
                task,
                interrupt_id=interrupt_id,
                expected_revision=expected_revision,
                steps=sanitized_steps,
            )
        return await self.repository.update_plan(
            task_id,
            interrupt_id=interrupt_id,
            expected_revision=expected_revision,
            steps=sanitized_steps,
        )

    async def validate_event_cursor(self, task_id: str, event_id: int) -> None:
        """Validate task existence and replay cursor before opening SSE."""

        await self.repository.events_after(task_id, event_id)

    async def stream_events(self, task_id: str, event_id: int) -> AsyncIterator[TaskEvent]:
        """Replay then follow normalized events until the task is terminal."""

        cursor = event_id
        while True:
            events = await self.repository.events_after(task_id, cursor)
            for event in events:
                yield event
                cursor = event.event_id

            task = await self.repository.get_task(task_id)
            if task.status.is_terminal and cursor >= task.last_event_id:
                return
            await self.repository.wait_for_events(task_id, cursor)


def _interrupt_id(task_id: str, generation: int) -> str:
    task_number = int(task_id.removeprefix("task_"))
    value = task_number + generation * 10_000_000
    if value > 99_999_999:
        raise RuntimeError("local fixture interrupt bound exceeded")
    return f"interrupt_{value:08d}"

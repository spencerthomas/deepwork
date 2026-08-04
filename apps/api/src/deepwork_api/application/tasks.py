"""Task use cases and deterministic asynchronous fixture execution."""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

from deepwork_api.application.local_runner import (
    LocalAgentServerRunner,
    LocalAgentSummary,
    LocalScheduleSummary,
)
from deepwork_api.domain import (
    DEFAULT_SECURITY_CONTEXT,
    MAX_PLAN_STEP_LENGTH,
    MAX_TASK_OBJECTIVE_LENGTH,
    AgentRegistryUnavailableError,
    CancellationRecord,
    DecisionBatchRecord,
    DecisionBatchUnsupportedError,
    DecisionBatchVersionStaleError,
    DecisionRecord,
    DecisionType,
    DecisionValue,
    EvidenceKind,
    EvidenceRecord,
    EvidenceSource,
    InterruptMismatchError,
    InvalidDecisionBatchError,
    OrderedDecision,
    PlanUnavailableError,
    PlanUpdateRecord,
    ProposedPlan,
    ScheduleRegistryUnavailableError,
    SecurityContext,
    TaskCancellationUnsupportedError,
    TaskCreation,
    TaskEvent,
    TaskEventName,
    TaskJourney,
    TaskNotFoundError,
    TaskSnapshot,
    TaskSourceUnavailableError,
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
_FIXTURE_REPOSITORY_ID = "fixture_repo_deepwork"
_FIXTURE_AGENT_ID = "deepwork-fixture-planner"


@dataclass(frozen=True, slots=True)
class _FixtureAgent:
    agent_id: str = _FIXTURE_AGENT_ID
    name: str = "Deep Work Planner"
    description: str = "Plans, pauses for review, and returns an evidence-backed local result."
    system_prompt: str | None = None
    is_default: bool = True
    created_at: str = "2026-01-01T00:00:00Z"
    updated_at: str = "2026-01-01T00:00:00Z"


_FIXTURE_AGENT = _FixtureAgent()


class _FixturePrCreateTimeout(Exception):
    """Signal the fixture timeout that occurs after a draft PR is retained."""


@dataclass(frozen=True, slots=True)
class _FixtureDraftPullRequest:
    number: int
    status: str


@dataclass(frozen=True, slots=True)
class _FixturePrCreateResult:
    draft_pr_number: int
    draft_pr_status: str
    pr_create_attempts: int
    reconciled_after_timeout: bool
    created_draft_numbers: tuple[int, ...]


@dataclass(slots=True)
class _FixturePrCreateState:
    """Model one timeout followed by lookup-based reconciliation."""

    attempts: int = 0
    retained_draft: _FixtureDraftPullRequest | None = None
    created_draft_numbers: list[int] = field(default_factory=list)
    timed_out_after_create: bool = False
    reconciled_after_timeout: bool = False

    def create_draft(self) -> None:
        """Retain draft PR 17, then simulate losing the create response."""

        if self.retained_draft is not None:
            raise RuntimeError("fixture draft PR was already created")
        self.attempts += 1
        self.retained_draft = _FixtureDraftPullRequest(number=17, status="draft")
        self.created_draft_numbers.append(self.retained_draft.number)
        self.timed_out_after_create = True
        raise _FixturePrCreateTimeout

    def lookup_retained_draft(self) -> _FixtureDraftPullRequest:
        """Return the retained draft instead of creating a duplicate."""

        self.attempts += 1
        if not self.timed_out_after_create or self.retained_draft is None:
            raise RuntimeError("fixture draft lookup has no timed-out create")
        self.reconciled_after_timeout = True
        return self.retained_draft

    def result(self, draft: _FixtureDraftPullRequest) -> _FixturePrCreateResult:
        if not self.reconciled_after_timeout or draft is not self.retained_draft:
            raise RuntimeError("fixture draft PR was not reconciled")
        return _FixturePrCreateResult(
            draft_pr_number=draft.number,
            draft_pr_status=draft.status,
            pr_create_attempts=self.attempts,
            reconciled_after_timeout=self.reconciled_after_timeout,
            created_draft_numbers=tuple(self.created_draft_numbers),
        )


def _reconcile_fixture_draft_pr_after_timeout() -> _FixturePrCreateResult:
    state = _FixturePrCreateState()
    try:
        state.create_draft()
    except _FixturePrCreateTimeout:
        retained_draft = state.lookup_retained_draft()
    else:  # pragma: no cover - the fixture create always loses its response
        raise RuntimeError("fixture draft create did not time out")
    return state.result(retained_draft)


def _digest_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _validate_task_idempotency_key(value: str) -> None:
    if (
        not value.strip()
        or len(value) > 128
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise ValueError("task idempotency key is invalid")


def _task_request_fingerprint(
    *,
    objective: str,
    agent_id: str | None,
    journey: TaskJourney | None,
    repository_id: str | None,
) -> str:
    normalized = json.dumps(
        {
            "agent": agent_id,
            "journey": journey.value if journey is not None else None,
            "prompt": objective,
            "repository": repository_id,
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return _digest_text(normalized)


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
                task_id=task.task_id,
                run_id=task.run_id,
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
                task_id=task.task_id,
                run_id=task.run_id,
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
        # Keep the real post-approval running state observable long enough for
        # clients to render live progress before the deterministic result lands.
        # This is a bounded fixture delay, not simulated provider latency.
        await asyncio.sleep(1.25)
        result = _build_task_brief(task.objective, plan)
        await self.repository.append_event(
            task.task_id,
            name=TaskEventName.CONTENT_DELTA,
            data=(("text", result), ("evidenceClass", "fixture")),
        )
        if task.journey is TaskJourney.CODING:
            if task.repository_id != _FIXTURE_REPOSITORY_ID:
                raise RuntimeError("coding fixture task lost its repository binding")
            pull_request = _reconcile_fixture_draft_pr_after_timeout()
            await self.repository.append_event(
                task.task_id,
                name=TaskEventName.CODING_COMPLETED,
                data=(
                    ("evidenceClass", "fixture"),
                    ("repositoryId", _FIXTURE_REPOSITORY_ID),
                    ("repository", "deepwork-fixtures/sample-app"),
                    ("baseBranch", "main"),
                    ("baseSha", "5d8f2de17703cb32fc4c6f6d7af0258ddf5f0f17"),
                    ("headSha", "bb525814d85c6e2e35233d703e0a4069dd625d75"),
                    ("environment", "Deep Work Node fixture"),
                    ("environmentVersion", 1),
                    ("snapshotDigest", "sha256:4e7d3f64f7df824d"),
                    ("sandboxState", "cleaned"),
                    ("setupStatus", "passed"),
                    ("changedFiles", ("src/session.ts", "tests/session.test.ts")),
                    ("draftPrNumber", pull_request.draft_pr_number),
                    ("draftPrStatus", pull_request.draft_pr_status),
                    ("prCreateAttempts", pull_request.pr_create_attempts),
                    ("reconciledAfterTimeout", pull_request.reconciled_after_timeout),
                    ("checks", ("lint:passed", "tests:passed")),
                    ("mergeState", "unavailable"),
                ),
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


@dataclass(slots=True)
class TaskService:
    """Coordinate task commands, queries, decisions, and event replay."""

    repository: TaskRepository
    runner: DeterministicFixtureRunner | LocalAgentServerRunner

    @property
    def batch_allowed_decisions(self) -> tuple[DecisionType, ...] | None:
        """Advertise only decisions this configured runner can submit atomically."""

        if isinstance(self.runner, LocalAgentServerRunner):
            return None
        return (
            DecisionType.APPROVE,
            DecisionType.EDIT,
            DecisionType.REJECT,
        )

    async def create_task(
        self,
        prompt: str,
        *,
        agent_id: str | None = None,
        journey: TaskJourney | None = None,
        repository_id: str | None = None,
        idempotency_key: str | None = None,
        security_context: SecurityContext = DEFAULT_SECURITY_CONTEXT,
    ) -> TaskCreation:
        """Create a queued task and start its deterministic runner.

        ``agent_id`` selects a specific registered agent for a real-agent-mode
        task or the immutable local fixture agent in credential-free mode.
        """

        # The fingerprint represents the caller's validated immutable request,
        # not the redacted value retained by the application. Distinct secrets
        # must conflict even when both sanitize to the same safe objective.
        request_fingerprint = _task_request_fingerprint(
            objective=prompt,
            agent_id=agent_id,
            journey=journey,
            repository_id=repository_id,
        )
        objective = sanitize_objective(prompt)
        title = _build_task_title(objective)
        if journey is TaskJourney.CODING:
            if repository_id != _FIXTURE_REPOSITORY_ID:
                raise TaskSourceUnavailableError
            if isinstance(self.runner, LocalAgentServerRunner):
                # The reviewed GitHub proxy/sandbox contracts remain gated. A
                # real source must never fall back to a browser or host token.
                raise TaskSourceUnavailableError
        elif repository_id is not None:
            raise TaskSourceUnavailableError
        if idempotency_key is not None:
            _validate_task_idempotency_key(idempotency_key)
            return await self._create_task(
                title=title,
                objective=objective,
                agent_id=agent_id,
                journey=journey,
                repository_id=repository_id,
                idempotency_key=idempotency_key,
                request_fingerprint=request_fingerprint,
                security_context=security_context,
            )
        return await self._create_task(
            title=title,
            objective=objective,
            agent_id=agent_id,
            journey=journey,
            repository_id=repository_id,
            idempotency_key=None,
            request_fingerprint=request_fingerprint,
            security_context=security_context,
        )

    async def _create_task(
        self,
        *,
        title: str,
        objective: str,
        agent_id: str | None,
        journey: TaskJourney | None,
        repository_id: str | None,
        idempotency_key: str | None,
        request_fingerprint: str,
        security_context: SecurityContext,
    ) -> TaskCreation:
        if isinstance(self.runner, LocalAgentServerRunner):
            return await self.runner.create(
                title=title,
                objective=objective,
                agent_id=agent_id,
                idempotency_key=idempotency_key,
                request_fingerprint=request_fingerprint,
                security_context=security_context,
            )
        if agent_id is not None and agent_id != _FIXTURE_AGENT_ID:
            raise TaskSourceUnavailableError
        if idempotency_key is None:
            task = await self.repository.create_task(
                title=title,
                objective=objective,
                agent_id=agent_id,
                journey=journey,
                repository_id=repository_id,
                security_context=security_context,
            )
            created = True
        else:
            creation = await self.repository.create_task_idempotently(
                title=title,
                objective=objective,
                agent_id=agent_id,
                journey=journey,
                repository_id=repository_id,
                idempotency_key=idempotency_key,
                request_fingerprint=request_fingerprint,
                security_context=security_context,
            )
            task = creation.task
            created = creation.created
        if created:
            self.runner.start(task)
        return TaskCreation(task=task, created=created)

    async def list_agents(self) -> tuple[LocalAgentSummary, ...]:
        """List agents registered on the configured real task source.

        Fixture mode exposes one immutable, explicitly labeled local agent so
        the same choose-agent contract is exercised without provider calls.
        """

        if not isinstance(self.runner, LocalAgentServerRunner):
            return (_FIXTURE_AGENT,)
        return await self.runner.list_agents()

    async def create_agent(
        self, *, name: str, description: str | None, system_prompt: str | None
    ) -> LocalAgentSummary:
        """Register a new agent sharing the deployed graph."""

        if not isinstance(self.runner, LocalAgentServerRunner):
            raise AgentRegistryUnavailableError
        return await self.runner.create_agent(
            name=name, description=description, system_prompt=system_prompt
        )

    async def update_agent(
        self,
        agent_id: str,
        *,
        name: str,
        description: str | None,
        system_prompt: str | None,
    ) -> LocalAgentSummary:
        """Replace the editable fields of one non-default registered agent."""

        if not isinstance(self.runner, LocalAgentServerRunner):
            raise AgentRegistryUnavailableError
        return await self.runner.update_agent(
            agent_id, name=name, description=description, system_prompt=system_prompt
        )

    async def delete_agent(self, agent_id: str) -> None:
        """Remove one non-default registered agent."""

        if not isinstance(self.runner, LocalAgentServerRunner):
            raise AgentRegistryUnavailableError
        await self.runner.delete_agent(agent_id)

    async def list_schedules(self) -> tuple[LocalScheduleSummary, ...]:
        """List recurring runs registered on the configured real task source.

        Fixture mode owns no schedule registry, so this reports an honest
        unavailable state instead of a fabricated empty list.
        """

        if not isinstance(self.runner, LocalAgentServerRunner):
            raise ScheduleRegistryUnavailableError
        return await self.runner.list_schedules()

    async def list_tasks(
        self, security_context: SecurityContext = DEFAULT_SECURITY_CONTEXT
    ) -> tuple[TaskSnapshot, ...]:
        """List local task summaries."""

        tasks = await self.repository.list_tasks()
        return tuple(task for task in tasks if self._is_owned_by(task, security_context))

    async def get_task(
        self, task_id: str, security_context: SecurityContext = DEFAULT_SECURITY_CONTEXT
    ) -> TaskSnapshot:
        """Read one local task."""

        return await self._get_owned_task(task_id, security_context)

    @staticmethod
    def _is_owned_by(task: TaskSnapshot, security_context: SecurityContext) -> bool:
        return (
            task.tenant_id == security_context.tenant_id
            and task.workspace_id == security_context.workspace_id
        )

    async def _get_owned_task(
        self, task_id: str, security_context: SecurityContext
    ) -> TaskSnapshot:
        task = await self.repository.get_task(task_id)
        if not self._is_owned_by(task, security_context):
            raise TaskNotFoundError
        return task

    async def cancel_task(
        self, task_id: str, security_context: SecurityContext = DEFAULT_SECURITY_CONTEXT
    ) -> CancellationRecord:
        """Cancel a live task, recording an honest terminal cancelled state.

        This is only truthful when Deep Work itself executes the task: the
        deterministic fixture runner runs the work in-process, so marking the
        repository terminal genuinely stops it. The gated loopback Agent Server
        source exposes no cancel operation and streams with
        ``cancel_on_disconnect=False``, so marking the task terminal would leave
        the upstream run executing while reporting it stopped. That mode refuses
        cancellation rather than publishing a false terminal state.

        For the fixture runner the cancellation is applied to the authoritative
        repository, whose terminal guard stops the background follower the next
        time it touches task state; no separate runner command is required.
        """

        await self._get_owned_task(task_id, security_context)
        if isinstance(self.runner, LocalAgentServerRunner):
            raise TaskCancellationUnsupportedError
        return await self.repository.cancel_task(task_id)

    async def record_decision(
        self,
        task_id: str,
        *,
        interrupt_id: str,
        decision: DecisionValue,
        comment: str | None,
        security_context: SecurityContext = DEFAULT_SECURITY_CONTEXT,
    ) -> DecisionRecord:
        """Record one bounded interrupt decision without replaying comment text."""

        await self._get_owned_task(task_id, security_context)
        response_digest = (
            _digest_text(comment)
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
        return await self.repository.record_decision(
            task_id,
            interrupt_id=interrupt_id,
            decision=decision,
            comment_provided=bool(comment),
            response_digest=response_digest,
        )

    async def record_decision_batch(
        self,
        task_id: str,
        *,
        interrupt_id: str,
        expected_version: str,
        idempotency_key: str,
        decisions: tuple[OrderedDecision, ...],
        security_context: SecurityContext = DEFAULT_SECURITY_CONTEXT,
    ) -> DecisionBatchRecord:
        """Validate and atomically accept one complete positional plan vector."""

        task = await self._get_owned_task(task_id, security_context)
        if task.pending_interrupt_id is not None and task.pending_interrupt_id != interrupt_id:
            raise InterruptMismatchError
        plan = task.proposed_plan
        if plan is None:
            raise PlanUnavailableError
        version = str(plan.revision)
        if task.pending_interrupt_id is not None and expected_version != version:
            raise DecisionBatchVersionStaleError
        try:
            expected_revision = int(expected_version)
        except ValueError:
            raise DecisionBatchVersionStaleError from None
        if str(expected_revision) != expected_version:
            raise DecisionBatchVersionStaleError
        if len(decisions) != len(plan.steps):
            raise InvalidDecisionBatchError

        uses_agent_server = isinstance(self.runner, LocalAgentServerRunner)
        if uses_agent_server:
            raise DecisionBatchUnsupportedError

        edited_steps = list(plan.steps)
        canonical: list[dict[str, object]] = []
        decision_types: list[DecisionType] = []
        advertised_decisions = self.batch_allowed_decisions
        allowed = (
            set(advertised_decisions)
            if advertised_decisions is not None
            else {DecisionType.APPROVE, DecisionType.REJECT, DecisionType.RESPOND}
        )
        for position, decision_input in enumerate(decisions, start=1):
            if decision_input.decision_type not in allowed:
                raise InvalidDecisionBatchError
            decision_types.append(decision_input.decision_type)
            item: dict[str, object] = {"type": decision_input.decision_type.value}
            if decision_input.decision_type is DecisionType.EDIT:
                if (
                    decision_input.edited_action_name != "execute_plan_step"
                    or decision_input.edited_position != position
                    or decision_input.edited_text is None
                ):
                    raise InvalidDecisionBatchError
                edited_text = sanitize_objective(decision_input.edited_text)
                if not edited_text.strip() or len(edited_text) > MAX_PLAN_STEP_LENGTH:
                    raise InvalidDecisionBatchError
                edited_steps[position - 1] = edited_text
                item["editedAction"] = {
                    "name": "execute_plan_step",
                    "args": {"position": position, "text": edited_text},
                }
            elif any(
                value is not None
                for value in (
                    decision_input.edited_action_name,
                    decision_input.edited_position,
                    decision_input.edited_text,
                )
            ):
                raise InvalidDecisionBatchError
            message_digest = (
                _digest_text(decision_input.message) if decision_input.message is not None else None
            )
            if message_digest is not None:
                item["messageDigest"] = message_digest
            if decision_input.decision_type is DecisionType.RESPOND and (
                decision_input.message is None or not decision_input.message.strip()
            ):
                raise InvalidDecisionBatchError
            canonical.append(item)

        vector_digest = _digest_text(json.dumps(canonical, sort_keys=True, separators=(",", ":")))
        if not idempotency_key.strip() or len(idempotency_key) > 128:
            raise InvalidDecisionBatchError
        request_fingerprint = _digest_text(
            f"{expected_version}:{_digest_text(idempotency_key)}:{vector_digest}"
        )
        types = tuple(decision_types)
        return await self.repository.record_decision_batch(
            task_id,
            interrupt_id=interrupt_id,
            expected_revision=expected_revision,
            decision_types=types,
            request_fingerprint=request_fingerprint,
            edited_steps=tuple(edited_steps),
        )

    async def update_plan(
        self,
        task_id: str,
        *,
        interrupt_id: str,
        expected_revision: int,
        steps: tuple[str, ...],
        security_context: SecurityContext = DEFAULT_SECURITY_CONTEXT,
    ) -> PlanUpdateRecord:
        """Edit the current plan before resuming its exact interrupt."""

        task = await self._get_owned_task(task_id, security_context)
        sanitized_steps = tuple(sanitize_objective(step) for step in steps)
        if isinstance(self.runner, LocalAgentServerRunner):
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

    async def validate_event_cursor(
        self,
        task_id: str,
        event_id: int,
        security_context: SecurityContext = DEFAULT_SECURITY_CONTEXT,
    ) -> None:
        """Validate task existence and replay cursor before opening SSE."""

        await self._get_owned_task(task_id, security_context)
        await self.repository.events_after(task_id, event_id)

    async def stream_events(
        self,
        task_id: str,
        event_id: int,
        security_context: SecurityContext = DEFAULT_SECURITY_CONTEXT,
    ) -> AsyncIterator[TaskEvent]:
        """Replay then follow normalized events until the task is terminal."""

        cursor = event_id
        await self._get_owned_task(task_id, security_context)
        while True:
            events = await self.repository.events_after(task_id, cursor)
            for event in events:
                yield event
                cursor = event.event_id

            task = await self._get_owned_task(task_id, security_context)
            if task.status.is_terminal and cursor >= task.last_event_id:
                return
            await self.repository.wait_for_events(task_id, cursor)


def _interrupt_id(task_id: str, generation: int) -> str:
    task_number = int(task_id.removeprefix("task_"))
    value = task_number + generation * 10_000_000
    if value > 99_999_999:
        raise RuntimeError("local fixture interrupt bound exceeded")
    return f"interrupt_{value:08d}"

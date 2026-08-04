"""Application mapping for the explicitly configured loopback source."""

from __future__ import annotations

import asyncio
import hashlib
import uuid
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass, field
from typing import Protocol

from deepwork_api.domain import (
    DEFAULT_SECURITY_CONTEXT,
    DecisionRecord,
    DecisionValue,
    EvidenceClass,
    InterruptMismatchError,
    PlanRevisionConflictError,
    PlanUnavailableError,
    PlanUpdateRecord,
    ProposedPlan,
    SecurityContext,
    StaleInterruptError,
    TaskCreation,
    TaskEventName,
    TaskSnapshot,
    TaskSourceContractError,
    TaskSourceLease,
    TaskSourcePlanTransition,
    TaskSourceUnavailableError,
    TaskStatus,
)
from deepwork_api.ports import PromptStore, TaskRepository

_SOURCE_UNAVAILABLE_REASON = "The local agent source became unavailable."
_SOURCE_CONTRACT_REASON = "The local agent source broke its supported contract."
_RUNNER_FAILURE_REASON = "The local source task runner failed safely."
_TERMINAL_REASON = "Local Agent Server run reached a terminal state."
_RESUME_SHUTDOWN_GRACE_SECONDS = 1.0
_SOURCE_STATE_RECONCILIATION_SECONDS = 1.0
_SOURCE_STATE_RECONCILIATION_MAX_SECONDS = 8.0
_SOURCE_LEASE_SECONDS = 15
_SOURCE_RECOVERY_MAX_DELAY_SECONDS = 2.0


class _SourceHandoffPersistenceError(Exception):
    """An accepted upstream transition still needs durable local reconciliation."""


async def _next_source_event(stream: AsyncIterator[object]) -> object:
    """Present ``anext`` as a coroutine accepted by ``asyncio.create_task``."""

    return await anext(stream)


def _source_event_key(thread_id: str, run_id: str, provider_cursor: object) -> str:
    """Derive a bounded application receipt without retaining provider data."""

    if not isinstance(provider_cursor, str) or not provider_cursor:
        raise TaskSourceContractError
    digest = hashlib.sha256()
    for value in (thread_id, run_id, provider_cursor):
        encoded = value.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, byteorder="big"))
        digest.update(encoded)
    return digest.hexdigest()


def _source_transition_id(task_id: str, interrupt_id: str) -> str:
    """Derive a stable bounded acknowledgement identity from application IDs."""

    digest = hashlib.sha256(f"{task_id}:{interrupt_id}".encode()).hexdigest()
    return f"transition-{digest}"


def _source_plan_transition_id(
    task_id: str,
    interrupt_id: str,
    expected_revision: int,
    steps: Sequence[str],
) -> str:
    """Derive one stable identity from the exact bounded plan-edit request."""

    digest = hashlib.sha256()
    for value in (task_id, interrupt_id, str(expected_revision), *steps):
        encoded = value.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, byteorder="big"))
        digest.update(encoded)
    return f"plan-transition-{digest.hexdigest()}"


def _local_task_run_id() -> str:
    """Create a globally unique, public-safe application run identity."""

    return f"run_{uuid.uuid4().hex}"


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


class LocalAgentSummary(Protocol):
    """One assistant sharing the deployed graph, sanitized by the source."""

    @property
    def agent_id(self) -> str: ...
    @property
    def name(self) -> str: ...
    @property
    def description(self) -> str | None: ...
    @property
    def system_prompt(self) -> str | None: ...
    @property
    def is_default(self) -> bool: ...
    @property
    def created_at(self) -> str: ...
    @property
    def updated_at(self) -> str: ...


class LocalScheduleSummary(Protocol):
    """One recurring run (cron) on our deployed graph, sanitized by the source."""

    @property
    def schedule_id(self) -> str: ...
    @property
    def agent_id(self) -> str: ...
    @property
    def cron_expression(self) -> str: ...
    @property
    def timezone(self) -> str | None: ...
    @property
    def end_time(self) -> str | None: ...
    @property
    def created_at(self) -> str: ...
    @property
    def updated_at(self) -> str: ...


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
    async def start(
        self,
        objective: str,
        *,
        dispatch_id: str,
        system_prompt: str | None = None,
        agent_id: str | None = None,
    ) -> LocalRun: ...
    async def get_state(self, thread_id: str) -> LocalState: ...
    async def resume(
        self,
        thread_id: str,
        *,
        interrupt_id: str,
        decision: str,
        transition_id: str,
        comment: str | None = None,
        agent_id: str | None = None,
    ) -> LocalRun: ...
    async def update_plan(
        self,
        thread_id: str,
        *,
        interrupt_id: str,
        expected_revision: int,
        steps: Sequence[str],
        transition_id: str,
        agent_id: str | None = None,
    ) -> LocalPlanUpdate: ...
    def stream(
        self,
        run: LocalRun,
        *,
        after_cursor: str | None = None,
    ) -> AsyncIterator[object]: ...
    async def list_agents(self) -> tuple[LocalAgentSummary, ...]: ...
    async def create_agent(
        self, *, name: str, description: str | None, system_prompt: str | None
    ) -> LocalAgentSummary: ...
    async def update_agent(
        self,
        agent_id: str,
        *,
        name: str,
        description: str | None,
        system_prompt: str | None,
    ) -> LocalAgentSummary: ...
    async def delete_agent(self, agent_id: str) -> None: ...
    async def list_schedules(self) -> tuple[LocalScheduleSummary, ...]: ...


@dataclass(slots=True)
class LocalAgentServerRunner:
    """Project source-authoritative state into the existing normalized task API."""

    repository: TaskRepository
    source: LocalSource
    prompt_store: PromptStore | None = None
    _threads: dict[str, str] = field(default_factory=dict, init=False)
    _tasks: dict[str, asyncio.Task[None]] = field(default_factory=dict, init=False)
    _review_comments: dict[tuple[str, str], str] = field(default_factory=dict, init=False)
    _resume_acknowledgements: dict[tuple[str, str], asyncio.Future[None]] = field(
        default_factory=dict, init=False
    )
    _command_locks: dict[str, asyncio.Lock] = field(default_factory=dict, init=False)
    _resumes_in_flight: set[tuple[str, str]] = field(default_factory=set, init=False)
    _plan_updates: dict[str, asyncio.Task[PlanUpdateRecord]] = field(
        default_factory=dict,
        init=False,
    )
    _plan_update_requests: dict[str, tuple[str, int, tuple[str, ...]]] = field(
        default_factory=dict,
        init=False,
    )
    _owner_id: str = field(
        default_factory=lambda: f"source-owner-{uuid.uuid4().hex}",
        init=False,
    )
    _source_leases: dict[str, TaskSourceLease] = field(default_factory=dict, init=False)
    _lease_heartbeats: dict[str, asyncio.Task[None]] = field(default_factory=dict, init=False)
    _recovery_tasks: dict[str, asyncio.Task[None]] = field(default_factory=dict, init=False)
    _closing: bool = field(default=False, init=False)

    async def create(
        self,
        *,
        title: str,
        objective: str,
        agent_id: str | None = None,
        idempotency_key: str | None = None,
        request_fingerprint: str | None = None,
        security_context: SecurityContext = DEFAULT_SECURITY_CONTEXT,
    ) -> TaskCreation:
        # The source owns assistant identity and suppresses this workspace
        # override when a different named agent is selected. Keeping that
        # decision at the adapter boundary avoids a second registry lookup.
        if idempotency_key is not None:
            if request_fingerprint is None:
                raise ValueError("idempotent task creation requires a request fingerprint")
            # Persist the scoped request before crossing the source boundary.
            # The atomic repository receipt is the durable dispatch claim: only
            # its creator may call source.start. Replays and other API processes
            # return the same task without creating another upstream run.
            creation = await self.repository.create_task_idempotently(
                title=title,
                objective=objective,
                run_id=_local_task_run_id(),
                agent_id=agent_id,
                idempotency_key=idempotency_key,
                request_fingerprint=request_fingerprint,
                security_context=security_context,
            )
            task = creation.task
            if not creation.created:
                async with self._command_lock(task.task_id):
                    current = await self.repository.get_task(task.task_id)
                    if not current.status.is_terminal and task.task_id not in self._tasks:
                        if not await self.recover(current):
                            self.watch_recovery(current)
                        current = await self.repository.get_task(task.task_id)
                    return TaskCreation(task=current, created=False)
        else:
            task = await self.repository.create_task(
                title=title,
                objective=objective,
                run_id=_local_task_run_id(),
                agent_id=agent_id,
                security_context=security_context,
            )

        if not await self._acquire_source_lease(task.task_id):
            raise TaskSourceUnavailableError
        system_prompt = await self._current_system_prompt(security_context)
        try:
            run = await self.source.start(
                objective,
                dispatch_id=task.run_id,
                system_prompt=system_prompt,
                agent_id=agent_id,
            )
        except TaskSourceContractError:
            if task is not None:
                await self._fail(task, _SOURCE_CONTRACT_REASON)
                await self._release_source_lease(task.task_id)
            raise
        except Exception:
            if task is not None:
                await self._fail(task, _SOURCE_UNAVAILABLE_REASON)
                await self._release_source_lease(task.task_id)
            raise TaskSourceUnavailableError from None
        try:
            await self.repository.bind_source_run(
                task.task_id,
                thread_id=run.thread_id,
                run_id=run.run_id,
            )
        except asyncio.CancelledError:
            await self._release_source_lease(task.task_id)
            raise
        except Exception:
            await self._release_source_lease(task.task_id)
            raise TaskSourceUnavailableError from None
        self._threads[task.task_id] = run.thread_id
        self.start(task, run)
        return TaskCreation(task=task, created=True)

    async def list_agents(self) -> tuple[LocalAgentSummary, ...]:
        return await self.source.list_agents()

    async def create_agent(
        self, *, name: str, description: str | None, system_prompt: str | None
    ) -> LocalAgentSummary:
        return await self.source.create_agent(
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
        return await self.source.update_agent(
            agent_id, name=name, description=description, system_prompt=system_prompt
        )

    async def delete_agent(self, agent_id: str) -> None:
        await self.source.delete_agent(agent_id)

    async def list_schedules(self) -> tuple[LocalScheduleSummary, ...]:
        return await self.source.list_schedules()

    async def _current_system_prompt(self, security_context: SecurityContext) -> str | None:
        """Read the workspace's editable prompt; never let it block task start.

        A missing store means no override. A store that errors is treated as
        "no override" rather than failing the task, so an editable-prompt
        problem degrades to the deployment default instead of an outage.
        """
        if self.prompt_store is None:
            return None
        try:
            return await self.prompt_store.get_system_prompt(
                tenant_id=security_context.tenant_id,
                workspace_id=security_context.workspace_id,
            )
        except Exception:
            return None

    async def recover(self, task: TaskSnapshot) -> bool:
        """Rejoin one persisted non-terminal source task after API startup."""

        if not await self._acquire_source_lease(task.task_id):
            return False
        binding = await self.repository.get_source_binding(task.task_id)
        if binding is None:
            system_prompt = await self._current_system_prompt(
                SecurityContext(
                    tenant_id=task.tenant_id,
                    workspace_id=task.workspace_id,
                    actor_id=task.created_by_actor_id,
                )
            )
            run = await self.source.start(
                task.objective,
                dispatch_id=task.run_id,
                system_prompt=system_prompt,
                agent_id=task.agent_id,
            )
            binding = await self.repository.bind_source_run(
                task.task_id,
                thread_id=run.thread_id,
                run_id=run.run_id,
            )
        plan_transition = await self.repository.get_source_plan_transition(task.task_id)
        if plan_transition is not None:
            if (
                binding.pending_interrupt_id != plan_transition.interrupt_id
                or binding.pending_transition_id != plan_transition.transition_id
                or (binding.thread_id, binding.run_id)
                != (plan_transition.thread_id, plan_transition.run_id)
            ):
                raise TaskSourceContractError
            updated = await self.source.update_plan(
                binding.thread_id,
                interrupt_id=plan_transition.interrupt_id,
                expected_revision=plan_transition.expected_revision,
                steps=plan_transition.steps,
                transition_id=plan_transition.transition_id,
                agent_id=task.agent_id,
            )
            if (
                updated.interrupt_id == plan_transition.interrupt_id
                or updated.plan_revision != plan_transition.expected_revision + 1
            ):
                raise TaskSourceContractError
            binding = await self.repository.accept_source_plan_transition(
                task.task_id,
                thread_id=updated.thread_id,
                previous_run_id=binding.run_id,
                run_id=updated.run_id,
                transition_id=plan_transition.transition_id,
                new_interrupt_id=updated.interrupt_id,
                plan_revision=updated.plan_revision,
            )
            task = await self.repository.get_task(task.task_id)
        elif binding.pending_transition_id is not None:
            if binding.pending_interrupt_id is None:
                raise TaskSourceContractError
            transition_id = _source_transition_id(task.task_id, binding.pending_interrupt_id)
            if binding.pending_transition_id != transition_id:
                raise TaskSourceContractError
            decision = await self.repository.wait_for_decision(
                task.task_id,
                binding.pending_interrupt_id,
            )
            next_run = await self.source.resume(
                binding.thread_id,
                interrupt_id=binding.pending_interrupt_id,
                decision=decision.value,
                transition_id=transition_id,
                # Review comments are deliberately not retained. The source
                # can rediscover an already accepted response transition, but
                # a lost, unaccepted response must fail closed.
                comment=None,
                agent_id=task.agent_id,
            )
            binding = await self.repository.accept_source_transition(
                task.task_id,
                thread_id=next_run.thread_id,
                previous_run_id=binding.run_id,
                run_id=next_run.run_id,
                transition_id=transition_id,
            )
        self._threads[task.task_id] = binding.thread_id
        self.start(
            task,
            binding,
            announce_started=task.status is TaskStatus.QUEUED,
        )
        if task.pending_interrupt_id is not None:
            transition_id = _source_transition_id(task.task_id, task.pending_interrupt_id)
            if binding.accepted_transition_id == transition_id:
                self._accept_resume((task.task_id, task.pending_interrupt_id))
        return True

    def watch_recovery(self, task: TaskSnapshot) -> None:
        """Poll a peer-owned task until its lease expires or it finishes."""

        self._watch_recovery_id(task.task_id)

    def _watch_recovery_id(self, task_id: str) -> None:
        if self._closing or task_id in self._recovery_tasks:
            return
        recovery = asyncio.create_task(
            self._recover_when_available(task_id),
            name=f"deepwork-local-recovery-{task_id}",
        )
        self._recovery_tasks[task_id] = recovery
        recovery.add_done_callback(lambda finished: self._discard_recovery(task_id, finished))

    async def _recover_when_available(self, task_id: str) -> None:
        delay = min(0.25, _SOURCE_RECOVERY_MAX_DELAY_SECONDS)
        while not self._closing:
            task: TaskSnapshot | None = None
            try:
                task = await self.repository.get_task(task_id)
                if task.status.is_terminal or await self.recover(task):
                    return
            except TaskSourceContractError:
                if task is not None:
                    await self._fail(task, _SOURCE_CONTRACT_REASON)
                return
            except Exception:
                # A bounded retry preserves accepted work through a transient
                # source or persistence outage without publishing false failure.
                pass
            await asyncio.sleep(delay)
            delay = min(delay * 2, _SOURCE_RECOVERY_MAX_DELAY_SECONDS)

    def _discard_recovery(self, task_id: str, recovery: asyncio.Task[None]) -> None:
        if self._recovery_tasks.get(task_id) is recovery:
            self._recovery_tasks.pop(task_id, None)
        if not recovery.cancelled():
            recovery.exception()

    async def _acquire_source_lease(self, task_id: str) -> bool:
        if task_id in self._source_leases:
            return True
        lease = await self.repository.acquire_source_lease(
            task_id,
            owner_id=self._owner_id,
            lease_seconds=_SOURCE_LEASE_SECONDS,
        )
        if lease is None:
            return False
        self._source_leases[task_id] = lease
        heartbeat = asyncio.create_task(
            self._renew_source_lease(task_id),
            name=f"deepwork-local-lease-{task_id}",
        )
        self._lease_heartbeats[task_id] = heartbeat
        heartbeat.add_done_callback(lambda finished: self._discard_heartbeat(task_id, finished))
        return True

    async def _renew_source_lease(self, task_id: str) -> None:
        while not self._closing:
            await asyncio.sleep(_SOURCE_LEASE_SECONDS / 3)
            lease = self._source_leases.get(task_id)
            if lease is None:
                return
            try:
                task = await self.repository.get_task(task_id)
                if task.status.is_terminal:
                    await self._release_source_lease(task_id)
                    return
                renewed = await self.repository.renew_source_lease(
                    task_id,
                    lease_token=lease.lease_token,
                    lease_seconds=_SOURCE_LEASE_SECONDS,
                )
            except asyncio.CancelledError:
                raise
            except Exception:
                renewed = None
            if renewed is None:
                self._source_leases.pop(task_id, None)
                follower = self._tasks.get(task_id)
                if follower is not None:
                    follower.cancel()
                self._watch_recovery_id(task_id)
                return
            self._source_leases[task_id] = renewed

    def _discard_heartbeat(self, task_id: str, heartbeat: asyncio.Task[None]) -> None:
        if self._lease_heartbeats.get(task_id) is heartbeat:
            self._lease_heartbeats.pop(task_id, None)
        if not heartbeat.cancelled():
            heartbeat.exception()

    async def _release_source_lease(self, task_id: str) -> None:
        lease = self._source_leases.pop(task_id, None)
        if lease is None:
            return
        await self.repository.release_source_lease(
            task_id,
            lease_token=lease.lease_token,
        )

    def start(
        self,
        task: TaskSnapshot,
        run: LocalRun,
        *,
        announce_started: bool = True,
    ) -> None:
        if self._closing or task.task_id in self._tasks:
            return
        if task.pending_interrupt_id is not None:
            self._register_resume_acknowledgement((task.task_id, task.pending_interrupt_id))
        background = asyncio.create_task(
            self._follow(
                task,
                run,
                announce_started=announce_started,
            ),
            name=f"deepwork-local-{task.task_id}",
        )
        self._tasks[task.task_id] = background
        background.add_done_callback(lambda finished: self._discard(task.task_id, finished))

    async def close(self) -> None:
        self._closing = True
        active = dict(self._tasks)
        active_plan_updates = tuple(self._plan_updates.values())
        ownership_tasks = tuple(
            set(self._lease_heartbeats.values()) | set(self._recovery_tasks.values())
        )
        for ownership_task in ownership_tasks:
            ownership_task.cancel()
        resuming_task_ids = {task_id for task_id, _ in self._resumes_in_flight}
        draining = tuple(
            background for task_id, background in active.items() if task_id in resuming_task_ids
        )
        for task_id, follower in active.items():
            if task_id not in resuming_task_ids:
                follower.cancel()
        if draining:
            _, unfinished = await asyncio.wait(draining, timeout=_RESUME_SHUTDOWN_GRACE_SECONDS)
            for unfinished_task in unfinished:
                unfinished_task.cancel()
        remaining = tuple(
            task
            for task in set(active.values()) | set(self._tasks.values()) | set(active_plan_updates)
            if not task.done()
        )
        for remaining_task in remaining:
            remaining_task.cancel()
        tracked = tuple(set(active.values()) | set(self._tasks.values()) | set(active_plan_updates))
        if tracked:
            await asyncio.gather(*tracked, return_exceptions=True)
        if ownership_tasks:
            await asyncio.gather(*ownership_tasks, return_exceptions=True)
        for task_id in tuple(self._source_leases):
            await self._release_source_lease(task_id)
        for acknowledgement in self._resume_acknowledgements.values():
            if not acknowledgement.done():
                acknowledgement.set_exception(TaskSourceUnavailableError())
        self._tasks.clear()
        self._plan_updates.clear()
        self._plan_update_requests.clear()
        self._lease_heartbeats.clear()
        self._recovery_tasks.clear()

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
            request = (interrupt_id, expected_revision, steps)
            operation = self._plan_updates.get(task.task_id)
            if operation is None:
                operation = asyncio.create_task(
                    self._update_plan(
                        task,
                        interrupt_id=interrupt_id,
                        expected_revision=expected_revision,
                        steps=steps,
                    ),
                    name=f"deepwork-local-plan-{task.task_id}",
                )
                self._plan_updates[task.task_id] = operation
                self._plan_update_requests[task.task_id] = request
                operation.add_done_callback(
                    lambda finished: self._discard_plan_update(task.task_id, finished)
                )
            elif self._plan_update_requests.get(task.task_id) != request:
                raise TaskSourceContractError
            return await asyncio.shield(operation)

    def _discard_plan_update(
        self,
        task_id: str,
        operation: asyncio.Task[PlanUpdateRecord],
    ) -> None:
        """Retire an exact task-owned plan operation and consume its exception."""

        if self._plan_updates.get(task_id) is operation:
            self._plan_updates.pop(task_id, None)
            self._plan_update_requests.pop(task_id, None)
        if not operation.cancelled():
            operation.exception()

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
        binding = await self.repository.get_source_binding(task.task_id)
        if binding is None:
            raise TaskSourceContractError
        transition_id = _source_plan_transition_id(
            task.task_id,
            interrupt_id,
            expected_revision,
            steps,
        )
        transition = await self.repository.mark_source_plan_transition_pending(
            task.task_id,
            thread_id=binding.thread_id,
            run_id=binding.run_id,
            interrupt_id=interrupt_id,
            transition_id=transition_id,
            expected_revision=expected_revision,
            steps=tuple(steps),
        )
        thread_id = self._threads.get(task.task_id)
        if thread_id is None or task.task_id not in self._source_leases:
            self.watch_recovery(current)
            return await self._wait_for_plan_transition_commit(transition)
        if binding.thread_id != thread_id:
            raise TaskSourceContractError
        updated, refreshed = await self._execute_source_plan_transition(
            current,
            transition,
        )
        active = self._tasks.pop(task.task_id, None)
        if active is not None:
            active.cancel()
            await asyncio.gather(active, return_exceptions=True)
        self.start(refreshed, updated)
        assert refreshed.proposed_plan is not None
        return PlanUpdateRecord(
            task.task_id,
            updated.run_id,
            updated.interrupt_id,
            refreshed.proposed_plan,
        )

    async def _execute_source_plan_transition(
        self,
        task: TaskSnapshot,
        transition: TaskSourcePlanTransition,
    ) -> tuple[LocalPlanUpdate, TaskSnapshot]:
        """Execute one durable plan intent from the process owning its source lease."""

        binding = await self.repository.get_source_binding(task.task_id)
        if binding is None or (
            binding.thread_id,
            binding.run_id,
            binding.pending_interrupt_id,
            binding.pending_transition_id,
        ) != (
            transition.thread_id,
            transition.run_id,
            transition.interrupt_id,
            transition.transition_id,
        ):
            raise TaskSourceContractError
        try:
            updated = await self.source.update_plan(
                transition.thread_id,
                interrupt_id=transition.interrupt_id,
                expected_revision=transition.expected_revision,
                steps=transition.steps,
                transition_id=transition.transition_id,
                agent_id=task.agent_id,
            )
        except (StaleInterruptError, TaskSourceContractError):
            raise
        except Exception:
            raise TaskSourceUnavailableError from None
        if (
            updated.interrupt_id == transition.interrupt_id
            or updated.plan_revision != transition.expected_revision + 1
        ):
            raise TaskSourceContractError
        await self.repository.accept_source_plan_transition(
            task.task_id,
            thread_id=updated.thread_id,
            previous_run_id=transition.run_id,
            run_id=updated.run_id,
            transition_id=transition.transition_id,
            new_interrupt_id=updated.interrupt_id,
            plan_revision=updated.plan_revision,
        )
        acknowledgement = self._resume_acknowledgements.pop(
            (task.task_id, transition.interrupt_id), None
        )
        if acknowledgement is not None and not acknowledgement.done():
            acknowledgement.set_exception(StaleInterruptError())
        self._threads[task.task_id] = updated.thread_id
        self._register_resume_acknowledgement((task.task_id, updated.interrupt_id))
        refreshed = await self.repository.get_task(task.task_id)
        if (
            refreshed.proposed_plan is None
            or refreshed.proposed_plan.revision != updated.plan_revision
            or refreshed.proposed_plan.steps != transition.steps
            or refreshed.pending_interrupt_id != updated.interrupt_id
        ):
            raise TaskSourceContractError
        return updated, refreshed

    async def _wait_for_plan_transition_commit(
        self,
        transition: TaskSourcePlanTransition,
    ) -> PlanUpdateRecord:
        """Wait for the lease owner to atomically publish a submitted plan edit."""

        while True:
            pending = await self.repository.get_source_plan_transition(transition.task_id)
            if pending is not None:
                if pending != transition:
                    raise TaskSourceContractError
                await asyncio.sleep(0.05)
                continue
            refreshed = await self.repository.get_task(transition.task_id)
            if (
                refreshed.status.is_terminal
                or refreshed.pending_interrupt_id in {None, transition.interrupt_id}
                or refreshed.proposed_plan is None
                or refreshed.proposed_plan.revision != transition.expected_revision + 1
                or refreshed.proposed_plan.steps != transition.steps
            ):
                raise TaskSourceContractError
            binding = await self.repository.get_source_binding(transition.task_id)
            if binding is None or binding.accepted_transition_id != transition.transition_id:
                raise TaskSourceContractError
            assert refreshed.pending_interrupt_id is not None
            assert refreshed.proposed_plan is not None
            return PlanUpdateRecord(
                transition.task_id,
                binding.run_id,
                refreshed.pending_interrupt_id,
                refreshed.proposed_plan,
            )

    async def _wait_for_interrupt_command(
        self,
        task_id: str,
        interrupt_id: str,
    ) -> DecisionValue | TaskSourcePlanTransition:
        """Observe either a decision or a cross-process plan edit for one pause."""

        decision = asyncio.create_task(
            self.repository.wait_for_decision(task_id, interrupt_id),
            name=f"deepwork-local-decision-{task_id}",
        )
        try:
            while True:
                done, _ = await asyncio.wait({decision}, timeout=0.05)
                if decision in done:
                    return decision.result()
                transition = await self.repository.get_source_plan_transition(task_id)
                if transition is None:
                    continue
                if transition.interrupt_id != interrupt_id:
                    raise TaskSourceContractError
                # A plan operation running in this process executes its own
                # source call and will replace this follower after commit.
                if task_id in self._plan_updates:
                    continue
                return transition
        finally:
            if not decision.done():
                decision.cancel()
            await asyncio.gather(decision, return_exceptions=True)

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
        if await self.repository.get_source_plan_transition(task_id) is not None:
            raise TaskSourceUnavailableError
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
                binding = await self.repository.get_source_binding(task_id)
                if not record.duplicate or binding is None:
                    raise TaskSourceContractError
                transition_id = _source_transition_id(task_id, interrupt_id)
                if binding.accepted_transition_id != transition_id:
                    raise TaskSourceContractError
            else:
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

    async def _follow(
        self,
        task: TaskSnapshot,
        run: LocalRun,
        *,
        announce_started: bool = True,
    ) -> None:
        resume_key: tuple[str, str] | None = None
        try:
            # A follower restarted after a source-confirmed plan edit already
            # owns a fresh pending interrupt. That checkpoint is paused, not a
            # new executing run: publishing RUN_STARTED here would overwrite
            # the durable waiting-approval state while the follower waits for
            # the exact new decision. Followers started for initial execution
            # or after an accepted decision have no pending interrupt and do
            # publish the normal running transition.
            if task.pending_interrupt_id is None and announce_started:
                await self.repository.append_event(
                    task.task_id,
                    name=TaskEventName.RUN_STARTED,
                    # The API owns a stable run identity that is durably claimed
                    # before the source starts. The source execution identity is
                    # server-only and used to join/resume that execution.
                    data=(("runId", task.run_id), ("status", "running")),
                    status=TaskStatus.RUNNING,
                )
            state = await self._follow_stream_to_source_state(task, run)
            if state.interrupt is not None:
                resume_key = (task.task_id, state.interrupt.interrupt_id)
                self._register_resume_acknowledgement(resume_key)
                if task.pending_interrupt_id is None:
                    await self._pause(task, state)
                elif task.pending_interrupt_id != state.interrupt.interrupt_id:
                    raise TaskSourceContractError
                command = await self._wait_for_interrupt_command(
                    task.task_id,
                    state.interrupt.interrupt_id,
                )
                if isinstance(command, TaskSourcePlanTransition):
                    updated, refreshed = await self._execute_source_plan_transition(
                        task,
                        command,
                    )
                    self._tasks.pop(task.task_id, None)
                    self.start(refreshed, updated)
                    return
                decision = command
                key = (task.task_id, state.interrupt.interrupt_id)
                transition_id = _source_transition_id(*key)
                self._resumes_in_flight.add(key)
                try:
                    await self.repository.mark_source_transition_pending(
                        task.task_id,
                        thread_id=run.thread_id,
                        run_id=run.run_id,
                        interrupt_id=state.interrupt.interrupt_id,
                        transition_id=transition_id,
                    )
                    next_run = await self.source.resume(
                        run.thread_id,
                        interrupt_id=state.interrupt.interrupt_id,
                        decision=decision.value,
                        transition_id=transition_id,
                        comment=self._review_comments.pop(key, None),
                        agent_id=task.agent_id,
                    )
                finally:
                    self._resumes_in_flight.discard(key)
                try:
                    await self.repository.accept_source_transition(
                        task.task_id,
                        thread_id=next_run.thread_id,
                        previous_run_id=run.run_id,
                        run_id=next_run.run_id,
                        transition_id=transition_id,
                    )
                except asyncio.CancelledError:
                    raise
                except Exception as error:
                    raise _SourceHandoffPersistenceError from error
                self._threads[task.task_id] = next_run.thread_id
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
        except _SourceHandoffPersistenceError:
            # The durable pending marker lets startup rediscover this accepted
            # transition. Do not turn recoverable upstream work into a false
            # terminal failure merely because the replacement write failed.
            self._reject_resume(resume_key, TaskSourceUnavailableError())
        except Exception:
            self._reject_resume(resume_key, TaskSourceUnavailableError())
            await self._fail(task, _RUNNER_FAILURE_REASON)

    async def _follow_stream_to_source_state(
        self,
        task: TaskSnapshot,
        run: LocalRun,
    ) -> LocalState:
        """Rejoin a transiently unavailable active stream without losing the task."""

        delay = 0.25
        while True:
            try:
                return await self._follow_stream_once(task, run)
            except TaskSourceUnavailableError:
                await asyncio.sleep(delay)
                delay = min(delay * 2, _SOURCE_RECOVERY_MAX_DELAY_SECONDS)

    async def _follow_stream_once(
        self,
        task: TaskSnapshot,
        run: LocalRun,
    ) -> LocalState:
        """Consume progress while reconciling a source run that settled before join.

        A resumable Agent Server stream can remain open without replaying an event
        when a short run reaches its interrupt or terminal checkpoint before the
        join request is attached. The thread state is source-authoritative, so a
        bounded idle poll prevents Deep Work from leaving the retained task stuck
        in ``running`` while preserving the same fail-closed state validation.
        """

        stream = self.source.stream(run)
        pending: asyncio.Task[object] = asyncio.create_task(_next_source_event(stream))
        reconciliation_seconds = _SOURCE_STATE_RECONCILIATION_SECONDS
        try:
            while True:
                done, _ = await asyncio.wait(
                    {pending},
                    timeout=reconciliation_seconds,
                )
                if pending not in done:
                    state = await self.source.get_state(run.thread_id)
                    if state.interrupt is not None or state.status in {"completed", "rejected"}:
                        return state
                    reconciliation_seconds = min(
                        reconciliation_seconds * 2,
                        _SOURCE_STATE_RECONCILIATION_MAX_SECONDS,
                    )
                    continue
                try:
                    event = pending.result()
                except StopAsyncIteration:
                    return await self.source.get_state(run.thread_id)
                kind = getattr(event, "kind", None)
                if kind == "error":
                    raise TaskSourceContractError
                cursor = getattr(event, "cursor", None)
                if kind == "progress":
                    if cursor is None:
                        raise TaskSourceContractError
                    data = (
                        ("text", "Local Agent Server progress received."),
                        ("evidenceClass", EvidenceClass.LOCAL_SOURCE.value),
                    )
                    await self.repository.append_source_progress(
                        task.task_id,
                        thread_id=run.thread_id,
                        run_id=run.run_id,
                        source_event_key=_source_event_key(
                            run.thread_id,
                            run.run_id,
                            cursor,
                        ),
                        data=data,
                    )
                reconciliation_seconds = _SOURCE_STATE_RECONCILIATION_SECONDS
                pending = asyncio.create_task(_next_source_event(stream))
        finally:
            stream_was_waiting = not pending.done()
            if stream_was_waiting:
                pending.cancel()
            await asyncio.gather(pending, return_exceptions=True)
            close = getattr(stream, "aclose", None)
            if close is not None and not stream_was_waiting:
                await close()

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

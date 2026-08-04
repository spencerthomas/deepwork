"""Regression coverage for local Agent Server runner failure boundaries."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from deepwork_api.adapters.fixture.tasks import InMemoryTaskRepository
from deepwork_api.adapters.persistence.sqlite import SQLiteTaskRepository
from deepwork_api.application.local_runner import (
    LocalAgentServerRunner,
    LocalRun,
    LocalScheduleSummary,
)
from deepwork_api.application.tasks import TaskService
from deepwork_api.domain import (
    DecisionValue,
    ProposedPlan,
    TaskCancellationUnsupportedError,
    TaskEventName,
    TaskSnapshot,
    TaskSourceBinding,
    TaskSourceContractError,
    TaskSourceUnavailableError,
    TaskStatus,
)


@dataclass(frozen=True)
class _Run:
    thread_id: str = "thread_1"
    run_id: str = "run_1"


@dataclass(frozen=True)
class _PlanUpdate(_Run):
    interrupt_id: str = "interrupt_2"
    plan_revision: int = 2


@dataclass(frozen=True)
class _AgentSummary:
    agent_id: str = "assistant-2"
    name: str = "Reviewer"
    description: str | None = None
    system_prompt: str | None = None
    is_default: bool = False
    created_at: str = "2026-01-01T00:00:00Z"
    updated_at: str = "2026-01-01T00:00:00Z"


@dataclass(frozen=True)
class _Interrupt:
    interrupt_id: str = "interrupt_1"
    plan: tuple[str, ...] = ("First step",)
    plan_revision: int = 1


@dataclass(frozen=True)
class _State:
    status: str | None = "planned"
    plan: tuple[str, ...] = ("First step",)
    plan_revision: int | None = 1
    final_answer: str | None = None
    interrupt: _Interrupt | None = _Interrupt()


class _Source:
    def __init__(
        self,
        *,
        events: tuple[object, ...] = (),
        default_agent_id: str = "assistant-default",
        state: _State | None = None,
    ) -> None:
        self.events = events
        self.default_agent_id = default_agent_id
        self.state = state or _State()
        self.resume_comment: str | None = None
        self.state_reads = 0
        self.start_system_prompts: list[str | None] = []
        self.start_agent_ids: list[str | None] = []
        self.update_plan_agent_ids: list[str | None] = []
        self.resume_agent_ids: list[str | None] = []
        self.dispatch_ids: list[str] = []
        self.transition_ids: list[str] = []

    async def start(
        self,
        objective: str,
        *,
        dispatch_id: str,
        system_prompt: str | None = None,
        agent_id: str | None = None,
    ) -> _Run:
        self.dispatch_ids.append(dispatch_id)
        effective_prompt = (
            system_prompt if agent_id is None or agent_id == self.default_agent_id else None
        )
        self.start_system_prompts.append(effective_prompt)
        self.start_agent_ids.append(agent_id)
        return _Run()

    async def get_state(self, thread_id: str) -> _State:
        self.state_reads += 1
        return self.state

    async def update_plan(
        self,
        thread_id: str,
        *,
        interrupt_id: str,
        expected_revision: int,
        steps: Sequence[str],
        transition_id: str,
        agent_id: str | None = None,
    ) -> _PlanUpdate:
        self.update_plan_agent_ids.append(agent_id)
        return _PlanUpdate()

    async def resume(
        self,
        thread_id: str,
        *,
        interrupt_id: str,
        decision: str,
        transition_id: str,
        comment: str | None = None,
        agent_id: str | None = None,
    ) -> _Run:
        self.transition_ids.append(transition_id)
        self.resume_agent_ids.append(agent_id)
        if comment is not None:
            self.resume_comment = comment
        return _Run(run_id="run_2")

    async def stream(
        self,
        run: LocalRun,
        *,
        after_cursor: str | None = None,
    ) -> AsyncIterator[object]:
        for event in self.events:
            yield event

    async def list_agents(self) -> tuple[_AgentSummary, ...]:
        return (_AgentSummary(),)

    async def create_agent(
        self, *, name: str, description: str | None, system_prompt: str | None
    ) -> _AgentSummary:
        return _AgentSummary(name=name, description=description, system_prompt=system_prompt)

    async def update_agent(
        self,
        agent_id: str,
        *,
        name: str,
        description: str | None,
        system_prompt: str | None,
    ) -> _AgentSummary:
        return _AgentSummary(
            agent_id=agent_id, name=name, description=description, system_prompt=system_prompt
        )

    async def delete_agent(self, agent_id: str) -> None:
        return None

    async def list_schedules(self) -> tuple[LocalScheduleSummary, ...]:
        return ()


class _HangingStreamSource(_Source):
    async def stream(
        self,
        run: LocalRun,
        *,
        after_cursor: str | None = None,
    ) -> AsyncIterator[object]:
        pending = asyncio.get_running_loop().create_future()
        yield await pending


class _IdempotentRecoverySource(_Source):
    def __init__(self) -> None:
        super().__init__()
        self.accepted_dispatches: dict[str, _Run] = {}
        self.accepted_transitions: dict[str, _Run] = {}
        self.accepted_plan_transitions: dict[str, _PlanUpdate] = {}
        self.upstream_starts = 0
        self.upstream_resumes = 0
        self.upstream_plan_updates = 0

    async def start(
        self,
        objective: str,
        *,
        dispatch_id: str,
        system_prompt: str | None = None,
        agent_id: str | None = None,
    ) -> _Run:
        self.dispatch_ids.append(dispatch_id)
        existing = self.accepted_dispatches.get(dispatch_id)
        if existing is not None:
            return existing
        self.upstream_starts += 1
        run = _Run()
        self.accepted_dispatches[dispatch_id] = run
        return run

    async def resume(
        self,
        thread_id: str,
        *,
        interrupt_id: str,
        decision: str,
        transition_id: str,
        comment: str | None = None,
        agent_id: str | None = None,
    ) -> _Run:
        self.transition_ids.append(transition_id)
        existing = self.accepted_transitions.get(transition_id)
        if existing is not None:
            return existing
        if decision == "respond" and comment is None:
            raise RuntimeError("lost response comment")
        self.upstream_resumes += 1
        run = _Run(run_id="run_2")
        self.accepted_transitions[transition_id] = run
        self.state = _State(
            status="completed",
            plan=("First step",),
            plan_revision=1,
            final_answer="Recovered result",
            interrupt=None,
        )
        return run

    async def update_plan(
        self,
        thread_id: str,
        *,
        interrupt_id: str,
        expected_revision: int,
        steps: Sequence[str],
        transition_id: str,
        agent_id: str | None = None,
    ) -> _PlanUpdate:
        self.update_plan_agent_ids.append(agent_id)
        existing = self.accepted_plan_transitions.get(transition_id)
        if existing is not None:
            return existing
        self.upstream_plan_updates += 1
        updated = _PlanUpdate()
        self.accepted_plan_transitions[transition_id] = updated
        self.state = _State(
            status="planned",
            plan=tuple(steps),
            plan_revision=expected_revision + 1,
            interrupt=_Interrupt(
                interrupt_id=updated.interrupt_id,
                plan=tuple(steps),
                plan_revision=expected_revision + 1,
            ),
        )
        return updated


class _CrashBeforeBindingRepository(InMemoryTaskRepository):
    crash_before_binding = True

    async def bind_source_run(
        self,
        task_id: str,
        *,
        thread_id: str,
        run_id: str,
    ) -> TaskSourceBinding:
        if self.crash_before_binding:
            self.crash_before_binding = False
            raise asyncio.CancelledError
        return await super().bind_source_run(
            task_id,
            thread_id=thread_id,
            run_id=run_id,
        )


class _CrashOnAcceptRepository(InMemoryTaskRepository):
    def __init__(self, *, after_commit: bool) -> None:
        super().__init__()
        self.after_commit = after_commit
        self.crash_once = True

    async def accept_source_transition(
        self,
        task_id: str,
        *,
        thread_id: str,
        previous_run_id: str,
        run_id: str,
        transition_id: str,
    ) -> TaskSourceBinding:
        if self.crash_once:
            self.crash_once = False
            if not self.after_commit:
                raise asyncio.CancelledError
            await super().accept_source_transition(
                task_id,
                thread_id=thread_id,
                previous_run_id=previous_run_id,
                run_id=run_id,
                transition_id=transition_id,
            )
            raise asyncio.CancelledError
        return await super().accept_source_transition(
            task_id,
            thread_id=thread_id,
            previous_run_id=previous_run_id,
            run_id=run_id,
            transition_id=transition_id,
        )


class _CrashOnAcceptPlanRepository(InMemoryTaskRepository):
    crash_once = True

    async def accept_source_plan_transition(
        self,
        task_id: str,
        *,
        thread_id: str,
        previous_run_id: str,
        run_id: str,
        transition_id: str,
        new_interrupt_id: str,
        plan_revision: int,
    ) -> TaskSourceBinding:
        if self.crash_once:
            self.crash_once = False
            raise RuntimeError("simulated plan binding crash")
        return await super().accept_source_plan_transition(
            task_id,
            thread_id=thread_id,
            previous_run_id=previous_run_id,
            run_id=run_id,
            transition_id=transition_id,
            new_interrupt_id=new_interrupt_id,
            plan_revision=plan_revision,
        )


class _BlockingAfterAcceptPlanRepository(InMemoryTaskRepository):
    def __init__(self) -> None:
        super().__init__()
        self.accepted = asyncio.Event()
        self.release = asyncio.Event()

    async def accept_source_plan_transition(
        self,
        task_id: str,
        *,
        thread_id: str,
        previous_run_id: str,
        run_id: str,
        transition_id: str,
        new_interrupt_id: str,
        plan_revision: int,
    ) -> TaskSourceBinding:
        binding = await super().accept_source_plan_transition(
            task_id,
            thread_id=thread_id,
            previous_run_id=previous_run_id,
            run_id=run_id,
            transition_id=transition_id,
            new_interrupt_id=new_interrupt_id,
            plan_revision=plan_revision,
        )
        self.accepted.set()
        await self.release.wait()
        return binding


class _CrashOnAcceptPlanSQLiteRepository(SQLiteTaskRepository):
    crash_once = True

    async def accept_source_plan_transition(
        self,
        task_id: str,
        *,
        thread_id: str,
        previous_run_id: str,
        run_id: str,
        transition_id: str,
        new_interrupt_id: str,
        plan_revision: int,
    ) -> TaskSourceBinding:
        if self.crash_once:
            self.crash_once = False
            raise RuntimeError("simulated SQLite plan binding crash")
        return await super().accept_source_plan_transition(
            task_id,
            thread_id=thread_id,
            previous_run_id=previous_run_id,
            run_id=run_id,
            transition_id=transition_id,
            new_interrupt_id=new_interrupt_id,
            plan_revision=plan_revision,
        )


async def _paused_task(
    repository: InMemoryTaskRepository | SQLiteTaskRepository,
    *,
    agent_id: str | None = None,
) -> TaskSnapshot:
    task = await repository.create_task(
        title="Task",
        objective="Objective",
        agent_id=agent_id,
    )
    await repository.bind_source_run(
        task.task_id,
        thread_id="thread_1",
        run_id="run_1",
    )
    await repository.set_plan(
        task.task_id,
        plan=ProposedPlan(1, "Plan", ("First step",), ()),
        event_name=TaskEventName.PLAN_PROPOSED,
    )
    await repository.append_event(
        task.task_id,
        name=TaskEventName.INTERRUPT_REQUESTED,
        data=(("interruptId", "interrupt_1"),),
        status=TaskStatus.WAITING_APPROVAL,
        pending_interrupt_id="interrupt_1",
    )
    return await repository.get_task(task.task_id)


@pytest.mark.asyncio
async def test_create_forwards_the_workspace_prompt_to_source_start() -> None:
    # The editable workspace prompt must flow into the source's start call so the
    # graph runs with that persona; no store means no override.
    from deepwork_api.adapters.prompt import InMemoryPromptStore

    repository = InMemoryTaskRepository()
    source = _Source()
    runner = LocalAgentServerRunner(
        repository, source, prompt_store=InMemoryPromptStore("Always be terse.")
    )
    try:
        await runner.create(title="t", objective="Do the thing")
    finally:
        await runner.close()

    assert source.start_system_prompts == ["Always be terse."]


async def test_service_idempotent_retry_does_not_restart_local_source() -> None:
    repository = InMemoryTaskRepository()
    source = _Source()
    runner = LocalAgentServerRunner(repository, source)
    service = TaskService(repository, runner)
    try:
        first = await service.create_task(
            "Do the thing",
            idempotency_key="local-source-task-key",
        )
        retried = await service.create_task(
            "Do the thing",
            idempotency_key="local-source-task-key",
        )
    finally:
        await runner.close()

    assert first.created is True
    assert retried.created is False
    assert retried.task.task_id == first.task.task_id
    assert retried.task.run_id == first.task.run_id
    assert source.start_system_prompts == [None]


async def test_shared_sqlite_claim_precedes_source_start_across_services(tmp_path: Path) -> None:
    class BlockingSource(_Source):
        def __init__(self) -> None:
            super().__init__()
            self.entered = asyncio.Event()
            self.release = asyncio.Event()
            self.starts = 0

        async def start(
            self,
            objective: str,
            *,
            dispatch_id: str,
            system_prompt: str | None = None,
            agent_id: str | None = None,
        ) -> _Run:
            self.starts += 1
            self.entered.set()
            await self.release.wait()
            return await super().start(
                objective,
                dispatch_id=dispatch_id,
                system_prompt=system_prompt,
                agent_id=agent_id,
            )

    database = tmp_path / "shared-task-create.sqlite"
    repositories = (SQLiteTaskRepository(database), SQLiteTaskRepository(database))
    for repository in repositories:
        await repository.initialize()
    source = BlockingSource()
    runners = tuple(LocalAgentServerRunner(repository, source) for repository in repositories)
    services = tuple(
        TaskService(repository, runner)
        for repository, runner in zip(repositories, runners, strict=True)
    )
    first_request = asyncio.create_task(
        services[0].create_task("Do the thing", idempotency_key="shared-source-key")
    )
    try:
        await asyncio.wait_for(source.entered.wait(), timeout=1)
        replay_request = asyncio.create_task(
            services[1].create_task("Do the thing", idempotency_key="shared-source-key")
        )
        replay = await asyncio.wait_for(replay_request, timeout=1)
        assert replay.created is False
        assert source.starts == 1
        source.release.set()
        created = await asyncio.wait_for(first_request, timeout=1)
        assert created.created is True
        assert replay.task.task_id == created.task.task_id
        assert source.starts == 1
    finally:
        source.release.set()
        if not first_request.done():
            first_request.cancel()
        await asyncio.gather(first_request, return_exceptions=True)
        for runner in runners:
            await runner.close()
        for repository in repositories:
            await repository.close()


async def test_startup_recovery_retries_a_transient_source_failure() -> None:
    class FlakySource(_Source):
        def __init__(self) -> None:
            super().__init__()
            self.attempts = 0

        async def start(
            self,
            objective: str,
            *,
            dispatch_id: str,
            system_prompt: str | None = None,
            agent_id: str | None = None,
        ) -> _Run:
            self.attempts += 1
            if self.attempts == 1:
                raise OSError("temporary source outage")
            return await super().start(
                objective,
                dispatch_id=dispatch_id,
                system_prompt=system_prompt,
                agent_id=agent_id,
            )

    repository = InMemoryTaskRepository()
    task = await repository.create_task(title="Recover", objective="Retry accepted work")
    source = FlakySource()
    runner = LocalAgentServerRunner(repository, source)
    runner.watch_recovery(task)
    try:
        for _ in range(20):
            if await repository.get_source_binding(task.task_id) is not None:
                break
            await asyncio.sleep(0.05)
        assert await repository.get_source_binding(task.task_id) is not None
        assert source.attempts == 2
    finally:
        await runner.close()


async def test_independent_task_keys_can_start_the_source_concurrently() -> None:
    class ConcurrentSource(_Source):
        def __init__(self) -> None:
            super().__init__()
            self.objectives: list[str] = []
            self.both_entered = asyncio.Event()
            self.release = asyncio.Event()

        async def start(
            self,
            objective: str,
            *,
            dispatch_id: str,
            system_prompt: str | None = None,
            agent_id: str | None = None,
        ) -> _Run:
            self.objectives.append(objective)
            if len(self.objectives) == 2:
                self.both_entered.set()
            await self.release.wait()
            return await super().start(
                objective,
                dispatch_id=dispatch_id,
                system_prompt=system_prompt,
                agent_id=agent_id,
            )

    repository = InMemoryTaskRepository()
    source = ConcurrentSource()
    runner = LocalAgentServerRunner(repository, source)
    service = TaskService(repository, runner)
    requests = (
        asyncio.create_task(service.create_task("First", idempotency_key="independent-a")),
        asyncio.create_task(service.create_task("Second", idempotency_key="independent-b")),
    )
    try:
        await asyncio.wait_for(source.both_entered.wait(), timeout=1)
        source.release.set()
        results = await asyncio.gather(*requests)
        assert all(result.created for result in results)
        assert source.objectives == ["First", "Second"]
    finally:
        source.release.set()
        await asyncio.gather(*requests, return_exceptions=True)
        await runner.close()


@pytest.mark.asyncio
async def test_create_reads_prompt_from_the_task_security_context() -> None:
    from deepwork_api.adapters.prompt import InMemoryPromptStore
    from deepwork_api.domain import SecurityContext

    context_a = SecurityContext("tenant-a", "workspace-shared", "actor-a")
    context_b = SecurityContext("tenant-b", "workspace-shared", "actor-b")
    prompt_store = InMemoryPromptStore("Default persona.")
    await prompt_store.set_system_prompt(
        "Tenant A persona.",
        tenant_id=context_a.tenant_id,
        workspace_id=context_a.workspace_id,
    )
    await prompt_store.set_system_prompt(
        "Tenant B persona.",
        tenant_id=context_b.tenant_id,
        workspace_id=context_b.workspace_id,
    )

    repository = InMemoryTaskRepository()
    source = _Source()
    runner = LocalAgentServerRunner(repository, source, prompt_store=prompt_store)
    try:
        await runner.create(
            title="a",
            objective="Use A",
            security_context=context_a,
        )
        await runner.create(
            title="b",
            objective="Use B",
            security_context=context_b,
        )
    finally:
        await runner.close()

    assert source.start_system_prompts == ["Tenant A persona.", "Tenant B persona."]


async def test_create_without_a_prompt_store_sends_no_override() -> None:
    repository = InMemoryTaskRepository()
    source = _Source()
    runner = LocalAgentServerRunner(repository, source)
    try:
        await runner.create(title="t", objective="Do the thing")
    finally:
        await runner.close()

    assert source.start_system_prompts == [None]


async def test_create_with_an_agent_id_skips_the_workspace_prompt_override() -> None:
    """A selected named agent's own config governs it; the two never fight."""
    from deepwork_api.adapters.prompt import InMemoryPromptStore

    repository = InMemoryTaskRepository()
    source = _Source()
    runner = LocalAgentServerRunner(
        repository, source, prompt_store=InMemoryPromptStore("Always be terse.")
    )
    try:
        task = await runner.create(title="t", objective="Do the thing", agent_id="assistant-2")
    finally:
        await runner.close()

    assert source.start_system_prompts == [None]
    assert source.start_agent_ids == ["assistant-2"]
    assert task.task.agent_id == "assistant-2"
    created_event = (await repository.events_after(task.task.task_id, 0))[0]
    assert dict(created_event.data)["agentId"] == "assistant-2"


async def test_create_with_explicit_default_agent_keeps_workspace_prompt_and_identity() -> None:
    """The chooser may name the default; its workspace prompt still applies."""
    from deepwork_api.adapters.prompt import InMemoryPromptStore

    repository = InMemoryTaskRepository()
    source = _Source(default_agent_id="assistant-default")
    runner = LocalAgentServerRunner(
        repository, source, prompt_store=InMemoryPromptStore("Always be terse.")
    )
    try:
        task = await runner.create(
            title="t", objective="Do the thing", agent_id="assistant-default"
        )
    finally:
        await runner.close()

    assert source.start_system_prompts == ["Always be terse."]
    assert source.start_agent_ids == ["assistant-default"]
    assert task.task.agent_id == "assistant-default"


async def test_runner_agent_registry_methods_delegate_to_the_source() -> None:
    repository = InMemoryTaskRepository()
    source = _Source()
    runner = LocalAgentServerRunner(repository, source)
    try:
        listed = await runner.list_agents()
        created = await runner.create_agent(
            name="Reviewer", description="Reviews things.", system_prompt="Be terse."
        )
        updated = await runner.update_agent(
            "assistant-2", name="Renamed", description=None, system_prompt=None
        )
        await runner.delete_agent("assistant-2")
    finally:
        await runner.close()

    assert listed == (_AgentSummary(),)
    assert created.name == "Reviewer"
    assert updated.name == "Renamed"


async def test_cancel_is_refused_without_a_source_cancel_capability() -> None:
    # The loopback Agent Server source exposes no cancel operation, so marking
    # the task terminal would leave the upstream run executing while reporting
    # it stopped. The service must refuse rather than publish a false state.
    repository = InMemoryTaskRepository()
    runner = LocalAgentServerRunner(repository, _Source())
    service = TaskService(repository=repository, runner=runner)
    task = await _paused_task(repository)
    before = await repository.get_task(task.task_id)

    with pytest.raises(TaskCancellationUnsupportedError):
        await service.cancel_task(task.task_id)

    after = await repository.get_task(task.task_id)
    assert after == before
    assert not after.status.is_terminal
    await runner.close()


@pytest.mark.asyncio
async def test_confirmed_plan_update_reconciles_without_second_state_read() -> None:
    repository = InMemoryTaskRepository()
    source = _Source()
    runner = LocalAgentServerRunner(repository, source)
    task = await _paused_task(repository)
    runner._threads[task.task_id] = "thread_1"

    update = await runner.update_plan(
        task,
        interrupt_id="interrupt_1",
        expected_revision=1,
        steps=("Updated step",),
    )

    current = await repository.get_task(task.task_id)
    assert source.state_reads == 0
    assert update.interrupt_id == "interrupt_2"
    assert current.pending_interrupt_id == "interrupt_2"
    assert current.proposed_plan is not None and current.proposed_plan.revision == 2
    await runner.close()


@pytest.mark.asyncio
async def test_plan_update_keeps_the_durable_selected_agent() -> None:
    repository = InMemoryTaskRepository()
    source = _Source()
    runner = LocalAgentServerRunner(repository, source)
    task = await _paused_task(repository, agent_id="assistant-reviewer")
    runner._threads[task.task_id] = "thread_1"

    await runner.update_plan(
        task,
        interrupt_id="interrupt_1",
        expected_revision=1,
        steps=("Updated step",),
    )

    assert source.update_plan_agent_ids == ["assistant-reviewer"]
    await runner.close()


@pytest.mark.asyncio
async def test_queued_binding_recovery_announces_run_started_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "deepwork_api.application.local_runner._SOURCE_STATE_RECONCILIATION_SECONDS",
        0.01,
    )
    repository = InMemoryTaskRepository()
    source = _HangingStreamSource()
    runner = LocalAgentServerRunner(repository, source)
    task = await repository.create_task(
        title="Task",
        objective="Objective",
        run_id="run_1",
    )
    await repository.bind_source_run(
        task.task_id,
        thread_id="thread_1",
        run_id="run_1",
    )

    assert await runner.recover(task) is True
    for _ in range(20):
        if (await repository.get_task(task.task_id)).status is TaskStatus.WAITING_APPROVAL:
            break
        await asyncio.sleep(0.01)

    assert (await repository.get_task(task.task_id)).status is TaskStatus.WAITING_APPROVAL
    events = await repository.events_after(task.task_id, 0)
    assert [event.name for event in events].count(TaskEventName.RUN_STARTED) == 1
    await runner.close()


@pytest.mark.asyncio
async def test_error_stream_event_fails_instead_of_completing() -> None:
    repository = InMemoryTaskRepository()
    runner = LocalAgentServerRunner(repository, _Source(events=(SimpleNamespace(kind="error"),)))
    task = await repository.create_task(title="Task", objective="Objective", run_id="run_1")

    await runner._follow(task, _Run())

    assert (await repository.get_task(task.task_id)).status is TaskStatus.FAILED


@pytest.mark.asyncio
async def test_cursorless_progress_fails_without_persisting_an_undedupeable_event() -> None:
    repository = InMemoryTaskRepository()
    source = _Source(events=(SimpleNamespace(kind="progress", cursor=None),))
    runner = LocalAgentServerRunner(repository, source)
    task = await repository.create_task(title="Task", objective="Objective", run_id="run_1")
    await repository.bind_source_run(
        task.task_id,
        thread_id="thread_1",
        run_id="run_1",
    )

    await runner._follow(task, _Run())

    current = await repository.get_task(task.task_id)
    events = await repository.events_after(task.task_id, 0)
    assert current.status is TaskStatus.FAILED
    assert TaskEventName.CONTENT_DELTA not in [event.name for event in events]


@pytest.mark.asyncio
async def test_nonterminal_source_state_fails_instead_of_completing() -> None:
    repository = InMemoryTaskRepository()
    source = _Source()

    async def nonterminal_state(thread_id: str) -> _State:
        source.state_reads += 1
        return replace(_State(), interrupt=None)

    source.get_state = nonterminal_state  # type: ignore[method-assign]
    runner = LocalAgentServerRunner(repository, source)
    task = await repository.create_task(title="Task", objective="Objective", run_id="run_1")

    await runner._follow(task, _Run())

    assert (await repository.get_task(task.task_id)).status is TaskStatus.FAILED


@pytest.mark.asyncio
async def test_source_state_reconciles_a_run_that_settled_before_stream_join(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "deepwork_api.application.local_runner._SOURCE_STATE_RECONCILIATION_SECONDS",
        0.01,
    )
    repository = InMemoryTaskRepository()
    source = _HangingStreamSource()
    runner = LocalAgentServerRunner(repository, source)
    task = await repository.create_task(title="Task", objective="Objective", run_id="run_1")

    runner.start(task, _Run())
    for _ in range(20):
        current = await repository.get_task(task.task_id)
        if current.status is TaskStatus.WAITING_APPROVAL:
            break
        await asyncio.sleep(0.01)

    current = await repository.get_task(task.task_id)
    assert source.state_reads == 1
    assert current.status is TaskStatus.WAITING_APPROVAL
    assert current.pending_interrupt_id == "interrupt_1"
    await runner.close()


@pytest.mark.parametrize(
    ("state", "expected_status", "expected_result"),
    [
        (
            _State(status="completed", final_answer="Finished safely.", interrupt=None),
            TaskStatus.COMPLETED,
            "Finished safely.",
        ),
        (
            _State(status="rejected", interrupt=None),
            TaskStatus.REJECTED,
            None,
        ),
    ],
)
@pytest.mark.asyncio
async def test_terminal_source_state_reconciles_before_stream_join(
    monkeypatch: pytest.MonkeyPatch,
    state: _State,
    expected_status: TaskStatus,
    expected_result: str | None,
) -> None:
    monkeypatch.setattr(
        "deepwork_api.application.local_runner._SOURCE_STATE_RECONCILIATION_SECONDS",
        0.01,
    )
    repository = InMemoryTaskRepository()
    source = _HangingStreamSource(state=state)
    runner = LocalAgentServerRunner(repository, source)
    task = await repository.create_task(title="Task", objective="Objective", run_id="run_1")

    runner.start(task, _Run())
    for _ in range(20):
        current = await repository.get_task(task.task_id)
        if current.status is expected_status:
            break
        await asyncio.sleep(0.01)

    current = await repository.get_task(task.task_id)
    assert current.status is expected_status
    assert current.result == expected_result
    await runner.close()


@pytest.mark.asyncio
async def test_response_comment_is_forwarded_to_source_resume() -> None:
    repository = InMemoryTaskRepository()
    source = _Source()
    runner = LocalAgentServerRunner(repository, source)
    service = TaskService(repository, runner)
    task = await _paused_task(repository)

    follower = asyncio.create_task(runner._follow(task, _Run()))
    for _ in range(20):
        if (task.task_id, "interrupt_1") in runner._resume_acknowledgements:
            break
        await asyncio.sleep(0)
    await service.record_decision(
        task.task_id,
        interrupt_id="interrupt_1",
        decision=DecisionValue.RESPOND,
        comment="Please make the plan more concise.",
    )
    await follower

    assert source.resume_comment == "Please make the plan more concise."
    assert source.resume_agent_ids == [None]
    await runner.close()


@pytest.mark.asyncio
async def test_recovery_reuses_start_accepted_before_binding() -> None:
    repository = _CrashBeforeBindingRepository()
    source = _IdempotentRecoverySource()
    first_runner = LocalAgentServerRunner(repository, source)

    with pytest.raises(asyncio.CancelledError):
        await first_runner.create(title="Task", objective="Objective")
    task = (await repository.list_tasks())[0]
    assert await repository.get_source_binding(task.task_id) is None

    recovered_runner = LocalAgentServerRunner(repository, source)
    assert await recovered_runner.recover(task) is True
    binding = await repository.get_source_binding(task.task_id)
    assert binding is not None
    assert binding.run_id == "run_1"
    assert source.dispatch_ids == [task.run_id, task.run_id]
    assert source.upstream_starts == 1

    await recovered_runner.close()
    await first_runner.close()


@pytest.mark.asyncio
async def test_idempotent_retry_repairs_an_accepted_start_missing_its_binding() -> None:
    repository = _CrashBeforeBindingRepository()
    source = _IdempotentRecoverySource()
    runner = LocalAgentServerRunner(repository, source)

    with pytest.raises(asyncio.CancelledError):
        await runner.create(
            title="Task",
            objective="Objective",
            idempotency_key="recover-live-retry",
            request_fingerprint="same-request",
        )

    replay = await runner.create(
        title="Task",
        objective="Objective",
        idempotency_key="recover-live-retry",
        request_fingerprint="same-request",
    )

    binding = await repository.get_source_binding(replay.task.task_id)
    assert replay.created is False
    assert binding is not None and binding.run_id == "run_1"
    assert source.upstream_starts == 1
    await runner.close()


async def _wait_for_repository_status(
    repository: InMemoryTaskRepository,
    task_id: str,
    status: TaskStatus,
) -> TaskSnapshot:
    for _ in range(100):
        task = await repository.get_task(task_id)
        if task.status is status:
            return task
        await asyncio.sleep(0)
    raise AssertionError(f"task did not reach {status}")


@pytest.mark.asyncio
async def test_recovery_discovers_resume_accepted_before_replacement_binding() -> None:
    repository = _CrashOnAcceptRepository(after_commit=False)
    source = _IdempotentRecoverySource()
    task = await _paused_task(repository)
    first_runner = LocalAgentServerRunner(repository, source)
    first_runner.start(task, _Run(), announce_started=False)

    decision = asyncio.create_task(
        first_runner.record_decision(
            task.task_id,
            interrupt_id="interrupt_1",
            decision=DecisionValue.APPROVE,
            comment=None,
            comment_provided=False,
            response_digest=None,
        )
    )
    with pytest.raises(TaskSourceUnavailableError):
        await decision
    pending = await repository.get_source_binding(task.task_id)
    assert pending is not None
    assert pending.pending_transition_id is not None

    recovered_runner = LocalAgentServerRunner(repository, source)
    current = await repository.get_task(task.task_id)
    assert await recovered_runner.recover(current) is True
    completed = await _wait_for_repository_status(
        repository,
        task.task_id,
        TaskStatus.COMPLETED,
    )
    assert completed.result == "Recovered result"
    assert source.upstream_resumes == 1
    assert len(source.transition_ids) == 2

    await recovered_runner.close()
    await first_runner.close()


@pytest.mark.asyncio
async def test_recovery_discovers_plan_edit_accepted_before_atomic_local_commit() -> None:
    repository = _CrashOnAcceptPlanRepository()
    source = _IdempotentRecoverySource()
    task = await _paused_task(repository, agent_id="assistant-reviewer")
    first_runner = LocalAgentServerRunner(repository, source)
    first_runner._threads[task.task_id] = "thread_1"

    with pytest.raises(RuntimeError, match="plan binding crash"):
        await first_runner.update_plan(
            task,
            interrupt_id="interrupt_1",
            expected_revision=1,
            steps=("Recovered edited step",),
        )
    pending = await repository.get_source_plan_transition(task.task_id)
    assert pending is not None

    recovered_runner = LocalAgentServerRunner(repository, source)
    assert await recovered_runner.recover(await repository.get_task(task.task_id)) is True
    current = await repository.get_task(task.task_id)

    assert current.pending_interrupt_id == "interrupt_2"
    assert current.proposed_plan is not None
    assert current.proposed_plan.revision == 2
    assert current.proposed_plan.steps == ("Recovered edited step",)
    assert await repository.get_source_plan_transition(task.task_id) is None
    assert source.upstream_plan_updates == 1
    assert source.update_plan_agent_ids == ["assistant-reviewer", "assistant-reviewer"]

    await recovered_runner.close()
    await first_runner.close()


@pytest.mark.asyncio
async def test_plan_edit_recovery_survives_a_real_sqlite_repository_reopen(
    tmp_path: Path,
) -> None:
    database = tmp_path / "tasks.sqlite"
    first_repository = _CrashOnAcceptPlanSQLiteRepository(database)
    source = _IdempotentRecoverySource()
    task = await _paused_task(first_repository, agent_id="assistant-reviewer")
    first_runner = LocalAgentServerRunner(first_repository, source)
    first_runner._threads[task.task_id] = "thread_1"

    with pytest.raises(RuntimeError, match="SQLite plan binding crash"):
        await first_runner.update_plan(
            task,
            interrupt_id="interrupt_1",
            expected_revision=1,
            steps=("Persisted edited step",),
        )
    await first_runner.close()
    await first_repository.close()

    reopened = SQLiteTaskRepository(database)
    recovered_runner = LocalAgentServerRunner(reopened, source)
    assert await recovered_runner.recover(await reopened.get_task(task.task_id)) is True
    current = await reopened.get_task(task.task_id)

    assert current.pending_interrupt_id == "interrupt_2"
    assert current.proposed_plan is not None
    assert current.proposed_plan.steps == ("Persisted edited step",)
    assert source.upstream_plan_updates == 1
    assert await reopened.get_source_plan_transition(task.task_id) is None

    await recovered_runner.close()
    await reopened.close()


@pytest.mark.asyncio
async def test_cancelled_plan_request_keeps_task_owned_operation_running() -> None:
    repository = InMemoryTaskRepository()
    source = _IdempotentRecoverySource()
    task = await _paused_task(repository)
    runner = LocalAgentServerRunner(repository, source)
    runner._threads[task.task_id] = "thread_1"
    entered = asyncio.Event()
    release = asyncio.Event()
    original = source.update_plan

    async def blocked_update_plan(
        thread_id: str,
        *,
        interrupt_id: str,
        expected_revision: int,
        steps: Sequence[str],
        transition_id: str,
        agent_id: str | None = None,
    ) -> _PlanUpdate:
        entered.set()
        await release.wait()
        return await original(
            thread_id,
            interrupt_id=interrupt_id,
            expected_revision=expected_revision,
            steps=steps,
            transition_id=transition_id,
            agent_id=agent_id,
        )

    source.update_plan = blocked_update_plan  # type: ignore[method-assign]
    request = asyncio.create_task(
        runner.update_plan(
            task,
            interrupt_id="interrupt_1",
            expected_revision=1,
            steps=("Continue after disconnect",),
        )
    )
    await entered.wait()
    request.cancel()
    with pytest.raises(asyncio.CancelledError):
        await request
    release.set()
    for _ in range(20):
        current = await repository.get_task(task.task_id)
        if current.proposed_plan is not None and current.proposed_plan.revision == 2:
            break
        await asyncio.sleep(0)

    current = await repository.get_task(task.task_id)
    assert current.pending_interrupt_id == "interrupt_2"
    assert current.proposed_plan is not None
    assert current.proposed_plan.steps == ("Continue after disconnect",)
    await runner.close()


@pytest.mark.asyncio
async def test_cancelled_plan_request_after_atomic_accept_still_swaps_follower() -> None:
    repository = _BlockingAfterAcceptPlanRepository()
    source = _IdempotentRecoverySource()
    task = await _paused_task(repository)
    runner = LocalAgentServerRunner(repository, source)
    runner._threads[task.task_id] = "thread_1"
    request = asyncio.create_task(
        runner.update_plan(
            task,
            interrupt_id="interrupt_1",
            expected_revision=1,
            steps=("Accepted before disconnect",),
        )
    )

    await repository.accepted.wait()
    request.cancel()
    with pytest.raises(asyncio.CancelledError):
        await request
    repository.release.set()
    for _ in range(20):
        if task.task_id in runner._tasks:
            break
        await asyncio.sleep(0)

    current = await repository.get_task(task.task_id)
    assert current.pending_interrupt_id == "interrupt_2"
    assert task.task_id in runner._tasks
    await runner.close()


@pytest.mark.asyncio
async def test_plan_recovery_rejects_a_reused_interrupt_before_local_commit() -> None:
    repository = InMemoryTaskRepository()
    source = _IdempotentRecoverySource()
    task = await _paused_task(repository)
    transition_id = "plan-transition-stale"
    await repository.mark_source_plan_transition_pending(
        task.task_id,
        thread_id="thread_1",
        run_id="run_1",
        interrupt_id="interrupt_1",
        transition_id=transition_id,
        expected_revision=1,
        steps=("Edited step",),
    )

    async def stale_update_plan(*args: object, **kwargs: object) -> _PlanUpdate:
        return _PlanUpdate(interrupt_id="interrupt_1", plan_revision=2)

    source.update_plan = stale_update_plan  # type: ignore[method-assign]
    runner = LocalAgentServerRunner(repository, source)

    with pytest.raises(TaskSourceContractError):
        await runner.recover(await repository.get_task(task.task_id))

    current = await repository.get_task(task.task_id)
    assert current.pending_interrupt_id == "interrupt_1"
    assert current.proposed_plan is not None and current.proposed_plan.revision == 1
    await runner.close()


@pytest.mark.asyncio
async def test_duplicate_decision_succeeds_after_binding_commit_before_memory_ack() -> None:
    repository = _CrashOnAcceptRepository(after_commit=True)
    source = _IdempotentRecoverySource()
    task = await _paused_task(repository)
    first_runner = LocalAgentServerRunner(repository, source)
    first_runner.start(task, _Run(), announce_started=False)

    first = asyncio.create_task(
        first_runner.record_decision(
            task.task_id,
            interrupt_id="interrupt_1",
            decision=DecisionValue.APPROVE,
            comment=None,
            comment_provided=False,
            response_digest=None,
        )
    )
    with pytest.raises(TaskSourceUnavailableError):
        await first
    accepted = await repository.get_source_binding(task.task_id)
    assert accepted is not None
    assert accepted.accepted_transition_id is not None

    recovered_runner = LocalAgentServerRunner(repository, source)
    current = await repository.get_task(task.task_id)
    assert await recovered_runner.recover(current) is True
    duplicate = await recovered_runner.record_decision(
        task.task_id,
        interrupt_id="interrupt_1",
        decision=DecisionValue.APPROVE,
        comment=None,
        comment_provided=False,
        response_digest=None,
    )
    assert duplicate.duplicate is True
    assert source.upstream_resumes == 1
    assert len(source.transition_ids) == 1

    await recovered_runner.close()
    await first_runner.close()

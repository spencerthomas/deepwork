"""Network-denied tests for the official local Agent Server adapter boundary."""

from __future__ import annotations

import asyncio
import hashlib
from collections.abc import AsyncIterator, Callable, Mapping, Sequence
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import cast

import httpx
import pytest

from deepwork_api.adapters.sources.local import (
    AgentSummary,
    LocalAgentServerSource,
    LocalAgentServerStatus,
    LocalRunReference,
    LocalSourceConfigurationError,
    LocalSourceContractError,
    LocalSourceDefaultAgentImmutableError,
    LocalSourceStaleInterruptError,
    LocalSourceUnavailableError,
    ScheduleSummary,
    create_official_client,
    validate_loopback_url,
)
from deepwork_api.adapters.sources.local.source import Decision
from deepwork_api.domain import MAX_PLAN_REVISION

OFFICIAL_INTERRUPT_ID = "bb51bb4b9474b86e0c58ac08fa85d3fa"
NEXT_OFFICIAL_INTERRUPT_ID = "cc51bb4b9474b86e0c58ac08fa85d3fc"
DISPATCH_ID = "task-source-contract"
TRANSITION_ID = "transition-source-contract"


def _interrupt(
    *,
    interrupt_id: str = OFFICIAL_INTERRUPT_ID,
    revision: object = 1,
    plan: list[str] | None = None,
    allowed_decisions: list[str] | None = None,
    action: str = "execute_plan",
    plan_trust: str = "untrusted",
) -> dict[str, object]:
    decisions = ["approve", "reject", "respond"] if allowed_decisions is None else allowed_decisions
    steps = ["Inspect inputs", "Produce result"] if plan is None else plan
    return {
        "id": interrupt_id,
        "value": {
            "kind": "deepwork-plan-approval",
            "action": action,
            "task": "private task text is ignored by the adapter",
            "plan": steps,
            "plan_revision": revision,
            "plan_trust": plan_trust,
            "allowed_decisions": decisions,
        },
    }


def _state(
    *,
    interrupt_id: str = OFFICIAL_INTERRUPT_ID,
    revision: object = 1,
    plan: list[str] | None = None,
    final_answer: str | None = None,
    allowed_decisions: list[str] | None = None,
    action: str = "execute_plan",
    plan_trust: str = "untrusted",
) -> dict[str, object]:
    steps = ["Inspect inputs", "Produce result"] if plan is None else plan
    values: dict[str, object] = {
        "task": "private task text is ignored by the adapter",
        "plan": steps,
        "plan_revision": revision,
        "status": "planned" if final_answer is None else "completed",
        "reviewer_comment": "private review note is ignored by the adapter",
    }
    if final_answer is not None:
        values["final_answer"] = final_answer
    return {
        "values": values,
        "next": ["approve"] if final_answer is None else [],
        "checkpoint": {"checkpoint_id": f"checkpoint-official-{revision}"},
        "interrupts": (
            [
                _interrupt(
                    interrupt_id=interrupt_id,
                    revision=revision,
                    plan=steps,
                    allowed_decisions=allowed_decisions,
                    action=action,
                    plan_trust=plan_trust,
                )
            ]
            if final_answer is None
            else []
        ),
    }


@dataclass
class FakeThreads:
    state: object = field(default_factory=_state)
    create_calls: list[dict[str, object]] = field(default_factory=list)
    update_calls: list[dict[str, object]] = field(default_factory=list)
    advance_after_update: bool = True
    state_after_update: object | None = None
    call_log: list[str] | None = None
    thread_id: str = "thread-official-1"
    returned_metadata: Mapping[str, object] | None = None
    raise_after_update: bool = False

    async def create(
        self,
        *,
        metadata: Mapping[str, object] | None = None,
        thread_id: str | None = None,
        if_exists: str | None = None,
    ) -> object:
        if thread_id is not None:
            self.thread_id = thread_id
        self.create_calls.append(
            {"metadata": metadata, "thread_id": thread_id, "if_exists": if_exists}
        )
        return {
            "thread_id": self.thread_id,
            "metadata": metadata if self.returned_metadata is None else self.returned_metadata,
        }

    async def get_state(self, thread_id: str) -> object:
        assert thread_id == self.thread_id
        if self.call_log is not None:
            self.call_log.append("get_state")
        return self.state

    async def update_state(
        self,
        thread_id: str,
        values: Mapping[str, object] | None,
        *,
        as_node: str | None = None,
    ) -> object:
        if self.call_log is not None:
            self.call_log.append("update_state")
        self.update_calls.append(
            {
                "thread_id": thread_id,
                "values": values,
                "as_node": as_node,
            }
        )
        await asyncio.sleep(0)
        if self.advance_after_update:
            assert values is not None
            plan = values["plan"]
            revision = values["plan_revision"]
            assert isinstance(plan, list)
            assert all(isinstance(step, str) for step in plan)
            assert isinstance(revision, int)
            self.state = (
                self.state_after_update
                if self.state_after_update is not None
                else _state(
                    interrupt_id=NEXT_OFFICIAL_INTERRUPT_ID,
                    revision=revision,
                    plan=cast("list[str]", plan),
                )
            )
        if self.raise_after_update:
            self.raise_after_update = False
            raise OSError("update response lost after acceptance")
        return {"checkpoint": {"checkpoint_id": "checkpoint-official-2"}}


@dataclass
class BlockingGetStateThreads(FakeThreads):
    entered: asyncio.Event = field(default_factory=asyncio.Event)
    release: asyncio.Event = field(default_factory=asyncio.Event)
    get_state_calls: int = 0

    async def get_state(self, thread_id: str) -> object:
        self.get_state_calls += 1
        if self.get_state_calls == 1:
            self.entered.set()
            await self.release.wait()
        return await super().get_state(thread_id)


@dataclass
class FakeRuns:
    create_calls: list[dict[str, object]] = field(default_factory=list)
    stream_calls: list[dict[str, object]] = field(default_factory=list)
    stream_events: list[object] = field(default_factory=list)
    create_error: Exception | None = None
    call_log: list[str] | None = None
    on_stream_drained: Callable[[], None] | None = None
    list_calls: list[dict[str, object]] = field(default_factory=list)
    accepted_runs: list[dict[str, object]] = field(default_factory=list)
    raise_after_accept: bool = False

    async def list(
        self,
        thread_id: str,
        *,
        limit: int = 10,
        offset: int = 0,
        status: str | None = None,
    ) -> object:
        self.list_calls.append(
            {"thread_id": thread_id, "limit": limit, "offset": offset, "status": status}
        )
        return list(self.accepted_runs[offset : offset + limit])

    async def create(
        self,
        thread_id: str | None,
        assistant_id: str,
        *,
        input: Mapping[str, object] | None = None,
        config: Mapping[str, object] | None = None,
        command: Mapping[str, object] | None = None,
        stream_mode: str | Sequence[str] = "values",
        stream_resumable: bool = False,
        multitask_strategy: str | None = None,
        durability: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> object:
        if self.create_error is not None:
            raise self.create_error
        if self.call_log is not None:
            self.call_log.append("runs.create")
        self.create_calls.append(
            {
                "thread_id": thread_id,
                "assistant_id": assistant_id,
                "input": input,
                "config": config,
                "command": command,
                "stream_mode": stream_mode,
                "stream_resumable": stream_resumable,
                "multitask_strategy": multitask_strategy,
                "durability": durability,
                "metadata": metadata,
            }
        )
        result: dict[str, object] = {
            "run_id": f"run-official-{len(self.create_calls)}",
            "metadata": metadata,
        }
        self.accepted_runs.append(result)
        if self.raise_after_accept:
            self.raise_after_accept = False
            raise OSError("response lost after acceptance")
        return result

    def join_stream(
        self,
        thread_id: str,
        run_id: str,
        *,
        cancel_on_disconnect: bool = False,
        stream_mode: str | Sequence[str] | None = None,
        last_event_id: str | None = None,
    ) -> AsyncIterator[object]:
        if self.call_log is not None:
            self.call_log.append("join_stream")
        self.stream_calls.append(
            {
                "thread_id": thread_id,
                "run_id": run_id,
                "cancel_on_disconnect": cancel_on_disconnect,
                "stream_mode": stream_mode,
                "last_event_id": last_event_id,
            }
        )

        async def events() -> AsyncIterator[object]:
            for event in self.stream_events:
                yield event
            if self.call_log is not None:
                self.call_log.append("stream_drained")
            if self.on_stream_drained is not None:
                self.on_stream_drained()

        return events()


@dataclass
class FakeAssistants:
    response: object = field(
        default_factory=lambda: {
            "assistant_id": "deep-work-local-agent",
            "graph_id": "deep-work-local-agent",
        }
    )
    error: Exception | None = None
    get_calls: list[str] = field(default_factory=list)
    search_response: object = field(
        default_factory=lambda: [
            {
                "assistant_id": "deep-work-local-agent",
                "graph_id": "deep-work-local-agent",
                "name": "deep-work-local-agent",
                "metadata": {"created_by": "system"},
            }
        ]
    )
    search_calls: list[dict[str, object]] = field(default_factory=list)
    search_error: Exception | None = None
    create_response: object | None = None
    create_calls: list[dict[str, object]] = field(default_factory=list)
    create_error: Exception | None = None
    update_response: object | None = None
    update_calls: list[dict[str, object]] = field(default_factory=list)
    update_error: Exception | None = None
    delete_calls: list[str] = field(default_factory=list)
    delete_error: Exception | None = None

    async def get(self, assistant_id: str) -> object:
        self.get_calls.append(assistant_id)
        if self.error is not None:
            raise self.error
        return self.response

    async def search(
        self, *, graph_id: str | None = None, limit: int = 10, offset: int = 0
    ) -> object:
        if self.search_error is not None:
            raise self.search_error
        if self.error is not None:
            raise self.error
        self.search_calls.append({"graph_id": graph_id, "limit": limit, "offset": offset})
        return self.search_response

    async def create(
        self,
        graph_id: str | None,
        config: Mapping[str, object] | None = None,
        *,
        metadata: Mapping[str, object] | None = None,
        assistant_id: str | None = None,
        if_exists: str | None = None,
        name: str | None = None,
        description: str | None = None,
    ) -> object:
        if self.create_error is not None:
            raise self.create_error
        self.create_calls.append(
            {
                "graph_id": graph_id,
                "config": config,
                "name": name,
                "description": description,
                "if_exists": if_exists,
            }
        )
        return self.create_response

    async def update(
        self,
        assistant_id: str,
        *,
        config: Mapping[str, object] | None = None,
        name: str | None = None,
        description: str | None = None,
    ) -> object:
        if self.update_error is not None:
            raise self.update_error
        self.update_calls.append(
            {
                "assistant_id": assistant_id,
                "config": config,
                "name": name,
                "description": description,
            }
        )
        return self.update_response

    async def delete(self, assistant_id: str) -> None:
        if self.delete_error is not None:
            raise self.delete_error
        self.delete_calls.append(assistant_id)


@dataclass
class FakeCrons:
    search_response: object = field(default_factory=list)
    search_calls: list[dict[str, object]] = field(default_factory=list)
    search_error: Exception | None = None

    async def search(
        self, *, assistant_id: str | None = None, limit: int = 10, offset: int = 0
    ) -> object:
        if self.search_error is not None:
            raise self.search_error
        self.search_calls.append({"assistant_id": assistant_id, "limit": limit, "offset": offset})
        return self.search_response


@dataclass
class FakeClient:
    threads: FakeThreads = field(default_factory=FakeThreads)
    runs: FakeRuns = field(default_factory=FakeRuns)
    assistants: FakeAssistants = field(default_factory=FakeAssistants)
    crons: FakeCrons = field(default_factory=FakeCrons)
    closed: bool = False

    async def aclose(self) -> None:
        self.closed = True


def _source(client: FakeClient | None = None) -> tuple[LocalAgentServerSource, FakeClient]:
    fake = client or FakeClient()
    return LocalAgentServerSource(client=fake), fake


@pytest.mark.parametrize(
    "value",
    [
        "https://127.0.0.1:2024",
        "http://localhost:2024",
        "http://127.0.0.2:2024",
        "http://127.0.0.1",
        "http://user:secret@127.0.0.1:2024",
        "http://127.0.0.1:2024/path",
        "http://127.0.0.1:2024?token=secret",
        "http://127.0.0.1:2024#fragment",
    ],
)
def test_source_rejects_every_non_fixed_loopback_origin(value: str) -> None:
    with pytest.raises(LocalSourceConfigurationError):
        validate_loopback_url(value)


def test_source_normalizes_supported_ipv4_and_ipv6_loopback() -> None:
    assert validate_loopback_url("http://127.0.0.1:2024/") == "http://127.0.0.1:2024"
    assert validate_loopback_url("http://[::1]:2024") == "http://[::1]:2024"


def test_official_client_explicitly_suppresses_ambient_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private_values = {
        "LANGGRAPH_API_KEY": "secret-langgraph-key",
        "LANGSMITH_API_KEY": "secret-langsmith-key",
        "LANGCHAIN_API_KEY": "secret-langchain-key",
    }
    for name, value in private_values.items():
        monkeypatch.setenv(name, value)
    captured: dict[str, object] = {}
    client = object()

    def get_client(**kwargs: object) -> object:
        captured.update(kwargs)
        return client

    monkeypatch.setattr(
        "deepwork_api.adapters.sources.local.source.importlib.import_module",
        lambda _: SimpleNamespace(get_client=get_client),
    )

    assert create_official_client() is client
    assert captured == {
        "url": "http://127.0.0.1:2024",
        "api_key": None,
        "headers": {},
        "timeout": (5.0, 300.0, 30.0, 5.0),
    }
    assert all(secret not in repr(captured) for secret in private_values.values())


async def test_start_uses_official_thread_and_resumable_run_calls() -> None:
    source, client = _source()

    run = await source.start("Prepare a release brief", dispatch_id=DISPATCH_ID)

    assert run == LocalRunReference(thread_id=client.threads.thread_id, run_id="run-official-1")
    assert client.threads.create_calls == [
        {
            "metadata": {
                "deepwork_source": "local-agent-server",
                "deepwork_dispatch_id": DISPATCH_ID,
            },
            "thread_id": client.threads.thread_id,
            "if_exists": "do_nothing",
        }
    ]
    assert client.runs.create_calls == [
        {
            "thread_id": client.threads.thread_id,
            "assistant_id": "deep-work-local-agent",
            "input": {"task": "Prepare a release brief"},
            "config": None,
            "command": None,
            "stream_mode": ("values", "updates"),
            "stream_resumable": True,
            "multitask_strategy": "reject",
            "durability": "sync",
            "metadata": {
                "deepwork_dispatch_id": DISPATCH_ID,
                "deepwork_transition_kind": "initial",
                "deepwork_objective_digest": (
                    "d580a514c19e3c658b72a9e3d29a67d38ab69fdbde94a445d066ae91b5e6d95f"
                ),
                "deepwork_agent_id": "deep-work-local-agent",
            },
        }
    ]


async def test_start_forwards_system_prompt_as_run_config() -> None:
    """A supplied workspace prompt reaches the run as configurable.system_prompt."""
    source, client = _source()

    await source.start(
        "Prepare a release brief",
        dispatch_id=DISPATCH_ID,
        system_prompt="  Always be terse.  ",
    )

    call = client.runs.create_calls[0]
    # Delivered in the input (reaches a hosted graph) and the config (local runs).
    assert call["input"] == {"task": "Prepare a release brief", "system_prompt": "Always be terse."}
    assert call["config"] == {"configurable": {"system_prompt": "Always be terse."}}


async def test_start_without_system_prompt_sends_no_run_config() -> None:
    """No override keeps the request shape identical to before (config=None)."""
    source, client = _source()

    await source.start("Prepare a release brief", dispatch_id=DISPATCH_ID)

    assert client.runs.create_calls[0]["config"] is None


async def test_start_reuses_an_already_accepted_dispatch_run() -> None:
    source, client = _source()

    first = await source.start("Prepare a release brief", dispatch_id=DISPATCH_ID)
    recovered = await source.start("Prepare a release brief", dispatch_id=DISPATCH_ID)

    assert recovered == first
    assert len(client.threads.create_calls) == 2
    assert len(client.runs.create_calls) == 1
    assert len(client.runs.list_calls) == 2


async def test_start_recovers_when_acceptance_response_is_lost() -> None:
    source, client = _source()
    client.runs.raise_after_accept = True

    recovered = await source.start("Prepare a release brief", dispatch_id=DISPATCH_ID)

    assert recovered.run_id == "run-official-1"
    assert len(client.runs.create_calls) == 1
    assert len(client.runs.list_calls) == 2


async def test_start_rejects_a_thread_owned_by_another_dispatch() -> None:
    source, client = _source()
    client.threads.returned_metadata = {
        "deepwork_source": "local-agent-server",
        "deepwork_dispatch_id": "run_someone-else",
    }

    with pytest.raises(LocalSourceContractError, match="ownership metadata"):
        await source.start("Prepare a release brief", dispatch_id=DISPATCH_ID)

    assert client.runs.create_calls == []


async def test_start_discovers_an_accepted_dispatch_after_the_first_run_page() -> None:
    source, client = _source()
    accepted_runs: list[dict[str, object]] = [
        {"run_id": f"unrelated-{position}", "metadata": {}} for position in range(100)
    ]
    accepted_runs.append(
        {
            "run_id": "run-accepted-later",
            "metadata": {
                "deepwork_dispatch_id": DISPATCH_ID,
                "deepwork_transition_kind": "initial",
                "deepwork_objective_digest": (
                    "d580a514c19e3c658b72a9e3d29a67d38ab69fdbde94a445d066ae91b5e6d95f"
                ),
                "deepwork_agent_id": "deep-work-local-agent",
            },
        }
    )
    client.runs.accepted_runs = accepted_runs

    recovered = await source.start("Prepare a release brief", dispatch_id=DISPATCH_ID)

    assert recovered.run_id == "run-accepted-later"
    assert client.runs.create_calls == []
    assert [call["offset"] for call in client.runs.list_calls] == [0, 100]


async def test_close_releases_official_client_transport() -> None:
    source, client = _source()

    await source.close()

    assert client.closed is True


async def test_status_is_sanitized_and_makes_no_provider_claim() -> None:
    source, _ = _source()

    status = await source.status()
    assert status.available is True
    assert status.code == "ready"
    capabilities = source.capabilities()
    assert capabilities.transport == "langgraph-sdk"
    assert capabilities.loopback_only is True
    assert capabilities.accepts_credentials is False
    assert not hasattr(capabilities, "external_providers")

    failing, _ = _source(
        FakeClient(
            assistants=FakeAssistants(error=RuntimeError("private upstream token=do-not-disclose"))
        )
    )
    unavailable = await failing.status()
    assert unavailable.code == "unavailable"
    assert "private" not in repr(unavailable)


async def test_graph_alias_resolves_the_system_default_uuid_for_runs() -> None:
    default_uuid = "96006ada-3e38-5556-9139-b74b9e91971e"
    assistants = FakeAssistants(
        search_response=[
            {
                "assistant_id": default_uuid,
                "graph_id": "deep-work-local-agent",
                "name": "deep-work-local-agent",
                "metadata": {"created_by": "system"},
            }
        ]
    )
    source, client = _source(FakeClient(assistants=assistants))

    await source.start(
        "Prepare a release brief",
        dispatch_id=DISPATCH_ID,
        system_prompt="Always be terse.",
        agent_id=default_uuid,
    )

    assert client.assistants.get_calls == []
    assert client.runs.create_calls[0]["assistant_id"] == default_uuid
    assert client.runs.create_calls[0]["input"] == {
        "task": "Prepare a release brief",
        "system_prompt": "Always be terse.",
    }


async def test_uuid_default_uses_direct_lookup_without_graph_search() -> None:
    default_uuid = "019f91f5-4e11-75f2-b86f-01c3f3d7b9ba"
    assistants = FakeAssistants(
        response={"assistant_id": default_uuid, "graph_id": "deep-work-local-agent"}
    )
    source = LocalAgentServerSource(
        client=FakeClient(assistants=assistants),
        assistant_id=default_uuid,
    )

    await source.start("Prepare a release brief", dispatch_id=DISPATCH_ID)

    assert assistants.get_calls == [default_uuid]
    assert assistants.search_calls == []


async def test_graph_alias_fails_closed_when_the_default_is_ambiguous() -> None:
    assistants = FakeAssistants(
        search_response=[
            {"assistant_id": "assistant-1", "graph_id": "deep-work-local-agent"},
            {"assistant_id": "assistant-2", "graph_id": "deep-work-local-agent"},
        ]
    )
    source, _ = _source(FakeClient(assistants=assistants))

    status = await source.status()

    assert status == LocalAgentServerStatus(available=False, code="contract-mismatch")


async def test_start_with_agent_id_overrides_the_default_assistant() -> None:
    source, client = _source()

    run = await source.start(
        "Prepare a release brief", dispatch_id=DISPATCH_ID, agent_id="assistant-2"
    )

    assert run == LocalRunReference(thread_id=client.threads.thread_id, run_id="run-official-1")
    assert client.runs.create_calls[0]["assistant_id"] == "assistant-2"


async def test_start_with_agent_id_ignores_the_workspace_prompt_override() -> None:
    """A selected named agent's own config governs it; the two never fight."""
    source, client = _source()

    await source.start(
        "Prepare a release brief",
        dispatch_id=DISPATCH_ID,
        system_prompt="Always be terse.",
        agent_id="assistant-2",
    )

    call = client.runs.create_calls[0]
    assert call["input"] == {"task": "Prepare a release brief"}
    assert call["config"] is None


async def test_start_with_explicit_default_agent_keeps_workspace_prompt_override() -> None:
    source, client = _source()

    await source.start(
        "Prepare a release brief",
        dispatch_id=DISPATCH_ID,
        system_prompt="Always be terse.",
        agent_id="deep-work-local-agent",
    )

    call = client.runs.create_calls[0]
    assert call["assistant_id"] == "deep-work-local-agent"
    assert call["input"] == {
        "task": "Prepare a release brief",
        "system_prompt": "Always be terse.",
    }
    assert call["config"] == {"configurable": {"system_prompt": "Always be terse."}}


async def test_resume_and_update_plan_replay_the_thread_bound_assistant() -> None:
    """A thread started with a non-default agent keeps using that exact agent."""
    source, client = _source()
    await source.start("Prepare a release brief", dispatch_id=DISPATCH_ID, agent_id="assistant-2")

    await source.resume(
        client.threads.thread_id,
        interrupt_id=OFFICIAL_INTERRUPT_ID,
        decision="approve",
        transition_id=TRANSITION_ID,
    )

    assert client.runs.create_calls[-1]["assistant_id"] == "assistant-2"


async def test_list_agents_scopes_search_to_the_default_agents_graph() -> None:
    assistant = {
        "assistant_id": "assistant-2",
        "graph_id": "deep-work-local-agent",
        "name": "Terse reviewer",
        "description": "Keeps everything short.",
        "config": {"configurable": {"system_prompt": "Always be terse."}},
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-02T00:00:00Z",
    }
    default: dict[str, object] = {
        "assistant_id": "deep-work-local-agent",
        "graph_id": "deep-work-local-agent",
        "name": "deep-work-local-agent",
        "description": None,
        "config": {},
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    }
    assistants = FakeAssistants(search_response=[default, assistant])
    source, client = _source(FakeClient(assistants=assistants))

    agents = await source.list_agents()

    assert client.assistants.search_calls == [
        {"graph_id": "deep-work-local-agent", "limit": 100, "offset": 0}
    ]
    assert agents == (
        AgentSummary(
            agent_id="deep-work-local-agent",
            name="deep-work-local-agent",
            description=None,
            system_prompt=None,
            is_default=True,
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
        ),
        AgentSummary(
            agent_id="assistant-2",
            name="Terse reviewer",
            description="Keeps everything short.",
            system_prompt="Always be terse.",
            is_default=False,
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-02T00:00:00Z",
        ),
    )


async def test_create_agent_binds_to_the_default_agents_graph_with_its_own_config() -> None:
    created = {
        "assistant_id": "assistant-3",
        "name": "Release reviewer",
        "description": "Reviews release notes.",
        "config": {"configurable": {"system_prompt": "Be precise."}},
        "created_at": "2026-01-03T00:00:00Z",
        "updated_at": "2026-01-03T00:00:00Z",
    }
    assistants = FakeAssistants(create_response=created)
    source, client = _source(FakeClient(assistants=assistants))

    agent = await source.create_agent(
        name="  Release reviewer  ",
        description="  Reviews release notes.  ",
        system_prompt="  Be precise.  ",
    )

    assert client.assistants.create_calls == [
        {
            "graph_id": "deep-work-local-agent",
            "config": {"configurable": {"system_prompt": "Be precise."}},
            "name": "Release reviewer",
            "description": "Reviews release notes.",
            "if_exists": "raise",
        }
    ]
    assert agent.agent_id == "assistant-3"
    assert agent.is_default is False


async def test_update_agent_sends_an_explicit_empty_config_to_clear_the_prompt() -> None:
    updated: dict[str, object] = {
        "assistant_id": "assistant-3",
        "name": "Renamed reviewer",
        "description": None,
        "config": {},
        "created_at": "2026-01-03T00:00:00Z",
        "updated_at": "2026-01-04T00:00:00Z",
    }
    assistants = FakeAssistants(update_response=updated)
    source, client = _source(FakeClient(assistants=assistants))

    agent = await source.update_agent(
        "assistant-3", name="Renamed reviewer", description=None, system_prompt=None
    )

    assert client.assistants.update_calls == [
        {
            "assistant_id": "assistant-3",
            "config": {},
            "name": "Renamed reviewer",
            "description": None,
        }
    ]
    assert agent.system_prompt is None


async def test_update_and_delete_reject_the_default_agent() -> None:
    source, client = _source()

    with pytest.raises(LocalSourceDefaultAgentImmutableError):
        await source.update_agent(
            "deep-work-local-agent", name="x", description=None, system_prompt=None
        )
    with pytest.raises(LocalSourceDefaultAgentImmutableError):
        await source.delete_agent("deep-work-local-agent")
    assert client.assistants.update_calls == []
    assert client.assistants.delete_calls == []


async def test_delete_agent_deletes_a_non_default_assistant() -> None:
    source, client = _source()

    await source.delete_agent("assistant-3")

    assert client.assistants.delete_calls == ["assistant-3"]


async def test_agent_registry_calls_wrap_upstream_failures() -> None:
    failing, _ = _source(FakeClient(assistants=FakeAssistants(search_error=RuntimeError("boom"))))
    with pytest.raises(LocalSourceUnavailableError):
        await failing.list_agents()

    failing, _ = _source(FakeClient(assistants=FakeAssistants(create_error=RuntimeError("boom"))))
    with pytest.raises(LocalSourceUnavailableError):
        await failing.create_agent(name="x", description=None, system_prompt=None)

    failing, _ = _source(FakeClient(assistants=FakeAssistants(update_error=RuntimeError("boom"))))
    with pytest.raises(LocalSourceUnavailableError):
        await failing.update_agent("assistant-3", name="x", description=None, system_prompt=None)

    failing, _ = _source(FakeClient(assistants=FakeAssistants(delete_error=RuntimeError("boom"))))
    with pytest.raises(LocalSourceUnavailableError):
        await failing.delete_agent("assistant-3")


async def test_list_schedules_filters_to_our_graphs_agents() -> None:
    assistants = FakeAssistants(
        search_response=[
            {
                "assistant_id": "deep-work-local-agent",
                "graph_id": "deep-work-local-agent",
                "name": "deep-work-local-agent",
                "description": None,
                "config": {},
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
            }
        ]
    )
    crons = FakeCrons(
        search_response=[
            {
                "cron_id": "cron-1",
                "assistant_id": "deep-work-local-agent",
                "schedule": "0 9 * * *",
                "timezone": "America/New_York",
                "end_time": None,
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
            },
            {
                "cron_id": "cron-2",
                "assistant_id": "unrelated-graph-assistant",
                "schedule": "0 10 * * *",
                "timezone": None,
                "end_time": None,
                "created_at": "2026-01-02T00:00:00Z",
                "updated_at": "2026-01-02T00:00:00Z",
            },
        ]
    )
    source, client = _source(FakeClient(assistants=assistants, crons=crons))

    schedules = await source.list_schedules()

    assert client.crons.search_calls == [{"assistant_id": None, "limit": 100, "offset": 0}]
    assert schedules == (
        ScheduleSummary(
            schedule_id="cron-1",
            agent_id="deep-work-local-agent",
            cron_expression="0 9 * * *",
            timezone="America/New_York",
            end_time=None,
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
        ),
    )


async def test_list_schedules_wraps_upstream_failure() -> None:
    failing, _ = _source(FakeClient(crons=FakeCrons(search_error=RuntimeError("boom"))))
    with pytest.raises(LocalSourceUnavailableError):
        await failing.list_schedules()


async def test_state_uses_official_interrupt_id_and_omits_private_fields() -> None:
    source, _ = _source()

    snapshot = await source.get_state("thread-official-1")

    assert snapshot.plan == ("Inspect inputs", "Produce result")
    assert snapshot.plan_revision == 1
    assert snapshot.interrupt is not None
    assert snapshot.interrupt.interrupt_id == OFFICIAL_INTERRUPT_ID
    assert snapshot.interrupt.allowed_decisions == ("approve", "reject", "respond")
    assert "private task" not in repr(snapshot)
    assert "private review" not in repr(snapshot)


@pytest.mark.parametrize(
    ("state", "message"),
    [
        (_state(action="delete_repository"), "action"),
        (_state(plan_trust="trusted"), "trust marker"),
    ],
)
async def test_state_rejects_wrong_interrupt_action_or_trust(
    state: dict[str, object],
    message: str,
) -> None:
    source, _ = _source(FakeClient(threads=FakeThreads(state=state)))

    with pytest.raises(LocalSourceContractError, match=message):
        await source.get_state("thread-official-1")


async def test_stream_sanitizes_payload_and_exposes_only_application_receipts() -> None:
    source, client = _source()
    client.runs.stream_events = [
        {
            "event": "metadata",
            "data": {"run_id": "run-official-1", "secret": "not-exposed"},
            "id": "event-alpha",
        },
        {
            "event": "updates",
            "data": {"plan": {"reviewer_comment": "not-exposed"}},
            "id": "event-beta",
        },
        {
            "event": "error",
            "data": {"message": "private upstream failure"},
            "id": "event-gamma",
        },
    ]

    events = [
        event
        async for event in source.stream(LocalRunReference("thread-official-1", "run-official-1"))
    ]

    assert client.runs.stream_calls == [
        {
            "thread_id": "thread-official-1",
            "run_id": "run-official-1",
            "cancel_on_disconnect": False,
            "stream_mode": ("values", "updates"),
            "last_event_id": None,
        }
    ]
    receipt_keys = [event.receipt_key for event in events]
    assert all(
        isinstance(receipt_key, str)
        and len(receipt_key) == 64
        and set(receipt_key) <= set("0123456789abcdef")
        for receipt_key in receipt_keys
    )
    assert len(set(receipt_keys)) == 3
    assert all(
        source_id not in repr(events) for source_id in ("event-alpha", "event-beta", "event-gamma")
    )
    assert events[0].run_id == "run-official-1"
    assert events[1].updated_nodes == ("plan",)
    assert events[2].summary == "The local Agent Server reported a run error."
    assert "not-exposed" not in repr(events)
    assert "private upstream" not in repr(events)


@pytest.mark.parametrize("decision", ["approve", "reject", "respond"])
async def test_resume_uses_public_command_for_exact_current_interrupt(
    decision: str,
) -> None:
    source, client = _source()
    comment = "Please tighten the evidence." if decision == "respond" else None

    run = await source.resume(
        "thread-official-1",
        interrupt_id=OFFICIAL_INTERRUPT_ID,
        decision=cast("Decision", decision),
        transition_id=TRANSITION_ID,
        comment=comment,
        agent_id="assistant-evidence-reviewer",
    )

    assert run.run_id == "run-official-1"
    resume_value = {"decision": decision}
    if comment is not None:
        resume_value["comment"] = comment
    assert client.runs.create_calls[0]["command"] == {
        "resume": {OFFICIAL_INTERRUPT_ID: resume_value}
    }
    assert client.runs.create_calls[0]["assistant_id"] == "assistant-evidence-reviewer"
    assert source._thread_locks == {}


async def test_resume_reuses_an_accepted_transition_without_the_lost_comment() -> None:
    source, client = _source()
    client.runs.accepted_runs.append(
        {
            "run_id": "run-resume-accepted",
            "metadata": {
                "deepwork_transition_id": TRANSITION_ID,
                "deepwork_interrupt_id": OFFICIAL_INTERRUPT_ID,
                "deepwork_decision": "respond",
                "deepwork_agent_id": "assistant-evidence-reviewer",
            },
        }
    )

    recovered = await source.resume(
        "thread-official-1",
        interrupt_id=OFFICIAL_INTERRUPT_ID,
        decision="respond",
        transition_id=TRANSITION_ID,
        comment=None,
        agent_id="assistant-evidence-reviewer",
    )

    assert recovered.run_id == "run-resume-accepted"
    assert client.runs.create_calls == []


async def test_resume_recovers_when_acceptance_response_is_lost() -> None:
    source, client = _source()
    client.runs.raise_after_accept = True

    recovered = await source.resume(
        client.threads.thread_id,
        interrupt_id=OFFICIAL_INTERRUPT_ID,
        decision="approve",
        transition_id=TRANSITION_ID,
        agent_id="assistant-evidence-reviewer",
    )

    assert recovered.run_id == "run-official-1"
    assert len(client.runs.create_calls) == 1
    assert len(client.runs.list_calls) == 2


async def test_resume_rejects_stale_interrupt_and_bounded_response_before_command() -> None:
    source, client = _source()

    with pytest.raises(LocalSourceStaleInterruptError, match="no longer current"):
        await source.resume(
            "thread-official-1",
            interrupt_id="interrupt-other",
            decision="approve",
            transition_id=TRANSITION_ID,
        )
    with pytest.raises(LocalSourceContractError, match="requires"):
        await source.resume(
            "thread-official-1",
            interrupt_id=OFFICIAL_INTERRUPT_ID,
            decision="respond",
            transition_id=TRANSITION_ID,
        )
    private_note = "private-" + "x" * 1_001
    with pytest.raises(LocalSourceContractError) as error:
        await source.resume(
            "thread-official-1",
            interrupt_id=OFFICIAL_INTERRUPT_ID,
            decision="respond",
            transition_id=TRANSITION_ID,
            comment=private_note,
        )
    assert private_note not in str(error.value)
    assert client.runs.create_calls == []
    assert source._thread_locks == {}


@pytest.mark.parametrize(
    "decisions",
    [
        ["approve", "reject"],
        ["respond", "reject", "approve"],
        ["approve", "approve", "reject", "respond"],
        [],
    ],
)
async def test_interrupt_requires_exact_canonical_decisions(
    decisions: list[str],
) -> None:
    source, _ = _source(
        FakeClient(
            threads=FakeThreads(
                state=_state(allowed_decisions=decisions),
            )
        )
    )

    with pytest.raises(LocalSourceContractError, match="decisions"):
        await source.get_state("thread-official-1")


async def test_interrupt_rejects_missing_decisions() -> None:
    state = _state()
    interrupts = cast("list[dict[str, object]]", state["interrupts"])
    payload = cast("dict[str, object]", interrupts[0]["value"])
    del payload["allowed_decisions"]
    source, _ = _source(FakeClient(threads=FakeThreads(state=state)))

    with pytest.raises(LocalSourceContractError, match="decisions"):
        await source.get_state("thread-official-1")


@pytest.mark.parametrize("status_code", [404, 409])
async def test_resume_keeps_ambiguous_source_errors_generic(status_code: int) -> None:
    request = httpx.Request("POST", "http://127.0.0.1:2024/threads/thread/runs")
    response = httpx.Response(status_code, request=request)
    upstream = httpx.HTTPStatusError(
        "private upstream conflict detail",
        request=request,
        response=response,
    )
    client = FakeClient(runs=FakeRuns(create_error=upstream))
    source, _ = _source(client)

    with pytest.raises(LocalSourceUnavailableError) as error:
        await source.resume(
            "thread-official-1",
            interrupt_id=OFFICIAL_INTERRUPT_ID,
            decision="approve",
            transition_id=TRANSITION_ID,
        )

    assert "private upstream" not in str(error.value)
    assert source._thread_locks == {}


async def test_plan_edit_uses_official_plan_node_and_reinvokes_for_new_interrupt() -> None:
    source, client = _source()

    update = await source.update_plan(
        "thread-official-1",
        interrupt_id=OFFICIAL_INTERRUPT_ID,
        expected_revision=1,
        steps=["Inspect exact inputs", "Produce evidenced result"],
        agent_id="assistant-evidence-reviewer",
    )

    assert update.plan_revision == 2
    assert update.run_id == "run-official-1"
    assert update.interrupt_id == NEXT_OFFICIAL_INTERRUPT_ID
    assert client.threads.update_calls == [
        {
            "thread_id": "thread-official-1",
            "values": {
                "plan": ["Inspect exact inputs", "Produce evidenced result"],
                "plan_revision": 2,
                "plan_trust": "untrusted",
                "approval": "pending",
                "status": "planned",
            },
            "as_node": "plan",
        }
    ]
    assert client.runs.create_calls[0]["input"] is None
    assert client.runs.create_calls[0]["command"] is None
    assert client.runs.create_calls[0]["assistant_id"] == "assistant-evidence-reviewer"
    assert client.runs.stream_calls == []
    with pytest.raises(LocalSourceStaleInterruptError):
        await source.resume(
            "thread-official-1",
            interrupt_id=OFFICIAL_INTERRUPT_ID,
            decision="approve",
            transition_id=TRANSITION_ID,
        )
    resumed = await source.resume(
        "thread-official-1",
        interrupt_id=update.interrupt_id,
        decision="approve",
        transition_id="transition-after-plan-edit",
    )
    assert resumed.run_id == "run-official-2"


async def test_plan_edit_recovers_when_update_state_response_is_lost() -> None:
    client = FakeClient(threads=FakeThreads(raise_after_update=True))
    source, _ = _source(client)

    update = await source.update_plan(
        "thread-official-1",
        interrupt_id=OFFICIAL_INTERRUPT_ID,
        expected_revision=1,
        steps=["Edited step"],
        transition_id=TRANSITION_ID,
    )

    assert update.plan_revision == 2
    assert update.interrupt_id == NEXT_OFFICIAL_INTERRUPT_ID
    assert len(client.threads.update_calls) == 1
    assert len(client.runs.create_calls) == 1


async def test_plan_edit_recovers_when_run_acceptance_response_is_lost() -> None:
    client = FakeClient(runs=FakeRuns(raise_after_accept=True))
    source, _ = _source(client)

    update = await source.update_plan(
        "thread-official-1",
        interrupt_id=OFFICIAL_INTERRUPT_ID,
        expected_revision=1,
        steps=["Edited step"],
        transition_id=TRANSITION_ID,
    )

    assert update.run_id == "run-official-1"
    assert len(client.runs.create_calls) == 1
    assert len(client.runs.list_calls) == 2


async def test_plan_edit_reuses_the_same_accepted_transition_on_retry() -> None:
    source, client = _source()

    first = await source.update_plan(
        "thread-official-1",
        interrupt_id=OFFICIAL_INTERRUPT_ID,
        expected_revision=1,
        steps=["Edited step"],
        transition_id=TRANSITION_ID,
    )
    recovered = await source.update_plan(
        "thread-official-1",
        interrupt_id=OFFICIAL_INTERRUPT_ID,
        expected_revision=1,
        steps=["Edited step"],
        transition_id=TRANSITION_ID,
    )

    assert recovered == first
    assert len(client.threads.update_calls) == 1
    assert len(client.runs.create_calls) == 1


async def test_plan_recovery_confirms_settled_state_without_waiting_for_a_silent_stream() -> None:
    step = "Edited step"
    encoded = step.encode()
    digest = hashlib.sha256()
    digest.update(len(encoded).to_bytes(8, byteorder="big"))
    digest.update(encoded)
    runs = FakeRuns(
        accepted_runs=[
            {
                "run_id": "run-plan-accepted",
                "metadata": {
                    "deepwork_transition_id": TRANSITION_ID,
                    "deepwork_transition_kind": "plan",
                    "deepwork_interrupt_id": OFFICIAL_INTERRUPT_ID,
                    "deepwork_plan_revision": "2",
                    "deepwork_plan_digest": digest.hexdigest(),
                    "deepwork_agent_id": "deep-work-local-agent",
                },
            }
        ]
    )
    threads = FakeThreads(
        state=_state(
            interrupt_id=NEXT_OFFICIAL_INTERRUPT_ID,
            revision=2,
            plan=[step],
        )
    )
    source, _ = _source(FakeClient(threads=threads, runs=runs))

    recovered = await source.update_plan(
        "thread-official-1",
        interrupt_id=OFFICIAL_INTERRUPT_ID,
        expected_revision=1,
        steps=[step],
        transition_id=TRANSITION_ID,
    )

    assert recovered.run_id == "run-plan-accepted"
    assert runs.stream_calls == []


async def test_plan_edit_preserves_exact_valid_step_whitespace() -> None:
    source, client = _source()
    steps = ["  Preserve exact spacing.  ", "\tPreserve tabs too.\t"]

    update = await source.update_plan(
        "thread-official-1",
        interrupt_id=OFFICIAL_INTERRUPT_ID,
        expected_revision=1,
        steps=steps,
    )
    state = await source.get_state("thread-official-1")
    update_values = cast(
        "Mapping[str, object]",
        client.threads.update_calls[0]["values"],
    )

    assert update_values["plan"] == steps
    assert state.plan == tuple(steps)
    assert state.interrupt is not None
    assert state.interrupt.interrupt_id == update.interrupt_id
    assert state.interrupt.plan == tuple(steps)


async def test_plan_edit_drains_run_before_reading_authoritative_state() -> None:
    call_log: list[str] = []
    threads = FakeThreads(
        advance_after_update=False,
        call_log=call_log,
    )

    def expose_fresh_state() -> None:
        threads.state = _state(
            interrupt_id=NEXT_OFFICIAL_INTERRUPT_ID,
            revision=2,
            plan=["Edited step"],
        )

    runs = FakeRuns(
        call_log=call_log,
        on_stream_drained=expose_fresh_state,
    )
    source, _ = _source(FakeClient(threads=threads, runs=runs))

    update = await source.update_plan(
        "thread-official-1",
        interrupt_id=OFFICIAL_INTERRUPT_ID,
        expected_revision=1,
        steps=["Edited step"],
    )

    assert update.interrupt_id == NEXT_OFFICIAL_INTERRUPT_ID
    assert call_log == [
        "get_state",
        "update_state",
        "runs.create",
        "get_state",
        "join_stream",
        "stream_drained",
        "get_state",
    ]


async def test_plan_edits_are_serialized_per_thread_before_current_head_check() -> None:
    client = FakeClient()
    source, _ = _source(client)

    results = await asyncio.gather(
        source.update_plan(
            "thread-official-1",
            interrupt_id=OFFICIAL_INTERRUPT_ID,
            expected_revision=1,
            steps=["First edit"],
        ),
        source.update_plan(
            "thread-official-1",
            interrupt_id=OFFICIAL_INTERRUPT_ID,
            expected_revision=1,
            steps=["Concurrent stale edit"],
        ),
        return_exceptions=True,
    )

    assert sum(isinstance(result, LocalSourceStaleInterruptError) for result in results) == 1
    assert len(client.threads.update_calls) == 1
    assert len(client.runs.create_calls) == 1
    assert source._thread_locks == {}


@pytest.mark.parametrize(
    "confirmed_state",
    [
        _state(
            interrupt_id=OFFICIAL_INTERRUPT_ID,
            revision=2,
            plan=["Edited step"],
        ),
        _state(
            interrupt_id=NEXT_OFFICIAL_INTERRUPT_ID,
            revision=2,
            plan=["Different step"],
        ),
        _state(
            interrupt_id=NEXT_OFFICIAL_INTERRUPT_ID,
            revision=3,
            plan=["Edited step"],
        ),
        _state(
            interrupt_id=NEXT_OFFICIAL_INTERRUPT_ID,
            revision=2,
            plan=["Edited step"],
            action="delete_repository",
        ),
        _state(
            interrupt_id=NEXT_OFFICIAL_INTERRUPT_ID,
            revision=2,
            plan=["Edited step"],
            plan_trust="trusted",
        ),
        _state(
            interrupt_id=NEXT_OFFICIAL_INTERRUPT_ID,
            revision=2,
            plan=["Edited step"],
            allowed_decisions=["approve", "reject"],
        ),
    ],
)
async def test_plan_edit_requires_fresh_canonical_interrupt(
    confirmed_state: dict[str, object],
) -> None:
    client = FakeClient(
        threads=FakeThreads(state_after_update=confirmed_state),
    )
    source, _ = _source(client)

    with pytest.raises(LocalSourceContractError):
        await source.update_plan(
            "thread-official-1",
            interrupt_id=OFFICIAL_INTERRUPT_ID,
            expected_revision=1,
            steps=["Edited step"],
        )

    assert len(client.threads.update_calls) == 1
    assert len(client.runs.create_calls) == 1
    assert source._thread_locks == {}


@pytest.mark.parametrize(
    "revision",
    [False, 0, -1, MAX_PLAN_REVISION + 1, "1"],
)
async def test_state_rejects_invalid_plan_revision(revision: object) -> None:
    source, _ = _source(
        FakeClient(
            threads=FakeThreads(
                state=_state(revision=revision),
            )
        )
    )

    with pytest.raises(LocalSourceContractError, match="revision"):
        await source.get_state("thread-official-1")


async def test_state_rejects_out_of_bound_interrupt_revision() -> None:
    state = _state()
    interrupts = cast("list[dict[str, object]]", state["interrupts"])
    payload = cast("dict[str, object]", interrupts[0]["value"])
    payload["plan_revision"] = MAX_PLAN_REVISION + 1
    source, _ = _source(FakeClient(threads=FakeThreads(state=state)))

    with pytest.raises(LocalSourceContractError, match="revision"):
        await source.get_state("thread-official-1")


@pytest.mark.parametrize("revision", [False, 0, -1, MAX_PLAN_REVISION + 1])
async def test_plan_edit_rejects_invalid_expected_revision_before_mutation(
    revision: int,
) -> None:
    source, client = _source()

    with pytest.raises(LocalSourceContractError, match="revision"):
        await source.update_plan(
            "thread-official-1",
            interrupt_id=OFFICIAL_INTERRUPT_ID,
            expected_revision=revision,
            steps=["Edited step"],
        )

    assert client.threads.update_calls == []
    assert client.runs.create_calls == []
    assert source._thread_locks == {}


async def test_plan_revision_can_advance_exactly_to_shared_maximum() -> None:
    revision = MAX_PLAN_REVISION - 1
    source, client = _source(
        FakeClient(
            threads=FakeThreads(
                state=_state(revision=revision),
            )
        )
    )

    update = await source.update_plan(
        "thread-official-1",
        interrupt_id=OFFICIAL_INTERRUPT_ID,
        expected_revision=revision,
        steps=["Edited step"],
    )
    state = await source.get_state("thread-official-1")
    update_values = cast(
        "Mapping[str, object]",
        client.threads.update_calls[0]["values"],
    )

    assert update.plan_revision == revision + 1
    assert update.interrupt_id == NEXT_OFFICIAL_INTERRUPT_ID
    assert update_values["plan_revision"] == revision + 1
    assert state.plan_revision == revision + 1


async def test_plan_revision_maximum_cannot_mutate_the_agent_server() -> None:
    source, client = _source(
        FakeClient(
            threads=FakeThreads(
                state=_state(revision=MAX_PLAN_REVISION),
            )
        )
    )

    with pytest.raises(LocalSourceContractError, match="cannot be advanced"):
        await source.update_plan(
            "thread-official-1",
            interrupt_id=OFFICIAL_INTERRUPT_ID,
            expected_revision=MAX_PLAN_REVISION,
            steps=["Edited step"],
        )

    assert client.threads.update_calls == []
    assert client.runs.create_calls == []
    assert client.runs.stream_calls == []
    assert source._thread_locks == {}


async def test_thread_lock_registry_evicts_cancelled_waiter_and_final_holder() -> None:
    threads = BlockingGetStateThreads()
    source, _ = _source(FakeClient(threads=threads))
    holder = asyncio.create_task(
        source.resume(
            "thread-official-1",
            interrupt_id=OFFICIAL_INTERRUPT_ID,
            decision="approve",
            transition_id=TRANSITION_ID,
        )
    )
    await threads.entered.wait()
    waiter = asyncio.create_task(
        source.resume(
            "thread-official-1",
            interrupt_id=OFFICIAL_INTERRUPT_ID,
            decision="approve",
            transition_id=TRANSITION_ID,
        )
    )
    for _ in range(10):
        entry = source._thread_locks.get("thread-official-1")
        if entry is not None and entry.users == 2:
            break
        await asyncio.sleep(0)
    assert entry is not None
    assert entry.users == 2

    waiter.cancel()
    with pytest.raises(asyncio.CancelledError):
        await waiter
    assert source._thread_locks["thread-official-1"].users == 1

    threads.release.set()
    await holder
    assert source._thread_locks == {}


async def test_thread_lock_registry_evicts_cancelled_holder() -> None:
    threads = BlockingGetStateThreads()
    source, _ = _source(FakeClient(threads=threads))
    holder = asyncio.create_task(
        source.resume(
            "thread-official-1",
            interrupt_id=OFFICIAL_INTERRUPT_ID,
            decision="approve",
            transition_id=TRANSITION_ID,
        )
    )
    await threads.entered.wait()

    holder.cancel()
    with pytest.raises(asyncio.CancelledError):
        await holder

    assert source._thread_locks == {}


async def test_plan_edit_fails_closed_for_revision_and_mixed_steps() -> None:
    source, client = _source()

    with pytest.raises(LocalSourceStaleInterruptError, match="revision"):
        await source.update_plan(
            "thread-official-1",
            interrupt_id=OFFICIAL_INTERRUPT_ID,
            expected_revision=2,
            steps=["Inspect exact inputs"],
        )
    with pytest.raises(LocalSourceContractError, match="text"):
        await source.update_plan(
            "thread-official-1",
            interrupt_id=OFFICIAL_INTERRUPT_ID,
            expected_revision=1,
            steps=["Inspect exact inputs", 42],  # type: ignore[list-item]
        )
    with pytest.raises(LocalSourceContractError, match="supported bound"):
        await source.update_plan(
            "thread-official-1",
            interrupt_id=OFFICIAL_INTERRUPT_ID,
            expected_revision=1,
            steps=[" \t "],
        )
    assert client.threads.update_calls == []
    assert client.runs.create_calls == []

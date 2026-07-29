"""Thin, fail-closed mapping to a loopback LangGraph Agent Server."""

from __future__ import annotations

import asyncio
import importlib
import re
from collections.abc import AsyncIterator, Callable, Mapping, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Literal, Protocol, cast
from urllib.parse import urlsplit

from deepwork_api.domain import (
    MAX_AGENT_DESCRIPTION_LENGTH,
    MAX_AGENT_NAME_LENGTH,
    MAX_PLAN_REVISION,
    MAX_PLAN_STEP_LENGTH,
    MAX_PLAN_STEPS,
    MAX_TASK_OBJECTIVE_LENGTH,
    MAX_TASK_RESULT_LENGTH,
    DefaultAgentImmutableError,
    StaleInterruptError,
    TaskSourceContractError,
    TaskSourceUnavailableError,
    normalize_system_prompt,
)

DEFAULT_LOCAL_AGENT_SERVER_URL = "http://127.0.0.1:2024"
DEFAULT_LOCAL_AGENT_SERVER_ASSISTANT = "deep-work-local-agent"
Decision = Literal["approve", "reject", "respond"]
StreamEventKind = Literal["run", "state", "progress", "error"]
_MAX_REVIEW_COMMENT_LENGTH = 1_000
_MAX_IDENTIFIER_LENGTH = 256
_MAX_AGENT_LIST = 100
_MAX_SCHEDULE_LIST = 100
_LOCAL_SDK_TIMEOUT = (5.0, 300.0, 30.0, 5.0)
_PLAN_UPDATE_CONFIRM_TIMEOUT_SECONDS = 30.0
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
_ASSISTANT_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_SAFE_AGENT_STATUSES = frozenset({"planned", "approved", "completed", "rejected"})
_SAFE_DECISIONS: tuple[Decision, ...] = ("approve", "reject", "respond")


class _ThreadsClient(Protocol):
    async def create(
        self,
        *,
        metadata: Mapping[str, object] | None = None,
    ) -> object: ...

    async def get_state(self, thread_id: str) -> object: ...

    async def update_state(
        self,
        thread_id: str,
        values: Mapping[str, object] | None,
        *,
        as_node: str | None = None,
    ) -> object: ...


class _RunsClient(Protocol):
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
    ) -> object: ...

    def join_stream(
        self,
        thread_id: str,
        run_id: str,
        *,
        cancel_on_disconnect: bool = False,
        stream_mode: str | Sequence[str] | None = None,
        last_event_id: str | None = None,
    ) -> AsyncIterator[object]: ...


class _AssistantsClient(Protocol):
    async def get(self, assistant_id: str) -> object: ...

    async def search(
        self,
        *,
        graph_id: str | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> object: ...

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
    ) -> object: ...

    async def update(
        self,
        assistant_id: str,
        *,
        config: Mapping[str, object] | None = None,
        name: str | None = None,
        description: str | None = None,
    ) -> object: ...

    async def delete(self, assistant_id: str) -> None: ...


class _CronsClient(Protocol):
    async def search(
        self,
        *,
        assistant_id: str | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> object: ...


class _AgentServerClient(Protocol):
    @property
    def threads(self) -> _ThreadsClient: ...

    @property
    def runs(self) -> _RunsClient: ...

    @property
    def assistants(self) -> _AssistantsClient: ...

    @property
    def crons(self) -> _CronsClient: ...

    async def aclose(self) -> None: ...


class LocalSourceError(Exception):
    """Safe base error for the loopback source boundary."""


class LocalSourceConfigurationError(LocalSourceError):
    """The source configuration is outside the fixed local boundary."""


class LocalSourceGatedError(LocalSourceError):
    """The local Agent Server capability is gated pending live-contract evidence.

    Wave 1 ``apps/api`` exposes only credential-free fixture behavior and makes
    no provider/service calls by default. Executing tasks through a real
    ``langgraph dev`` Agent Server is a development-only capability that stays
    disabled until its contract gate (``SPIKE-SOURCE-001``) is accepted; it is
    reachable only through a deliberate, documented local-development opt-in.
    """


class LocalSourceUnavailableError(LocalSourceError, TaskSourceUnavailableError):
    """The loopback Agent Server or official SDK is unavailable.

    Also a domain ``TaskSourceUnavailableError`` so the application layer can
    classify it without importing adapter modules.
    """


class LocalSourceContractError(LocalSourceError, TaskSourceContractError):
    """The Agent Server response does not match the supported graph contract.

    Also a domain ``TaskSourceContractError`` so the application layer can
    classify it without importing adapter modules.
    """


class LocalSourceStaleInterruptError(LocalSourceError, StaleInterruptError):
    """The requested interrupt is no longer the source-authoritative interrupt.

    Also a domain ``StaleInterruptError`` so transport maps it to the same
    conflict contract as every other stale interrupt.
    """


class LocalSourceDefaultAgentImmutableError(LocalSourceError, DefaultAgentImmutableError):
    """The default agent bound to the deployed graph cannot be edited or deleted.

    Also a domain ``DefaultAgentImmutableError`` so the application layer can
    classify it without importing adapter modules.
    """


@dataclass(frozen=True, slots=True)
class LocalAgentServerCapabilities:
    """Static capabilities of this source adapter, not model/provider claims."""

    source_kind: Literal["local-agent-server"] = "local-agent-server"
    transport: Literal["langgraph-sdk"] = "langgraph-sdk"
    loopback_only: Literal[True] = True
    creates_thread_runs: Literal[True] = True
    resumable_run_stream: Literal["last-event-id"] = "last-event-id"
    interrupt_resume: tuple[Decision, ...] = _SAFE_DECISIONS
    plan_state_update: Literal["update-state-as-plan"] = "update-state-as-plan"
    accepts_credentials: Literal[False] = False


@dataclass(frozen=True, slots=True)
class LocalAgentServerStatus:
    """Sanitized source reachability without upstream exception content."""

    available: bool
    code: Literal["ready", "unavailable", "contract-mismatch"]


@dataclass(frozen=True, slots=True)
class LocalRunReference:
    """Source-authoritative identifiers for one Agent Server run."""

    thread_id: str
    run_id: str


@dataclass(frozen=True, slots=True)
class LocalInterrupt:
    """Sanitized current Deep Work plan interrupt."""

    interrupt_id: str
    kind: Literal["deepwork-plan-approval"]
    plan: tuple[str, ...]
    plan_revision: int
    allowed_decisions: tuple[Decision, ...]


@dataclass(frozen=True, slots=True)
class LocalStateSnapshot:
    """Bounded state projection safe for the application service."""

    status: Literal["planned", "approved", "completed", "rejected"] | None
    plan: tuple[str, ...]
    plan_revision: int | None
    final_answer: str | None
    interrupt: LocalInterrupt | None
    next_nodes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AgentSummary:
    """Sanitized projection of one Assistant sharing our deployed graph.

    Deep Work owns none of this: it is read from (and written back to) the
    configured task source's official Assistants API, never stored locally.
    """

    agent_id: str
    name: str
    description: str | None
    system_prompt: str | None
    is_default: bool
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class ScheduleSummary:
    """Sanitized projection of one Cron (recurring run) on our deployed graph.

    Deep Work owns none of this: it is read from the configured task
    source's official Crons API, never stored locally. Read-only: a
    schedule-triggered run starts a fresh thread on the source directly, so
    it does not yet appear in this application's task repository or event
    stream. Creating schedules from here is deferred until that
    reconciliation exists, so this type carries no mutation affordance.
    """

    schedule_id: str
    agent_id: str
    cron_expression: str
    timezone: str | None
    end_time: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class LocalPlanUpdate:
    """Official state-edit checkpoint followed by a new approval run."""

    thread_id: str
    run_id: str
    plan_revision: int
    interrupt_id: str


@dataclass(frozen=True, slots=True)
class LocalStreamEvent:
    """Sanitized projection of one official resumable run-stream event."""

    cursor: str | None
    kind: StreamEventKind
    summary: str
    run_id: str | None = None
    state: LocalStateSnapshot | None = None
    updated_nodes: tuple[str, ...] = ()


@dataclass(slots=True)
class _ThreadLockEntry:
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    users: int = 0


def validate_loopback_url(value: str) -> str:
    """Accept only an explicit HTTP IP-literal loopback origin."""

    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        message = "local Agent Server URL must be a valid loopback origin"
        raise LocalSourceConfigurationError(message) from None
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"127.0.0.1", "::1"}
        or port is None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        message = "local Agent Server URL must be an explicit HTTP loopback IP and port"
        raise LocalSourceConfigurationError(message)
    host = f"[{parsed.hostname}]" if parsed.hostname == "::1" else parsed.hostname
    return f"http://{host}:{port}"


def create_official_client(endpoint: str = DEFAULT_LOCAL_AGENT_SERVER_URL) -> _AgentServerClient:
    """Construct the public ``langgraph_sdk`` client after bootstrap installs it."""

    normalized = validate_loopback_url(endpoint)
    try:
        module = importlib.import_module("langgraph_sdk")
        factory_value = getattr(module, "get_client", None)
        if not callable(factory_value):
            raise AttributeError
        factory = cast("Callable[..., object]", factory_value)
        return cast(
            "_AgentServerClient",
            factory(
                url=normalized,
                api_key=None,
                headers={},
                timeout=_LOCAL_SDK_TIMEOUT,
            ),
        )
    except Exception:
        message = "official LangGraph SDK is unavailable"
        raise LocalSourceUnavailableError(message) from None


@dataclass(frozen=True, slots=True)
class LocalAgentServerSource:
    """Invoke one fixed loopback Agent Server through its official SDK client."""

    client: _AgentServerClient
    endpoint: str = DEFAULT_LOCAL_AGENT_SERVER_URL
    assistant_id: str = DEFAULT_LOCAL_AGENT_SERVER_ASSISTANT
    _thread_locks: dict[str, _ThreadLockEntry] = field(
        default_factory=dict,
        init=False,
        repr=False,
        compare=False,
    )
    _thread_locks_guard: asyncio.Lock = field(
        default_factory=asyncio.Lock,
        init=False,
        repr=False,
        compare=False,
    )
    # Threads are bound to whichever assistant started them; resume and plan
    # updates must keep replaying that exact assistant, not silently fall
    # back to the source's configured default.
    _thread_assistants: dict[str, str] = field(
        default_factory=dict,
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "endpoint", validate_loopback_url(self.endpoint))
        if not _ASSISTANT_IDENTIFIER.fullmatch(self.assistant_id):
            message = "local Agent Server assistant identifier is invalid"
            raise LocalSourceConfigurationError(message)

    @classmethod
    def from_official_sdk(
        cls,
        *,
        endpoint: str = DEFAULT_LOCAL_AGENT_SERVER_URL,
        assistant_id: str = DEFAULT_LOCAL_AGENT_SERVER_ASSISTANT,
    ) -> LocalAgentServerSource:
        """Build the adapter with the official client after explicit bootstrap."""

        return cls(
            client=create_official_client(endpoint),
            endpoint=endpoint,
            assistant_id=assistant_id,
        )

    def capabilities(self) -> LocalAgentServerCapabilities:
        """Return adapter mechanics without claiming model/provider availability."""

        return LocalAgentServerCapabilities()

    async def close(self) -> None:
        """Close the official client transport without exposing upstream details."""

        try:
            await self.client.aclose()
        except Exception:
            message = "local Agent Server client close failed"
            raise LocalSourceUnavailableError(message) from None

    async def status(self) -> LocalAgentServerStatus:
        """Probe the configured assistant and suppress all upstream details."""

        try:
            assistant = _as_mapping(await self.client.assistants.get(self.assistant_id))
            _required_identifier(assistant, "assistant_id")
        except LocalSourceContractError:
            return LocalAgentServerStatus(available=False, code="contract-mismatch")
        except Exception:
            return LocalAgentServerStatus(available=False, code="unavailable")
        return LocalAgentServerStatus(available=True, code="ready")

    async def start(
        self,
        objective: str,
        *,
        system_prompt: str | None = None,
        agent_id: str | None = None,
    ) -> LocalRunReference:
        """Create a thread and a resumable run for the integrated agent graph.

        ``agent_id`` selects a specific assistant sharing our deployed graph,
        falling back to the source's configured default assistant when
        omitted. When ``system_prompt`` is supplied (the workspace's editable
        prompt) it flows to the graph as ``configurable.system_prompt``, but
        only applies to the default assistant: a selected named agent's own
        registered config governs its persona instead, so the two overrides
        never fight each other.
        """

        normalized = _bounded_text(
            objective,
            field="task objective",
            maximum=MAX_TASK_OBJECTIVE_LENGTH,
        )
        resolved_assistant = (
            _validate_assistant_identifier(agent_id) if agent_id is not None else self.assistant_id
        )
        effective_prompt = system_prompt if agent_id is None else None
        prompt_override = normalize_system_prompt(effective_prompt)
        run_input: dict[str, object] = {"task": normalized}
        if prompt_override is not None:
            # Deliver the editable prompt in the input (always reaches a hosted
            # graph) and in the config (belt-and-suspenders for local runs).
            run_input["system_prompt"] = prompt_override
        run_config = _run_config(effective_prompt)
        try:
            thread = _as_mapping(
                await self.client.threads.create(
                    metadata={"deepwork_source": "local-agent-server"},
                )
            )
            thread_id = _required_identifier(thread, "thread_id")
            run = await self.client.runs.create(
                thread_id,
                resolved_assistant,
                input=run_input,
                config=run_config,
                stream_mode=("values", "updates"),
                stream_resumable=True,
                multitask_strategy="reject",
                durability="sync",
            )
            run_id = _required_identifier(_as_mapping(run), "run_id")
        except LocalSourceContractError:
            raise
        except Exception:
            message = "local Agent Server start failed"
            raise LocalSourceUnavailableError(message) from None
        self._thread_assistants[thread_id] = resolved_assistant
        return LocalRunReference(thread_id=thread_id, run_id=run_id)

    async def get_state(self, thread_id: str) -> LocalStateSnapshot:
        """Read and sanitize source-authoritative thread state."""

        safe_thread_id = _validate_identifier(thread_id, field="thread identifier")
        try:
            raw = await self.client.threads.get_state(safe_thread_id)
        except Exception:
            message = "local Agent Server state read failed"
            raise LocalSourceUnavailableError(message) from None
        return _state_snapshot(raw)

    async def stream(
        self,
        run: LocalRunReference,
        *,
        after_cursor: str | None = None,
    ) -> AsyncIterator[LocalStreamEvent]:
        """Join or reconnect to the official resumable stream with Last-Event-ID."""

        thread_id = _validate_identifier(run.thread_id, field="thread identifier")
        run_id = _validate_identifier(run.run_id, field="run identifier")
        cursor = _validate_cursor(after_cursor) if after_cursor is not None else None
        try:
            source_stream = self.client.runs.join_stream(
                thread_id,
                run_id,
                cancel_on_disconnect=False,
                stream_mode=("values", "updates"),
                last_event_id=cursor,
            )
            async for raw_event in source_stream:
                yield _stream_event(raw_event)
        except LocalSourceContractError:
            raise
        except Exception:
            message = "local Agent Server stream failed"
            raise LocalSourceUnavailableError(message) from None

    async def resume(
        self,
        thread_id: str,
        *,
        interrupt_id: str,
        decision: Decision,
        comment: str | None = None,
    ) -> LocalRunReference:
        """Resume the exact current official interrupt with a public Command payload."""

        safe_thread_id = _validate_identifier(thread_id, field="thread identifier")
        safe_interrupt_id = _validate_identifier(interrupt_id, field="interrupt identifier")
        if decision not in _SAFE_DECISIONS:
            message = "decision must be approve, reject, or respond"
            raise LocalSourceContractError(message)
        normalized_comment = _review_comment(decision, comment)
        async with self._thread_guard(safe_thread_id):
            current = await self.get_state(safe_thread_id)
            if current.interrupt is None or current.interrupt.interrupt_id != safe_interrupt_id:
                message = "interrupt is no longer current"
                raise LocalSourceStaleInterruptError(message)
            if decision not in current.interrupt.allowed_decisions:
                message = "decision is not allowed by the current interrupt"
                raise LocalSourceContractError(message)
            response: dict[str, object] = {"decision": decision}
            if normalized_comment is not None:
                response["comment"] = normalized_comment
            try:
                run = await self.client.runs.create(
                    safe_thread_id,
                    self._thread_assistants.get(safe_thread_id, self.assistant_id),
                    command={"resume": {safe_interrupt_id: response}},
                    stream_mode=("values", "updates"),
                    stream_resumable=True,
                    multitask_strategy="reject",
                    durability="sync",
                )
                run_id = _required_identifier(_as_mapping(run), "run_id")
            except LocalSourceContractError:
                raise
            except Exception:
                message = "local Agent Server resume failed"
                raise LocalSourceUnavailableError(message) from None
        return LocalRunReference(thread_id=safe_thread_id, run_id=run_id)

    async def update_plan(
        self,
        thread_id: str,
        *,
        interrupt_id: str,
        expected_revision: int,
        steps: Sequence[str],
    ) -> LocalPlanUpdate:
        """Edit state as the plan node, then run forward to a fresh official interrupt."""

        safe_thread_id = _validate_identifier(thread_id, field="thread identifier")
        safe_interrupt_id = _validate_identifier(interrupt_id, field="interrupt identifier")
        validated_steps = _plan_steps(steps)
        expected = _plan_revision(expected_revision, field="expected plan revision")
        if expected == MAX_PLAN_REVISION:
            message = "plan revision cannot be advanced beyond the shared bound"
            raise LocalSourceContractError(message)
        async with self._thread_guard(safe_thread_id):
            current = await self.get_state(safe_thread_id)
            if current.interrupt is None or current.interrupt.interrupt_id != safe_interrupt_id:
                message = "interrupt is no longer current"
                raise LocalSourceStaleInterruptError(message)
            if current.plan_revision != expected:
                message = "plan revision is no longer current"
                raise LocalSourceStaleInterruptError(message)
            next_revision = expected + 1
            try:
                _as_mapping(
                    await self.client.threads.update_state(
                        safe_thread_id,
                        {
                            "plan": list(validated_steps),
                            "plan_revision": next_revision,
                            "plan_trust": "untrusted",
                            "approval": "pending",
                            "status": "planned",
                        },
                        as_node="plan",
                    )
                )
                run = await self.client.runs.create(
                    safe_thread_id,
                    self._thread_assistants.get(safe_thread_id, self.assistant_id),
                    stream_mode=("values", "updates"),
                    stream_resumable=True,
                    multitask_strategy="reject",
                    durability="sync",
                )
                run_id = _required_identifier(_as_mapping(run), "run_id")
                run_reference = LocalRunReference(
                    thread_id=safe_thread_id,
                    run_id=run_id,
                )
                async with asyncio.timeout(_PLAN_UPDATE_CONFIRM_TIMEOUT_SECONDS):
                    async for _ in self.stream(run_reference):
                        pass
                confirmed = await self.get_state(safe_thread_id)
            except LocalSourceContractError:
                raise
            except Exception:
                message = "local Agent Server plan update failed"
                raise LocalSourceUnavailableError(message) from None
            new_interrupt = _confirmed_plan_interrupt(
                confirmed,
                previous_interrupt_id=safe_interrupt_id,
                expected_plan=validated_steps,
                expected_revision=next_revision,
            )
        return LocalPlanUpdate(
            thread_id=safe_thread_id,
            run_id=run_id,
            plan_revision=next_revision,
            interrupt_id=new_interrupt.interrupt_id,
        )

    async def _resolve_graph_id(self) -> str:
        """Read the graph identifier of the configured default assistant.

        Every agent this source lists, creates, updates, or deletes is scoped
        to this graph_id: it is the only compiled graph contract this
        adapter's state and stream parsing supports.
        """

        try:
            default = _as_mapping(await self.client.assistants.get(self.assistant_id))
        except LocalSourceContractError:
            raise
        except Exception:
            message = "local Agent Server default assistant lookup failed"
            raise LocalSourceUnavailableError(message) from None
        return _required_identifier(default, "graph_id")

    async def list_agents(self) -> tuple[AgentSummary, ...]:
        """List assistants sharing our deployed graph, sanitized for the app boundary."""

        graph_id = await self._resolve_graph_id()
        try:
            raw = await self.client.assistants.search(graph_id=graph_id, limit=_MAX_AGENT_LIST)
        except LocalSourceContractError:
            raise
        except Exception:
            message = "local Agent Server agent list failed"
            raise LocalSourceUnavailableError(message) from None
        if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
            message = "local Agent Server agent list shape is unsupported"
            raise LocalSourceContractError(message)
        return tuple(self._agent_summary(_as_mapping(item)) for item in raw)

    async def create_agent(
        self,
        *,
        name: str,
        description: str | None,
        system_prompt: str | None,
    ) -> AgentSummary:
        """Create a new assistant on our deployed graph with its own config."""

        graph_id = await self._resolve_graph_id()
        safe_name = _bounded_text(name, field="agent name", maximum=MAX_AGENT_NAME_LENGTH)
        safe_description = _optional_bounded_text(
            description, field="agent description", maximum=MAX_AGENT_DESCRIPTION_LENGTH
        )
        try:
            created = await self.client.assistants.create(
                graph_id,
                _agent_config(system_prompt),
                name=safe_name,
                description=safe_description,
                if_exists="raise",
            )
        except LocalSourceContractError:
            raise
        except Exception:
            message = "local Agent Server agent create failed"
            raise LocalSourceUnavailableError(message) from None
        return self._agent_summary(_as_mapping(created))

    async def update_agent(
        self,
        agent_id: str,
        *,
        name: str,
        description: str | None,
        system_prompt: str | None,
    ) -> AgentSummary:
        """Replace the editable fields of one non-default assistant.

        This always sends a full ``config`` (an explicit ``{}`` when
        ``system_prompt`` is unset) so a cleared prompt genuinely clears the
        stored override rather than leaving the prior value untouched.
        """

        safe_id = _validate_assistant_identifier(agent_id)
        if safe_id == self.assistant_id:
            raise LocalSourceDefaultAgentImmutableError
        safe_name = _bounded_text(name, field="agent name", maximum=MAX_AGENT_NAME_LENGTH)
        safe_description = _optional_bounded_text(
            description, field="agent description", maximum=MAX_AGENT_DESCRIPTION_LENGTH
        )
        config = _agent_config(system_prompt)
        try:
            updated = await self.client.assistants.update(
                safe_id,
                config=config if config is not None else {},
                name=safe_name,
                description=safe_description,
            )
        except LocalSourceContractError:
            raise
        except Exception:
            message = "local Agent Server agent update failed"
            raise LocalSourceUnavailableError(message) from None
        return self._agent_summary(_as_mapping(updated))

    async def delete_agent(self, agent_id: str) -> None:
        """Delete one non-default assistant."""

        safe_id = _validate_assistant_identifier(agent_id)
        if safe_id == self.assistant_id:
            raise LocalSourceDefaultAgentImmutableError
        try:
            await self.client.assistants.delete(safe_id)
        except LocalSourceContractError:
            raise
        except Exception:
            message = "local Agent Server agent delete failed"
            raise LocalSourceUnavailableError(message) from None

    def _agent_summary(self, mapping: Mapping[str, object]) -> AgentSummary:
        agent_id = _required_identifier(mapping, "assistant_id")
        raw_name = mapping.get("name")
        name = _bounded_text(
            raw_name if isinstance(raw_name, str) and raw_name.strip() else "Untitled",
            field="agent name",
            maximum=MAX_AGENT_NAME_LENGTH,
        )
        description = _optional_bounded_text(
            mapping.get("description"),
            field="agent description",
            maximum=MAX_AGENT_DESCRIPTION_LENGTH,
        )
        return AgentSummary(
            agent_id=agent_id,
            name=name,
            description=description,
            system_prompt=_config_system_prompt(mapping.get("config")),
            is_default=agent_id == self.assistant_id,
            created_at=_agent_timestamp(mapping.get("created_at")),
            updated_at=_agent_timestamp(mapping.get("updated_at")),
        )

    async def list_schedules(self) -> tuple[ScheduleSummary, ...]:
        """List recurring runs (crons) scoped to our deployed graph's assistants.

        Crons are a licensed LangGraph Platform capability: an unsupported
        deployment answers with an error here, which callers map to an
        honest unavailable state rather than a fabricated empty list.
        """

        # Crons search has no graph_id filter, only assistant_id/thread_id, so
        # one unfiltered call is cross-referenced against our graph's own
        # assistants (already graph-scoped by list_agents) rather than trusting
        # every cron the deployment returns — a cron pointed at an unrelated
        # graph on a multi-graph deployment must never be surfaced as ours.
        agents = await self.list_agents()
        known_agents = {agent.agent_id for agent in agents}
        try:
            raw = await self.client.crons.search(limit=_MAX_SCHEDULE_LIST)
        except LocalSourceContractError:
            raise
        except Exception:
            message = "local Agent Server schedule list failed"
            raise LocalSourceUnavailableError(message) from None
        if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
            message = "local Agent Server schedule list shape is unsupported"
            raise LocalSourceContractError(message)
        schedules = tuple(self._schedule_summary(_as_mapping(item)) for item in raw)
        return tuple(schedule for schedule in schedules if schedule.agent_id in known_agents)

    def _schedule_summary(self, mapping: Mapping[str, object]) -> ScheduleSummary:
        schedule_id = _required_identifier(mapping, "cron_id")
        agent_id = _required_identifier(mapping, "assistant_id")
        raw_schedule = mapping.get("schedule")
        if not isinstance(raw_schedule, str) or not raw_schedule.strip():
            message = "local Agent Server schedule cron expression is missing"
            raise LocalSourceContractError(message)
        return ScheduleSummary(
            schedule_id=schedule_id,
            agent_id=agent_id,
            cron_expression=raw_schedule,
            timezone=_optional_bounded_text(
                mapping.get("timezone"), field="schedule timezone", maximum=64
            ),
            end_time=_agent_timestamp(mapping.get("end_time")) or None,
            created_at=_agent_timestamp(mapping.get("created_at")),
            updated_at=_agent_timestamp(mapping.get("updated_at")),
        )

    @asynccontextmanager
    async def _thread_guard(self, thread_id: str) -> AsyncIterator[None]:
        """Serialize one thread and evict its lock after the final user exits."""

        async with self._thread_locks_guard:
            entry = self._thread_locks.get(thread_id)
            if entry is None:
                entry = _ThreadLockEntry()
                self._thread_locks[thread_id] = entry
            entry.users += 1
        acquired = False
        try:
            await entry.lock.acquire()
            acquired = True
            yield
        finally:
            if acquired:
                entry.lock.release()
            async with self._thread_locks_guard:
                entry.users -= 1
                if entry.users == 0:
                    current = self._thread_locks.get(thread_id)
                    if current is entry:
                        del self._thread_locks[thread_id]


def _as_mapping(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        message = "local Agent Server response shape is unsupported"
        raise LocalSourceContractError(message)
    return cast("Mapping[str, object]", value)


def _validate_identifier(value: str, *, field: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) > _MAX_IDENTIFIER_LENGTH
        or not _IDENTIFIER.fullmatch(value)
    ):
        message = f"{field} is invalid"
        raise LocalSourceContractError(message)
    return value


def _required_identifier(value: Mapping[str, object], key: str) -> str:
    raw = value.get(key)
    if not isinstance(raw, str):
        message = "local Agent Server response identifier is missing"
        raise LocalSourceContractError(message)
    return _validate_identifier(raw, field="source identifier")


def _validate_assistant_identifier(value: str) -> str:
    if not isinstance(value, str) or not _ASSISTANT_IDENTIFIER.fullmatch(value):
        message = "agent identifier is invalid"
        raise LocalSourceContractError(message)
    return value


def _optional_bounded_text(value: object, *, field: str, maximum: int) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        message = f"{field} must be text"
        raise LocalSourceContractError(message)
    normalized = value.strip()
    if not normalized:
        return None
    if len(normalized) > maximum:
        message = f"{field} is outside its supported bound"
        raise LocalSourceContractError(message)
    return normalized


def _agent_config(system_prompt: str | None) -> dict[str, object] | None:
    """Build the assistant config carrying an optional bound system prompt."""
    normalized = normalize_system_prompt(system_prompt)
    if normalized is None:
        return None
    return {"configurable": {"system_prompt": normalized}}


def _config_system_prompt(value: object) -> str | None:
    if not isinstance(value, Mapping):
        return None
    configurable = value.get("configurable")
    if not isinstance(configurable, Mapping):
        return None
    prompt = configurable.get("system_prompt")
    if not isinstance(prompt, str):
        return None
    return normalize_system_prompt(prompt)


def _agent_timestamp(value: object) -> str:
    return value if isinstance(value, str) and value else ""


def _validate_cursor(value: object) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > _MAX_IDENTIFIER_LENGTH
        or any(character in value for character in ("\0", "\r", "\n"))
    ):
        message = "event cursor is invalid"
        raise LocalSourceContractError(message)
    return value


def _bounded_text(value: object, *, field: str, maximum: int) -> str:
    if not isinstance(value, str):
        message = f"{field} must be text"
        raise LocalSourceContractError(message)
    normalized = value.strip()
    if not normalized or len(normalized) > maximum:
        message = f"{field} is outside its supported bound"
        raise LocalSourceContractError(message)
    return normalized


def _run_config(system_prompt: str | None) -> dict[str, object] | None:
    """Build the run config carrying an optional per-run system prompt.

    Returns ``None`` when there is no override so the run uses the graph's
    default persona and the request stays byte-for-byte the prior shape.
    """
    normalized = normalize_system_prompt(system_prompt)
    if normalized is None:
        return None
    return {"configurable": {"system_prompt": normalized}}


def _plan_revision(value: object, *, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= MAX_PLAN_REVISION:
        message = f"{field} is outside its supported bound"
        raise LocalSourceContractError(message)
    return value


def _plan_step(value: object) -> str:
    if not isinstance(value, str):
        message = "plan step must be text"
        raise LocalSourceContractError(message)
    if not value.strip() or len(value) > MAX_PLAN_STEP_LENGTH:
        message = "plan step is outside its supported bound"
        raise LocalSourceContractError(message)
    return value


def _plan_steps(value: object) -> tuple[str, ...]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or not 1 <= len(value) <= MAX_PLAN_STEPS
    ):
        message = "plan must contain a supported number of steps"
        raise LocalSourceContractError(message)
    result: list[str] = []
    for item in value:
        result.append(_plan_step(item))
    return tuple(result)


def _review_comment(decision: Decision, comment: str | None) -> str | None:
    if comment is None:
        if decision == "respond":
            message = "respond requires a review comment"
            raise LocalSourceContractError(message)
        return None
    normalized = _bounded_text(
        comment,
        field="review comment",
        maximum=_MAX_REVIEW_COMMENT_LENGTH,
    )
    return normalized


def _interrupt(value: object) -> LocalInterrupt:
    mapping = _as_mapping(value)
    interrupt_id = _required_identifier(mapping, "id")
    payload = _as_mapping(mapping.get("value"))
    if payload.get("kind") != "deepwork-plan-approval":
        message = "local Agent Server interrupt kind is unsupported"
        raise LocalSourceContractError(message)
    if payload.get("action") != "execute_plan":
        message = "local Agent Server interrupt action is unsupported"
        raise LocalSourceContractError(message)
    if payload.get("plan_trust") != "untrusted":
        message = "local Agent Server interrupt trust marker is unsupported"
        raise LocalSourceContractError(message)
    revision = _plan_revision(
        payload.get("plan_revision"),
        field="local Agent Server plan revision",
    )
    allowed = payload.get("allowed_decisions")
    if not isinstance(allowed, list) or tuple(allowed) != _SAFE_DECISIONS:
        message = "local Agent Server interrupt decisions are invalid"
        raise LocalSourceContractError(message)
    return LocalInterrupt(
        interrupt_id=interrupt_id,
        kind="deepwork-plan-approval",
        plan=_plan_steps(payload.get("plan")),
        plan_revision=revision,
        allowed_decisions=_SAFE_DECISIONS,
    )


def _state_snapshot(value: object) -> LocalStateSnapshot:
    mapping = _as_mapping(value)
    values = _as_mapping(mapping.get("values"))
    status_value = values.get("status")
    status = (
        cast("Literal['planned', 'approved', 'completed', 'rejected']", status_value)
        if status_value in _SAFE_AGENT_STATUSES
        else None
    )
    raw_plan = values.get("plan")
    plan = _plan_steps(raw_plan) if raw_plan is not None else ()
    raw_revision = values.get("plan_revision")
    revision = (
        _plan_revision(
            raw_revision,
            field="local Agent Server state plan revision",
        )
        if raw_revision is not None
        else None
    )
    raw_answer = values.get("final_answer")
    final_answer = (
        _bounded_output_text(
            raw_answer,
            field="final answer",
            maximum=MAX_TASK_RESULT_LENGTH,
        )
        if raw_answer is not None
        else None
    )
    raw_next = mapping.get("next", ())
    if not isinstance(raw_next, Sequence) or isinstance(raw_next, (str, bytes)):
        message = "local Agent Server next-node state is invalid"
        raise LocalSourceContractError(message)
    next_nodes = tuple(
        _validate_identifier(node, field="next node") for node in raw_next if isinstance(node, str)
    )
    if len(next_nodes) != len(raw_next):
        message = "local Agent Server next-node state is invalid"
        raise LocalSourceContractError(message)
    raw_interrupts = mapping.get("interrupts", ())
    if not isinstance(raw_interrupts, Sequence) or isinstance(raw_interrupts, (str, bytes)):
        message = "local Agent Server interrupts are invalid"
        raise LocalSourceContractError(message)
    interrupts = tuple(_interrupt(item) for item in raw_interrupts)
    if len(interrupts) > 1:
        message = "multiple local Agent Server interrupts are unsupported"
        raise LocalSourceContractError(message)
    interrupt = interrupts[0] if interrupts else None
    if (plan or interrupt is not None) and revision is None:
        message = "local Agent Server state plan revision is missing"
        raise LocalSourceContractError(message)
    if interrupt is not None:
        if plan and interrupt.plan != plan:
            message = "local Agent Server interrupt plan does not match state"
            raise LocalSourceContractError(message)
        if revision is not None and interrupt.plan_revision != revision:
            message = "local Agent Server interrupt revision does not match state"
            raise LocalSourceContractError(message)
    return LocalStateSnapshot(
        status=status,
        plan=plan,
        plan_revision=revision,
        final_answer=final_answer,
        interrupt=interrupt,
        next_nodes=next_nodes,
    )


def _confirmed_plan_interrupt(
    state: LocalStateSnapshot,
    *,
    previous_interrupt_id: str,
    expected_plan: tuple[str, ...],
    expected_revision: int,
) -> LocalInterrupt:
    interrupt = state.interrupt
    if (
        state.status != "planned"
        or state.plan != expected_plan
        or state.plan_revision != expected_revision
        or interrupt is None
        or interrupt.interrupt_id == previous_interrupt_id
        or interrupt.plan != expected_plan
        or interrupt.plan_revision != expected_revision
    ):
        message = "edited plan did not reach a fresh authoritative interrupt"
        raise LocalSourceContractError(message)
    return interrupt


def _bounded_output_text(value: object, *, field: str, maximum: int) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        message = f"{field} is outside its supported bound"
        raise LocalSourceContractError(message)
    return value


def _stream_event(value: object) -> LocalStreamEvent:
    if isinstance(value, tuple) and hasattr(value, "event") and hasattr(value, "data"):
        event_name = getattr(value, "event", None)
        data = getattr(value, "data", None)
        event_id = getattr(value, "id", None)
    elif isinstance(value, Mapping):
        mapping = cast("Mapping[str, object]", value)
        event_name = mapping.get("event")
        data = mapping.get("data")
        event_id = mapping.get("id")
    else:
        message = "local Agent Server stream event shape is unsupported"
        raise LocalSourceContractError(message)
    cursor = _validate_cursor(event_id) if isinstance(event_id, str) else None
    if event_id is not None and cursor is None:
        message = "local Agent Server stream cursor is invalid"
        raise LocalSourceContractError(message)
    if event_name == "values":
        state = _state_snapshot(
            {
                "values": data,
                "next": (),
                "interrupts": (data.get("__interrupt__", ()) if isinstance(data, Mapping) else ()),
            }
        )
        return LocalStreamEvent(
            cursor=cursor,
            kind="state",
            summary="Agent state updated.",
            state=state,
        )
    if event_name == "updates":
        update = _as_mapping(data)
        # Real LangGraph servers include framework keys in update events (for
        # example "__interrupt__" when a node interrupts). Keep the recognizable
        # node names and ignore the rest, rather than failing the whole stream on
        # what is only an informational progress event.
        nodes = tuple(
            sorted(key for key in update if isinstance(key, str) and _IDENTIFIER.fullmatch(key))
        )
        return LocalStreamEvent(
            cursor=cursor,
            kind="progress",
            summary="Agent progress updated.",
            updated_nodes=nodes,
        )
    if event_name == "metadata":
        metadata = _as_mapping(data)
        return LocalStreamEvent(
            cursor=cursor,
            kind="run",
            summary="Agent run connected.",
            run_id=_required_identifier(metadata, "run_id"),
        )
    if event_name == "error":
        return LocalStreamEvent(
            cursor=cursor,
            kind="error",
            summary="The local Agent Server reported a run error.",
        )
    return LocalStreamEvent(
        cursor=cursor,
        kind="progress",
        summary="The local Agent Server emitted a progress event.",
    )

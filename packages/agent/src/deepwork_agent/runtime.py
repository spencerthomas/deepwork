"""Serving composition root for the local Deep Work agent graph.

This is the deliberate wiring seam that turns the injected-model graph in
:mod:`deepwork_agent.graph` into a graph a LangGraph Agent Server can serve.
``packages/agent`` core stays provider-agnostic; provider selection and the
keyless development stand-in live here, exactly as ``apps/api`` bootstrap is the
only zone allowed to construct concrete adapters.

Model resolution, in order:

1. ``DEEPWORK_AGENT_FAKE=1`` -> a deterministic, network-free stand-in so the
   full pipeline (plan, interrupt, approve/reject/revise, execute) runs with no
   provider credential. Honest for local development and smoke tests; it is not a
   real model and never claims to be.
2. ``DEEPWORK_AGENT_MODEL`` set (for example ``anthropic:claude-sonnet-5``) ->
   the real provider model via ``langchain.chat_models.init_chat_model``. The
   provider credential is read from the server environment and never leaves it.

``langgraph.json`` points at :data:`graph` in this module.
"""

from __future__ import annotations

from contextlib import contextmanager, suppress
from typing import TYPE_CHECKING, Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from deepwork_agent.config import AgentConfig, ServingConfig
from deepwork_agent.graph import LocalAgentGraph, create_graph
from deepwork_agent.memory import InMemoryWorkspaceMemory, SupabaseWorkspaceMemory, WorkspaceMemory
from deepwork_agent.verification import RubricCriterion, RubricSpec

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence

__all__ = ["DeterministicLocalModel", "build_model", "make_graph"]

_OPENROUTER_PREFIX = "openrouter:"
_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class DeterministicLocalModel(BaseChatModel):
    """A keyless, network-free stand-in satisfying the plan/execute contract.

    It returns a short newline plan for planning prompts and a single concise
    answer otherwise, and never requests tools. It exists so the real graph,
    interrupt, and resume machinery can run without a provider credential.
    """

    @property
    def _llm_type(self) -> str:
        return "deepwork-deterministic-local"

    def bind_tools(self, tools: Any, **kwargs: Any) -> DeterministicLocalModel:  # noqa: ANN401, ARG002
        """Accept tool binding while deliberately never requesting a tool."""
        # The stand-in never requests tools; expose the interface so tool-using
        # executors (deepagents) accept it as their model.
        return self

    def _generate(
        self,
        messages: Sequence[BaseMessage],
        stop: list[str] | None = None,  # noqa: ARG002
        run_manager: Any = None,  # noqa: ANN401, ARG002
        **kwargs: Any,  # noqa: ANN401, ARG002
    ) -> ChatResult:
        joined = "\n".join(message.text for message in messages).lower()
        if "execution plan" in joined or "revise the plan" in joined:
            content = "Inspect only the supplied inputs\nProduce a concise, evidence-based result"
        else:
            content = (
                "Completed the approved plan using only the supplied inputs and "
                "returned a concise result."
            )
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))])


def build_model(settings: ServingConfig | None = None) -> BaseChatModel:
    """Resolve the chat model from typed server-side serving settings."""
    serving = settings or ServingConfig.from_environment()
    if serving.use_fake_model:
        return DeterministicLocalModel()
    identifier = serving.model_identifier
    if not identifier:
        msg = (
            "no model configured: set DEEPWORK_AGENT_MODEL (for example "
            "'anthropic:claude-sonnet-5' or 'openrouter:openai/gpt-4o-mini') with the "
            "provider credential in the server environment, or set "
            "DEEPWORK_AGENT_FAKE=1 for the keyless deterministic development stand-in"
        )
        raise RuntimeError(msg)
    if identifier.startswith(_OPENROUTER_PREFIX):
        return _openrouter_model(
            identifier[len(_OPENROUTER_PREFIX) :],
            api_key=serving.openrouter_api_key,
        )
    try:
        from langchain.chat_models import init_chat_model  # noqa: PLC0415
    except ImportError as error:  # pragma: no cover - depends on optional provider extra
        msg = (
            "DEEPWORK_AGENT_MODEL is set but 'langchain' with a provider integration "
            "is not installed; install the provider package (for example "
            "'langchain-anthropic') or set DEEPWORK_AGENT_FAKE=1"
        )
        raise RuntimeError(msg) from error
    return init_chat_model(identifier)


def _openrouter_model(model_name: str, *, api_key: str | None) -> BaseChatModel:
    """Build a chat model backed by OpenRouter's OpenAI-compatible gateway.

    OpenRouter serves leading provider models (``anthropic/...``, ``openai/...``,
    ``google/...``) behind one account and one ``OPENROUTER_API_KEY``.
    """
    if not api_key or not api_key.strip():
        msg = "OPENROUTER_API_KEY is required for an 'openrouter:' model"
        raise RuntimeError(msg)
    if not model_name.strip():
        msg = "openrouter model id is empty (use for example 'openrouter:openai/gpt-4o-mini')"
        raise RuntimeError(msg)
    try:
        from langchain_openai import ChatOpenAI  # ty: ignore[unresolved-import]  # noqa: PLC0415
    except ImportError as error:  # pragma: no cover - optional provider extra
        msg = "install 'langchain-openai' to use OpenRouter models"
        raise RuntimeError(msg) from error
    return ChatOpenAI(model=model_name, base_url=_OPENROUTER_BASE_URL, api_key=api_key)


def make_graph() -> LocalAgentGraph:
    """Build the servable compiled graph around the resolved model.

    This is the entry point referenced by ``langgraph.json``. It is a factory so
    the model (and its credential) is resolved when the server builds the graph,
    not at module import — a deployment can import this module without the model
    environment being present yet.

    The system prompt comes from ``DEEPWORK_AGENT_SYSTEM_PROMPT`` when set (the
    deployment-level edit point), otherwise the bundled default in
    ``system_prompt.txt``. When ``DEEPWORK_SANDBOX=langsmith`` is set (with
    ``LANGSMITH_API_KEY``), each task executes with a real LangSmith sandbox
    backend — full filesystem plus shell/code execution — instead of the
    in-memory virtual filesystem.
    """
    settings = ServingConfig.from_environment()
    sandbox_factory = None
    if settings.sandbox_backend == "langsmith":
        sandbox_factory = _langsmith_sandbox_factory(settings.langsmith_api_key)
    rubric = (
        _default_rubric(settings.verification_iterations) if settings.verification_enabled else None
    )
    memory_backend = _memory_backend(settings)
    return create_graph(
        model=build_model(settings),
        config=AgentConfig(),
        system_prompt=settings.system_prompt,
        sandbox_factory=sandbox_factory,
        rubric=rubric,
        memory_backend=memory_backend,
    )


def _memory_backend(settings: ServingConfig) -> WorkspaceMemory | None:
    """Resolve the durable workspace-memory backend from serving settings.

    ``DEEPWORK_SUPABASE_URL`` + ``DEEPWORK_SUPABASE_SERVICE_KEY`` -> Supabase
    Postgres over PostgREST (durable across redeploys). Otherwise, when
    ``DEEPWORK_MEMORY=1`` is set without Supabase, a process-local stand-in that
    remembers within the running deployment. Memory is off by default.
    """
    url = settings.supabase_url
    key = settings.supabase_service_key
    if url and key:
        return SupabaseWorkspaceMemory(url, key, table=settings.memory_table)
    if settings.memory_enabled:
        return InMemoryWorkspaceMemory()
    return None


def _default_rubric(iterations: int) -> RubricSpec:
    """Build the general-purpose result rubric used when verification is on.

    Enabled with ``DEEPWORK_VERIFY=1``. The public ``RubricMiddleware`` grades the
    result against these criteria and repairs within a bounded iteration cap; a
    passed verdict is rubric coverage, never ground truth. ``DEEPWORK_VERIFY_ITERS``
    caps the grader loop (default 1: a single verify pass, no repair).
    """
    return RubricSpec(
        rubric_id="deepwork-general-default",
        version=1,
        criteria=(
            RubricCriterion(
                criterion_id="addresses-task",
                text="The result directly and completely addresses what the task asked for.",
            ),
            RubricCriterion(
                criterion_id="evidence-grounded",
                text=(
                    "Claims are grounded in the supplied inputs or the work actually "
                    "performed, with inference distinguished from evidence."
                ),
            ),
            RubricCriterion(
                criterion_id="no-unsupported-claims",
                text="The result makes no fabricated or unverifiable factual claims.",
            ),
            RubricCriterion(
                criterion_id="clear-and-actionable",
                text="The result is concise, clear, and actionable for the reader.",
                required=False,
            ),
        ),
        max_iterations=iterations,
    )


def _langsmith_sandbox_factory(api_key: str | None) -> Callable[[], object] | None:
    """Build a context-manager factory for a fresh per-task LangSmith sandbox.

    Returns ``None`` when no LangSmith credential is configured, so the graph
    falls back to the in-memory virtual filesystem. The credential is read only
    here, in the composition seam — never in the graph. Private GitHub operations
    remain unavailable until the reviewed sandbox auth-proxy contract exists. No
    GitHub token is minted, injected, written, or passed to sandbox commands.
    """
    if not api_key:
        return None

    @contextmanager
    def factory() -> Iterator[object]:
        from deepagents.backends import LangSmithSandbox  # noqa: PLC0415
        from langsmith.sandbox import SandboxClient  # noqa: PLC0415

        client = SandboxClient(api_key=api_key, timeout=30.0)
        sandbox = client.create_sandbox(name="deepwork-task", timeout=120)
        try:
            yield LangSmithSandbox(sandbox)
        finally:
            if sandbox.id is not None:
                with suppress(Exception):
                    client.delete_sandbox(sandbox.id)
            with suppress(Exception):
                client.close()

    return factory

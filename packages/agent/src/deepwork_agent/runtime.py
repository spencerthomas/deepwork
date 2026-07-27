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

import os
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from deepwork_agent.config import AgentConfig
from deepwork_agent.graph import LocalAgentGraph, create_graph

__all__ = ["DeterministicLocalModel", "build_model", "make_graph"]

_MODEL_ENV = "DEEPWORK_AGENT_MODEL"
_FAKE_ENV = "DEEPWORK_AGENT_FAKE"
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


def build_model() -> BaseChatModel:
    """Resolve the chat model for serving from the server environment."""
    if os.environ.get(_FAKE_ENV) == "1":
        return DeterministicLocalModel()
    identifier = os.environ.get(_MODEL_ENV)
    if not identifier:
        msg = (
            "no model configured: set DEEPWORK_AGENT_MODEL (for example "
            "'anthropic:claude-sonnet-5' or 'openrouter:openai/gpt-4o-mini') with the "
            "provider credential in the server environment, or set "
            "DEEPWORK_AGENT_FAKE=1 for the keyless deterministic development stand-in"
        )
        raise RuntimeError(msg)
    if identifier.startswith(_OPENROUTER_PREFIX):
        return _openrouter_model(identifier[len(_OPENROUTER_PREFIX) :])
    try:
        from langchain.chat_models import init_chat_model
    except ImportError as error:  # pragma: no cover - depends on optional provider extra
        msg = (
            "DEEPWORK_AGENT_MODEL is set but 'langchain' with a provider integration "
            "is not installed; install the provider package (for example "
            "'langchain-anthropic') or set DEEPWORK_AGENT_FAKE=1"
        )
        raise RuntimeError(msg) from error
    return init_chat_model(identifier)


def _openrouter_model(model_name: str) -> BaseChatModel:
    """Build a chat model backed by OpenRouter's OpenAI-compatible gateway.

    OpenRouter serves leading provider models (``anthropic/...``, ``openai/...``,
    ``google/...``) behind one account and one ``OPENROUTER_API_KEY``.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key or not api_key.strip():
        msg = "OPENROUTER_API_KEY is required for an 'openrouter:' model"
        raise RuntimeError(msg)
    if not model_name.strip():
        msg = "openrouter model id is empty (use for example 'openrouter:openai/gpt-4o-mini')"
        raise RuntimeError(msg)
    try:
        from langchain_openai import ChatOpenAI
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
    system_prompt = os.environ.get("DEEPWORK_AGENT_SYSTEM_PROMPT") or None
    sandbox_factory = None
    if os.environ.get("DEEPWORK_SANDBOX") == "langsmith":
        sandbox_factory = _langsmith_sandbox_factory()
    rubric = _default_rubric() if os.environ.get("DEEPWORK_VERIFY") == "1" else None
    memory_backend = _memory_backend()
    return create_graph(
        model=build_model(),
        config=AgentConfig(),
        system_prompt=system_prompt,
        sandbox_factory=sandbox_factory,
        rubric=rubric,
        memory_backend=memory_backend,
    )


def _memory_backend() -> object | None:
    """Resolve the durable workspace-memory backend from the server environment.

    ``DEEPWORK_SUPABASE_URL`` + ``DEEPWORK_SUPABASE_SERVICE_KEY`` -> Supabase
    Postgres over PostgREST (durable across redeploys). Otherwise, when
    ``DEEPWORK_MEMORY=1`` is set without Supabase, a process-local stand-in that
    remembers within the running deployment. Memory is off by default.
    """
    url = os.environ.get("DEEPWORK_SUPABASE_URL")
    key = os.environ.get("DEEPWORK_SUPABASE_SERVICE_KEY")
    if url and key:
        from deepwork_agent.memory import SupabaseWorkspaceMemory

        table = os.environ.get("DEEPWORK_MEMORY_TABLE", "workspace_memory")
        return SupabaseWorkspaceMemory(url, key, table=table)
    if os.environ.get("DEEPWORK_MEMORY") == "1":
        from deepwork_agent.memory import InMemoryWorkspaceMemory

        return InMemoryWorkspaceMemory()
    return None


def _default_rubric() -> object:
    """A general-purpose result rubric applied to every task when verification is on.

    Enabled with ``DEEPWORK_VERIFY=1``. The public ``RubricMiddleware`` grades the
    result against these criteria and repairs within a bounded iteration cap; a
    passed verdict is rubric coverage, never ground truth. ``DEEPWORK_VERIFY_ITERS``
    caps the grader loop (default 1: a single verify pass, no repair).
    """
    from deepwork_agent.verification import RubricCriterion, RubricSpec

    try:
        iters = int(os.environ.get("DEEPWORK_VERIFY_ITERS", "1"))
    except ValueError:
        iters = 1
    iters = max(1, min(iters, 3))
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
        max_iterations=iters,
    )


def _langsmith_sandbox_factory() -> Callable[[], object] | None:
    """A context-manager factory yielding a fresh per-task LangSmith sandbox backend.

    Returns ``None`` when no LangSmith credential is configured, so the graph
    falls back to the in-memory virtual filesystem. The credential is read only
    here, in the composition seam — never in the graph.
    """
    api_key = os.environ.get("LANGSMITH_API_KEY")
    if not api_key:
        return None

    @contextmanager
    def factory() -> Iterator[object]:
        from deepagents.backends import LangSmithSandbox
        from langsmith.sandbox import SandboxClient

        client = SandboxClient(api_key=api_key, timeout=30.0)
        sandbox = client.create_sandbox(name="deepwork-task", timeout=120)
        token = _resolve_github_token()
        if token:
            _configure_sandbox_github(sandbox, token)
        try:
            yield LangSmithSandbox(sandbox)
        finally:
            try:
                client.delete_sandbox(sandbox.id)
            except Exception:  # noqa: BLE001 - cleanup must never mask the task result
                pass
            try:
                client.close()
            except Exception:  # noqa: BLE001 - cleanup must never mask the task result
                pass

    return factory


def _resolve_github_token() -> str | None:
    """Resolve a GitHub credential for the sandbox, preferring the GitHub App.

    Order:
    1. ``DEEPWORK_GITHUB_APP_ID`` + ``DEEPWORK_GITHUB_APP_PRIVATE_KEY`` -> mint a
       fresh ~1-hour installation token (the recommended model; short-lived and
       scoped to the app's installation). Optional ``DEEPWORK_GITHUB_APP_INSTALLATION_ID``.
    2. ``DEEPWORK_GITHUB_TOKEN`` -> a supplied PAT (simpler fallback).
    3. Otherwise ``None`` -> the sandbox gets no git credential (push disabled).

    A minting failure falls back to the PAT (if any) rather than crashing the
    task; the App private key is read only here and never enters task content.
    """
    app_id = os.environ.get("DEEPWORK_GITHUB_APP_ID")
    app_key = os.environ.get("DEEPWORK_GITHUB_APP_PRIVATE_KEY")
    if app_id and app_key:
        from deepwork_agent.github_app import (
            GitHubAppError,
            mint_installation_token,
            normalize_private_key,
        )

        raw_installation = os.environ.get("DEEPWORK_GITHUB_APP_INSTALLATION_ID")
        installation_id = None
        if raw_installation and raw_installation.strip().isdigit():
            installation_id = int(raw_installation.strip())
        try:
            return mint_installation_token(
                app_id=app_id,
                private_key_pem=normalize_private_key(app_key),
                installation_id=installation_id,
            )
        except GitHubAppError:
            pass  # fall through to the PAT fallback below
    return os.environ.get("DEEPWORK_GITHUB_TOKEN")


def _configure_sandbox_github(sandbox: object, token: str) -> None:
    """Give the sandbox a scoped GitHub credential for push/PR, server-side only.

    Writes a git credential helper and identity inside the sandbox so the agent
    can push and open PRs. The token is passed straight to the sandbox and never
    logged or returned; it is a short-lived, repo-scoped token supplied by the
    application, not a reusable secret placed in agent-visible task content.
    """
    setup = (
        "git config --global credential.helper store && "
        f"printf 'https://x-access-token:%s@github.com\\n' '{token}' > ~/.git-credentials && "
        "chmod 600 ~/.git-credentials && "
        "git config --global user.name 'Deep Work' && "
        "git config --global user.email 'agent@deepwork.local' && "
        "git config --global url.'https://github.com/'.insteadOf 'git@github.com:'"
    )
    try:
        sandbox.run(setup)  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001 - a failed setup must not crash task execution
        pass

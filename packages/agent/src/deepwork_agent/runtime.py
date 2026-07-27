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
import shlex
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager, suppress
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from deepwork_agent.config import AgentConfig
from deepwork_agent.graph import LocalAgentGraph, create_graph

__all__ = [
    "DeterministicLocalModel",
    "build_git_credential_setup_command",
    "build_model",
    "make_graph",
]


class SandboxCredentialError(RuntimeError):
    """Raised when the sandbox GitHub credential could not be configured.

    The message is deliberately non-specific and never contains the token, so it
    is safe to surface as a task failure reason.
    """


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
    return create_graph(
        model=build_model(),
        config=AgentConfig(),
        system_prompt=system_prompt,
        sandbox_factory=sandbox_factory,
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

    github_token = os.environ.get("DEEPWORK_GITHUB_TOKEN")

    @contextmanager
    def factory() -> Iterator[object]:
        from deepagents.backends import LangSmithSandbox
        from langsmith.sandbox import SandboxClient

        client = SandboxClient(api_key=api_key, timeout=30.0)
        sandbox = client.create_sandbox(name="deepwork-task", timeout=120)
        if github_token:
            _configure_sandbox_github(sandbox, github_token)
        try:
            yield LangSmithSandbox(sandbox)
        finally:
            # Cleanup must never mask the task result, but it must not vanish
            # silently either: a leaked sandbox still holds the credential.
            with suppress(Exception):
                client.delete_sandbox(sandbox.id)
            with suppress(Exception):
                client.close()

    return factory


def build_git_credential_setup_command(token: str) -> str:
    """Build the shell command that installs the GitHub credential in a sandbox.

    The token is passed through :func:`shlex.quote` so a value containing quotes,
    ``;``, ``$(...)``, or backticks cannot break out of the command and execute in
    the sandbox shell. Extracted as a pure function so this quoting is unit-tested
    without a live sandbox.
    """
    quoted_token = shlex.quote(token)
    return (
        "git config --global credential.helper store && "
        f"printf 'https://x-access-token:%s@github.com\\n' {quoted_token} > ~/.git-credentials && "
        "chmod 600 ~/.git-credentials && "
        "git config --global user.name 'Deep Work' && "
        "git config --global user.email 'agent@deepwork.local' && "
        "git config --global url.'https://github.com/'.insteadOf 'git@github.com:'"
    )


def _configure_sandbox_github(sandbox: object, token: str) -> None:
    """Give the sandbox a GitHub credential for push/PR, server-side only.

    Trust model, stated honestly: this writes a credential into the sandbox
    filesystem (``~/.git-credentials``) so ``git`` can push. The sandbox is where
    the model-driven agent executes, so the token is within the agent's reach for
    the sandbox's lifetime. The durable mitigation (roadmap A2.3) is to supply a
    per-task, single-repo, short-lived GitHub App installation token minted and
    revoked outside the sandbox; ``DEEPWORK_GITHUB_TOKEN`` is the interim static
    fallback. The value is never logged or returned, and the setup command quotes
    it so it cannot be interpreted as shell.

    Raises:
        SandboxCredentialError: If the credential could not be installed, so the
            run fails clearly instead of silently pushing without credentials.

    """
    try:
        sandbox.run(build_git_credential_setup_command(token))  # type: ignore[attr-defined]
    except Exception as error:  # noqa: BLE001 - normalized to a non-secret failure
        msg = "failed to configure the sandbox GitHub credential"
        raise SandboxCredentialError(msg) from error

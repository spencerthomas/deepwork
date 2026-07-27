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
from collections.abc import Sequence
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from deepwork_agent.config import AgentConfig
from deepwork_agent.graph import LocalAgentGraph, create_graph

__all__ = ["DeterministicLocalModel", "build_model", "make_graph", "graph"]

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
    ``system_prompt.txt``.
    """
    system_prompt = os.environ.get("DEEPWORK_AGENT_SYSTEM_PROMPT") or None
    return create_graph(model=build_model(), config=AgentConfig(), system_prompt=system_prompt)

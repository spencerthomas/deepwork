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
            "'anthropic:claude-sonnet-5') with the provider credential in the "
            "server environment, or set DEEPWORK_AGENT_FAKE=1 for the keyless "
            "deterministic development stand-in"
        )
        raise RuntimeError(msg)
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


def make_graph() -> LocalAgentGraph:
    """Build the servable compiled graph around the resolved model."""
    return create_graph(model=build_model(), config=AgentConfig())


graph = make_graph()

"""Typed, package-local configuration for the Deep Work graph."""

from dataclasses import dataclass
from typing import Literal

_MIN_PLAN_STEPS = 1
_MAX_PLAN_STEPS = 12

# Bounds on the reliability envelope. These cap runaway agent loops and provider
# cost without constraining ordinary tasks; a deployment can tune within the range.
_MIN_MODEL_CALLS = 1
_MAX_MODEL_CALLS = 200
_MIN_TOOL_CALLS = 1
_MAX_TOOL_CALLS = 500
_MIN_RECURSION_LIMIT = 4
_MAX_RECURSION_LIMIT = 500
_MAX_RETRIES_CEILING = 8


@dataclass(frozen=True, slots=True)
class AgentConfig:
    """Configure the local graph around a caller-injected model.

    Model selection, credentials, deployment, sessions, and durable persistence are
    deliberately outside this configuration. Callers inject an initialized chat
    model into :func:`deepwork_agent.create_graph`.

    The reliability fields bound execution so an approved plan cannot spend
    unboundedly or loop forever. They are enforced by the maintained LangChain
    middleware stack (call limits, retries) plus a LangGraph ``recursion_limit`` on
    the executor invoke — reuse-first, not a custom budget engine.
    """

    schema_version: Literal[1] = 1
    runtime_mode: Literal["local-runtime"] = "local-runtime"
    require_plan_approval: bool = True
    max_plan_steps: int = 6
    # Reliability envelope for the Deep Agents executor (per run).
    max_model_calls: int = 25
    max_tool_calls: int = 50
    model_max_retries: int = 2
    tool_max_retries: int = 2
    recursion_limit: int = 50

    def __post_init__(self) -> None:
        """Validate the small local-runtime configuration contract."""
        if self.schema_version != 1:
            msg = "unsupported agent configuration schema version"
            raise ValueError(msg)
        if self.runtime_mode != "local-runtime":
            msg = "only the injected-model local-runtime mode is supported"
            raise ValueError(msg)
        if not _MIN_PLAN_STEPS <= self.max_plan_steps <= _MAX_PLAN_STEPS:
            msg = "max_plan_steps must be between 1 and 12"
            raise ValueError(msg)
        if not _MIN_MODEL_CALLS <= self.max_model_calls <= _MAX_MODEL_CALLS:
            msg = "max_model_calls must be between 1 and 200"
            raise ValueError(msg)
        if not _MIN_TOOL_CALLS <= self.max_tool_calls <= _MAX_TOOL_CALLS:
            msg = "max_tool_calls must be between 1 and 500"
            raise ValueError(msg)
        if not _MIN_RECURSION_LIMIT <= self.recursion_limit <= _MAX_RECURSION_LIMIT:
            msg = "recursion_limit must be between 4 and 500"
            raise ValueError(msg)
        if not 0 <= self.model_max_retries <= _MAX_RETRIES_CEILING:
            msg = "model_max_retries must be between 0 and 8"
            raise ValueError(msg)
        if not 0 <= self.tool_max_retries <= _MAX_RETRIES_CEILING:
            msg = "tool_max_retries must be between 0 and 8"
            raise ValueError(msg)

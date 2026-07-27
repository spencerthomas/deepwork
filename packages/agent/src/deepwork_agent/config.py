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
    # Tool retries default OFF: retrying an arbitrary tool on any exception can
    # duplicate a non-idempotent side effect (a push, a PR, a write) whose call
    # succeeded remotely but whose response failed. A caller that knows its tools
    # are idempotent may opt in by raising this.
    tool_max_retries: int = 0
    recursion_limit: int = 50

    def __post_init__(self) -> None:
        """Validate the small local-runtime configuration contract."""
        if self.schema_version != 1:
            msg = "unsupported agent configuration schema version"
            raise ValueError(msg)
        if self.runtime_mode != "local-runtime":
            msg = "only the injected-model local-runtime mode is supported"
            raise ValueError(msg)
        self._validate_reliability_envelope()

    def _validate_reliability_envelope(self) -> None:
        """Reject non-integer or out-of-range reliability settings.

        Integer-ness is checked first because ``bool`` is an ``int`` subclass and a
        fractional value would otherwise pass the bound comparisons.
        """
        bounds = (
            ("max_plan_steps", self.max_plan_steps, _MIN_PLAN_STEPS, _MAX_PLAN_STEPS),
            ("max_model_calls", self.max_model_calls, _MIN_MODEL_CALLS, _MAX_MODEL_CALLS),
            ("max_tool_calls", self.max_tool_calls, _MIN_TOOL_CALLS, _MAX_TOOL_CALLS),
            ("model_max_retries", self.model_max_retries, 0, _MAX_RETRIES_CEILING),
            ("tool_max_retries", self.tool_max_retries, 0, _MAX_RETRIES_CEILING),
            ("recursion_limit", self.recursion_limit, _MIN_RECURSION_LIMIT, _MAX_RECURSION_LIMIT),
        )
        for name, value, low, high in bounds:
            if type(value) is not int:
                msg = f"{name} must be an integer"
                raise ValueError(msg)
            if not low <= value <= high:
                msg = f"{name} must be between {low} and {high}"
                raise ValueError(msg)

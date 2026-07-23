"""Typed, package-local configuration for the Deep Work graph."""

from dataclasses import dataclass
from typing import Literal

_MIN_PLAN_STEPS = 1
_MAX_PLAN_STEPS = 12
_MAX_RUBRIC_ITERATIONS = 20


@dataclass(frozen=True, slots=True)
class AgentConfig:
    """Configure the local graph around a caller-injected model.

    Model selection, credentials, deployment, sessions, and durable persistence are
    deliberately outside this configuration. Callers inject an initialized chat
    model into :func:`deepwork_agent.create_graph`.
    """

    schema_version: Literal[1] = 1
    runtime_mode: Literal["local-runtime"] = "local-runtime"
    require_plan_approval: bool = True
    max_plan_steps: int = 6
    max_rubric_iterations: int = 3

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
        if not _MIN_PLAN_STEPS <= self.max_rubric_iterations <= _MAX_RUBRIC_ITERATIONS:
            msg = "max_rubric_iterations must be between 1 and 20"
            raise ValueError(msg)

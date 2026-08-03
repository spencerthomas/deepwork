"""Typed, package-local configuration for the Deep Work graph."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from collections.abc import Mapping

_MIN_PLAN_STEPS = 1
_MAX_PLAN_STEPS = 12

_DEFAULT_MEMORY_TABLE = "workspace_memory"
_MAX_VERIFICATION_ITERATIONS = 3


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


@dataclass(frozen=True, slots=True)
class ServingConfig:
    """Typed server-only settings consumed by the serving composition root.

    Credentials remain in this server-side object and are excluded from its
    representation so ordinary diagnostics cannot print them accidentally.
    """

    use_fake_model: bool = False
    model_identifier: str | None = None
    openrouter_api_key: str | None = field(default=None, repr=False)
    system_prompt: str | None = None
    sandbox_backend: Literal["langsmith"] | None = None
    langsmith_api_key: str | None = field(default=None, repr=False)
    verification_enabled: bool = False
    verification_iterations: int = 1
    supabase_url: str | None = None
    supabase_service_key: str | None = field(default=None, repr=False)
    memory_table: str = _DEFAULT_MEMORY_TABLE
    memory_enabled: bool = False

    @classmethod
    def from_environment(cls, environment: Mapping[str, str] | None = None) -> ServingConfig:
        """Read and normalize the serving environment at the config boundary."""
        source = os.environ if environment is None else environment
        sandbox = source.get("DEEPWORK_SANDBOX")
        return cls(
            use_fake_model=source.get("DEEPWORK_AGENT_FAKE") == "1",
            model_identifier=source.get("DEEPWORK_AGENT_MODEL"),
            openrouter_api_key=source.get("OPENROUTER_API_KEY"),
            system_prompt=source.get("DEEPWORK_AGENT_SYSTEM_PROMPT") or None,
            sandbox_backend="langsmith" if sandbox == "langsmith" else None,
            langsmith_api_key=source.get("LANGSMITH_API_KEY"),
            verification_enabled=source.get("DEEPWORK_VERIFY") == "1",
            verification_iterations=_verification_iterations(
                source.get("DEEPWORK_VERIFY_ITERS", "1")
            ),
            supabase_url=source.get("DEEPWORK_SUPABASE_URL"),
            supabase_service_key=source.get("DEEPWORK_SUPABASE_SERVICE_KEY"),
            memory_table=source.get("DEEPWORK_MEMORY_TABLE", _DEFAULT_MEMORY_TABLE),
            memory_enabled=source.get("DEEPWORK_MEMORY") == "1",
        )


def _verification_iterations(raw_value: str) -> int:
    """Parse and bound the verification repair count while preserving defaults."""
    try:
        iterations = int(raw_value)
    except ValueError:
        iterations = 1
    return max(1, min(iterations, _MAX_VERIFICATION_ITERATIONS))

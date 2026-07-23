"""Tests for deliberate package exports and import behavior."""

from importlib.resources import files

import deepwork_agent

EXPECTED_EXPORTS = {
    "DEEP_WORK_SYSTEM_PROMPT",
    "PROTECTED_ACTION",
    "RUNTIME_MODE",
    "AgentConfig",
    "AgentInput",
    "AgentOutput",
    "AgentState",
    "ApprovalDecision",
    "ApprovalRequest",
    "ApprovalResponse",
    "RuntimeCapabilities",
    "create_graph",
    "initial_state",
    "runtime_capabilities",
    "validate_approval_response",
    "validate_plan_edit",
}


def test_public_exports_are_deliberate() -> None:
    """The package root exposes only the reviewed local-runtime API."""
    assert set(deepwork_agent.__all__) == EXPECTED_EXPORTS


def test_typed_package_marker_is_installed() -> None:
    """The source package exposes its PEP 561 marker."""
    assert files("deepwork_agent").joinpath("py.typed").is_file()

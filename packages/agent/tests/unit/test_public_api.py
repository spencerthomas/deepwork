"""Tests for deliberate package exports and import behavior."""

from importlib.resources import files

import deepwork_agent

EXPECTED_EXPORTS = {
    "CONFIG_CONTRACT_GATE",
    "AgentPackageConfig",
    "RuntimeAvailability",
    "RuntimeCapabilityUnavailable",
    "UnavailableAgentState",
    "create_graph",
    "initial_unavailable_state",
    "runtime_availability",
}


def test_public_exports_are_deliberate() -> None:
    """The package root exposes only the reviewed scaffold API."""
    assert set(deepwork_agent.__all__) == EXPECTED_EXPORTS


def test_typed_package_marker_is_installed() -> None:
    """The source package exposes its PEP 561 marker."""
    assert files("deepwork_agent").joinpath("py.typed").is_file()

"""Tests for the explicit unavailable graph boundary."""

import pytest

from deepwork_agent import (
    CONFIG_CONTRACT_GATE,
    RuntimeCapabilityUnavailable,
    create_graph,
    runtime_availability,
)


def test_runtime_availability_is_deterministic() -> None:
    """Availability names the gate and never implies live support."""
    availability = runtime_availability()

    assert availability.available is False
    assert availability.contract_gate == CONFIG_CONTRACT_GATE
    assert "unavailable" in availability.reason


def test_create_graph_fails_truthfully() -> None:
    """Graph creation cannot simulate a runtime while its contract is open."""
    with pytest.raises(RuntimeCapabilityUnavailable) as captured:
        create_graph()

    assert captured.value.availability == runtime_availability()
    assert str(captured.value).startswith("SPIKE-CONFIG-001:")

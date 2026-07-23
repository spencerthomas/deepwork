"""Tests for the deterministic unavailable state."""

from deepwork_agent import initial_unavailable_state


def test_initial_state_is_safe_and_unavailable() -> None:
    """State reports the gate without endpoint, provider, or credential data."""
    state = initial_unavailable_state()

    assert state["status"] == "unavailable"
    assert state["contract_gate"] == "SPIKE-CONFIG-001"
    assert "unavailable" in state["reason"]
    assert set(state) == {"status", "contract_gate", "reason"}

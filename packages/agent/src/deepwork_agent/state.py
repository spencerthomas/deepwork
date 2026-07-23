"""Typed unavailable state for the package scaffold."""

from typing import Literal, TypedDict

from deepwork_agent.graph import CONFIG_CONTRACT_GATE, runtime_availability


class UnavailableAgentState(TypedDict):
    """Represent the package's explicit non-runtime state without provider data."""

    status: Literal["unavailable"]
    contract_gate: Literal["SPIKE-CONFIG-001"]
    reason: str


def initial_unavailable_state() -> UnavailableAgentState:
    """Return deterministic state suitable for local no-network tests."""
    availability = runtime_availability()
    return {
        "status": "unavailable",
        "contract_gate": CONFIG_CONTRACT_GATE,
        "reason": availability.reason,
    }

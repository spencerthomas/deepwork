"""Offline plan-approval contract harness.

This package intentionally does not implement or infer a provider HITL transport.
It consumes normalized decision values after an upstream adapter has validated
their count, order, freshness, and provider-specific resume syntax.
"""

from .contract import (
    Authority,
    Boundary,
    Decision,
    DecisionType,
    PlanProposal,
    PlanStep,
)
from .engine import PlanApprovalEngine
from .errors import ContractViolation
from .store import AppendOnlyCheckpointStore

__all__ = [
    "AppendOnlyCheckpointStore",
    "Authority",
    "Boundary",
    "ContractViolation",
    "Decision",
    "DecisionType",
    "PlanApprovalEngine",
    "PlanProposal",
    "PlanStep",
]

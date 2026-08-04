"""Pure values for truthful source qualification."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

SourceProbeState = Literal[
    "available",
    "unavailable",
    "gated",
    "permission-denied",
    "unknown",
]
SourceCapabilityEvidenceClass = Literal["documented", "live-contract", "fixture"]
SourceCapabilitySafeReason = Literal[
    "contract-not-verified",
    "not-supported",
    "permission-required",
    "source-unavailable",
    "adapter-disabled",
]
_SAFE_REASONS_BY_STATE: dict[SourceProbeState, tuple[SourceCapabilitySafeReason, ...]] = {
    "available": (),
    "unavailable": ("not-supported", "source-unavailable", "adapter-disabled"),
    "gated": ("permission-required", "adapter-disabled"),
    "permission-denied": ("permission-required",),
    "unknown": ("contract-not-verified",),
}


@dataclass(frozen=True, slots=True)
class SourceCapabilityObservation:
    """One sanitized capability observation from a bounded source check."""

    name: str
    state: SourceProbeState
    observed_at: str
    adapter_version: str
    contract_version: str
    evidence_class: SourceCapabilityEvidenceClass
    safe_reason: SourceCapabilitySafeReason | None = None

    def __post_init__(self) -> None:
        if self.state == "available" and self.safe_reason is not None:
            raise ValueError("available source capability cannot carry a safe reason")
        if self.state != "available" and self.safe_reason is None:
            raise ValueError("unavailable source capability requires a safe reason")
        if (
            self.safe_reason is not None
            and self.safe_reason not in _SAFE_REASONS_BY_STATE[self.state]
        ):
            raise ValueError("source capability state and safe reason are not coherent")


@dataclass(frozen=True, slots=True)
class SourceProbeResult:
    """Credential-free result of checking one source candidate."""

    state: SourceProbeState
    assistant_id: str | None
    graph_id: str | None
    reason: str
    capabilities: tuple[SourceCapabilityObservation, ...] = field(default_factory=tuple)


class SourceEndpointInvalidError(ValueError):
    """The candidate endpoint is unsafe before any provider request."""


class SourceTargetUnavailableError(LookupError):
    """The caller cannot use the requested server-owned source target."""

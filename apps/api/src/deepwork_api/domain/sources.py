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


@dataclass(frozen=True, slots=True)
class SourceCapabilityObservation:
    """One sanitized capability observation from a bounded source check."""

    name: str
    state: SourceProbeState
    reason: str


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


class SourceProbeUnavailableError(RuntimeError):
    """No server-held source qualification capability is configured."""

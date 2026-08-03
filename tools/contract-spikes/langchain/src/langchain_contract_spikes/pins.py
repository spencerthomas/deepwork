"""Lightweight access to the exact direct dependencies in the installed probe wheel."""

from __future__ import annotations

from importlib.metadata import requires, version

PROBE_DISTRIBUTION = "deepwork-langchain-contract-spikes"


def pinned_distributions() -> dict[str, str]:
    """Derive exact direct pins from the probe wheel metadata."""
    requirements = requires(PROBE_DISTRIBUTION)
    if not requirements:
        raise RuntimeError("installed probe metadata contains no direct dependency pins")
    pins: dict[str, str] = {}
    for requirement in requirements:
        name, separator, pinned_version = requirement.partition("==")
        if not separator or not name or not pinned_version:
            raise RuntimeError(f"probe dependency is not exactly pinned: {requirement}")
        pins[name] = pinned_version
    return pins


def installed_distributions() -> dict[str, str]:
    """Return direct installed versions, rejecting drift from wheel metadata."""
    expected = pinned_distributions()
    installed = {name: version(name) for name in expected}
    if installed != expected:
        raise RuntimeError(f"installed contract drift: expected {expected}, got {installed}")
    return installed

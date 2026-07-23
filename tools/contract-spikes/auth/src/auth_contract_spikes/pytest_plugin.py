"""Keep the packet's exact repo-root pytest command scoped to this project."""

from __future__ import annotations

from pathlib import Path


def pytest_addoption(parser) -> None:
    group = parser.getgroup("auth-contract-spikes")
    group.addoption("--live-profile", action="store", default=None)
    group.addoption("--evidence-dir", action="store", default=None)


def pytest_configure(config) -> None:
    config.addinivalue_line(
        "markers",
        "live_contract: opt-in read-only probes against a sanctioned non-production classic account",
    )


def pytest_ignore_collect(collection_path: Path, config):
    allowed = (
        Path(__file__).resolve().parents[2] / "tests"
    ).resolve()
    candidate = Path(collection_path).resolve()
    if candidate == allowed or allowed in candidate.parents:
        return None
    if candidate in allowed.parents:
        return None
    return True

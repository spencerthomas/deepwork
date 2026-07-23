"""Keep the packet's exact root-invoked pytest command isolated."""

from __future__ import annotations

from pathlib import Path


def pytest_configure(config: object) -> None:
    config.addinivalue_line(
        "markers",
        "live_contract: requires explicit non-production authority and accepted upstream evidence",
    )


def pytest_ignore_collect(collection_path: Path, config: object) -> bool:
    root = Path(__file__).resolve().parents[2]
    tests = root / "tests"
    candidate = collection_path.resolve()
    if tests.is_relative_to(candidate):
        return False
    try:
        candidate.relative_to(tests)
    except ValueError:
        return True
    return False

"""Keep the required root-invoked pytest command inside this isolated project."""

from __future__ import annotations

from pathlib import Path


PROJECT_TESTS = Path("tools/contract-spikes/attachments/tests")


def pytest_configure(config: object) -> None:
    """Register the live marker even when pytest discovers the root config first."""
    getattr(config, "addinivalue_line")(
        "markers",
        "live_contract: requires explicitly sanctioned non-production dependencies",
    )


def pytest_ignore_collect(collection_path: Path, config: object) -> bool:
    """Ignore every repository path outside the spike's own tests."""
    root = Path(getattr(config, "rootpath")).resolve()
    target = (root / PROJECT_TESTS).resolve()
    candidate = collection_path.resolve()
    return not (
        candidate == target
        or candidate.is_relative_to(target)
        or target.is_relative_to(candidate)
    )

"""Run pinned project-local pytest against only the isolated probe tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_RELATIVE = Path("tools/contract-spikes/coding-review-surfaces")


def main() -> int:
    project = Path.cwd() / PROJECT_RELATIVE
    if not project.is_dir():
        raise RuntimeError("run probe validation from the repository root")
    return pytest.main(
        [
            "-c",
            str(project / "pyproject.toml"),
            str(project / "tests"),
            *sys.argv[1:],
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())

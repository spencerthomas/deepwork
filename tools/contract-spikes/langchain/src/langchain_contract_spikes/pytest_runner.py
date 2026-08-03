"""Run only this probe's tests with the pytest pinned in its isolated lock."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

def _project_root() -> Path:
    candidate = Path.cwd() / "tools/contract-spikes/langchain"
    if not candidate.is_dir():
        raise RuntimeError("run the probe validation from the repository root")
    return candidate

def main() -> int:
    project = _project_root()
    arguments = [
        "-c",
        str(project / "pyproject.toml"),
        str(project / "tests"),
        *sys.argv[1:],
    ]
    return pytest.main(arguments)


if __name__ == "__main__":
    raise SystemExit(main())

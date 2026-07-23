"""Scoped delegate to the workspace pytest when public-index installation is blocked."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

EXPECTED_PYTEST = "pytest 9.0.2"


def _project_root() -> Path:
    candidate = Path.cwd() / "tools/contract-spikes/langchain"
    if not candidate.is_dir():
        raise RuntimeError("run the probe validation from the repository root")
    return candidate


def _workspace_pytest() -> str:
    current = Path(sys.argv[0]).resolve()
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        candidate = Path(directory) / "pytest"
        if candidate.exists() and candidate.resolve() != current:
            version = subprocess.run(
                [str(candidate), "--version"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            if version == EXPECTED_PYTEST:
                return str(candidate)
    raise RuntimeError(f"required workspace runner {EXPECTED_PYTEST!r} is unavailable")


def main() -> int:
    project = _project_root()
    pytest_executable = _workspace_pytest()
    environment = os.environ.copy()
    source = str(project / "src")
    environment["PYTHONPATH"] = source + os.pathsep + environment.get("PYTHONPATH", "")
    command = [
        pytest_executable,
        "-c",
        str(project / "pyproject.toml"),
        str(project / "tests"),
        *sys.argv[1:],
    ]
    return subprocess.run(command, env=environment, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())

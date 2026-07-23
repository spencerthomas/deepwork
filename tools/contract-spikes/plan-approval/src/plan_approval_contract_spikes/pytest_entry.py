from __future__ import annotations

from pathlib import Path
import sys

import pytest


def main() -> None:
    """Run only this isolated harness, even when invoked from the repo root."""

    project = Path(__file__).resolve().parents[2]
    arguments = [
        "-c",
        str(project / "pyproject.toml"),
        *sys.argv[1:],
        str(project / "tests"),
    ]
    raise SystemExit(pytest.main(arguments))

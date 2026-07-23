"""Offline command-policy regressions."""

from __future__ import annotations

import subprocess
from pathlib import Path


def test_only_bootstrap_recipe_uses_network_eligible_uv() -> None:
    project_root = Path(__file__).resolve().parents[2]
    makefile = (project_root / "Makefile").read_text()
    network_eligible_recipes = [
        line.strip()
        for line in makefile.splitlines()
        if line.startswith("\t") and "$(UV)" in line and "$(OFFLINE_UV)" not in line
    ]

    assert network_eligible_recipes == [
        "$(UV) sync --python $(PYTHON_VERSION) --frozen --all-groups"
    ]
    assert "OFFLINE_UV := $(UV) --offline --no-python-downloads" in makefile


def test_doctor_fails_closed_for_cold_package_state(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [
            "make",
            "UV_PROJECT_ENVIRONMENT=" + str(tmp_path / "missing-environment"),
            "UV_CACHE_DIR=" + str(tmp_path / "empty-cache"),
            "doctor",
        ],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "offline package state is not bootstrapped" in result.stderr
    assert "run 'make -C apps/api bootstrap' explicitly" in result.stderr

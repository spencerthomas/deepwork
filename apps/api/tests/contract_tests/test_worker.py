"""Worker entry-point contract tests."""

from __future__ import annotations

import json
from pathlib import Path

from pytest import CaptureFixture

from deepwork_api.bootstrap.worker import main, worker_status


def test_worker_reports_unavailable_durability() -> None:
    status = worker_status()

    assert status.mode.value == "fixture"
    assert status.durability == "unavailable"


def test_configured_worker_reports_local_sqlite_proof_only() -> None:
    status = worker_status(durable=True)

    assert status.mode.value == "fixture"
    assert status.durability == "local-sqlite-proof"
    assert "not production" in status.safe_reason


def test_worker_check_prints_safe_json(capsys: CaptureFixture[str]) -> None:
    assert main(["--check"]) == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["mode"] == "fixture"
    assert payload["durability"] == "unavailable"


def test_worker_check_with_database_labels_local_proof(
    tmp_path: Path,
    capsys: CaptureFixture[str],
) -> None:
    database = (tmp_path / "jobs.sqlite3").resolve()

    assert main(["--check", "--job-database", str(database)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["durability"] == "local-sqlite-proof"
    assert "tenant" not in payload


def test_worker_once_reports_idle_queue(
    tmp_path: Path,
    capsys: CaptureFixture[str],
) -> None:
    database = (tmp_path / "jobs.sqlite3").resolve()

    assert main(["--job-database", str(database), "--once"]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "status": "idle",
        "durability": "local-sqlite-proof",
    }

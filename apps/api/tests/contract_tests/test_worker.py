"""Worker entry-point contract tests."""

from __future__ import annotations

import json

from pytest import CaptureFixture

from deepwork_api.bootstrap.worker import main, worker_status


def test_worker_reports_unavailable_durability() -> None:
    status = worker_status()

    assert status.mode.value == "fixture"
    assert status.durability == "unavailable"


def test_worker_check_prints_safe_json(capsys: CaptureFixture[str]) -> None:
    assert main(["--check"]) == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["mode"] == "fixture"
    assert payload["durability"] == "unavailable"

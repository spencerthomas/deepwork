from __future__ import annotations

from pathlib import Path

import pytest

from auth_contract_spikes.live import run_read_only_profile


@pytest.mark.live_contract
def test_live_profile_is_explicit_and_read_only(live_profile, request) -> None:
    evidence_dir = request.config.getoption("--evidence-dir")
    if not evidence_dir:
        pytest.fail("live probes require --evidence-dir")
    evidence = run_read_only_profile(live_profile, Path(evidence_dir))
    assert evidence["request_count"] == 2

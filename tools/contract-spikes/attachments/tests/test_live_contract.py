from __future__ import annotations

import os

import pytest


@pytest.mark.live_contract
def test_live_profile_fails_closed_without_all_sanctioned_components(
    request: pytest.FixtureRequest,
) -> None:
    profile = request.config.getoption("--live-profile")
    evidence_dir = request.config.getoption("--evidence-dir")
    assert profile == "non-production-classic-attachments", (
        "live profile must be explicitly non-production-classic-attachments"
    )
    assert evidence_dir is not None, "live evidence directory is required"
    required = {
        "DW_ATTACH_OBJECT_PROFILE",
        "DW_ATTACH_SCANNER_PROFILE",
        "DW_ATTACH_CLASSIC_RUNTIME_PROFILE",
    }
    missing = sorted(name for name in required if not os.environ.get(name))
    assert not missing, f"live profile is incomplete; missing named component(s): {missing}"
    pytest.fail(
        "Sanctioned live adapters are intentionally absent from this research-only "
        "packet; capability remains blocked-live-evidence."
    )

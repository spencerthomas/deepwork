"""Template for the gated installed-public conformance observations.

The marker and test bodies are activated only in the reviewer-approved commit
that adds exact public distribution pins and hashes. This blocked template avoids
importing or inferring an unavailable API.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
PINS = ROOT / "approved-public-pins.json"


@pytest.mark.installed_public
def test_preflight_and_exact_pins_exist_before_import() -> None:
    assert PINS.is_file(), "blocked-package-index-evidence"
    pins = json.loads(PINS.read_text())
    assert pins["preflight_state"] == "approved"
    assert pins["distributions"]
    assert all(item["version"] and item["sha256"] for item in pins["distributions"])


@pytest.mark.installed_public
def test_required_public_exports_with_deterministic_fake_model() -> None:
    assert PINS.is_file(), "blocked-package-index-evidence"
    pytest.fail(
        "The approved pinning commit must replace this fail-closed template with "
        "observations against its exact installed public versions."
    )


@pytest.mark.live_contract
def test_live_contract_requires_sanctioned_profile_and_accepted_upstreams() -> None:
    pytest.fail("blocked-live-evidence")

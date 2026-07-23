from __future__ import annotations

import json
import os
from pathlib import Path

import pytest


@pytest.fixture
def live_profile(request: pytest.FixtureRequest) -> dict[str, object]:
    profile_name = request.config.getoption("--live-profile")
    if profile_name != "non-production-classic":
        pytest.fail("live probes require --live-profile non-production-classic")
    configured_path = os.environ.get("AUTH_CONTRACT_LIVE_PROFILE_FILE")
    if not configured_path:
        pytest.fail(
            "live probes fail closed: an out-of-repository, explicitly staged profile was not mounted"
        )
    profile_path = Path(configured_path).expanduser().resolve()
    repository = Path.cwd().resolve()
    if repository in profile_path.parents:
        pytest.fail("live probes fail closed: profile must be mounted outside the repository")
    if not profile_path.is_file():
        pytest.fail("live probes fail closed: mounted profile is unavailable")
    profile = json.loads(profile_path.read_text())
    if profile.get("account_class") != "non-production-classic":
        pytest.fail("live probes fail closed: profile is not non-production-classic")
    if profile.get("read_only") is not True:
        pytest.fail("live probes fail closed: profile is not explicitly read-only")
    return profile

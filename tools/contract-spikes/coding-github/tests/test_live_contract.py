from __future__ import annotations

import pytest


@pytest.mark.live_contract
def test_live_profile_requires_external_authority() -> None:
    pytest.fail(
        "live contract intentionally unavailable: accepted sandbox evidence, "
        "dedicated GitHub App, disposable repository, and mutation grant required"
    )

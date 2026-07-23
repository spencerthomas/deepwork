import pytest


@pytest.mark.live_contract
def test_live_contract_fails_closed_on_offline_base(request):
    profile = request.config.getoption("--live-profile")
    evidence_dir = request.config.getoption("--evidence-dir")
    pytest.fail(
        "live plan approval is blocked on this base: upstream gates are unaccepted "
        f"and no sanctioned sandbox may be used (profile={bool(profile)}, "
        f"evidence_dir={bool(evidence_dir)})"
    )

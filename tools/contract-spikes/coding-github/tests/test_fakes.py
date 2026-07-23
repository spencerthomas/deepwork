from __future__ import annotations

import pytest

from coding_github_spikes.contracts import ContractDenied, MutationLedger
from coding_github_spikes.fakes import FakeGitHub


def test_fake_git_ref_push_and_exactly_one_draft_pr() -> None:
    fake = FakeGitHub(base_sha="a" * 40)
    ref = "deep-work/task"
    fake.create_ref(ref, "a" * 40)
    fake.push(ref, "a" * 40, "b" * 40)
    ledger = MutationLedger()
    ledger.claim("sha256:grant")
    first = fake.create_draft_pr(base="main", head=ref, head_sha="b" * 40, ledger=ledger)
    second = fake.create_draft_pr(base="main", head=ref, head_sha="b" * 40, ledger=ledger)
    assert first == second
    assert first["draft"] is True
    assert len(fake.prs) == 1


def test_fake_denies_unknown_ref_collision_and_force_push() -> None:
    fake = FakeGitHub(base_sha="a" * 40)
    fake.create_ref("deep-work/task", "a" * 40)
    with pytest.raises(ContractDenied, match="collision"):
        fake.create_ref("deep-work/task", "b" * 40)
    with pytest.raises(ContractDenied, match="force"):
        fake.push("deep-work/task", "a" * 40, "b" * 40, force=True)


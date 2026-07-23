from __future__ import annotations

import json
from pathlib import Path

import pytest

from coding_github_spikes.catalog import canonical_hash
from coding_github_spikes.scrub import scan
from coding_github_spikes.validate_matrix import ValidationError, validate


ROOT = Path(__file__).parents[4] / "docs/references/research/coding-github-contracts"


def load(name: str) -> dict:
    return json.loads((ROOT / name).read_text())


def test_retained_matrix_is_complete_and_blocked_honestly() -> None:
    validate(load("matrix.json"), load("matrix-scope.json"), load("upstream-lock.json"), ROOT / "fixtures")
    assert all(row["state"] == "blocked-live-evidence" for row in load("matrix.json")["rows"])


def test_validator_rejects_fake_promoted_to_live() -> None:
    matrix = load("matrix.json")
    matrix["rows"][0]["state"] = "accepted-live"
    matrix["matrix_hash"] = canonical_hash(matrix["rows"])
    with pytest.raises(ValidationError, match="non-live evidence promoted"):
        validate(matrix, load("matrix-scope.json"), load("upstream-lock.json"), ROOT / "fixtures")


def test_validator_rejects_an_empty_evidence_list() -> None:
    matrix = load("matrix.json")
    matrix["rows"][0]["evidence"] = []
    matrix["matrix_hash"] = canonical_hash(matrix["rows"])
    with pytest.raises(ValidationError, match="non-empty ordered source list"):
        validate(matrix, load("matrix-scope.json"), load("upstream-lock.json"), ROOT / "fixtures")


def test_no_live_mutation_recorded() -> None:
    ledger = load("live-mutation-ledger.json")
    assert ledger["state"] == "not-run"
    assert ledger["draft_pr_create_attempts"] == 0
    assert ledger["draft_pr_identities"] == []
    assert ledger["merge_mutations"] == 0


def test_evidence_scrub_is_clean() -> None:
    assert not any(scan(ROOT).values())

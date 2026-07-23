from __future__ import annotations

import json
from pathlib import Path

import pytest

from attachment_contract_spikes.generate_matrix import generate
from attachment_contract_spikes.scope import derive_identities, load_json, scope_sha256
from attachment_contract_spikes.validate_matrix import validate


REPO_ROOT = Path(__file__).resolve().parents[4]
SCOPE = REPO_ROOT / "docs/references/research/attachment-contract-spikes/matrix-scope.json"


def test_scope_derives_declared_cross_product() -> None:
    scope = load_json(SCOPE)
    identities = derive_identities(scope)
    assert len(identities) == 912
    assert scope["expected_row_count"] == len(identities)


def test_generated_matrix_is_complete(tmp_path: Path) -> None:
    output = tmp_path / "matrix.json"
    payload = generate(SCOPE, output)
    assert payload["row_count"] == 912
    assert payload["scope_sha256"] == scope_sha256(SCOPE)
    summary = validate(
        output,
        SCOPE,
        require_complete_cross_product=True,
        reject_unresolved_precedence_conflicts=True,
    )
    assert summary["valid"] is True
    assert summary["conclusions"]["unsupported"] > 0
    assert summary["conclusions"]["unknown"] > 0
    assert summary["conclusions"].get("accepted-live", 0) == 0


def test_validator_rejects_missing_row(tmp_path: Path) -> None:
    output = tmp_path / "matrix.json"
    payload = generate(SCOPE, output)
    payload["rows"].pop()
    payload["row_count"] -= 1
    output.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="cross-product mismatch"):
        validate(
            output,
            SCOPE,
            require_complete_cross_product=True,
            reject_unresolved_precedence_conflicts=True,
        )


def test_validator_rejects_provider_overclaim(tmp_path: Path) -> None:
    output = tmp_path / "matrix.json"
    payload = generate(SCOPE, output)
    payload["rows"][0]["provider_proof"] = True
    output.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="provider proof"):
        validate(
            output,
            SCOPE,
            require_complete_cross_product=True,
            reject_unresolved_precedence_conflicts=True,
        )


def test_validator_rejects_precedence_conflict(tmp_path: Path) -> None:
    output = tmp_path / "matrix.json"
    payload = generate(SCOPE, output)
    payload["rows"][0]["precedence_conflict"] = True
    output.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="precedence conflict"):
        validate(
            output,
            SCOPE,
            require_complete_cross_product=True,
            reject_unresolved_precedence_conflicts=True,
        )

"""Validate completeness, provenance, safety, and precedence for matrix evidence."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from attachment_contract_spikes.scope import (
    derive_identities,
    load_json,
    row_id,
    scope_sha256,
)


REQUIRED_ROW_FIELDS = {
    "row_id",
    "identity",
    "scope_sha256",
    "scope_revision",
    "packet_id",
    "gate_id",
    "versions",
    "live_context",
    "expected_conclusion_class",
    "source_observations",
    "state_transitions",
    "request_schema",
    "response_schema",
    "policy",
    "fixture_sha256",
    "integrity",
    "authorization",
    "evidence_tier",
    "conclusion",
    "blocker",
    "blocker_owner",
    "fallback",
    "provider_proof",
    "precedence_conflict",
    "acceptance_contribution",
    "e2e_v1_01_effect",
}


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def validate(
    matrix_path: Path,
    scope_path: Path,
    *,
    require_complete_cross_product: bool,
    reject_unresolved_precedence_conflicts: bool,
) -> dict[str, Any]:
    """Validate the matrix and return a bounded summary."""
    matrix = load_json(matrix_path)
    scope = load_json(scope_path)
    digest = scope_sha256(scope_path)
    rows = matrix.get("rows")
    if not isinstance(rows, list):
        raise ValueError("matrix rows must be a list")

    errors: list[str] = []
    expected_identities = derive_identities(scope)
    expected = {row_id(identity): identity for identity in expected_identities}
    seen: dict[str, dict[str, Any]] = {}
    allowed_tiers = set(scope["evidence_tiers"])
    allowed_conclusions = set(scope["conclusion_states"])
    required_representations = {
        item["id"]
        for item in scope["matrix_dimensions"]["transfer_representations"]
    }
    observed_representations: set[str] = set()

    _require(matrix.get("scope_sha256") == digest, "matrix scope hash mismatch", errors)
    _require(matrix.get("row_count") == len(rows), "matrix row_count mismatch", errors)

    for index, row in enumerate(rows):
        prefix = f"row[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{prefix}: must be an object")
            continue
        missing = REQUIRED_ROW_FIELDS - set(row)
        _require(not missing, f"{prefix}: missing fields {sorted(missing)}", errors)
        row_key = row.get("row_id")
        identity = row.get("identity")
        if not isinstance(row_key, str) or not isinstance(identity, dict):
            errors.append(f"{prefix}: invalid row_id or identity")
            continue
        _require(row_key not in seen, f"{prefix}: duplicate row_id {row_key}", errors)
        seen[row_key] = row
        _require(expected.get(row_key) == identity, f"{prefix}: unscoped identity", errors)
        _require(row.get("scope_sha256") == digest, f"{prefix}: scope hash", errors)
        _require(
            row.get("scope_revision") == scope["scope_revision"],
            f"{prefix}: scope revision",
            errors,
        )
        _require(
            row.get("evidence_tier") in allowed_tiers,
            f"{prefix}: unknown evidence tier",
            errors,
        )
        _require(
            row.get("conclusion") in allowed_conclusions,
            f"{prefix}: unknown conclusion",
            errors,
        )
        observations = row.get("source_observations")
        _require(
            isinstance(observations, list) and bool(observations),
            f"{prefix}: absent evidence provenance",
            errors,
        )
        if isinstance(observations, list):
            for observation in observations:
                _require(
                    isinstance(observation, dict)
                    and observation.get("evidence_tier") in allowed_tiers
                    and bool(observation.get("source_ref"))
                    and bool(observation.get("observation")),
                    f"{prefix}: invalid source observation",
                    errors,
                )
        fallback = row.get("fallback")
        _require(
            fallback == scope["required_fallback"],
            f"{prefix}: missing or changed deterministic fallback",
            errors,
        )
        fixture_hash = row.get("fixture_sha256")
        _require(
            isinstance(fixture_hash, str)
            and len(fixture_hash) == 64
            and all(character in "0123456789abcdef" for character in fixture_hash),
            f"{prefix}: invalid fixture hash",
            errors,
        )
        policy = row.get("policy")
        _require(
            isinstance(policy, dict)
            and policy.get("max_count") == 4
            and isinstance(policy.get("max_bytes"), int)
            and policy.get("max_bytes") > 0
            and bool(policy.get("declared_media_type"))
            and policy.get("detected_media_type_required") is True,
            f"{prefix}: incomplete media policy",
            errors,
        )
        _require(
            row.get("e2e_v1_01_effect") == "neither-blocks-nor-satisfies",
            f"{prefix}: E2E-V1-01 overclaim",
            errors,
        )
        _require(
            set(row.get("acceptance_contribution", []))
            == {
                "AC-DW-TASK-002-03",
                "AC-DW-QUAL-001-03",
                "AC-DW-QUAL-001-04",
            },
            f"{prefix}: acceptance scope expansion",
            errors,
        )
        if row.get("evidence_tier") == "accepted-live":
            live = row.get("live_context", {})
            for name in (
                "account_tier",
                "region",
                "authentication_context",
                "observation_date",
            ):
                _require(
                    bool(live.get(name)) and live.get(name) not in {"unknown", "not-supplied"},
                    f"{prefix}: accepted-live lacks {name}",
                    errors,
                )
        if any(
            observation.get("evidence_tier") == "deterministic-fake"
            for observation in observations
            if isinstance(observation, dict)
        ):
            _require(
                row.get("provider_proof") is False,
                f"{prefix}: deterministic fake labeled provider proof",
                errors,
            )
        if row.get("conclusion") in {"blocked-live-evidence", "unknown", "unsupported"}:
            _require(bool(row.get("blocker")), f"{prefix}: missing blocker", errors)
            _require(
                bool(row.get("blocker_owner")), f"{prefix}: missing blocker owner", errors
            )
        if reject_unresolved_precedence_conflicts:
            _require(
                row.get("precedence_conflict") is False,
                f"{prefix}: unresolved precedence conflict",
                errors,
            )
        source = str(identity.get("target_sources", "")).lower()
        _require(
            "fleet" not in source
            and "managed-deep" not in source
            and source == "classic-langsmith-deployment-public-baseline",
            f"{prefix}: excluded or unknown source",
            errors,
        )
        representation = identity.get("transfer_representations")
        if isinstance(representation, str):
            observed_representations.add(representation)

    if require_complete_cross_product:
        _require(
            set(seen) == set(expected),
            (
                f"cross-product mismatch: missing={len(set(expected) - set(seen))} "
                f"extra={len(set(seen) - set(expected))}"
            ),
            errors,
        )
    _require(
        observed_representations == required_representations,
        "discovered representation coverage mismatch",
        errors,
    )
    conclusions = Counter(row.get("conclusion") for row in rows if isinstance(row, dict))
    _require(conclusions["unsupported"] > 0, "unsupported rows were omitted", errors)
    _require(conclusions["unknown"] > 0, "unknown rows were omitted", errors)
    _require(conclusions["accepted-live"] == 0, "unsanctioned accepted-live row", errors)

    if errors:
        preview = "\n".join(f"- {item}" for item in errors[:30])
        raise ValueError(f"matrix validation failed ({len(errors)} errors):\n{preview}")
    summary = {
        "valid": True,
        "row_count": len(rows),
        "scope_sha256": digest,
        "conclusions": dict(sorted(conclusions.items())),
        "representations": sorted(observed_representations),
    }
    print(json.dumps(summary, sort_keys=True))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("matrix", type=Path)
    parser.add_argument("--scope", required=True, type=Path)
    parser.add_argument("--require-complete-cross-product", action="store_true")
    parser.add_argument(
        "--reject-unresolved-precedence-conflicts", action="store_true"
    )
    args = parser.parse_args()
    validate(
        args.matrix,
        args.scope,
        require_complete_cross_product=args.require_complete_cross_product,
        reject_unresolved_precedence_conflicts=args.reject_unresolved_precedence_conflicts,
    )


if __name__ == "__main__":
    main()

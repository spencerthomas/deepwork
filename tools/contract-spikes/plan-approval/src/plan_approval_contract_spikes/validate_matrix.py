from __future__ import annotations

import argparse
import hashlib
import json
from itertools import product
from pathlib import Path
from typing import Any

from .catalog import ALLOWED_BLOCKERS, EXPECTED_CONCLUSION, SCENARIOS, TEMPLATES
from .errors import ContractViolation


REQUIRED_ROW_FIELDS = {
    "row_id",
    "template",
    "scenario",
    "evidence_tier",
    "upstream_status",
    "proposal_schema",
    "request_schema",
    "decision_schema",
    "resume_schema",
    "state_transitions",
    "side_effect_count_before_approval",
    "side_effect_count_after_resume",
    "recovery_result",
    "conclusion",
    "blocker",
    "fallback",
    "conflict",
}

RELEASED_SCENARIOS = {
    "approve_unchanged",
    "edit_then_approve",
    "explicit_restart_after_rejection",
    "reconnect_after_resume",
    "process_restart",
    "deployment_restart",
    "repeated_delivery",
    "retry_after_timeout",
}

BLOCKED_SCENARIOS = {
    "wrong_request",
    "wrong_plan",
    "wrong_task",
    "wrong_run",
    "wrong_actor",
    "stale_revision",
    "superseded_revision",
    "expired_actor",
    "cross_workspace_replay",
    "permission_widening",
    "side_effect_widening",
    "model_text_claims_approved",
    "tool_output_imitates_decision",
    "direct_resume",
    "config_template_drift",
    "cancellation_not_a_decision",
}


def _walk_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _walk_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_strings(item)


def validate(
    matrix: dict[str, Any],
    *,
    require_complete_cross_product: bool,
    reject_blocked_dependency_promotion: bool,
    reject_unresolved_precedence_conflicts: bool,
    evidence_root: Path | None = None,
) -> None:
    errors: list[str] = []
    rows = matrix.get("rows")
    if not isinstance(rows, list):
        raise ContractViolation("matrix rows must be a list")
    if matrix.get("templates") != list(TEMPLATES):
        errors.append("template catalog does not match the harness")
    if matrix.get("scenarios") != list(SCENARIOS):
        errors.append("scenario catalog does not match the harness")

    upstream = matrix.get("upstream_dependencies", [])
    upstream_by_gate = {item.get("gate"): item for item in upstream}
    for gate in ("SPIKE-HITL-001", "SPIKE-COMPOSE-001", "SPIKE-CONFIG-001"):
        item = upstream_by_gate.get(gate)
        if not item:
            errors.append(f"missing upstream dependency {gate}")
            continue
        if not item.get("artifact_commit") or not item.get("fixture_hash"):
            errors.append(f"unpinned upstream dependency {gate}")
        elif len(item["artifact_commit"]) != 40 or len(item["fixture_hash"]) != 64:
            errors.append(f"invalid upstream pin for {gate}")
        if item.get("status") == "accepted":
            errors.append(f"{gate} cannot be accepted on this dispatch base")

    targets = {item.get("gate"): item.get("status") for item in matrix.get("target_spikes", [])}
    for gate in ("SPIKE-PLAN-001", "SPIKE-HITL-002"):
        if gate not in targets:
            errors.append(f"missing target gate {gate}")
        elif targets[gate] in {"accepted", "complete", "passed"}:
            errors.append(f"{gate} must remain unaccepted")

    seen_ids: set[str] = set()
    seen_pairs: set[tuple[str, str]] = set()
    for index, row in enumerate(rows):
        missing = REQUIRED_ROW_FIELDS - set(row)
        if missing:
            errors.append(f"row {index} missing fields: {sorted(missing)}")
            continue
        row_id = row["row_id"]
        pair = (row["template"], row["scenario"])
        if row_id in seen_ids:
            errors.append(f"duplicate row identity {row_id}")
        if pair in seen_pairs:
            errors.append(f"duplicate template/scenario identity {pair}")
        seen_ids.add(row_id)
        seen_pairs.add(pair)
        if row["conclusion"] != EXPECTED_CONCLUSION:
            errors.append(f"{row_id} promotes unsupported conclusion")
        blockers = (
            {row["blocker"]} if isinstance(row["blocker"], str) else set(row["blocker"])
        )
        if not blockers or not blockers <= ALLOWED_BLOCKERS:
            errors.append(f"{row_id} has an invalid blocker")
        if not str(row["fallback"]).strip():
            errors.append(f"{row_id} is missing a fallback")
        if row["side_effect_count_before_approval"] != 0:
            errors.append(f"{row_id} reports a pre-approval side effect")
        if row["side_effect_count_after_resume"] not in {0, 1}:
            errors.append(f"{row_id} reports non-idempotent side effects")
        expected_effect_count = 1 if row["scenario"] in RELEASED_SCENARIOS else 0
        if row["side_effect_count_after_resume"] != expected_effect_count:
            errors.append(
                f"{row_id} has unexpected protected-effect count for its scenario"
            )
        if row["scenario"] in BLOCKED_SCENARIOS and not str(
            row.get("observed_result", "")
        ).startswith("blocked:"):
            errors.append(f"{row_id} did not fail closed")
        if row.get("state_transitions", []).count("protected_effect_released") != (
            expected_effect_count
        ):
            errors.append(f"{row_id} transition log contradicts its effect count")
        if row.get("contributes_only_to") != [
            "AC-DW-TASK-002-02",
            "AC-DW-QUAL-001-03",
        ]:
            errors.append(f"{row_id} claims an out-of-scope acceptance contribution")
        if row.get("end_to_end_contribution") is not False:
            errors.append(f"{row_id} claims end-to-end contribution")
        fallback = row.get("fallback")
        if not isinstance(fallback, dict) or fallback.get("planApproval") is not False:
            errors.append(f"{row_id} lacks the disabled capability fallback")
        if row.get("resume_schema", {}).get("provider_syntax_tested") is not False:
            errors.append(f"{row_id} claims provider resume evidence")
        fixture = row.get("fixture")
        if not isinstance(fixture, dict) or not fixture.get("path") or not fixture.get(
            "sha256"
        ):
            errors.append(f"{row_id} lacks a hashed fixture")
        elif evidence_root is not None:
            fixture_path = evidence_root / fixture["path"]
            if not fixture_path.is_file():
                errors.append(f"{row_id} fixture is missing")
            else:
                actual = hashlib.sha256(fixture_path.read_bytes()).hexdigest()
                if actual != fixture["sha256"]:
                    errors.append(f"{row_id} fixture hash does not match")
        normalized = {item.lower() for item in _walk_strings(row["decision_schema"])}
        if "cancel" in normalized or "cancellation" in normalized:
            errors.append(f"{row_id} treats cancellation as a normalized decision")
        if reject_blocked_dependency_promotion and row["upstream_status"] in {
            "blocked-live-evidence",
            "blocked-upstream-contract",
        } and row["conclusion"] != EXPECTED_CONCLUSION:
            errors.append(f"{row_id} promotes a blocked dependency")
        if reject_unresolved_precedence_conflicts and row["conflict"] not in {
            None,
            "none",
            "resolved-blocked",
        }:
            errors.append(f"{row_id} has an unresolved precedence conflict")

    if require_complete_cross_product:
        expected = set(product(TEMPLATES, SCENARIOS))
        missing_pairs = expected - seen_pairs
        extra_pairs = seen_pairs - expected
        if missing_pairs:
            errors.append(f"missing {len(missing_pairs)} template/scenario rows")
        if extra_pairs:
            errors.append(f"unexpected template/scenario rows: {sorted(extra_pairs)}")

    manifest = matrix.get("fixture_manifest")
    if not isinstance(manifest, dict) or not manifest.get("path") or not manifest.get(
        "sha256"
    ):
        errors.append("fixture manifest is not pinned")
    elif evidence_root is not None:
        manifest_path = evidence_root / manifest["path"]
        if not manifest_path.is_file():
            errors.append("fixture manifest is missing")
        elif hashlib.sha256(manifest_path.read_bytes()).hexdigest() != manifest["sha256"]:
            errors.append("fixture manifest hash does not match")

    if errors:
        raise ContractViolation("\n".join(errors))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("matrix", type=Path)
    parser.add_argument("--require-complete-cross-product", action="store_true")
    parser.add_argument("--reject-blocked-dependency-promotion", action="store_true")
    parser.add_argument("--reject-unresolved-precedence-conflicts", action="store_true")
    args = parser.parse_args()
    matrix = json.loads(args.matrix.read_text(encoding="utf-8"))
    validate(
        matrix,
        require_complete_cross_product=args.require_complete_cross_product,
        reject_blocked_dependency_promotion=args.reject_blocked_dependency_promotion,
        reject_unresolved_precedence_conflicts=args.reject_unresolved_precedence_conflicts,
        evidence_root=args.matrix.parent,
    )
    print(f"validated {len(matrix['rows'])} offline matrix rows")


if __name__ == "__main__":
    main()

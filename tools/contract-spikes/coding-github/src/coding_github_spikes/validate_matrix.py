"""Validate completeness, evidence precedence, and mutation limits."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from coding_github_spikes.catalog import canonical_hash


class ValidationError(ValueError):
    pass


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def validate(matrix: dict, scope: dict, upstream: dict, fixtures_root: Path) -> None:
    unhashed = dict(scope)
    observed_hash = unhashed.pop("scope_hash", None)
    if observed_hash != canonical_hash(unhashed):
        raise ValidationError("scope hash mismatch")
    if matrix.get("scope_hash") != observed_hash:
        raise ValidationError("matrix scope hash mismatch")
    rows = matrix.get("rows", [])
    by_id = {row.get("id"): row for row in rows}
    required = set(scope["required_rows"])
    if set(by_id) != required or len(rows) != len(required):
        missing = sorted(required - set(by_id))
        extra = sorted(set(by_id) - required)
        raise ValidationError(f"row cross-product mismatch; missing={missing}, extra={extra}")
    if matrix.get("matrix_hash") != canonical_hash(rows):
        raise ValidationError("matrix hash mismatch")
    allowed_states = {"accepted-live", "blocked-live-evidence", "rejected", "unknown"}
    for item in rows:
        if item["state"] not in allowed_states:
            raise ValidationError(f"{item['id']}: invalid state")
        if item["evidence_tier"] != "accepted-live" and item["state"] == "accepted-live":
            raise ValidationError(f"{item['id']}: non-live evidence promoted")
        if not item.get("fallback") or not item.get("owner"):
            raise ValidationError(f"{item['id']}: fallback/owner missing")
        if item.get("contradiction"):
            raise ValidationError(f"{item['id']}: unresolved precedence conflict")
    if upstream.get("state") != "accepted-live":
        promoted = [row["id"] for row in rows if row["state"] == "accepted-live"]
        if promoted:
            raise ValidationError(f"blocked dependency promoted: {promoted}")
    if scope["mutation_budget"]["draft_pull_requests"] != 1:
        raise ValidationError("draft PR budget must equal one")
    forbidden = ("ready", "reviews", "approvals", "workflow_reruns", "workflow_cancels", "merges", "force_pushes", "deployments")
    if any(scope["mutation_budget"][key] != 0 for key in forbidden):
        raise ValidationError("forbidden mutation budget is nonzero")
    if scope["app_permissions"].get("workflows") == "write":
        raise ValidationError("excessive workflow permission")
    expected_fixtures = set(scope["required_fixtures"])
    present = {path.stem for path in fixtures_root.glob("*.json")} - {"manifest"}
    if not expected_fixtures.issubset(present):
        raise ValidationError(f"missing fixtures: {sorted(expected_fixtures - present)}")
    if not any(row["id"] == "ci.merge-timeout-reconciliation-no-second-request" for row in rows):
        raise ValidationError("merge timeout contract row absent")
    for workflow_row in ("ci.workflow-rerun-contract-no-mutation", "ci.workflow-cancel-contract-no-mutation"):
        if workflow_row not in by_id:
            raise ValidationError(f"{workflow_row}: absent")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("matrix", type=Path)
    parser.add_argument("--scope", required=True, type=Path)
    parser.add_argument("--upstream-lock", required=True, type=Path)
    parser.add_argument("--require-complete-cross-product", action="store_true")
    parser.add_argument("--require-workflow-and-merge-timeout-fixtures", action="store_true")
    parser.add_argument("--max-draft-prs", type=int, required=True)
    parser.add_argument("--reject-blocked-dependency-promotion", action="store_true")
    parser.add_argument("--reject-unresolved-precedence-conflicts", action="store_true")
    args = parser.parse_args()
    if args.max_draft_prs != 1:
        raise ValidationError("CLI max draft PRs must equal one")
    validate(
        load(args.matrix),
        load(args.scope),
        load(args.upstream_lock),
        args.matrix.parent / "fixtures",
    )
    print("matrix valid: complete; live rows blocked; draft PR budget=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


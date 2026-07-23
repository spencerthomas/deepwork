"""Validate completeness, evidence precedence, and mutation limits."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from coding_github_spikes.catalog import FIXTURES, canonical_hash


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
        prefix, operation = item["id"].split(".", 1)
        if item.get("schema_hash") != canonical_hash({"prefix": prefix, "operation": operation}):
            raise ValidationError(f"{item['id']}: row schema hash mismatch")
        evidence = item.get("evidence")
        sources = [evidence] if isinstance(evidence, str) else evidence
        if (
            not isinstance(sources, list)
            or not sources
            or not all(isinstance(source, str) and source for source in sources)
        ):
            raise ValidationError(f"{item['id']}: evidence must be a non-empty ordered source list")
        for source in sources:
            if source.startswith("fixtures/"):
                evidence_path = fixtures_root.parent / source
                if not evidence_path.is_file():
                    raise ValidationError(f"{item['id']}: fixture evidence missing")
                if item["evidence_tier"] != "deterministic-fake":
                    raise ValidationError(f"{item['id']}: fixture tier mismatch")
            elif not source.startswith("https://docs.github.com/"):
                raise ValidationError(f"{item['id']}: unsupported evidence source")
    if upstream.get("state") != "accepted-live":
        promoted = [row["id"] for row in rows if row["state"] == "accepted-live"]
        if promoted:
            raise ValidationError(f"blocked dependency promoted: {promoted}")
        if upstream.get("reviewed_commit") is not None or any(upstream.get("hashes", {}).values()):
            raise ValidationError("blocked upstream contains unaccepted reviewed hashes")
    else:
        hashes = upstream.get("hashes", {})
        if (
            upstream.get("review_verdict") != "accepted"
            or not upstream.get("reviewed_commit")
            or not all(hashes.get(name) for name in ("matrix_scope", "matrix", "versions", "fixtures"))
            or not upstream.get("consumed_rows")
        ):
            raise ValidationError("accepted upstream lock is incomplete")
    if scope["mutation_budget"]["draft_pull_requests"] != 1:
        raise ValidationError("draft PR budget must equal one")
    forbidden = ("ready", "reviews", "approvals", "workflow_reruns", "workflow_cancels", "merges", "force_pushes", "deployments")
    if any(scope["mutation_budget"][key] != 0 for key in forbidden):
        raise ValidationError("forbidden mutation budget is nonzero")
    exact_permissions = {
        "actions": "read",
        "checks": "read",
        "contents": "write",
        "metadata": "read",
        "pull_requests": "write",
    }
    if scope.get("app_permissions") != exact_permissions:
        raise ValidationError("GitHub App permissions differ from reviewed minimum")
    exact_forbidden = ["administration", "members", "secrets", "workflows:write"]
    if scope.get("forbidden_permissions") != exact_forbidden:
        raise ValidationError("forbidden permission ceiling changed")
    expected_fixtures = set(scope["required_fixtures"])
    if expected_fixtures != set(FIXTURES):
        raise ValidationError("required fixture scope changed")
    present = {path.stem for path in fixtures_root.glob("*.json")} - {"manifest"}
    if expected_fixtures != present:
        raise ValidationError(
            f"fixture set mismatch: missing={sorted(expected_fixtures - present)}, "
            f"extra={sorted(present - expected_fixtures)}"
        )
    manifest = load(fixtures_root / "manifest.json")
    if set(manifest.get("fixtures", [])) != expected_fixtures:
        raise ValidationError("fixture manifest membership mismatch")
    for name in sorted(expected_fixtures):
        value = load(fixtures_root / f"{name}.json")
        if (
            value.get("fixture_id") != name
            or value.get("deterministic") is not True
            or value.get("network") != "denied"
            or value.get("credentials") != "none"
            or not isinstance(value.get("input"), dict)
            or not isinstance(value.get("expected"), dict)
        ):
            raise ValidationError(f"{name}: fixture semantics incomplete")
        if manifest.get("hashes", {}).get(name) != canonical_hash(value):
            raise ValidationError(f"{name}: manifest hash mismatch")
    required_schemas = {
        "installation",
        "repository-ref",
        "proxy-intent",
        "pull-request",
        "ci",
        "webhook",
        "mutation-ledger",
        "evidence",
    }
    schemas_root = fixtures_root.parent / "schemas"
    for name in required_schemas:
        schema = load(schemas_root / f"{name}.schema.json")
        if schema.get("type") != "object" or not schema.get("required"):
            raise ValidationError(f"{name}: schema missing or incomplete")
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
    required_flags = (
        args.require_complete_cross_product,
        args.require_workflow_and_merge_timeout_fixtures,
        args.reject_blocked_dependency_promotion,
        args.reject_unresolved_precedence_conflicts,
    )
    if not all(required_flags):
        raise ValidationError("all strict validator flags are required")
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

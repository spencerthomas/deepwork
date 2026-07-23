"""Validate the sanitized live ledger, even when live execution was not run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ZERO_MUTATIONS = (
    "ready_mutations",
    "review_mutations",
    "approval_mutations",
    "workflow_mutations",
    "workflow_cancel_mutations",
    "merge_mutations",
    "force_push_mutations",
    "branch_delete_mutations",
    "deployment_mutations",
)


def validate_ledger(value: dict, *, max_draft_prs: int, require_draft: bool, forbid_merge: bool) -> None:
    state = value.get("state")
    attempts = value.get("draft_pr_create_attempts")
    identities = value.get("draft_pr_identities")
    if not isinstance(attempts, int) or attempts < 0 or attempts > max_draft_prs:
        raise ValueError("draft PR create-attempt budget exceeded")
    if not isinstance(identities, list) or len(identities) > max_draft_prs:
        raise ValueError("draft PR identity budget exceeded")
    for field in ZERO_MUTATIONS:
        if value.get(field, 0) != 0:
            raise ValueError(f"forbidden mutation recorded: {field}")
    if forbid_merge and value.get("merge_mutations", 0):
        raise ValueError("merge mutation recorded")
    if state == "not-run":
        if attempts or identities:
            raise ValueError("not-run ledger cannot contain an attempt or PR")
        return
    if state == "ambiguous":
        if attempts != 1 or identities or value.get("mutation_budget_spent") is not True:
            raise ValueError("ambiguous create must spend the sole budget without an identity")
        return
    if state not in {"created", "reconciled"}:
        raise ValueError("invalid live ledger state")
    if attempts != 1 or len(identities) != 1:
        raise ValueError("live ledger must contain exactly one attempt and identity")
    pr = value.get("pull_request")
    if not isinstance(pr, dict):
        raise ValueError("pull request tuple missing")
    if require_draft and pr.get("draft") is not True:
        raise ValueError("pull request is not draft")
    required = ("node_id", "number", "base_ref", "base_sha", "head_ref", "head_sha")
    if not all(pr.get(field) for field in required):
        raise ValueError("pull request identity/base/head tuple incomplete")
    if pr["node_id"] != identities[0]:
        raise ValueError("pull request identity mismatch")
    for field in ("grant_hash", "repository_binding_hash"):
        if not isinstance(value.get(field), str) or not value[field].startswith("sha256:"):
            raise ValueError(f"{field} missing")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ledger", type=Path)
    parser.add_argument("--max-draft-prs", type=int, required=True)
    parser.add_argument("--require-draft", action="store_true")
    parser.add_argument("--forbid-merge", action="store_true")
    args = parser.parse_args()
    value = json.loads(args.ledger.read_text())
    try:
        validate_ledger(
            value,
            max_draft_prs=args.max_draft_prs,
            require_draft=args.require_draft,
            forbid_merge=args.forbid_merge,
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    print("live ledger valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

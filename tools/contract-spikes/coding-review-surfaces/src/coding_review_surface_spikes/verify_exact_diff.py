"""Fail-closed verifier for an opt-in live exact-diff evidence directory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from coding_review_surface_spikes.contracts import exact_diff_errors, validate_upstream_lock


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence_dir", type=Path)
    parser.add_argument("--upstream-lock", type=Path, required=True)
    args = parser.parse_args()
    upstream = json.loads(args.upstream_lock.read_text(encoding="utf-8"))
    errors = validate_upstream_lock(upstream)
    dependencies = upstream.get("dependencies", [])
    accepted = bool(dependencies) and all(
        item.get("review_verdict") == "accepted" and item.get("consumable") is True
        for item in dependencies
    )
    read_grant = upstream.get("current_read_grant", {})
    if (
        errors
        or not accepted
        or upstream.get("live_profile_allowed") is not True
        or read_grant.get("present") is not True
        or not read_grant.get("grant_hash")
    ):
        print("live exact-diff verification blocked by unaccepted upstream evidence")
        return 1
    document_path = args.evidence_dir / "exact-diff.json"
    patch_path = args.evidence_dir / "exact-review.patch"
    if not document_path.is_file() or not patch_path.is_file():
        print("live exact-diff evidence is incomplete")
        return 1
    document = json.loads(document_path.read_text(encoding="utf-8"))
    errors = exact_diff_errors(document, patch_path.read_bytes())
    if errors:
        for error in errors:
            print(error)
        return 1
    print("verified live exact diff")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

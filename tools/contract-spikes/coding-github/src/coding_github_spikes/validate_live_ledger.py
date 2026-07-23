"""Validate the sanitized live ledger, even when live execution was not run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ledger", type=Path)
    parser.add_argument("--max-draft-prs", type=int, required=True)
    parser.add_argument("--require-draft", action="store_true")
    parser.add_argument("--forbid-merge", action="store_true")
    args = parser.parse_args()
    value = json.loads(args.ledger.read_text())
    identities = value.get("draft_pr_identities", [])
    if len(identities) > args.max_draft_prs:
        raise SystemExit("draft PR identity budget exceeded")
    if args.forbid_merge and value.get("merge_mutations", 0):
        raise SystemExit("merge mutation recorded")
    if value.get("state") == "not-run" and identities:
        raise SystemExit("not-run ledger cannot contain a PR")
    print("live ledger valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


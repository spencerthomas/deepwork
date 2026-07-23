"""Emit a sanitized inventory of installed and generated public contracts."""

from __future__ import annotations

import argparse
import json
import platform
from datetime import UTC, datetime
from pathlib import Path

SOURCE_REVISIONS = {
    "SRC-LC": "7b9215d708e0b57e6fbae7b5d0762c4118b8e309",
    "SRC-DA": "7794b61a6e76230e8c7a49bdce808b3728305914",
    "SRC-LCPY": "592055e15e138f5369dce95dd049ce22430996e2",
    "SRC-LG": "31f90df3e6b0268fa77fd2d118a917d420b84a68",
}


def build_inventory() -> dict[str, object]:
    candidate_versions = {
        "deepagents": "0.6.12",
        "langchain": "1.3.14",
        "langgraph": "1.2.9",
        "langgraph-sdk": "0.4.2",
    }
    return {
        "schema_version": "1.0",
        "collected_at": datetime.now(UTC).date().isoformat(),
        "interpreter": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
        },
        "packages": {
            "status": "blocked-package-index-evidence",
            "candidate_versions_from_pinned_sources": candidate_versions,
            "installed_public_distributions": {},
            "blocker": "Public package-index egress was not authorized; pinned source candidates were not promoted to installed public contracts.",
        },
        "source_revisions": SOURCE_REVISIONS,
        "generated_contracts": {
            "agent_server_openapi": {
                "contract_version": "0.1.0",
                "source_revision": SOURCE_REVISIONS["SRC-LC"],
                "sha256": "0b4d3d1e2da065a50a53838e7f63f5d90763a1dc759b165dd7a4409b5959888c",
            }
        },
        "live_context": {
            "server_revision": None,
            "sdk": None,
            "candidate_sdk_from_pinned_source": candidate_versions["langgraph-sdk"],
            "account_tier": None,
            "region": None,
            "authentication_context": None,
            "status": "blocked-live-evidence",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    inventory = build_inventory()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote sanitized package inventory to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

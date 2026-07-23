"""Write a bounded, scrubbed runtime and evidence inventory."""

from __future__ import annotations

import argparse
import platform
import subprocess
from datetime import date
from pathlib import Path

from .common import BLOCKED_UPSTREAM, dump_json


def _uv_version() -> str:
    result = subprocess.run(
        ["uv", "--version"],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = {
        "schema_version": "dw.research-writing-versions.v1",
        "observed_date": date.today().isoformat(),
        "python": platform.python_version(),
        "uv": _uv_version(),
        "offline_project": {
            "dependencies": [],
            "network_policy": "python-process-audit-hook-plus-test-assertions",
            "test_runner": "stdlib-unittest",
            "lock_mode": "frozen-offline",
            "proof_limit": "Deep Work normalization only; not Deep Agents behavior",
        },
        "installed_public": {
            "state": "blocked-package-index-evidence",
            "lock_created": False,
            "commands_run": False,
            "required_public_exports": [
                "deepagents.create_deep_agent",
                "deepagents.RubricMiddleware",
                "deepagents.SubAgent",
                "deepagents.SubAgentMiddleware",
            ],
            "versions": None,
            "file_hashes": None,
        },
        "classic_sandbox": {
            "state": "blocked-live-evidence",
            "account_tier": None,
            "region": None,
            "server_version": None,
            "auth_context": None,
            "synthetic_data_only": True,
        },
        "upstream_artifacts": {
            spike: {
                "state": "blocked-live-evidence",
                "reviewed_head": "758c1d4a2230b7c4261fcfbd0f3008634509e096",
            }
            for spike in BLOCKED_UPSTREAM
        },
        "pinned_sources": {
            "SRC-LC": "7b9215d708e0b57e6fbae7b5d0762c4118b8e309",
            "SRC-DA": "7794b61a6e76230e8c7a49bdce808b3728305914",
            "SRC-LCPY": "592055e15e138f5369dce95dd049ce22430996e2",
            "SRC-LG": "31f90df3e6b0268fa77fd2d118a917d420b84a68",
        },
        "public_export_source_blobs": {
            "deepagents.__init__": "e4f49a7bfb606bd208212f5c28a9f41d9e87ee33",
            "middleware.rubric": "44ca2fc1a0cdcf72b53eb20b5529f21cfcacc21d",
            "middleware.subagents": "0ba32e11490f24f13b3c11c08235499522c88f06",
        },
        "reference_examples": [
            {
                "path": "examples/deep_research",
                "tree": "221c48af3799b2f1ddf30da38c123782fe43d08d",
                "starter_contract_state": "blocked-not-a-deep-work-starter-contract",
            },
            {
                "path": "examples/deploy-content-writer",
                "tree": "1092e58bced52dc204184273f30f8a7244874158",
                "starter_contract_state": "blocked-not-a-deep-work-starter-contract",
            },
        ],
        "e2e_ids_credited": [],
        "excluded_acceptance_ids": ["AC-DW-TASK-005-04"],
    }
    dump_json(Path(args.output), result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

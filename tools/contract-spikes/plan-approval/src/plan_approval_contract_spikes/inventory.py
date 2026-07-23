from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
import subprocess
from pathlib import Path

from .catalog import SCENARIOS, TEMPLATES
from .generate_evidence import UPSTREAM, UPSTREAM_COMMIT


SOURCE_REVISIONS = {
    "SRC-LC": "7b9215d708e0b57e6fbae7b5d0762c4118b8e309",
    "SRC-DA": "7794b61a6e76230e8c7a49bdce808b3728305914",
    "SRC-LCPY": "592055e15e138f5369dce95dd049ce22430996e2",
    "SRC-LG": "31f90df3e6b0268fa77fd2d118a917d420b84a68",
}


def _command_version(command: list[str]) -> str:
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return result.stdout.strip().splitlines()[0]


def build_inventory() -> dict[str, object]:
    return {
        "schema_version": "plan-approval-inventory.v1",
        "evidence_class": "deterministic-offline-harness",
        "collected_at": "2026-07-23",
        "packet": {
            "base_commit": "fff1bfd278d550d01de6e8d74f553f45c4003a8c",
            "seed_commit": "886f6b12d812b1e34df2e45da3d839a0853d72e8",
        },
        "python": platform.python_version(),
        "uv": _command_version(["uv", "--version"]),
        "pytest": importlib.metadata.version("pytest"),
        "package": importlib.metadata.version("plan-approval-contract-spikes"),
        "starter_templates": [
            {
                "template": template,
                "template_version": "synthetic-v1",
                "config_version": "synthetic-v1",
                "source": "deterministic-fake",
            }
            for template in TEMPLATES
        ],
        "scenario_catalog": list(SCENARIOS),
        "source_revisions": SOURCE_REVISIONS,
        "upstream_provenance": {
            "integrated": False,
            "research_commit": UPSTREAM_COMMIT,
            "artifacts": [
                {
                    "gate": gate,
                    "path": path,
                    "sha256": fixture_hash,
                    "status": "provenance-only-blocked-live-evidence",
                }
                for gate, path, fixture_hash in UPSTREAM
            ],
        },
        "upstream_contracts": [
            {
                "gate": gate,
                "status": "blocked-live-evidence",
                "accepted_artifact": None,
            }
            for gate in ("SPIKE-HITL-001", "SPIKE-COMPOSE-001", "SPIKE-CONFIG-001")
        ],
        "runtime": {
            "server": None,
            "account_tier": None,
            "region": None,
            "live_profile": None,
            "status": "not-run-no-sanctioned-sandbox",
        },
        "installed_public_generated_contracts": {
            "status": "not-present-on-offline-base",
            "distributions": {},
        },
        "target_gates": [
            {"gate": "SPIKE-PLAN-001", "status": "unaccepted"},
            {"gate": "SPIKE-HITL-002", "status": "unaccepted"},
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(build_inventory(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import socket
import tempfile

from .catalog import EXPECTED_CONCLUSION, SCENARIOS, TEMPLATES
from .scenarios import run_scenario


UPSTREAM_COMMIT = "758c1d4a2230b7c4261fcfbd0f3008634509e096"
UPSTREAM = (
    (
        "SPIKE-HITL-001",
        "docs/references/research/langchain-contract-spikes/fixtures/hitl-ordered-batch.json",
        "bcbb3f0e0e5cd745795e3687271f03e0a91061089841aa4f22837f08c18b062d",
    ),
    (
        "SPIKE-COMPOSE-001",
        "docs/references/research/langchain-contract-spikes/matrix.json",
        "682241e63d76f8507b41efec38f5d4b911704a27f951b3c40d9639c7adc93629",
    ),
    (
        "SPIKE-CONFIG-001",
        "docs/references/research/langchain-contract-spikes/matrix.json",
        "682241e63d76f8507b41efec38f5d4b911704a27f951b3c40d9639c7adc93629",
    ),
)


def _write_json(path: Path, value: object) -> str:
    content = json.dumps(value, indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return hashlib.sha256(content.encode()).hexdigest()


def build_evidence(output_dir: Path) -> dict[str, object]:
    fixture_dir = output_dir / "fixtures"
    fixture_entries: list[dict[str, object]] = []
    rows: list[dict[str, object]] = []

    original_create_connection = socket.create_connection
    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex

    def blocked_network(*_args, **_kwargs):
        raise RuntimeError("network access is denied in deterministic evidence generation")

    socket.create_connection = blocked_network
    socket.socket.connect = blocked_network
    socket.socket.connect_ex = blocked_network
    try:
        with tempfile.TemporaryDirectory(prefix="plan-approval-offline-") as temporary:
            temporary_root = Path(temporary)
            template_results = {
                template: [
                    run_scenario(
                        template,
                        scenario,
                        temporary_root / template / f"{scenario}.jsonl",
                    )
                    for scenario in SCENARIOS
                ]
                for template in TEMPLATES
            }
    finally:
        socket.create_connection = original_create_connection
        socket.socket.connect = original_connect
        socket.socket.connect_ex = original_connect_ex

    for template, results in template_results.items():
            fixture_path = fixture_dir / f"{template}-offline.json"
            fixture_hash = _write_json(
                fixture_path,
                {
                    "schema_version": "plan-approval-transcript.v1",
                    "evidence_class": "deterministic-offline-fake",
                    "network": "denied",
                    "provider_resume": "not-implemented-or-invoked",
                    "template": template,
                    "template_version": "synthetic-v1",
                    "config_version": "synthetic-v1",
                    "scenarios": results,
                },
            )
            relative_fixture = f"fixtures/{fixture_path.name}"
            fixture_entries.append(
                {
                    "path": relative_fixture,
                    "sha256": fixture_hash,
                    "scenario_count": len(results),
                }
            )

            for result in results:
                rows.append(
                    {
                        "row_id": f"offline-{template}-{result['scenario']}",
                        "template": template,
                        "scenario": result["scenario"],
                        "evidence_tier": "deterministic-fake",
                        "exact_versions": {
                            "template": "synthetic-v1",
                            "config": "synthetic-v1",
                            "proposal_schema": "plan-proposal.v1",
                        },
                        "upstream_status": "blocked-upstream-contract",
                        "upstream_artifact_commit": UPSTREAM_COMMIT,
                        "proposal_schema": {
                            "identity": [
                                "plan_id",
                                "schema_version",
                                "template_id",
                                "template_version",
                                "config_version",
                                "created_at",
                                "workspace_id",
                                "actor_id",
                                "task_id",
                                "run_id",
                                "request_id",
                                "revision",
                            ],
                            "ordered_steps": True,
                            "permission_and_side_effect_boundary": True,
                        },
                        "request_schema": {
                            "owner": "SPIKE-HITL-001",
                            "correlation_only": [
                                "workspace_id",
                                "actor_id",
                                "task_id",
                                "run_id",
                                "request_id",
                                "plan_id",
                                "revision",
                            ],
                        },
                        "decision_schema": {
                            "owner": "SPIKE-HITL-001",
                            "consumed_values": ["approve", "edit", "reject", "respond"],
                            "plan_specific_checks": [
                                "identity",
                                "revision",
                                "current_actor_authority",
                                "non_widening_boundary",
                            ],
                        },
                        "resume_schema": {
                            "provider_owner": "SPIKE-HITL-001",
                            "provider_syntax_tested": False,
                            "local_release_idempotency_only": True,
                        },
                        "state_transitions": result["state_transitions"],
                        "side_effect_count_before_approval": result[
                            "side_effect_count_before_approval"
                        ],
                        "side_effect_count_after_resume": result[
                            "side_effect_count_after_resume"
                        ],
                        "recovery_result": result["recovery_result"],
                        "observed_result": result["observed_result"],
                        "fixture": {
                            "path": relative_fixture,
                            "sha256": fixture_hash,
                        },
                        "conclusion": EXPECTED_CONCLUSION,
                        "blocker": [
                            "blocked-upstream-contract",
                            "blocked-live-evidence",
                        ],
                        "fallback": {
                            "planApproval": False,
                            "reason": "blocked_upstream_contract_and_live_evidence",
                            "draftPreserved": True,
                            "textOnlyDispatchAvailable": True,
                        },
                        "conflict": "resolved-blocked",
                        "contributes_only_to": [
                            "AC-DW-TASK-002-02",
                            "AC-DW-QUAL-001-03",
                        ],
                        "end_to_end_contribution": False,
                    }
                )

    manifest_hash = _write_json(
        fixture_dir / "manifest.json",
        {
            "schema_version": "plan-approval-fixture-manifest.v1",
            "evidence_class": "deterministic-offline-fake",
            "fixtures": fixture_entries,
        },
    )
    matrix = {
        "schema_version": "plan-approval-matrix.v1",
        "evidence_class": "deterministic-offline-harness",
        "templates": list(TEMPLATES),
        "scenarios": list(SCENARIOS),
        "upstream_dependencies": [
            {
                "gate": gate,
                "status": "blocked-live-evidence",
                "artifact_commit": UPSTREAM_COMMIT,
                "artifact_path": path,
                "fixture_hash": fixture_hash,
            }
            for gate, path, fixture_hash in UPSTREAM
        ],
        "target_spikes": [
            {"gate": "SPIKE-PLAN-001", "status": "unaccepted"},
            {"gate": "SPIKE-HITL-002", "status": "unaccepted"},
        ],
        "fixture_manifest": {
            "path": "fixtures/manifest.json",
            "sha256": manifest_hash,
        },
        "rows": rows,
    }
    _write_json(output_dir / "matrix.json", matrix)
    return matrix


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    matrix = build_evidence(args.output_dir)
    print(f"generated {len(matrix['rows'])} deterministic offline rows")


if __name__ == "__main__":
    main()

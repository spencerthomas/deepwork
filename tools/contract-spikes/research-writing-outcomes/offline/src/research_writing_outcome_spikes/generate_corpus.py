"""Generate the deterministic retained corpus from closed, local fixtures."""

from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path
from typing import Any

from .common import IDENTITY_FIELDS, STREAMS, canonical_json, dump_json, sha256_bytes
from .validate_matrix import REQUIRED_CAPABILITIES, SUBSTITUTION_DIMENSIONS


IDENTITY = {
    "tenant_id": "tenant-synthetic-01",
    "workspace_id": "workspace-synthetic-01",
    "source_id": "source-fake-normalizer-v1",
    "actor_id": "actor-synthetic-reviewer",
    "task_id": "task-outcome-contract-001",
    "run_id": "run-outcome-contract-001",
    "attempt_id": "attempt-001",
}

ACCEPTANCE_BY_STREAM = {
    "artifact": ["AC-DW-TASK-005-02"],
    "subagent": ["AC-DW-TASK-005-03"],
    "rubric": [
        "AC-DW-HITL-002-01",
        "AC-DW-HITL-002-02",
        "AC-DW-HITL-002-04",
    ],
    "verification": [
        "AC-DW-TASK-005-01",
        "AC-DW-HITL-002-01",
        "AC-DW-HITL-002-02",
        "AC-DW-HITL-002-03",
        "AC-DW-HITL-002-04",
    ],
}

BLOCKED_LIVE_ARTIFACT = {
    "access",
    "range_size",
    "expiry_revocation",
    "retention_deletion",
    "unavailable_stale",
}
BLOCKED_PUBLIC = {
    ("subagent", "spawn_discover"),
    ("subagent", "parent_attribution"),
    ("subagent", "terminal_states"),
    ("rubric", "immutable_ordered_rubric"),
    ("rubric", "interrupt"),
}


def schema(title: str, properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"https://schemas.example.invalid/deepwork/{title}.v1.json",
        "title": title,
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": required,
    }


def identity_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            field: {"type": "string", "minLength": 1} for field in IDENTITY_FIELDS
        },
        "required": list(IDENTITY_FIELDS),
    }


def write_schemas(root: Path) -> None:
    string = {"type": "string", "minLength": 1}
    schemas = {
        "artifact.schema.json": schema(
            "artifact",
            {
                "schema_version": {"const": "dw.artifact.v1"},
                "identity": identity_schema(),
                "artifact_id": string,
                "version": string,
                "state": {"enum": ["working", "promoted", "expired", "revoked", "deleted", "unavailable"]},
                "content_hash": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
                "evidence_id": string,
            },
            ["schema_version", "identity", "artifact_id", "version", "state", "content_hash", "evidence_id"],
        ),
        "subagent.schema.json": schema(
            "subagent",
            {
                "schema_version": {"const": "dw.subagent-event.v1"},
                "identity": identity_schema(),
                "subagent_id": string,
                "namespace": string,
                "sequence": {"type": "integer", "minimum": 0},
                "state": {"enum": ["spawned", "progress", "completed", "failed", "cancelled", "reconnected", "unknown"]},
                "display_summary": {"type": "string", "maxLength": 240},
                "evidence_id": string,
            },
            ["schema_version", "identity", "subagent_id", "namespace", "sequence", "state", "display_summary", "evidence_id"],
        ),
        "rubric.schema.json": schema(
            "rubric",
            {
                "schema_version": {"const": "dw.rubric.v1"},
                "identity": identity_schema(),
                "rubric_id": string,
                "version": string,
                "criteria": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "criterion_id": string,
                            "order": {"type": "integer", "minimum": 0},
                            "semantics": {"enum": ["required", "advisory"]},
                            "state": {"enum": ["pass", "fail", "uncertain", "not_evaluated"]},
                            "evidence_refs": {"type": "array", "items": string},
                        },
                        "required": ["criterion_id", "order", "semantics", "state", "evidence_refs"],
                    },
                },
            },
            ["schema_version", "identity", "rubric_id", "version", "criteria"],
        ),
        "verdict.schema.json": schema(
            "verdict",
            {
                "schema_version": {"const": "dw.verdict.v1"},
                "identity": identity_schema(),
                "verdict_id": string,
                "template_id": string,
                "rubric_version": string,
                "candidate_hash": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
                "evidence_versions": {"type": "object", "additionalProperties": {"type": "string"}},
                "state": {"enum": ["passed", "failed", "unsupported", "manually_reviewed", "cancelled", "capped"]},
                "display_rationale": {"type": "string", "maxLength": 240},
            },
            ["schema_version", "identity", "verdict_id", "template_id", "rubric_version", "candidate_hash", "evidence_versions", "state", "display_rationale"],
        ),
        "cross-reference.schema.json": schema(
            "cross-reference",
            {
                "schema_version": {"const": "dw.cross-reference.v1"},
                "identity": identity_schema(),
                "artifact_id": string,
                "subagent_id": string,
                "criterion_id": string,
                "evidence_id": string,
                "candidate_hash": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
                "verdict_id": string,
            },
            ["schema_version", "identity", "artifact_id", "subagent_id", "criterion_id", "evidence_id", "candidate_hash", "verdict_id"],
        ),
    }
    for name, value in schemas.items():
        dump_json(root / "schemas" / name, value)


def fixture_evidence(root: Path) -> list[dict[str, Any]]:
    research_body = b"Synthetic report: claim A is supported; claim B remains unresolved.\n"
    writing_body = b"Synthetic final deliverable.\n"
    fixtures = {
        "research-transcript.json": {
            "schema_version": "dw.fixture.research.v1",
            "identity": IDENTITY,
            "template_id": "research-v1",
            "model_output": "Everything passed.",
            "report": {
                "candidate_hash": sha256_bytes(research_body),
                "claims": [
                    {"claim_id": "claim-a", "state": "supported", "evidence_id": "ev-citation-valid"},
                    {"claim_id": "claim-b", "state": "unresolved", "evidence_id": None},
                ],
            },
            "citation_cases": [
                {"case": "valid", "evidence_id": "ev-citation-valid", "state": "valid"},
                {"case": "missing", "evidence_id": "ev-citation-missing", "state": "missing"},
                {"case": "unreachable", "evidence_id": "ev-citation-unreachable", "state": "invalid"},
                {"case": "mismatched", "evidence_id": "ev-citation-mismatched", "state": "invalid"},
                {"case": "fabricated", "evidence_id": "ev-citation-fabricated", "state": "invalid"},
            ],
            "expected_verdict": "failed",
            "truth_limit": "Citation presence does not establish factual truth.",
        },
        "writing-transcript.json": {
            "schema_version": "dw.fixture.writing.v1",
            "identity": IDENTITY,
            "template_id": "writing-v1",
            "model_output": "Everything passed.",
            "working_file": {
                "artifact_id": "working-draft-01",
                "state": "working",
                "content_hash": sha256_bytes(b"Synthetic draft.\n"),
            },
            "promotion": {
                "artifact_id": "artifact-final-01",
                "state": "promoted",
                "content_hash": sha256_bytes(writing_body),
                "attestation_id": "promotion-001",
            },
            "negative_cases": ["missing", "empty", "stale", "working-only"],
            "expected_verdict": "failed-without-promoted-final",
        },
        "coding-negative-transcript.json": {
            "schema_version": "dw.fixture.coding-negative.v1",
            "identity": IDENTITY,
            "template_id": "coding-negative-only-v1",
            "model_output": "Everything passed.",
            "test_evidence": {"evidence_id": "ev-test-failed", "state": "fail", "exit_status": 1},
            "expected_verdict": "failed",
            "scope_limit": "Evidence-binding negative only; no coding journey credit.",
        },
        "artifact-manifest.json": {
            "schema_version": "dw.fixture.artifact-manifest.v1",
            "identity": IDENTITY,
            "working": {
                "artifact_id": "working-draft-01",
                "version": "working-v1",
                "content_hash": sha256_bytes(b"Synthetic draft.\n"),
                "promoted": False,
            },
            "promoted": {
                "artifact_id": "artifact-final-01",
                "version": "artifact-v1",
                "content_hash": sha256_bytes(writing_body),
                "promotion_attestation": "promotion-001",
                "safe_media": {"media_type": "text/plain", "size_bytes": len(writing_body)},
            },
            "source_native_link": "https://source.example.invalid/artifacts/artifact-final-01",
            "live_content_access": "blocked-live-evidence",
            "ownership": {
                "source_owner": IDENTITY["source_id"],
                "state_owner": "source-fake-normalizer-v1",
                "file_owner": "source-fake-normalizer-v1",
                "sandbox_owner": None,
            },
            "live_operations": {
                operation: {
                    "state": "blocked-live-evidence",
                    "blocker": "sanctioned-non-production-classic-sandbox",
                    "fallback": "metadata-and-authorized-source-native-link-only",
                }
                for operation in (
                    "open",
                    "download",
                    "range",
                    "size_limit",
                    "expiry",
                    "revocation",
                    "retention",
                    "deletion",
                    "unavailable_content",
                    "stale_link",
                )
            },
        },
        "subagent-events.json": {
            "schema_version": "dw.fixture.subagent-events.v1",
            "identity": IDENTITY,
            "subagent_id": "subagent-sync-01",
            "namespace": "parent/subagent-sync-01",
            "events": [
                {"sequence": 1, "state": "spawned", "display_summary": "Synthetic subagent started."},
                {"sequence": 2, "state": "progress", "display_summary": "One bounded source fact was supplied."},
                {"sequence": 2, "state": "progress", "display_summary": "Duplicate ignored."},
                {"sequence": 4, "state": "completed", "display_summary": "Synthetic subagent completed."},
                {"sequence": 3, "state": "reconnected", "display_summary": "Out-of-order event ignored after checkpoint."},
            ],
            "compacted_before_sequence": 2,
            "terminal_states": ["completed", "failed", "cancelled"],
            "negative_cases": [
                "wrong-parent-identity",
                "cross-workspace-replay",
                "evidence-substitution",
                "unknown-state",
                "malformed-content",
                "duplicate-event",
                "out-of-order-event",
            ],
            "fallback": "generic-parent-timeline",
            "public_api_state": "blocked-package-index-evidence",
        },
        "rubric-history.json": {
            "schema_version": "dw.fixture.rubric-history.v1",
            "identity": IDENTITY,
            "rubric_id": "rubric-research-writing-v1",
            "version": "1",
            "criteria": [
                {"criterion_id": "criterion-provenance", "order": 1, "semantics": "required", "state": "fail", "evidence_refs": ["ev-citation-missing"]},
                {"criterion_id": "criterion-deliverable", "order": 2, "semantics": "required", "state": "pass", "evidence_refs": ["ev-artifact-promoted"]},
                {"criterion_id": "criterion-style", "order": 3, "semantics": "advisory", "state": "uncertain", "evidence_refs": []},
            ],
            "history_mode": "append-only",
            "iteration_cap": 3,
            "time_ceiling_seconds": 30,
            "cost_ceiling_units": 10,
            "operation_cases": {
                "interrupt": "blocked-live-evidence",
                "cancel": "cancelled",
                "verifier_error": "unsupported",
                "restart": "resume-from-last-immutable-verdict",
                "cap": "capped",
            },
        },
        "verdict-history.json": {
            "schema_version": "dw.fixture.verdict-history.v1",
            "identity": IDENTITY,
            "entries": [
                {
                    "iteration": 1,
                    "verdict_id": "verdict-001",
                    "candidate_hash": sha256_bytes(b"candidate-1"),
                    "evidence_versions": {"ev-citation-missing": "1"},
                    "state": "failed",
                    "supersedes_verdict_id": None,
                },
                {
                    "iteration": 2,
                    "verdict_id": "verdict-002",
                    "candidate_hash": sha256_bytes(b"candidate-2"),
                    "evidence_versions": {"ev-citation-valid": "2"},
                    "state": "passed",
                    "supersedes_verdict_id": "verdict-001",
                },
                {
                    "iteration": 3,
                    "verdict_id": "verdict-003",
                    "candidate_hash": sha256_bytes(b"candidate-3"),
                    "evidence_versions": {"ev-citation-valid": "3"},
                    "state": "capped",
                    "supersedes_verdict_id": "verdict-002",
                },
            ],
            "restart_checkpoint": {"last_iteration": 3, "last_verdict_id": "verdict-003"},
            "manual_fallback_state": "manually_reviewed",
        },
        "expected-outcomes.json": {
            "schema_version": "dw.fixture.expected-outcomes.v1",
            "generic_model_pass_overridden": True,
            "research_missing_required_evidence": "failed",
            "writing_without_promoted_final": "failed",
            "coding_failed_or_missing_tests": "failed",
            "required_uncertain": "failed",
            "required_not_evaluated": "failed",
            "cap_reached": "capped",
            "cancelled": "cancelled",
            "verifier_error": "unsupported",
            "manual_checklist": "manually_reviewed",
            "automatic_numeric_score": None,
        },
    }
    for name, value in fixtures.items():
        dump_json(root / "fixtures" / name, value)

    evidence_specs = [
        ("ev-artifact-working", "artifact", "fixtures/artifact-manifest.json", "working-v1"),
        ("ev-artifact-promoted", "artifact", "fixtures/artifact-manifest.json", "artifact-v1"),
        ("ev-subagent-events", "subagent", "fixtures/subagent-events.json", "event-set-v1"),
        ("ev-rubric-history", "rubric", "fixtures/rubric-history.json", "rubric-v1"),
        ("ev-verdict-history", "verification", "fixtures/verdict-history.json", "history-v1"),
        ("ev-citation-valid", "verification", "fixtures/research-transcript.json", "citation-v1"),
        ("ev-citation-missing", "verification", "fixtures/research-transcript.json", "missing-v1"),
        ("ev-citation-unreachable", "verification", "fixtures/research-transcript.json", "unreachable-v1"),
        ("ev-citation-mismatched", "verification", "fixtures/research-transcript.json", "mismatch-v1"),
        ("ev-citation-fabricated", "verification", "fixtures/research-transcript.json", "fabricated-v1"),
        ("ev-test-failed", "verification", "fixtures/coding-negative-transcript.json", "test-v1"),
        ("ev-writing-transcript", "verification", "fixtures/writing-transcript.json", "writing-v1"),
    ]
    return [
        {
            "evidence_id": evidence_id,
            "owner_stream": owner_stream,
            "identity": deepcopy(IDENTITY),
            "version": version,
            "path": path,
            "content_sha256": sha256_bytes((root / path).read_bytes()),
            "immutable": True,
        }
        for evidence_id, owner_stream, path, version in evidence_specs
    ]


def make_row(
    stream: str,
    capability: str,
    index: int,
    evidence_id: str,
    *,
    result: str = "accepted-deterministic-normalization",
) -> dict[str, Any]:
    if result == "accepted-deterministic-normalization":
        tier = "deterministic-fake"
        blocker = None
    elif result == "blocked-package-index-evidence":
        tier = "unknown"
        blocker = "approved-public-package-index-access"
    else:
        tier = "unknown"
        blocker = "sanctioned-non-production-classic-sandbox"
    row = {
        "row_id": f"{stream}-{index:03d}-{capability}",
        "stream": stream,
        "capability": capability,
        "case": "positive-or-fallback",
        "identity": deepcopy(IDENTITY),
        "evidence_refs": [evidence_id],
        "evidence_tier": tier,
        "request_schema": f"dw.{stream}-request.v1",
        "output_schema": f"dw.{stream}.v1",
        "transitions": ["received", "validated", "normalized"],
        "result": result,
        "blocker": blocker,
        "fallback": {
            "artifact": "metadata-and-authorized-source-native-link-only",
            "subagent": "generic-parent-timeline-with-source-supplied-facts-only",
            "rubric": "immutable-manual-checklist-without-automatic-score",
            "verification": "unsupported-or-manually-reviewed",
        }[stream],
        "acceptance_ids": ACCEPTANCE_BY_STREAM[stream],
        "automatic_pass": result == "accepted-deterministic-normalization",
        "provider_proof": False,
        "artifact_state": "working" if stream == "artifact" and capability == "working_vs_promoted" else None,
        "promoted": False if stream == "artifact" and capability == "working_vs_promoted" else None,
        "fact_origin": "source-supplied" if stream == "subagent" else None,
        "history_mode": "append-only" if stream == "rubric" else None,
    }
    return row


def build_matrix(evidence: list[dict[str, Any]]) -> dict[str, Any]:
    evidence_by_stream = {
        "artifact": "ev-artifact-promoted",
        "subagent": "ev-subagent-events",
        "rubric": "ev-rubric-history",
        "verification": "ev-verdict-history",
    }
    rows: list[dict[str, Any]] = []
    counter = 1
    for stream in STREAMS:
        for capability in sorted(REQUIRED_CAPABILITIES[stream]):
            result = "accepted-deterministic-normalization"
            if stream == "artifact" and capability in BLOCKED_LIVE_ARTIFACT:
                result = "blocked-live-evidence"
            elif (stream, capability) in BLOCKED_PUBLIC:
                result = "blocked-package-index-evidence"
            evidence_id = evidence_by_stream[stream]
            if capability == "research_citation_negatives":
                evidence_id = "ev-citation-missing"
            elif capability == "research_provenance":
                evidence_id = "ev-citation-valid"
            elif capability in {"writing_promotion", "writing_deliverable_negatives"}:
                evidence_id = "ev-writing-transcript"
            elif capability == "coding_test_negative":
                evidence_id = "ev-test-failed"
            row = make_row(stream, capability, counter, evidence_id, result=result)
            if capability in {"research_citation_negatives", "writing_deliverable_negatives", "coding_test_negative"}:
                row["required_evidence_state"] = "missing" if capability != "coding_test_negative" else "fail"
                row["automatic_pass"] = False
                row["result"] = "rejected-invalid-evidence"
            rows.append(row)
            counter += 1

    # Ensure every retained evidence record participates in the cross-stream closure.
    used = {ref for row in rows for ref in row["evidence_refs"]}
    for item in evidence:
        if item["evidence_id"] not in used:
            row = make_row(
                item["owner_stream"],
                sorted(REQUIRED_CAPABILITIES[item["owner_stream"]])[0],
                counter,
                item["evidence_id"],
            )
            row["row_id"] = f"{item['owner_stream']}-{counter:03d}-evidence-closure-{item['evidence_id']}"
            rows.append(row)
            counter += 1

    for stream in STREAMS:
        for dimension in sorted(SUBSTITUTION_DIMENSIONS[stream]):
            row = make_row(stream, f"substitution_{dimension}", counter, evidence_by_stream[stream])
            row.update(
                {
                    "case": "substitution",
                    "substitution_dimension": dimension,
                    "presented_value": f"wrong-{dimension}",
                    "result": "rejected-substitution",
                    "automatic_pass": False,
                    "transitions": ["received", "identity-rejected"],
                }
            )
            rows.append(row)
            counter += 1

    for export in (
        "create_deep_agent",
        "RubricMiddleware",
        "SubAgent",
        "SubAgentMiddleware",
    ):
        stream = "rubric" if export == "RubricMiddleware" else "subagent"
        row = make_row(
            stream,
            f"installed_public_{export}",
            counter,
            evidence_by_stream[stream],
            result="blocked-package-index-evidence",
        )
        row["automatic_pass"] = False
        rows.append(row)
        counter += 1

    return {
        "schema_version": "dw.research-writing-matrix.v1",
        "identity_fields": list(IDENTITY_FIELDS),
        "upstream_dependencies": {
            spike: {
                "state": "blocked-live-evidence",
                "reviewed_head": "758c1d4a2230b7c4261fcfbd0f3008634509e096",
                "accepted_as_input": False,
            }
            for spike in (
                "SPIKE-COMPOSE-001",
                "SPIKE-CONFIG-001",
                "SPIKE-STREAM-003",
                "SPIKE-HITL-001",
            )
        },
        "installed_public": {
            "state": "blocked-package-index-evidence",
            "lock_created": False,
            "commands_run": False,
        },
        "live_contract": {
            "state": "blocked-live-evidence",
            "sandbox_supplied": False,
            "accepted_upstreams_supplied": False,
        },
        "evidence": evidence,
        "rows": rows,
        "precedence_conflicts": [],
        "e2e_ids_credited": [],
        "excluded_acceptance_ids": ["AC-DW-TASK-005-04"],
    }


REPORT = """# Research and writing outcome contract

## Outcome

This corpus accepts dependency-free Deep Work normalization and nothing broader.
It binds artifact, synchronous subagent, rubric, and verification records to one
tenant/workspace/source/actor/task/run/attempt tuple plus stream-specific stable
identities. Generic model summaries are untrusted: missing required citations,
promoted deliverables, or test records produce a failed verdict.

## Evidence boundary

The no-index project has no dependencies, uses only `unittest`, denies network
access globally in tests, and runs frozen and offline. It proves deterministic
normalization, substitution rejection, append-only repair history, and manual
fallbacks. It does not prove Deep Agents behavior.

The installed-public project is intentionally unlocked and unexecuted. Public
`create_deep_agent`, `RubricMiddleware`, `SubAgent`, and `SubAgentMiddleware`
constructors remain `blocked-package-index-evidence` until reviewer-approved index
preflight permits exact public versions and file hashes. Source or editable
installs are prohibited.

The inherited COMPOSE-001, CONFIG-001, STREAM-003, and HITL-001 rows at reviewed
head `758c1d4a2230b7c4261fcfbd0f3008634509e096` remain
`blocked-live-evidence`. They were not copied, accepted, or reclassified.
Artifact content/access and real subagent rows also remain blocked without a
sanctioned non-production classic sandbox.

## Four correlated streams

- Artifact records distinguish working files from explicitly promoted immutable
  versions. Offline fixtures validate metadata and promotion hashes. Live
  download, range, size, expiry, revocation, retention, deletion, and stale-link
  behavior fall back to metadata plus an authorized source-native link.
- Subagent records accept only source-supplied bounded display facts with stable
  namespace and parent attribution. Duplicate, out-of-order, malformed, replayed,
  and substituted events are rejected or safely projected to the parent timeline.
  No prompt content or private reasoning is retained.
- Rubrics are immutable and ordered. Required `fail`, `uncertain`, or
  `not_evaluated` states cannot pass. Repairs append a new candidate, evidence
  version, iteration, and superseding verdict until cap, cancellation, error, or
  completion. Unsupported automation becomes the same rubric as a manual
  checklist with no numeric score.
- Verification binds the exact identity tuple, template, rubric, candidate hash,
  evidence versions, and verdict. Research fixtures preserve provenance and
  unresolved claims without treating citation presence as truth. Writing fixtures
  require a promoted final artifact. A minimal coding-negative fixture rejects a
  generic pass when tests fail or are missing and confers no coding-journey credit.

## Contradictions and disposition

Pinned reference examples help formulate contract questions but are not Deep Work
starter templates. Public export source blobs guide review but cannot substitute
for installed distributions. Fake-model fixtures can accept normalization rows
but can never become provider or hosted-runtime proof. These precedence rules
leave no unresolved conflict: lower-tier evidence is bounded instead of promoted.

SPIKE-VERIFICATION-001 has accepted deterministic-normalization evidence.
SPIKE-ARTIFACT-001 retains accepted metadata/promotion normalization with live
content operations blocked. SPIKE-SUBAGENT-001 retains accepted fallback
normalization with public constructors and live lifecycle blocked.
SPIKE-RUBRIC-001 retains accepted ordered/evidence/repair normalization with
installed middleware and live interrupt behavior blocked.

## Contribution limits

Supporting contract slices are limited to AC-DW-TASK-005-01, -02, -03 and
AC-DW-HITL-002-01 through -04. The corpus credits zero E2E scenarios, excludes
AC-DW-TASK-005-04, and does not prove application, UI, persistence,
authorization, browser, accessibility, performance, release, provider, or
end-to-end behavior.
"""


COMMANDS = """# exit-status<TAB>command
0\tpython3 tools/contract-spikes/research-writing-outcomes/index_preflight.py --mode no-index --output docs/references/research/research-writing-outcomes/index-status.json
0\tuv lock --project tools/contract-spikes/research-writing-outcomes/offline --offline
0\tuv sync --project tools/contract-spikes/research-writing-outcomes/offline --frozen --offline
0\tUV_OFFLINE=true uv run --project tools/contract-spikes/research-writing-outcomes/offline --frozen python -m unittest discover -s tools/contract-spikes/research-writing-outcomes/offline/tests -p 'test_*.py'
0\tUV_OFFLINE=true uv run --project tools/contract-spikes/research-writing-outcomes/offline --frozen python -m research_writing_outcome_spikes.inventory --output docs/references/research/research-writing-outcomes/versions.json
0\tUV_OFFLINE=true uv run --project tools/contract-spikes/research-writing-outcomes/offline --frozen python -m research_writing_outcome_spikes.validate_matrix docs/references/research/research-writing-outcomes/matrix.json --require-all-streams --require-complete-cross-product --require-installed-public-blocked --reject-orphaned-evidence --reject-blocked-dependency-promotion --reject-unresolved-precedence-conflicts
0\tUV_OFFLINE=true uv run --project tools/contract-spikes/research-writing-outcomes/offline --frozen python -m research_writing_outcome_spikes.scrub docs/references/research/research-writing-outcomes
0\tUV_OFFLINE=true uv run --project tools/contract-spikes/research-writing-outcomes/offline --frozen python -m research_writing_outcome_spikes.hash_evidence docs/references/research/research-writing-outcomes --output docs/references/research/research-writing-outcomes/hashes.json
0\tUV_OFFLINE=true uv run --project tools/contract-spikes/research-writing-outcomes/offline --frozen python -m research_writing_outcome_spikes.validate_evidence docs/references/research/research-writing-outcomes --require-command-statuses --require-fixture-hash-closure --require-fresh-scrub
0\tUV_OFFLINE=true uv run --project tools/contract-spikes/research-writing-outcomes/offline --frozen python -m research_writing_outcome_spikes.validate_scope --base fff1bfd278d550d01de6e8d74f553f45c4003a8c --include-untracked
0\tuv lock --project tools/contract-spikes/research-writing-outcomes/offline --check --offline
0\tpython3 tools/docs/generate.py --check
0\tpython3 tools/docs/check.py
0\tgit diff --check fff1bfd278d550d01de6e8d74f553f45c4003a8c...HEAD
0\tgit diff --name-only fff1bfd278d550d01de6e8d74f553f45c4003a8c
0\tgit status --short
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(args.output)
    root.mkdir(parents=True, exist_ok=True)
    write_schemas(root)
    evidence = fixture_evidence(root)
    dump_json(root / "matrix.json", build_matrix(evidence))
    (root / "report.md").write_text(REPORT)
    (root / "commands.txt").write_text(COMMANDS)
    print("deterministic corpus generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Validate the complete four-stream outcome contract matrix."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from .common import (
    BLOCKED_UPSTREAM,
    IDENTITY_FIELDS,
    STREAMS,
    SUPPORTED_ACCEPTANCE,
    ValidationError,
    exact_identity,
    load_json,
    require,
)


REQUIRED_CAPABILITIES = {
    "artifact": {
        "metadata",
        "working_vs_promoted",
        "content_hash",
        "access",
        "range_size",
        "expiry_revocation",
        "retention_deletion",
        "unavailable_stale",
    },
    "subagent": {
        "spawn_discover",
        "parent_attribution",
        "bounded_input_summary",
        "progress",
        "terminal_states",
        "reconnect_compaction",
        "ordering_deduplication",
        "unknown_malformed",
    },
    "rubric": {
        "immutable_ordered_rubric",
        "required_advisory",
        "evaluation_states",
        "repair_supersession",
        "interrupt",
        "cap_cancel",
        "verifier_error_resume",
        "ceilings",
    },
    "verification": {
        "research_provenance",
        "research_citation_negatives",
        "writing_promotion",
        "writing_deliverable_negatives",
        "coding_test_negative",
        "repair_evidence_change",
        "cap_cancel_error_resume",
        "manual_fallback",
    },
}

SUBSTITUTION_DIMENSIONS = {
    "artifact": {*IDENTITY_FIELDS, "evidence_id", "artifact_id"},
    "subagent": {*IDENTITY_FIELDS, "evidence_id", "subagent_id"},
    "rubric": {*IDENTITY_FIELDS, "evidence_id", "criterion_id"},
    "verification": {
        *IDENTITY_FIELDS,
        "evidence_id",
        "candidate_hash",
        "template_id",
        "rubric_version",
    },
}

ALLOWED_RESULTS = {
    "accepted-deterministic-normalization",
    "blocked-package-index-evidence",
    "blocked-live-evidence",
    "rejected-substitution",
    "rejected-invalid-evidence",
    "manual-fallback",
}
EVIDENCE_TIERS = {
    "deterministic-fake",
    "pinned-reference",
    "official-documentation",
    "installed-public",
    "accepted-live-fixture",
    "unknown",
}


def validate_matrix(data: dict[str, Any], *, installed_public_blocked: bool) -> None:
    require(data.get("schema_version") == "dw.research-writing-matrix.v1", "matrix schema drifted")
    require(tuple(data.get("identity_fields", ())) == IDENTITY_FIELDS, "identity tuple drifted")
    upstream = data.get("upstream_dependencies", {})
    for spike in BLOCKED_UPSTREAM:
        cell = upstream.get(spike, {})
        require(cell.get("state") == "blocked-live-evidence", f"{spike} must remain blocked")
        require(
            cell.get("reviewed_head") == "758c1d4a2230b7c4261fcfbd0f3008634509e096",
            f"{spike} reviewed head drifted",
        )

    public = data.get("installed_public", {})
    if installed_public_blocked:
        require(
            public.get("state") == "blocked-package-index-evidence",
            "installed-public cells must remain blocked",
        )
        require(public.get("lock_created") is False, "blocked installed-public project cannot be locked")
        require(public.get("commands_run") is False, "blocked installed-public project cannot run")

    evidence_items = data.get("evidence", [])
    evidence_by_id: dict[str, dict[str, Any]] = {}
    for item in evidence_items:
        evidence_id = item.get("evidence_id")
        require(isinstance(evidence_id, str) and evidence_id, "evidence id missing")
        require(evidence_id not in evidence_by_id, f"duplicate evidence: {evidence_id}")
        exact_identity(item.get("identity"), label=f"evidence {evidence_id}")
        require(item.get("immutable") is True, f"evidence must be immutable: {evidence_id}")
        require(isinstance(item.get("version"), str) and item["version"], f"evidence version missing: {evidence_id}")
        evidence_by_id[evidence_id] = item

    rows = data.get("rows", [])
    require(isinstance(rows, list) and rows, "matrix rows missing")
    ids: set[str] = set()
    seen_capabilities = {stream: set() for stream in STREAMS}
    seen_substitutions = {stream: set() for stream in STREAMS}
    referenced_evidence: set[str] = set()
    for row in rows:
        row_id = row.get("row_id")
        require(isinstance(row_id, str) and row_id, "row id missing")
        require(row_id not in ids, f"duplicate row id: {row_id}")
        ids.add(row_id)
        stream = row.get("stream")
        require(stream in STREAMS, f"invalid stream in {row_id}")
        seen_capabilities[stream].add(row.get("capability"))
        identity = exact_identity(row.get("identity"), label=f"row {row_id}")
        require(row.get("result") in ALLOWED_RESULTS, f"invalid result in {row_id}")
        require(row.get("evidence_tier") in EVIDENCE_TIERS, f"invalid evidence tier in {row_id}")
        require(isinstance(row.get("request_schema"), str) and row["request_schema"], f"request schema missing in {row_id}")
        require(isinstance(row.get("output_schema"), str) and row["output_schema"], f"output schema missing in {row_id}")
        require(isinstance(row.get("transitions"), list) and row["transitions"], f"transitions missing in {row_id}")
        require(isinstance(row.get("fallback"), str) and row["fallback"], f"fallback missing in {row_id}")
        acceptance = set(row.get("acceptance_ids", []))
        require(not any(value.startswith("E2E-") for value in acceptance), f"E2E credit forbidden in {row_id}")
        require("AC-DW-TASK-005-04" not in acceptance, f"TASK-005-04 forbidden in {row_id}")
        require(acceptance <= SUPPORTED_ACCEPTANCE, f"unsupported acceptance id in {row_id}")
        for evidence_id in row.get("evidence_refs", []):
            require(evidence_id in evidence_by_id, f"orphaned evidence ref in {row_id}: {evidence_id}")
            referenced_evidence.add(evidence_id)
            owner = evidence_by_id[evidence_id]["identity"]
            require(owner == identity, f"cross-owner evidence substitution in {row_id}")
        if row.get("case") == "substitution":
            dimension = row.get("substitution_dimension")
            seen_substitutions[stream].add(dimension)
            require(row.get("result") == "rejected-substitution", f"substitution accepted in {row_id}")
            require(row.get("automatic_pass") is False, f"substitution auto-passed in {row_id}")
        if row.get("required_evidence_state") in {"fail", "uncertain", "not_evaluated", "missing"}:
            require(row.get("automatic_pass") is False, f"required evidence auto-passed in {row_id}")
        if row.get("result") == "accepted-deterministic-normalization":
            require(row.get("evidence_tier") == "deterministic-fake", f"fake tier mismatch in {row_id}")
            require(row.get("provider_proof") is False, f"fake promoted to provider proof in {row_id}")
        if row.get("result") == "blocked-live-evidence":
            require(isinstance(row.get("blocker"), str) and row["blocker"], f"live blocker missing in {row_id}")
            require(row.get("automatic_pass") is False, f"blocked live row passed in {row_id}")
        if stream == "artifact" and row.get("artifact_state") == "working":
            require(row.get("promoted") is False, f"working file confused with artifact in {row_id}")
        if stream == "subagent":
            require(row.get("fact_origin") in {"source-supplied", "none"}, f"inferred subagent fact in {row_id}")
        if stream == "rubric":
            require(row.get("history_mode") == "append-only", f"mutable rubric history in {row_id}")

    for stream in STREAMS:
        missing_capabilities = REQUIRED_CAPABILITIES[stream] - seen_capabilities[stream]
        require(not missing_capabilities, f"{stream} capabilities missing: {sorted(missing_capabilities)}")
        missing_substitutions = SUBSTITUTION_DIMENSIONS[stream] - seen_substitutions[stream]
        require(not missing_substitutions, f"{stream} substitutions missing: {sorted(missing_substitutions)}")
    orphaned = set(evidence_by_id) - referenced_evidence
    require(not orphaned, f"unreferenced evidence records: {sorted(orphaned)}")
    require(data.get("precedence_conflicts") == [], "unresolved evidence precedence conflicts")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("matrix")
    parser.add_argument("--require-all-streams", action="store_true")
    parser.add_argument("--require-complete-cross-product", action="store_true")
    public = parser.add_mutually_exclusive_group()
    public.add_argument("--require-installed-public-blocked", action="store_true")
    public.add_argument("--require-installed-public-conformance", action="store_true")
    parser.add_argument("--reject-orphaned-evidence", action="store_true")
    parser.add_argument("--reject-blocked-dependency-promotion", action="store_true")
    parser.add_argument("--reject-unresolved-precedence-conflicts", action="store_true")
    args = parser.parse_args()
    try:
        validate_matrix(load_json(Path(args.matrix)), installed_public_blocked=args.require_installed_public_blocked)
    except ValidationError as exc:
        print(f"matrix validation failed: {exc}")
        return 1
    print("matrix validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

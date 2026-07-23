"""Validate the complete four-stream outcome contract matrix."""

from __future__ import annotations

import argparse
import re
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
    sha256_file,
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
    "accepted-installed-public-conformance",
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

LIVE_BLOCKED_CAPABILITIES = {
    ("artifact", "access"),
    ("artifact", "range_size"),
    ("artifact", "expiry_revocation"),
    ("artifact", "retention_deletion"),
    ("artifact", "unavailable_stale"),
    ("rubric", "interrupt"),
}
PUBLIC_EXPORTS = {
    "create_deep_agent",
    "RubricMiddleware",
    "SubAgent",
    "SubAgentMiddleware",
}
HEX_SHA256 = re.compile(r"^[a-f0-9]{64}$")
VERSION = re.compile(r"^[0-9]+(?:\.[0-9]+){1,3}(?:[A-Za-z0-9.+-]*)$")


def validate_matrix(
    data: dict[str, Any],
    *,
    installed_public_blocked: bool,
    evidence_root: Path | None = None,
) -> None:
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
    else:
        require(evidence_root is not None, "installed-public conformance needs retained evidence root")
        require(
            public.get("state") == "accepted-installed-public-conformance",
            "installed-public conformance result missing",
        )
        require(public.get("lock_created") is True, "installed-public conformance lock missing")
        require(public.get("commands_run") is True, "installed-public conformance commands missing")
        pins = public.get("distribution_pins")
        require(isinstance(pins, list) and pins, "installed-public distribution pins missing")
        pin_names = [pin.get("name") for pin in pins]
        require(len(pin_names) == len(set(pin_names)), "duplicate installed-public pin")
        require({"deepagents", "pytest"} <= set(pin_names), "required installed-public pins missing")
        for pin in pins:
            require(isinstance(pin.get("name"), str) and pin["name"], "distribution name missing")
            require(
                isinstance(pin.get("version"), str) and VERSION.fullmatch(pin["version"]),
                "distribution version invalid",
            )
            require(
                isinstance(pin.get("sha256"), str) and HEX_SHA256.fullmatch(pin["sha256"]),
                "distribution hash invalid",
            )
        require(
            isinstance(public.get("lock_sha256"), str)
            and HEX_SHA256.fullmatch(public["lock_sha256"]),
            "installed-public lock hash invalid",
        )
        lock_path = public.get("lock_path")
        require(
            lock_path
            == "tools/contract-spikes/research-writing-outcomes/installed-public/uv.lock",
            "installed-public lock path invalid",
        )
        repo_root = evidence_root.parents[3]
        resolved_lock = repo_root / lock_path
        require(resolved_lock.is_file(), "installed-public lock file missing")
        require(sha256_file(resolved_lock) == public["lock_sha256"], "installed-public lock hash mismatch")
        lock_text = resolved_lock.read_text()
        for pin in pins:
            require(f'name = "{pin["name"]}"' in lock_text, f"pin absent from lock: {pin['name']}")
            require(f'version = "{pin["version"]}"' in lock_text, f"pin version absent from lock: {pin['name']}")
            require(pin["sha256"] in lock_text, f"pin hash absent from lock: {pin['name']}")
        observations = public.get("export_observations")
        require(isinstance(observations, list), "installed-public observations missing")
        observed_exports = {item.get("export") for item in observations}
        require(observed_exports == PUBLIC_EXPORTS, "installed-public export observations incomplete")
        for observation in observations:
            require(observation.get("state") == "passed", "installed-public export observation failed")
            require(observation.get("fake_model") == "deterministic", "installed-public fake model missing")
            require(observation.get("provider_network") is False, "provider network used in conformance")
        observation_path = public.get("observation_path")
        require(
            observation_path == "fixtures/installed-public-conformance.json",
            "installed-public observation path invalid",
        )
        retained_observation = evidence_root / observation_path
        require(retained_observation.is_file(), "installed-public observation file missing")
        require(
            sha256_file(retained_observation) == public.get("observation_sha256"),
            "installed-public observation hash mismatch",
        )
        require(
            load_json(retained_observation).get("export_observations") == observations,
            "installed-public observation content drifted",
        )

    evidence_items = data.get("evidence", [])
    binding_catalog = data.get("binding_catalog")
    require(isinstance(binding_catalog, dict), "binding catalog missing")
    expected_binding_keys = {
        "artifact_id",
        "subagent_id",
        "criterion_id",
        "candidate_hash",
        "template_id",
        "rubric_version",
    }
    require(set(binding_catalog) == expected_binding_keys, "binding catalog drifted")
    if evidence_root is not None:
        artifact = load_json(evidence_root / "fixtures/artifact-manifest.json")
        subagent = load_json(evidence_root / "fixtures/subagent-events.json")
        rubric = load_json(evidence_root / "fixtures/rubric-history.json")
        verdict = load_json(evidence_root / "fixtures/verdict-history.json")
        research = load_json(evidence_root / "fixtures/research-transcript.json")
        derived_catalog = {
            "artifact_id": artifact["promoted"]["artifact_id"],
            "subagent_id": subagent["subagent_id"],
            "criterion_id": rubric["criteria"][0]["criterion_id"],
            "candidate_hash": verdict["entries"][0]["candidate_hash"],
            "template_id": research["template_id"],
            "rubric_version": rubric["version"],
        }
        require(binding_catalog == derived_catalog, "binding catalog does not match retained fixtures")
    evidence_by_id: dict[str, dict[str, Any]] = {}
    for item in evidence_items:
        evidence_id = item.get("evidence_id")
        require(isinstance(evidence_id, str) and evidence_id, "evidence id missing")
        require(evidence_id not in evidence_by_id, f"duplicate evidence: {evidence_id}")
        exact_identity(item.get("identity"), label=f"evidence {evidence_id}")
        require(item.get("owner_stream") in STREAMS, f"evidence owner stream invalid: {evidence_id}")
        require(item.get("immutable") is True, f"evidence must be immutable: {evidence_id}")
        require(isinstance(item.get("version"), str) and item["version"], f"evidence version missing: {evidence_id}")
        path_value = item.get("path")
        require(isinstance(path_value, str) and path_value, f"evidence path missing: {evidence_id}")
        path = Path(path_value)
        require(not path.is_absolute() and ".." not in path.parts, f"unsafe evidence path: {evidence_id}")
        require(
            isinstance(item.get("content_sha256"), str)
            and len(item["content_sha256"]) == 64,
            f"evidence hash missing: {evidence_id}",
        )
        if evidence_root is not None:
            resolved = evidence_root / path
            require(resolved.is_file(), f"evidence file missing: {evidence_id}")
            require(sha256_file(resolved) == item["content_sha256"], f"evidence hash mismatch: {evidence_id}")
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
            require(
                evidence_by_id[evidence_id]["owner_stream"] == stream,
                f"cross-stream evidence substitution in {row_id}",
            )
        if row.get("case") == "substitution":
            dimension = row.get("substitution_dimension")
            seen_substitutions[stream].add(dimension)
            expected = row.get("expected_value")
            presented = row.get("presented_value")
            require(isinstance(expected, str) and expected, f"expected binding missing in {row_id}")
            require(isinstance(presented, str) and presented, f"presented binding missing in {row_id}")
            require(expected != presented, f"substitution did not change value in {row_id}")
            if dimension in IDENTITY_FIELDS:
                require(expected == identity[dimension], f"identity substitution target drifted in {row_id}")
            if dimension == "evidence_id":
                require(expected in row.get("evidence_refs", []), f"evidence substitution target drifted in {row_id}")
            if dimension in expected_binding_keys:
                require(
                    expected == binding_catalog[dimension],
                    f"stream-specific substitution target drifted in {row_id}",
                )
            require(row.get("result") == "rejected-substitution", f"substitution accepted in {row_id}")
            require(row.get("automatic_pass") is False, f"substitution auto-passed in {row_id}")
        if row.get("required_evidence_state") in {"fail", "uncertain", "not_evaluated", "missing", "invalid"}:
            require(row.get("automatic_pass") is False, f"required evidence auto-passed in {row_id}")
        if row.get("capability") == "manual_fallback":
            require(row.get("result") == "manual-fallback", f"manual fallback result drifted in {row_id}")
            require(row.get("automatic_pass") is False, f"manual fallback auto-passed in {row_id}")
            require(
                row.get("normalized_verdict") in {"manually_reviewed", "unsupported"},
                f"manual fallback verdict drifted in {row_id}",
            )
        if row.get("result") == "accepted-deterministic-normalization":
            require(row.get("evidence_tier") == "deterministic-fake", f"fake tier mismatch in {row_id}")
            require(row.get("provider_proof") is False, f"fake promoted to provider proof in {row_id}")
        if row.get("result") == "accepted-installed-public-conformance":
            require(
                not installed_public_blocked
                and row.get("evidence_tier") == "installed-public",
                f"installed-public row accepted without conformance in {row_id}",
            )
        if row.get("result") == "blocked-live-evidence":
            require(isinstance(row.get("blocker"), str) and row["blocker"], f"live blocker missing in {row_id}")
            require(row.get("automatic_pass") is False, f"blocked live row passed in {row_id}")
        if (stream, row.get("capability")) in LIVE_BLOCKED_CAPABILITIES:
            require(row.get("result") == "blocked-live-evidence", f"live-blocked capability promoted in {row_id}")
        if stream == "rubric" and row.get("capability") == "interrupt":
            blockers = set(row.get("blockers", []))
            require(
                {"SPIKE-HITL-001", "sanctioned-non-production-classic-sandbox"} <= blockers,
                f"interrupt blockers incomplete in {row_id}",
            )
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
    if not installed_public_blocked:
        for export in PUBLIC_EXPORTS:
            rows_for_export = [
                row for row in rows
                if row.get("capability") == f"installed_public_{export}"
            ]
            require(len(rows_for_export) == 1, f"installed-public row missing: {export}")
            require(
                rows_for_export[0].get("result")
                == "accepted-installed-public-conformance",
                f"installed-public row not accepted: {export}",
            )
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
        matrix_path = Path(args.matrix)
        validate_matrix(
            load_json(matrix_path),
            installed_public_blocked=args.require_installed_public_blocked,
            evidence_root=matrix_path.parent,
        )
    except ValidationError as exc:
        print(f"matrix validation failed: {exc}")
        return 1
    print("matrix validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

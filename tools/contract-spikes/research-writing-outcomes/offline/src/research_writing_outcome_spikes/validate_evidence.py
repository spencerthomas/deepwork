"""Validate retained versions, command statuses, hashes, and scrub freshness."""

from __future__ import annotations

import argparse
from pathlib import Path

from .common import (
    BLOCKED_UPSTREAM,
    ValidationError,
    exact_identity,
    load_json,
    require,
)
from .hash_evidence import EXCLUDED, collect
from .fake_runtime import evidence_case_verdict, project_subagent_events


REQUIRED_FILES = {
    "matrix.json",
    "report.md",
    "versions.json",
    "commands.txt",
    "scrub-report.json",
    "index-status.json",
    "hashes.json",
    "schemas/artifact.schema.json",
    "schemas/subagent.schema.json",
    "schemas/rubric.schema.json",
    "schemas/verdict.schema.json",
    "schemas/cross-reference.schema.json",
    "fixtures/research-transcript.json",
    "fixtures/writing-transcript.json",
    "fixtures/coding-negative-transcript.json",
    "fixtures/artifact-manifest.json",
    "fixtures/subagent-events.json",
    "fixtures/rubric-history.json",
    "fixtures/verdict-history.json",
    "fixtures/expected-outcomes.json",
}

REQUIRED_COMMANDS = (
    "python3 tools/contract-spikes/research-writing-outcomes/index_preflight.py --mode no-index --output docs/references/research/research-writing-outcomes/index-status.json",
    "uv lock --project tools/contract-spikes/research-writing-outcomes/offline --offline",
    "uv sync --project tools/contract-spikes/research-writing-outcomes/offline --frozen --offline",
    "UV_OFFLINE=true uv run --project tools/contract-spikes/research-writing-outcomes/offline --frozen python -m unittest discover -s tools/contract-spikes/research-writing-outcomes/offline/tests -p 'test_*.py'",
    "UV_OFFLINE=true uv run --project tools/contract-spikes/research-writing-outcomes/offline --frozen python -m research_writing_outcome_spikes.inventory --output docs/references/research/research-writing-outcomes/versions.json",
    "UV_OFFLINE=true uv run --project tools/contract-spikes/research-writing-outcomes/offline --frozen python -m research_writing_outcome_spikes.validate_matrix docs/references/research/research-writing-outcomes/matrix.json --require-all-streams --require-complete-cross-product --require-installed-public-blocked --reject-orphaned-evidence --reject-blocked-dependency-promotion --reject-unresolved-precedence-conflicts",
    "UV_OFFLINE=true uv run --project tools/contract-spikes/research-writing-outcomes/offline --frozen python -m research_writing_outcome_spikes.scrub docs/references/research/research-writing-outcomes",
    "UV_OFFLINE=true uv run --project tools/contract-spikes/research-writing-outcomes/offline --frozen python -m research_writing_outcome_spikes.hash_evidence docs/references/research/research-writing-outcomes --output docs/references/research/research-writing-outcomes/hashes.json",
    "UV_OFFLINE=true uv run --project tools/contract-spikes/research-writing-outcomes/offline --frozen python -m research_writing_outcome_spikes.validate_evidence docs/references/research/research-writing-outcomes --require-command-statuses --require-fixture-hash-closure --require-fresh-scrub",
    "UV_OFFLINE=true uv run --project tools/contract-spikes/research-writing-outcomes/offline --frozen python -m research_writing_outcome_spikes.validate_scope --base fff1bfd278d550d01de6e8d74f553f45c4003a8c --include-untracked",
    "uv lock --project tools/contract-spikes/research-writing-outcomes/offline --check --offline",
    "python3 tools/docs/generate.py --check",
    "python3 tools/docs/check.py",
    "git diff --check fff1bfd278d550d01de6e8d74f553f45c4003a8c...HEAD",
    "git diff --name-only fff1bfd278d550d01de6e8d74f553f45c4003a8c",
    "git status --short",
)


def validate_versions(root: Path) -> None:
    value = load_json(root / "versions.json")
    require(value.get("schema_version") == "dw.research-writing-versions.v1", "versions schema drifted")
    offline = value.get("offline_project", {})
    require(offline.get("dependencies") == [], "offline project gained dependencies")
    require(offline.get("test_runner") == "stdlib-unittest", "offline runner drifted")
    require(
        offline.get("network_policy")
        == "python-process-audit-hook-plus-test-assertions",
        "network policy drifted",
    )
    public = value.get("installed_public", {})
    require(public.get("state") == "blocked-package-index-evidence", "public evidence state drifted")
    require(public.get("versions") is None and public.get("file_hashes") is None, "unapproved package pins present")
    require(value.get("e2e_ids_credited") == [], "E2E credit forbidden")
    require(value.get("excluded_acceptance_ids") == ["AC-DW-TASK-005-04"], "exclusion drifted")
    for spike in BLOCKED_UPSTREAM:
        require(
            value.get("upstream_artifacts", {}).get(spike, {}).get("state")
            == "blocked-live-evidence",
            f"upstream state drifted: {spike}",
        )


def validate_commands(root: Path) -> None:
    lines = [
        line for line in (root / "commands.txt").read_text().splitlines()
        if line and not line.startswith("#")
    ]
    require(len(lines) == len(REQUIRED_COMMANDS), "exact command record count drifted")
    recorded: list[str] = []
    for line in lines:
        status, separator, command = line.partition("\t")
        require(separator == "\t" and command, f"invalid command record: {line}")
        require(status == "0", f"nonzero or missing command status: {line}")
        forbidden = ("env ", "printenv", "set ", "approved-public-index", "installed-public --frozen pytest", "--live-profile")
        require(not any(value in command for value in forbidden), f"forbidden command recorded: {command}")
        recorded.append(command)
    require(tuple(recorded) == REQUIRED_COMMANDS, "exact command sequence drifted")


def validate_fixture_semantics(root: Path) -> None:
    research = load_json(root / "fixtures/research-transcript.json")
    research_cases = {item["case"]: item for item in research.get("citation_cases", [])}
    require(
        set(research_cases) == {"valid", "missing", "unreachable", "mismatched", "fabricated"},
        "research negative cases incomplete",
    )
    for name, case in research_cases.items():
        exact_identity(case.get("identity"), label=f"research case {name}")
        derived = evidence_case_verdict("research", case)
        require(case.get("expected_verdict") == derived, f"research verdict not derived: {name}")
        require(case.get("required") is True, f"research required binding missing: {name}")
    require(research_cases["valid"]["state"] == "valid", "valid research state drifted")
    require(research_cases["missing"]["state"] == "missing", "missing research state drifted")
    for name in ("unreachable", "mismatched", "fabricated"):
        require(research_cases[name]["state"] == "invalid", f"invalid research state drifted: {name}")

    writing = load_json(root / "fixtures/writing-transcript.json")
    exact_identity(writing.get("source_attribution", {}).get("identity"), label="writing source attribution")
    require(writing.get("source_attribution", {}).get("state") == "valid", "writing attribution invalid")
    writing_cases = {item["case"]: item for item in writing.get("cases", [])}
    require(
        set(writing_cases) == {"valid-promoted", "missing", "empty", "stale", "working-only"},
        "writing negative cases incomplete",
    )
    for name, case in writing_cases.items():
        exact_identity(case.get("identity"), label=f"writing case {name}")
        derived = evidence_case_verdict("writing", case)
        require(case.get("expected_verdict") == derived, f"writing verdict not derived: {name}")
    require(
        writing_cases["valid-promoted"]["artifact_state"] == "promoted",
        "valid writing case is not promoted",
    )
    require(writing_cases["valid-promoted"]["size_bytes"] > 0, "valid writing deliverable empty")
    require(writing_cases["missing"]["candidate_hash"] is None, "missing writing candidate present")
    require(writing_cases["empty"]["size_bytes"] == 0, "empty writing candidate nonempty")
    require(writing_cases["stale"]["artifact_state"] == "stale", "stale writing state drifted")
    require(writing_cases["working-only"]["artifact_state"] == "working", "working writing state drifted")

    coding = load_json(root / "fixtures/coding-negative-transcript.json")
    coding_cases = {item["case"]: item for item in coding.get("cases", [])}
    require(set(coding_cases) == {"failed-tests", "missing-tests"}, "coding negatives incomplete")
    for name, case in coding_cases.items():
        exact_identity(case.get("identity"), label=f"coding case {name}")
        derived = evidence_case_verdict("coding-negative", case)
        require(case.get("expected_verdict") == derived, f"coding verdict not derived: {name}")
    require(
        coding_cases["failed-tests"]["state"] == "fail"
        and coding_cases["failed-tests"]["exit_status"] != 0,
        "failed-test inputs drifted",
    )
    require(
        coding_cases["missing-tests"]["state"] == "missing"
        and coding_cases["missing-tests"]["exit_status"] is None,
        "missing-test inputs drifted",
    )

    subagent = load_json(root / "fixtures/subagent-events.json")
    summary = subagent.get("input_summary", {})
    require(summary.get("actual_characters") == len(summary.get("text", "")), "subagent summary length drifted")
    require(summary["actual_characters"] <= summary.get("max_characters", -1), "subagent summary bound exceeded")
    declared_sequence_outcomes = [
        item for item in subagent.get("normalized_outcomes", [])
        if "sequence" in item
    ]
    derived_sequence_outcomes = project_subagent_events(subagent.get("events", []))
    require(
        declared_sequence_outcomes == derived_sequence_outcomes,
        "subagent normalized outcomes are not derived from events",
    )
    outcomes = {(item.get("sequence"), item.get("outcome")) for item in declared_sequence_outcomes}
    require((2, "ignored-duplicate") in outcomes, "subagent duplicate outcome missing")
    require((3, "ignored-out-of-order") in outcomes, "subagent ordering outcome missing")

    history = load_json(root / "fixtures/verdict-history.json").get("entries", [])
    require(history, "verdict history missing")
    for index, entry in enumerate(history):
        exact_identity(entry.get("identity"), label=f"verdict history {index}")
        if index:
            previous = history[index - 1]
            require(entry.get("supersedes_verdict_id") == previous.get("verdict_id"), "verdict supersession drifted")
            require(
                entry.get("candidate_hash") != previous.get("candidate_hash")
                or entry.get("evidence_versions") != previous.get("evidence_versions"),
                "verdict repair bindings unchanged",
            )
    checkpoint = load_json(root / "fixtures/verdict-history.json").get("restart_checkpoint", {})
    require(checkpoint.get("last_iteration") == history[-1]["iteration"], "restart iteration drifted")
    require(checkpoint.get("last_verdict_id") == history[-1]["verdict_id"], "restart verdict drifted")
    require(history[-1].get("state") == "capped", "cap terminal state drifted")


def validate_hashes(root: Path) -> None:
    manifest = load_json(root / "hashes.json")
    require(manifest.get("schema_version") == "dw.evidence-hashes.v1", "hash schema drifted")
    require(set(manifest.get("excluded", [])) == EXCLUDED, "hash exclusions drifted")
    actual = collect(root)
    require(manifest.get("files") == actual, "retained evidence hash closure drifted")
    require(REQUIRED_FILES - {"hashes.json"} <= set(actual), "required retained files missing from closure")
    fixture_paths = {
        path.relative_to(root).as_posix()
        for path in (root / "fixtures").rglob("*")
        if path.is_file()
    }
    require(fixture_paths <= set(actual), "fixture missing from hash closure")


def validate_scrub(root: Path) -> None:
    report_path = root / "scrub-report.json"
    report = load_json(report_path)
    require(report.get("schema_version") == "dw.scrub-report.v1", "scrub schema drifted")
    require(report.get("finding_count") == 0 and report.get("findings") == [], "scrub findings remain")
    covered = [
        path for path in root.rglob("*")
        if path.is_file() and path.name not in {"scrub-report.json", "hashes.json", "review.json"}
    ]
    current_max = max(path.stat().st_mtime_ns for path in covered)
    require(report.get("covered_max_mtime_ns") == current_max, "scrub report does not cover latest evidence")
    require(report_path.stat().st_mtime_ns >= current_max, "scrub report is stale")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root")
    parser.add_argument("--require-command-statuses", action="store_true")
    parser.add_argument("--require-fixture-hash-closure", action="store_true")
    parser.add_argument("--require-fresh-scrub", action="store_true")
    args = parser.parse_args()
    root = Path(args.root)
    try:
        missing = [path for path in REQUIRED_FILES if not (root / path).is_file()]
        require(not missing, f"required evidence missing: {sorted(missing)}")
        validate_versions(root)
        validate_commands(root)
        validate_fixture_semantics(root)
        validate_scrub(root)
        validate_hashes(root)
        index = load_json(root / "index-status.json")
        require(index.get("state") == "blocked-package-index-evidence", "index status must fail closed")
        require(index.get("network_request_performed") is False, "no-index preflight made a request")
        require(index.get("permitted_validation_path") == "offline-no-index-only", "validation path drifted")
        for schema_path in sorted((root / "schemas").glob("*.json")):
            schema = load_json(schema_path)
            require(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", f"schema draft drifted: {schema_path.name}")
            require(schema.get("additionalProperties") is False, f"schema not closed: {schema_path.name}")
    except (OSError, ValidationError) as exc:
        print(f"evidence validation failed: {exc}")
        return 1
    print("evidence validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

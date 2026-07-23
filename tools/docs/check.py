#!/usr/bin/env python3
"""Validate the canonical Wave 0 knowledge system using the Python standard library."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
SPEC_ROOT = DOCS / "product-specs"
ACTIVE_PLANS = DOCS / "exec-plans" / "active"
ERRORS: list[str] = []

ACTIVE_PLAN_REQUIRED = (
    "exec_plan_id", "title", "status", "superseded_by", "owner",
    "reviewed_by", "reviewed_at", "primary_feature_id",
    "supporting_feature_ids", "issue", "created", "last_updated",
    "base_commit", "last_verified_commit", "risk", "governed_paths",
    "contract_gates", "decision_gates", "gate_review_status",
    "gate_reviewed_by", "gate_reviewed_at", "authoritative_sources",
    "scenario_ids", "dispatch_kind", "dispatch_ready",
    "agent_review_required", "dependencies", "blockers",
)
FORBIDDEN_AUTHORITY_PREFIXES = (
    "docs/plan/", "docs/plans/", "docs/proposals/", "docs/research/",
    "docs/generated/", "docs/references/agent-guidance/",
    "docs/references/audits/", "docs/references/legacy-plans/",
    "docs/references/research/",
)
FORBIDDEN_GOVERNED_PREFIXES = (
    "docs/plan/", "docs/plans/", "docs/proposals/", "docs/research/",
    "docs/references/legacy-plans/",
)

REQUIRED = [
    "AGENTS.md", "ARCHITECTURE.md", "docs/AGENTS.md", "docs/PLANS.md",
    "docs/PRODUCT_SENSE.md", "docs/DESIGN.md", "docs/FRONTEND.md",
    "docs/SECURITY.md", "docs/RELIABILITY.md", "docs/QUALITY_SCORE.md",
    "docs/design-docs/index.md", "docs/product-specs/index.md",
    "docs/exec-plans/index.md", "docs/generated/README.md",
    "docs/references/index.md", "docs/exec-plans/active/DW-EXEC-M1-REPOSITORY-SCAFFOLD.md",
    "CONTRIBUTING.md", "CODE_OF_CONDUCT.md", "SECURITY.md",
    "packages/ui/AGENTS.md", "tools/architecture/graph.json",
]

LEGACY_HASHES = {
    "2026-07-22-001-feat-deepwork-v1-delivery-plan.md": "3f4b6ed96054289426ac6c53ee6b4702484a934067a11b5761c0d68d756e3b0c",
    "application-architecture.md": "728cb61f5d31cd27385b91171fcce14daaa53c09c3983c275bdfd0e1667b730b",
    "code-conventions.md": "c06b1a0b97bc28c81dc1a33675ef3574e60951ef3d4f7f4e7bd3dba48629abab",
    "features/01-monorepo-scaffold.md": "f9faba6cad6f610b26c7265d39d37d789a1599ee37c57965421f40a68eadcd58",
    "features/02-web-import-hygiene.md": "d70325e0254399446322e6dde7cf16da0dfdadd4c7dd1ab6b026d27a7b7dcfe1",
    "features/03-oauth-spike.md": "4df1be1a878fc4cc954f7cccd76b79a633ee59c363e0fefa5d90cc9167b644d9",
    "features/04-mda-loop-spike.md": "ef6209a462d369f95d001a6cdf59ff15eec99fec87df7c73c3f498f662bb8d29",
    "features/05-stream-contract-spike.md": "e0e1eeca18f1029ba07a159bc53aae2604107c61e2c570df7f9d456c3c517bb5",
    "features/06-agent-project.md": "e22303ca019b844d9f919e2911fdc45814cd55ef7c5418ae696ccfe80444ffb1",
    "features/07b-api-backend.md": "76ad4168568c56e0a05f87f99c9134a1d5a5d6829bc098c498e148da01f20f05",
    "features/08-mobile-and-surfaces.md": "ba97390980e0591f6bf0c9d6a8ad922c3ca112c19c35787e769a25ef566fc3b8",
}


def error(message: str) -> None:
    ERRORS.append(message)


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end < 0:
        error(f"unterminated front matter: {path.relative_to(ROOT)}")
        return {}
    data: dict[str, str] = {}
    for number, line in enumerate(text[4:end].splitlines(), 2):
        if not line or line.startswith((" ", "\t", "#")):
            continue
        if ":" not in line:
            error(f"invalid front matter at {path.relative_to(ROOT)}:{number}: {line}")
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", key):
            error(f"invalid front matter key at {path.relative_to(ROOT)}:{number}: {key}")
        if key in data:
            error(f"duplicate front matter key at {path.relative_to(ROOT)}:{number}: {key}")
        data[key] = value.strip()
    return data


def inline_list(value: str) -> list[str]:
    if not (value.startswith("[") and value.endswith("]")):
        return []
    return [item.strip().strip("'\"") for item in value[1:-1].split(",") if item.strip()]


def is_inline_list(value: str) -> bool:
    return value.startswith("[") and value.endswith("]")


def is_iso_date(value: str) -> bool:
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value))


def commit_exists(value: str) -> bool:
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        return False
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{value}^{{commit}}"], cwd=ROOT,
        capture_output=True, text=True, check=False,
    )
    return result.returncode == 0


def forbidden_relative_path(value: str, prefixes: tuple[str, ...]) -> bool:
    path = Path(value)
    normalized = value.removeprefix("./")
    return (
        path.is_absolute() or ".." in path.parts or "\\" in value
        or normalized.startswith(prefixes)
    )


def dependency_cycle(graph: dict[str, set[str]]) -> list[str]:
    """Return one dependency cycle, or an empty list for an acyclic graph."""
    state: dict[str, int] = {}
    stack: list[str] = []

    def visit(node: str) -> list[str]:
        state[node] = 1
        stack.append(node)
        for dependency in graph.get(node, set()):
            if dependency not in graph:
                continue
            if state.get(dependency) == 1:
                start = stack.index(dependency)
                return stack[start:] + [dependency]
            if state.get(dependency, 0) == 0:
                found = visit(dependency)
                if found:
                    return found
        stack.pop()
        state[node] = 2
        return []

    for node in graph:
        if state.get(node, 0) == 0:
            found = visit(node)
            if found:
                return found
    return []


def canonical_markdown() -> list[Path]:
    files = list(ROOT.glob("*.md"))
    files.extend(ROOT.glob("packages/**/AGENTS.md"))
    for path in DOCS.rglob("*.md"):
        rel = path.relative_to(DOCS).as_posix()
        excluded = (
            rel.startswith("proposals/") or rel.startswith("plan/")
            or rel.startswith("plans/") or rel.startswith("research/")
            or rel.startswith("references/research/")
            or rel.startswith("references/legacy-plans/canonical-")
            or rel.startswith("references/legacy-plans/unreviewed-") and path.name != "README.md"
            or rel.startswith("references/agent-guidance/")
            or rel.startswith("references/audits/2026-07-22-")
        )
        if not excluded:
            files.append(path)
    return sorted(set(path for path in files if path.exists()))


def check_required_and_frontmatter() -> None:
    for rel in REQUIRED:
        if not (ROOT / rel).exists():
            error(f"missing canonical path: {rel}")
    if (ROOT / "WORKFLOW.md").exists():
        error("WORKFLOW.md must remain absent until SPIKE-SYMPHONY-001 passes")
    for path in canonical_markdown():
        frontmatter(path)
    try:
        graph = json.loads((ROOT / "tools/architecture/graph.json").read_text(encoding="utf-8"))
        if graph.get("schema_version") != 1 or not graph.get("zones"):
            error("architecture graph lacks schema_version=1 or zones")
    except (OSError, json.JSONDecodeError) as exc:
        error(f"invalid architecture graph: {exc}")


def check_links() -> None:
    pattern = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
    for path in canonical_markdown():
        text = path.read_text(encoding="utf-8")
        for raw in pattern.findall(text):
            target = raw.strip().split()[0].strip("<>")
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = unquote(target.split("#", 1)[0])
            if not target:
                continue
            resolved = (path.parent / target).resolve()
            exists = resolved.exists()
            if resolved.is_dir():
                exists = (resolved / "README.md").exists() or (resolved / "index.md").exists()
            if not exists:
                error(f"broken internal link: {path.relative_to(ROOT)} -> {raw}")


def check_ids_and_indexes() -> None:
    specs: dict[str, tuple[Path, dict[str, str]]] = {}
    releases: Counter[str] = Counter()
    for path in SPEC_ROOT.rglob("*.md"):
        data = frontmatter(path)
        feature_id = data.get("feature_id")
        if not feature_id:
            continue
        if feature_id in specs:
            error(f"duplicate feature ID {feature_id}: {path} and {specs[feature_id][0]}")
        specs[feature_id] = (path, data)
        releases[data.get("release", "missing")] += 1
        for required_key in ("title", "release", "status", "owners", "runtime_scopes", "source_refs"):
            if required_key not in data:
                error(f"{feature_id} missing front matter key {required_key}")
    if len(specs) != 39:
        error(f"expected 39 feature specs, found {len(specs)}")
    expected_releases = Counter({"v1": 28, "v1.x": 3, "v2": 7, "v3": 1})
    if releases != expected_releases:
        error(f"release assignments drifted: {dict(releases)} expected {dict(expected_releases)}")

    register_text = (SPEC_ROOT / "acceptance-scenarios.md").read_text(encoding="utf-8")
    registry_lines = [line for line in register_text.splitlines() if line.startswith("| DW-") and "AC-DW-" in line]
    scenario_defs = []
    registry_features = set()
    for line in registry_lines:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        registry_features.add(cells[0])
        scenario_defs.extend(dict.fromkeys(re.findall(r"AC-[A-Z0-9-]+", line)))
    duplicates = [item for item, count in Counter(scenario_defs).items() if count > 1]
    if duplicates:
        error(f"duplicate scenario definitions: {', '.join(duplicates)}")
    if len(scenario_defs) != 179:
        error(f"expected 179 feature scenarios, found {len(scenario_defs)}")
    if registry_features != {feature for feature, (_, data) in specs.items() if data.get('release') == 'v1'}:
        error("v1 feature/scenario registry ownership differs")

    e2e_defs = re.findall(r"^\| `(E2E-V1-[A-Z0-9-]+)` ", register_text, re.MULTILINE)
    if len(e2e_defs) != 12 or len(set(e2e_defs)) != 12:
        error(f"expected 12 unique v1 release scenarios, found {len(set(e2e_defs))}")

    decisions_text = (DOCS / "design-docs/decisions/index.md").read_text(encoding="utf-8")
    decision_defs = re.findall(r"^\| (DEC-\d{3}) ", decisions_text, re.MULTILINE)
    spike_defs = re.findall(r"^\| (SPIKE-[A-Z0-9-]+) ", decisions_text, re.MULTILINE)
    if len(decision_defs) != 43 or len(set(decision_defs)) != 43:
        error(f"expected 43 unique decisions, found {len(set(decision_defs))}")
    if len(spike_defs) != 44 or len(set(spike_defs)) != 44:
        error(f"expected 44 unique spikes, found {len(set(spike_defs))}")
    all_canonical = "\n".join(path.read_text(encoding="utf-8") for path in canonical_markdown())
    dangling_spikes = sorted(set(re.findall(r"SPIKE-[A-Z0-9-]+", all_canonical)) - set(spike_defs))
    if dangling_spikes:
        error(f"dangling spike IDs: {', '.join(dangling_spikes)}")

    ledger = (DOCS / "references/source-ledger.md").read_text(encoding="utf-8")
    source_defs = re.findall(r"^\| (SRC-[A-Z0-9-]+) ", ledger, re.MULTILINE)
    if len(source_defs) != len(set(source_defs)):
        error("duplicate source IDs in source ledger")
    for feature_id, (_, data) in specs.items():
        for source in inline_list(data.get("source_refs", "[]")):
            if source not in source_defs:
                error(f"{feature_id} has dangling source ID {source}")
        for spike in inline_list(data.get("contract_gates", "[]")):
            if spike not in spike_defs:
                error(f"{feature_id} has dangling contract gate {spike}")
        for dependency in inline_list(data.get("dependencies", "[]")):
            if dependency.startswith("DW-") and dependency not in specs:
                error(f"{feature_id} has dangling feature dependency {dependency}")

    index_text = (SPEC_ROOT / "index.md").read_text(encoding="utf-8")
    indexed = set(re.findall(r"\(([^)]+\.md)\)", index_text))
    for feature_id, (path, _) in specs.items():
        expected = path.relative_to(SPEC_ROOT).as_posix()
        if expected not in indexed:
            error(f"product spec not indexed: {feature_id} at {expected}")


def check_design_authority() -> set[str]:
    index = DOCS / "design-docs/index.md"
    text = index.read_text(encoding="utf-8")
    linked: set[Path] = set()
    for target in re.findall(r"(?<!!)\[[^\]]*\]\(([^)]+\.md)(?:#[^)]+)?\)", text):
        resolved = (index.parent / unquote(target)).resolve()
        if not resolved.is_relative_to(index.parent.resolve()):
            error(f"design authority escapes docs/design-docs: {target}")
            continue
        linked.add(resolved)

    design_files = {
        path.resolve() for path in index.parent.rglob("*.md") if path != index
    }
    for path in sorted(design_files - linked):
        body = path.read_text(encoding="utf-8")
        if re.search(r"(?im)^status:.*canonical|canonical design|accepted design", body):
            error(f"canonical design document is not indexed: {path.relative_to(ROOT)}")
        else:
            error(f"design document is not indexed: {path.relative_to(ROOT)}")
    for path in sorted(linked - design_files):
        error(f"design index target is missing: {path.relative_to(ROOT)}")

    design_ids: dict[str, Path] = {}
    for path in sorted(linked & design_files):
        data = frontmatter(path)
        design_id = data.get("design_id")
        if design_id:
            if design_id in design_ids:
                error(
                    f"duplicate design ID {design_id}: "
                    f"{path.relative_to(ROOT)} and {design_ids[design_id].relative_to(ROOT)}"
                )
            design_ids[design_id] = path
    return {path.relative_to(ROOT).as_posix() for path in linked & design_files}


def validate_exec_plan(
    path: Path,
    *,
    feature_ids: set[str],
    scenario_ids: set[str],
    decision_ids: set[str],
    spike_ids: set[str],
    indexed_design_docs: set[str],
    known_dependency_refs: set[str] | None = None,
    terminal_dependency_refs: set[str] | None = None,
    verify_commits: bool = True,
) -> list[str]:
    problems: list[str] = []
    try:
        rel = path.relative_to(ROOT).as_posix()
    except ValueError:
        rel = path.as_posix()
    data = frontmatter(path)

    for key in ACTIVE_PLAN_REQUIRED:
        if key not in data:
            problems.append(f"{rel} missing ExecPlan metadata {key}")
    if problems:
        return problems

    if data["status"] not in {"reviewed", "active"}:
        problems.append(
            f"{rel} has unsupported active ExecPlan status {data['status']!r}; "
            "expected reviewed or active"
        )
    if data["risk"] not in {"low", "medium", "high"}:
        problems.append(f"{rel} has invalid risk {data['risk']!r}")
    if data["dispatch_kind"] not in {"cell", "program"}:
        problems.append(f"{rel} has invalid dispatch_kind {data['dispatch_kind']!r}")
    if data["agent_review_required"] != "true":
        problems.append(f"{rel} must set agent_review_required: true")
    if data["dispatch_ready"] not in {"true", "false"}:
        problems.append(f"{rel} dispatch_ready must be exact boolean true or false")
    if data["dispatch_kind"] == "program" and data["dispatch_ready"] != "false":
        problems.append(f"{rel} program control plan cannot be dispatch-ready")
    if not data["owner"] or not data["issue"]:
        problems.append(f"{rel} requires non-empty owner and issue identity")
    if data["superseded_by"] not in {"null", ""}:
        problems.append(f"{rel} active plan cannot set superseded_by")

    list_keys = (
        "reviewed_by", "supporting_feature_ids", "governed_paths",
        "contract_gates", "decision_gates", "gate_reviewed_by",
        "authoritative_sources", "scenario_ids", "dependencies", "blockers",
    )
    for key in list_keys:
        if not is_inline_list(data[key]):
            problems.append(f"{rel} metadata {key} must be an inline list")

    reviewers = inline_list(data["reviewed_by"])
    gate_reviewers = inline_list(data["gate_reviewed_by"])
    governed_paths = inline_list(data["governed_paths"])
    authorities = inline_list(data["authoritative_sources"])
    contract_gates = inline_list(data["contract_gates"])
    decision_gates = inline_list(data["decision_gates"])
    scenarios = inline_list(data["scenario_ids"])
    dependencies = inline_list(data["dependencies"])
    blockers = inline_list(data["blockers"])

    for key, values in (("dependencies", dependencies), ("blockers", blockers)):
        duplicates = [item for item, count in Counter(values).items() if count > 1]
        if duplicates:
            problems.append(f"{rel} has duplicate {key}: {', '.join(duplicates)}")
    overlap = sorted(set(dependencies) & set(blockers))
    if overlap:
        problems.append(f"{rel} lists the same dependency and blocker: {', '.join(overlap)}")
    known_refs = known_dependency_refs or (feature_ids | decision_ids | spike_ids)
    terminal_refs = terminal_dependency_refs or set()
    for dependency in dependencies:
        if dependency not in known_refs:
            problems.append(f"{rel} has unknown dependency {dependency}")
    for blocker in blockers:
        if blocker not in known_refs:
            problems.append(f"{rel} has unknown blocker {blocker}")
    if data["dispatch_kind"] == "cell":
        if data["dispatch_ready"] == "true":
            if blockers:
                problems.append(f"{rel} dispatch-ready cell has unresolved blockers")
            unresolved = [item for item in dependencies if item not in terminal_refs]
            if unresolved:
                problems.append(
                    f"{rel} dispatch-ready cell has non-terminal dependencies: "
                    f"{', '.join(unresolved)}"
                )
        elif not dependencies and not blockers:
            problems.append(
                f"{rel} non-ready cell must record a dependency or blocker"
            )

    if not reviewers or data["owner"] in reviewers:
        problems.append(f"{rel} requires independent non-owner reviewer metadata")
    if not gate_reviewers:
        problems.append(f"{rel} requires completed gate reviewer metadata")
    for key in ("created", "last_updated", "reviewed_at", "gate_reviewed_at"):
        if not is_iso_date(data[key]):
            problems.append(f"{rel} metadata {key} must be YYYY-MM-DD")
    for key in ("base_commit", "last_verified_commit"):
        value = data[key]
        valid = bool(re.fullmatch(r"[0-9a-f]{40}", value))
        if valid and verify_commits:
            valid = commit_exists(value)
        if not valid:
            problems.append(f"{rel} metadata {key} must name an existing full commit")

    if data["primary_feature_id"] not in feature_ids:
        problems.append(f"{rel} has unknown primary feature {data['primary_feature_id']}")
    for feature_id in inline_list(data["supporting_feature_ids"]):
        if feature_id not in feature_ids:
            problems.append(f"{rel} has unknown supporting feature {feature_id}")
    if not scenarios:
        problems.append(f"{rel} requires at least one acceptance scenario")
    for scenario_id in scenarios:
        if scenario_id not in scenario_ids:
            problems.append(f"{rel} has unknown acceptance scenario {scenario_id}")

    for gate in contract_gates:
        if gate not in spike_ids:
            problems.append(f"{rel} has unknown contract gate {gate}")
    for gate in decision_gates:
        if gate not in decision_ids:
            problems.append(f"{rel} has unknown decision gate {gate}")
    has_gates = bool(contract_gates or decision_gates)
    expected_gate_status = "reviewed-with-gates" if has_gates else "reviewed-none"
    if data["gate_review_status"] != expected_gate_status:
        problems.append(
            f"{rel} gate_review_status must be {expected_gate_status} for its gate arrays"
        )

    if not governed_paths:
        problems.append(f"{rel} requires non-empty governed_paths")
    for governed in governed_paths:
        if forbidden_relative_path(governed, FORBIDDEN_GOVERNED_PREFIXES):
            problems.append(f"{rel} has forbidden governed path {governed}")

    if not authorities:
        problems.append(f"{rel} requires non-empty authoritative_sources")
    for authority in authorities:
        if forbidden_relative_path(authority, FORBIDDEN_AUTHORITY_PREFIXES):
            problems.append(f"{rel} uses non-canonical authority {authority}")
            continue
        authority_path = ROOT / authority
        if not authority_path.is_file():
            problems.append(f"{rel} authority does not exist: {authority}")
        if authority.startswith("docs/design-docs/") and authority not in indexed_design_docs:
            problems.append(f"{rel} uses unindexed design authority {authority}")

    body = path.read_text(encoding="utf-8")
    required_sections = (
        "Purpose", "Context", "Scope", "Progress", "Surprises",
        "Decision Log", "Validation", "Recovery", "Outcomes",
    )
    for section in required_sections:
        if not re.search(rf"(?im)^##\s+[^\n]*\b{re.escape(section)}\b", body):
            problems.append(f"{rel} missing living ExecPlan section containing {section!r}")
    return problems


def check_active_exec_plans(indexed_design_docs: set[str]) -> tuple[int, int]:
    feature_ids = {
        data["feature_id"] for path in SPEC_ROOT.rglob("*.md")
        if (data := frontmatter(path)).get("feature_id")
    }
    scenario_text = (SPEC_ROOT / "acceptance-scenarios.md").read_text(encoding="utf-8")
    scenario_ids = set(re.findall(r"(?:AC-DW|E2E-V1)-[A-Z0-9-]+", scenario_text))
    decisions_text = (DOCS / "design-docs/decisions/index.md").read_text(encoding="utf-8")
    decision_ids = set(re.findall(r"^\| (DEC-\d{3}) ", decisions_text, re.MULTILINE))
    spike_ids = set(re.findall(r"^\| (SPIKE-[A-Z0-9-]+) ", decisions_text, re.MULTILINE))

    plans = sorted(ACTIVE_PLANS.glob("*.md"))
    plan_data = {plan: frontmatter(plan) for plan in plans}
    plan_ids = [data.get("exec_plan_id", "") for data in plan_data.values()]
    duplicate_plan_ids = [
        item for item, count in Counter(plan_ids).items() if item and count > 1
    ]
    if duplicate_plan_ids:
        error(f"duplicate active ExecPlan IDs: {', '.join(duplicate_plan_ids)}")

    completed_refs: set[str] = set()
    for completed in (DOCS / "exec-plans/completed").glob("*.md"):
        completed_data = frontmatter(completed)
        if completed_data.get("status") == "completed":
            completed_refs.update(
                value for key in ("exec_plan_id", "issue")
                if (value := completed_data.get(key))
            )
    active_refs = {
        value for data in plan_data.values()
        for key in ("exec_plan_id", "issue") if (value := data.get(key))
    }
    known_refs = feature_ids | decision_ids | spike_ids | active_refs | completed_refs

    alias_to_plan = {
        alias: data.get("exec_plan_id", "") for data in plan_data.values()
        for key in ("exec_plan_id", "issue") if (alias := data.get(key))
    }
    graph = {
        data.get("exec_plan_id", ""): {
            alias_to_plan[dependency]
            for dependency in inline_list(data.get("dependencies", "[]"))
            if dependency in alias_to_plan
        }
        for data in plan_data.values() if data.get("exec_plan_id")
    }
    cycle = dependency_cycle(graph)
    if cycle:
        error(f"active ExecPlan dependency cycle: {' -> '.join(cycle)}")

    index_text = (DOCS / "exec-plans/index.md").read_text(encoding="utf-8")
    indexed_targets = {
        (DOCS / "exec-plans" / target).resolve()
        for target in re.findall(r"\[[^\]]+\]\((active/[^)]+\.md)\)", index_text)
    }
    for plan in plans:
        if plan.resolve() not in indexed_targets:
            error(f"active ExecPlan is not indexed: {plan.relative_to(ROOT)}")
        for problem in validate_exec_plan(
            plan,
            feature_ids=feature_ids,
            scenario_ids=scenario_ids,
            decision_ids=decision_ids,
            spike_ids=spike_ids,
            indexed_design_docs=indexed_design_docs,
            known_dependency_refs=known_refs,
            terminal_dependency_refs=completed_refs,
        ):
            error(problem)
    for target in indexed_targets:
        if target not in {plan.resolve() for plan in plans}:
            error(f"ExecPlan index target is missing: {target.relative_to(ROOT)}")

    issues = [plan_data[plan].get("issue", "") for plan in plans]
    duplicate_issues = [item for item, count in Counter(issues).items() if item and count > 1]
    if duplicate_issues:
        error(f"duplicate active ExecPlan issue identities: {', '.join(duplicate_issues)}")
    ready = sum(plan_data[plan].get("dispatch_ready") == "true" for plan in plans)
    return len(plans), ready


def check_legacy_preservation() -> None:
    original_root = DOCS / "plans"
    copy_root = DOCS / "references/legacy-plans/unreviewed-2026-07-22"
    originals_present = original_root.exists()
    for rel, expected in LEGACY_HASHES.items():
        copy = copy_root / rel
        if not copy.exists():
            error(f"missing uncertain legacy reference copy: {copy.relative_to(ROOT)}")
        elif hashlib.sha256(copy.read_bytes()).hexdigest() != expected:
            error(f"uncertain legacy reference copy changed: {copy.relative_to(ROOT)}")
        if originals_present:
            original = original_root / rel
            if not original.exists():
                error(f"local uncertain legacy set is incomplete: {original.relative_to(ROOT)}")
            elif hashlib.sha256(original.read_bytes()).hexdigest() != expected:
                error(f"local uncertain legacy original changed: {original.relative_to(ROOT)}")


def check_generated() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools/docs/generate.py"), "--check"],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    if result.returncode:
        error(result.stdout.strip() or result.stderr.strip())


def main() -> int:
    check_required_and_frontmatter()
    check_links()
    check_ids_and_indexes()
    indexed_design_docs = check_design_authority()
    active_plan_count, dispatch_ready_count = check_active_exec_plans(indexed_design_docs)
    check_legacy_preservation()
    check_generated()
    if ERRORS:
        print(f"documentation validation failed with {len(ERRORS)} error(s):")
        for item in ERRORS:
            print(f"- {item}")
        return 1
    print("documentation validation passed")
    print(f"  canonical paths: {len(REQUIRED)}")
    print("  feature specs: 39 (v1=28, v1.x=3, v2=7, v3=1)")
    print("  feature scenarios: 179; v1 release scenarios: 12")
    print("  decisions: 43; open spikes: 44")
    print(
        f"  active ExecPlans: {active_plan_count}; "
        f"dispatch-ready cells: {dispatch_ready_count}"
    )
    local_state = "local originals verified" if (DOCS / "plans").exists() else "clean worktree"
    print(f"  uncertain legacy files: 11 preserved references; {local_state}")
    print("  generated documents: 6, drift-free")
    return 0


if __name__ == "__main__":
    sys.exit(main())

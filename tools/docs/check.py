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
ERRORS: list[str] = []

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
    local_state = "local originals verified" if (DOCS / "plans").exists() else "clean worktree"
    print(f"  uncertain legacy files: 11 preserved references; {local_state}")
    print("  generated documents: 6, drift-free")
    return 0


if __name__ == "__main__":
    sys.exit(main())

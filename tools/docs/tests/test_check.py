"""Negative and positive tests for Wave 0.1 ExecPlan dispatch validation."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

CHECK_PATH = Path(__file__).resolve().parents[1] / "check.py"
SPEC = importlib.util.spec_from_file_location("deepwork_docs_check", CHECK_PATH)
assert SPEC and SPEC.loader
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class ExecPlanValidationTests(unittest.TestCase):
    """Exercise fail-closed dispatch metadata without mutating the repository."""

    maxDiff = None

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "plan.md"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def plan(self, **overrides: str) -> str:
        data = {
            "exec_plan_id": "DW-EXEC-TEST",
            "title": "Test plan",
            "status": "reviewed",
            "superseded_by": "null",
            "owner": "implementation",
            "reviewed_by": "[reviewer]",
            "reviewed_at": "2026-07-23",
            "primary_feature_id": "DW-FND-001",
            "supporting_feature_ids": "[]",
            "issue": "local:TEST-001",
            "created": "2026-07-23",
            "last_updated": "2026-07-23",
            "base_commit": "1" * 40,
            "last_verified_commit": "1" * 40,
            "risk": "medium",
            "governed_paths": "[packages/domain/**]",
            "contract_gates": "[SPIKE-WORKTREE-001]",
            "decision_gates": "[DEC-032]",
            "gate_review_status": "reviewed-with-gates",
            "gate_reviewed_by": "[reviewer]",
            "gate_reviewed_at": "2026-07-23",
            "authoritative_sources": "[ARCHITECTURE.md, docs/design-docs/architecture/application-architecture.md]",
            "scenario_ids": "[AC-DW-FND-001-01]",
            "dispatch_kind": "cell",
            "dispatch_ready": "true",
            "agent_review_required": "true",
            "dependencies": "[]",
            "blockers": "[]",
        }
        data.update(overrides)
        frontmatter = "\n".join(f"{key}: {value}" for key, value in data.items())
        body = """---
{frontmatter}
---

# Test plan

## Purpose
## Context
## Scope
## Progress
## Surprises & Discoveries
## Decision Log
## Validation
## Recovery
## Outcomes & Retrospective
""".format(frontmatter=frontmatter)
        self.path.write_text(body, encoding="utf-8")
        return body

    def problems(self) -> list[str]:
        return CHECK.validate_exec_plan(
            self.path,
            feature_ids={"DW-FND-001"},
            scenario_ids={"AC-DW-FND-001-01"},
            decision_ids={"DEC-032"},
            spike_ids={"SPIKE-WORKTREE-001"},
            indexed_design_docs={
                "docs/design-docs/architecture/application-architecture.md"
            },
            verify_commits=False,
        )

    def assert_problem(self, text: str) -> None:
        self.assertTrue(any(text in problem for problem in self.problems()), self.problems())

    def test_reviewed_cell_is_dispatch_ready(self) -> None:
        self.plan()
        self.assertEqual([], self.problems())

    def test_unsupported_status_fails(self) -> None:
        self.plan(status="reviewed-ready")
        self.assert_problem("unsupported active ExecPlan status")

    def test_missing_reviewer_fails(self) -> None:
        self.plan(reviewed_by="[]")
        self.assert_problem("independent non-owner reviewer")

    def test_self_review_fails(self) -> None:
        self.plan(reviewed_by="[implementation]")
        self.assert_problem("independent non-owner reviewer")

    def test_gate_review_mismatch_fails(self) -> None:
        self.plan(gate_review_status="reviewed-none")
        self.assert_problem("gate_review_status must be reviewed-with-gates")

    def test_proposal_authority_fails(self) -> None:
        self.plan(authoritative_sources="[docs/proposals/example.md]")
        self.assert_problem("non-canonical authority")

    def test_protected_governed_path_fails(self) -> None:
        self.plan(governed_paths="[docs/plans/**]")
        self.assert_problem("forbidden governed path")

    def test_dispatch_readiness_fails_closed(self) -> None:
        self.plan(dispatch_ready="false")
        self.assert_problem("non-ready cell must record a dependency or blocker")

    def test_dispatch_ready_cell_with_blocker_fails(self) -> None:
        self.plan(blockers="[SPIKE-WORKTREE-001]")
        self.assert_problem("dispatch-ready cell has unresolved blockers")

    def test_known_blocker_keeps_cell_safely_non_ready(self) -> None:
        self.plan(dispatch_ready="false", blockers="[SPIKE-WORKTREE-001]")
        self.assertEqual([], self.problems())

    def test_unknown_dependency_fails(self) -> None:
        self.plan(dispatch_ready="false", dependencies="[UNKNOWN-CELL]")
        self.assert_problem("unknown dependency UNKNOWN-CELL")

    def test_unknown_blocker_fails(self) -> None:
        self.plan(dispatch_ready="false", blockers="[UNKNOWN-BLOCKER]")
        self.assert_problem("unknown blocker UNKNOWN-BLOCKER")

    def test_dependency_cycle_is_detected(self) -> None:
        graph = {"A": {"B"}, "B": {"C"}, "C": {"A"}}
        self.assertEqual(["A", "B", "C", "A"], CHECK.dependency_cycle(graph))


if __name__ == "__main__":
    unittest.main()

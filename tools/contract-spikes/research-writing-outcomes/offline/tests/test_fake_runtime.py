from __future__ import annotations

from research_writing_outcome_spikes.fake_runtime import (
    FakeModel,
    append_repair,
    bind_verdict,
    evidence_case_verdict,
    evaluate_required_criteria,
    normalize_subagent_event,
    project_subagent_events,
    promote_artifact,
    substitution_rejected,
)

from support import OfflineTestCase


IDENTITY = {
    "tenant_id": "t",
    "workspace_id": "w",
    "source_id": "s",
    "actor_id": "a",
    "task_id": "task",
    "run_id": "run",
    "attempt_id": "attempt",
}


class FakeRuntimeTests(OfflineTestCase):
    def test_working_file_requires_matching_promotion(self) -> None:
        working = {"identity": IDENTITY, "content_hash": "abc", "state": "working"}
        promotion = {
            "identity": IDENTITY,
            "candidate_hash": "abc",
            "artifact_id": "artifact-1",
            "version": "1",
            "attestation_id": "promote-1",
        }
        promoted = promote_artifact(working, promotion)
        self.assertEqual("promoted", promoted["state"])
        self.assertEqual("artifact-1", promoted["artifact_id"])

    def test_subagent_parent_identity_is_exact(self) -> None:
        event = {
            "identity": IDENTITY,
            "state": "progress",
            "display_summary": "Bounded fact.",
            "subagent_id": "sub-1",
            "namespace": "parent/sub-1",
        }
        normalized = normalize_subagent_event(event, IDENTITY)
        self.assertEqual("parent_timeline", normalized["kind"])
        wrong = {**event, "identity": {**IDENTITY, "workspace_id": "wrong"}}
        with self.assertRaisesRegex(ValueError, "workspace_id"):
            normalize_subagent_event(wrong, IDENTITY)
        with self.assertRaisesRegex(ValueError, "namespace"):
            normalize_subagent_event({**event, "namespace": "parent/wrong"}, IDENTITY)

    def test_required_nonpassing_states_cannot_pass(self) -> None:
        for state in ("fail", "uncertain", "not_evaluated"):
            verdict, failed = evaluate_required_criteria(
                [{"criterion_id": "c1", "semantics": "required", "state": state}]
            )
            self.assertEqual("failed", verdict)
            self.assertEqual(["c1"], failed)

    def test_generic_model_pass_cannot_replace_required_evidence(self) -> None:
        candidate = {
            "identity": IDENTITY,
            "attempt_id": "attempt",
            "template_id": "research-v1",
            "rubric_version": "1",
        }
        evidence = [
            {
                "evidence_id": "ev-1",
                "identity": IDENTITY,
                "required": True,
                "state": "missing",
                "version": "1",
            }
        ]
        verdict = bind_verdict(candidate, evidence, FakeModel("Everything passed."))
        self.assertEqual("failed", verdict["state"])
        self.assertEqual(["ev-1"], verdict["invalid_required_evidence"])
        self.assertNotEqual("Everything passed.", verdict["display_rationale"])

    def test_repair_history_is_append_only(self) -> None:
        first = {
            "iteration": 1,
            "verdict_id": "v1",
            "supersedes_verdict_id": None,
            "identity": IDENTITY,
            "candidate_hash": "a" * 64,
            "evidence_versions": {"ev-1": "1"},
        }
        second = {
            "iteration": 2,
            "verdict_id": "v2",
            "supersedes_verdict_id": "v1",
            "identity": IDENTITY,
            "candidate_hash": "b" * 64,
            "evidence_versions": {"ev-1": "2"},
        }
        history = append_repair([], first)
        updated = append_repair(history, second)
        self.assertEqual(["v1"], [item["verdict_id"] for item in history])
        self.assertEqual(["v1", "v2"], [item["verdict_id"] for item in updated])

    def test_missing_identity_and_malformed_rubric_fail_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "identity fields"):
            promote_artifact(
                {"identity": {}, "content_hash": "x"},
                {
                    "identity": {},
                    "candidate_hash": "x",
                    "artifact_id": "a",
                    "version": "1",
                    "attestation_id": "p",
                },
            )
        with self.assertRaisesRegex(ValueError, "identity fields"):
            normalize_subagent_event(
                {
                    "identity": {},
                    "state": "progress",
                    "display_summary": "x",
                    "subagent_id": "s",
                    "namespace": "n",
                },
                {},
            )
        with self.assertRaisesRegex(ValueError, "criterion state"):
            evaluate_required_criteria(
                [{"criterion_id": "c", "semantics": "required", "state": "malformed"}]
            )
        with self.assertRaisesRegex(ValueError, "identity fields"):
            bind_verdict(
                {
                    "identity": {},
                    "attempt_id": "a",
                    "template_id": "t",
                    "rubric_version": "1",
                },
                [
                    {
                        "identity": {},
                        "evidence_id": "e",
                        "version": "1",
                        "required": True,
                        "state": "valid",
                    }
                ],
                FakeModel(),
            )

    def test_substitution_requires_distinct_presented_value(self) -> None:
        self.assertTrue(substitution_rejected("tenant-1", "tenant-2"))
        self.assertFalse(substitution_rejected("tenant-1", "tenant-1"))

    def test_duplicate_and_out_of_order_events_are_derived(self) -> None:
        events = [
            {"sequence": 1, "state": "spawned"},
            {"sequence": 2, "state": "progress"},
            {"sequence": 2, "state": "progress"},
            {"sequence": 4, "state": "completed"},
            {"sequence": 3, "state": "reconnected"},
        ]
        self.assertEqual(
            ["projected", "projected", "ignored-duplicate", "projected", "ignored-out-of-order"],
            [item["outcome"] for item in project_subagent_events(events)],
        )

    def test_fixture_verdicts_are_derived_from_inputs(self) -> None:
        self.assertEqual("failed", evidence_case_verdict("research", {"state": "missing"}))
        self.assertEqual(
            "failed",
            evidence_case_verdict(
                "writing",
                {"artifact_state": "promoted", "candidate_hash": "hash", "size_bytes": 0},
            ),
        )
        self.assertEqual(
            "failed",
            evidence_case_verdict(
                "coding-negative",
                {"state": "missing", "exit_status": None},
            ),
        )

    def test_candidate_attempt_must_match_identity(self) -> None:
        candidate = {
            "identity": IDENTITY,
            "attempt_id": "wrong-attempt",
            "template_id": "research-v1",
            "rubric_version": "1",
        }
        evidence = [
            {
                "evidence_id": "ev-1",
                "identity": IDENTITY,
                "required": True,
                "state": "valid",
                "version": "1",
            }
        ]
        with self.assertRaisesRegex(ValueError, "attempt id"):
            bind_verdict(candidate, evidence, FakeModel())

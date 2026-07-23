from __future__ import annotations

from research_writing_outcome_spikes.fake_runtime import (
    FakeModel,
    append_repair,
    bind_verdict,
    evaluate_required_criteria,
    normalize_subagent_event,
    promote_artifact,
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
        }
        second = {
            "iteration": 2,
            "verdict_id": "v2",
            "supersedes_verdict_id": "v1",
        }
        history = append_repair([], first)
        updated = append_repair(history, second)
        self.assertEqual(["v1"], [item["verdict_id"] for item in history])
        self.assertEqual(["v1", "v2"], [item["verdict_id"] for item in updated])

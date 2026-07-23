"""Tests for rubric versions and truthful verification records."""

from __future__ import annotations

from typing import Any

import pytest

from deepwork_agent import (
    HARD_VERIFICATION_ITERATION_CAP,
    VERIFIER_REF,
    RubricCriterion,
    RubricSpec,
    render_rubric,
)
from deepwork_agent.verification import build_verification_record

REPAIRED_ITERATIONS = 2
CAPPED_MAX_ITERATIONS = 2
SUMMARY_LENGTH_CAP = 1_000


def _spec(*, max_iterations: int = 2) -> RubricSpec:
    return RubricSpec(
        rubric_id="test-rubric",
        version=1,
        criteria=(
            RubricCriterion(criterion_id="claims-labeled", text="Claims are labeled."),
            RubricCriterion(
                criterion_id="style-advisory",
                text="Style suggestions are applied.",
                required=False,
            ),
        ),
        max_iterations=max_iterations,
    )


def _evaluation(
    result: str,
    iteration: int,
    criteria: list[dict[str, Any]],
    explanation: str = "Summary.",
) -> dict[str, Any]:
    return {
        "grading_run_id": "run-1",
        "iteration": iteration,
        "result": result,
        "explanation": explanation,
        "criteria": criteria,
    }


def test_verifier_ref_names_the_pinned_middleware_version() -> None:
    """The verifier reference is the pinned public middleware, no secret."""
    assert VERIFIER_REF == "deepagents:RubricMiddleware:0.6.12"


def test_render_rubric_lists_ids_and_requirement_labels() -> None:
    """The rendered rubric carries exact ids so verdicts map back onto it."""
    rendered = render_rubric(_spec())

    assert "set `name` to the exact criterion id" in rendered
    assert "- claims-labeled (required): Claims are labeled." in rendered
    assert "- style-advisory (advisory): Style suggestions are applied." in rendered


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"rubric_id": "Bad Id"}, "lowercase kebab-case"),
        ({"version": 0}, "version must be at least 1"),
        ({"criteria": ()}, "between 1 and 12"),
        (
            {
                "criteria": (
                    RubricCriterion(criterion_id="dup", text="a"),
                    RubricCriterion(criterion_id="dup", text="b"),
                )
            },
            "unique identifiers",
        ),
        ({"max_iterations": 0}, "between 1 and 5"),
        ({"max_iterations": HARD_VERIFICATION_ITERATION_CAP + 1}, "between 1 and 5"),
    ],
)
def test_rubric_spec_is_validated(kwargs: dict[str, Any], match: str) -> None:
    """Rubric versions fail closed on malformed identity, criteria, or caps."""
    arguments: dict[str, Any] = {
        "rubric_id": "test-rubric",
        "version": 1,
        "criteria": (RubricCriterion(criterion_id="one", text="One."),),
    }
    arguments.update(kwargs)
    with pytest.raises(ValueError, match=match):
        RubricSpec(**arguments)


def test_criterion_text_and_id_are_bounded() -> None:
    """Criterion identity and text respect explicit bounds."""
    with pytest.raises(ValueError, match="lowercase kebab-case"):
        RubricCriterion(criterion_id="UPPER", text="x")
    with pytest.raises(ValueError, match="1 to 500 characters"):
        RubricCriterion(criterion_id="ok", text="x" * 501)


def test_missing_evaluations_never_report_a_pass() -> None:
    """No grader verdict means an error status, not an implicit pass."""
    record = build_verification_record(_spec(), [])

    assert record["status"] == "error"
    assert record["status_reason"] == "no-verdict-recorded"
    assert record["iterations_used"] == 0
    assert record["verdicts"] == []
    assert record["trust"] == "untrusted"


def test_repair_history_is_preserved_in_order() -> None:
    """Earlier failed verdicts stay visible after a later pass."""
    evaluations = [
        _evaluation(
            "needs_revision",
            0,
            [{"name": "claims-labeled", "passed": False, "gap": "Label the claims."}],
        ),
        _evaluation(
            "satisfied",
            1,
            [
                {"name": "claims-labeled", "passed": True},
                {"name": "style-advisory", "passed": True},
            ],
        ),
    ]

    record = build_verification_record(_spec(), evaluations)

    assert record["status"] == "passed"
    assert record["status_reason"] == "satisfied"
    assert record["iterations_used"] == REPAIRED_ITERATIONS
    first, second = record["verdicts"]
    assert first["verdict"] == "needs_revision"
    assert first["results"][0]["outcome"] == "fail"
    assert first["results"][0]["rationale_summary"] == "Label the claims."
    assert first["results"][1]["outcome"] == "not_evaluated"
    assert second["verdict"] == "satisfied"
    assert all(result["outcome"] == "pass" for result in second["results"])


def test_cap_status_when_final_verdict_still_needs_revision() -> None:
    """Hitting the iteration cap reports capped, never a silent pass."""
    evaluations = [
        _evaluation(
            "needs_revision",
            iteration,
            [{"name": "claims-labeled", "passed": False, "gap": "Still failing."}],
        )
        for iteration in range(2)
    ]

    record = build_verification_record(_spec(max_iterations=2), evaluations)

    assert record["status"] == "capped"
    assert record["status_reason"] == "iteration-cap-reached"
    assert record["max_iterations"] == CAPPED_MAX_ITERATIONS
    assert record["verdicts"][-1]["results"][0]["outcome"] == "fail"


def test_statuses_distinguish_rubric_and_grader_failures() -> None:
    """Rubric-unevaluable and grader outages map to distinct error reasons."""
    unevaluable = build_verification_record(
        _spec(), [_evaluation("failed", 0, [], explanation="Contradictory rubric.")]
    )
    outage = build_verification_record(_spec(), [_evaluation("grader_error", 0, [])])
    failing = build_verification_record(
        _spec(max_iterations=3),
        [
            _evaluation(
                "needs_revision", 0, [{"name": "claims-labeled", "passed": False, "gap": "g"}]
            )
        ],
    )

    assert (unevaluable["status"], unevaluable["status_reason"]) == ("error", "rubric-unevaluable")
    assert (outage["status"], outage["status_reason"]) == ("error", "grader-error")
    assert (failing["status"], failing["status_reason"]) == ("failed", "criteria-failing")


def test_untrusted_grader_content_is_bounded_and_mapped_defensively() -> None:
    """Unknown names, oversized text, and wrong types cannot corrupt the record."""
    evaluations = [
        _evaluation(
            "satisfied",
            0,
            [
                {"name": "claims-labeled", "passed": True},
                {"name": "invented-criterion", "passed": True},
                {"name": 42, "passed": True},
                "not a mapping",
            ],
            explanation="x" * 5_000,
        ),
        {"result": "unexpected-status", "iteration": "one", "criteria": None},
    ]

    record = build_verification_record(_spec(), evaluations)

    first, second = record["verdicts"]
    assert first["unmatched_criteria"] == ["invented-criterion"]
    assert len(first["summary"]) == SUMMARY_LENGTH_CAP
    assert second["verdict"] == "grader_error"
    assert second["iteration"] == 1
    assert all(result["outcome"] == "not_evaluated" for result in second["results"])
    assert record["status"] == "error"

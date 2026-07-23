"""Versioned rubric criteria and truthful verification records.

The automatic loop itself is owned by the pinned public
``deepagents.RubricMiddleware``; this module only declares the immutable rubric
a journey dispatches with, renders it into the middleware's ``rubric`` state
contract, and maps the middleware's evaluation history into an append-ordered
verification record. Verdicts are fallible model output and are always marked
``untrusted``; a passed verdict is rubric coverage, never ground truth.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, cast

from deepagents import __version__ as _deepagents_version
from typing_extensions import TypedDict

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

VERIFIER_REF = f"deepagents:RubricMiddleware:{_deepagents_version}"
"""Identity of the pinned verifier implementation, without any secret."""

HARD_VERIFICATION_ITERATION_CAP = 5
"""Package-level hard cap on grader iterations per journey run.

Deliberately stricter than the middleware's own hard cap of 20 so a local run
can never spend unbounded repair iterations.
"""

_MAX_CRITERIA = 12
_MAX_CRITERION_TEXT_LENGTH = 500
_MAX_IDENTIFIER_LENGTH = 64
_MAX_SUMMARY_LENGTH = 1_000
_MAX_UNMATCHED_NAMES = 12
_IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")

CriterionOutcome = Literal["pass", "fail", "not_evaluated"]
GraderVerdictLabel = Literal["satisfied", "needs_revision", "failed", "grader_error"]
VerificationStatus = Literal["passed", "failed", "capped", "error"]


def _require_identifier(value: str, *, field: str) -> str:
    """Validate a lowercase kebab-case identifier."""
    if not value or len(value) > _MAX_IDENTIFIER_LENGTH or not _IDENTIFIER_PATTERN.fullmatch(value):
        msg = f"{field} must be lowercase kebab-case with at most 64 characters"
        raise ValueError(msg)
    return value


@dataclass(frozen=True, slots=True)
class RubricCriterion:
    """One reviewable success criterion inside a versioned rubric."""

    criterion_id: str
    text: str
    required: bool = True

    def __post_init__(self) -> None:
        """Validate identifier and bounded criterion text."""
        _require_identifier(self.criterion_id, field="criterion_id")
        text = self.text.strip()
        if not text or len(text) > _MAX_CRITERION_TEXT_LENGTH:
            msg = "criterion text must contain 1 to 500 characters"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class RubricSpec:
    """Immutable rubric version dispatched with one journey run."""

    rubric_id: str
    version: int
    criteria: tuple[RubricCriterion, ...]
    max_iterations: int = 3

    def __post_init__(self) -> None:
        """Validate identifiers, bounded criteria, and the hard iteration cap."""
        _require_identifier(self.rubric_id, field="rubric_id")
        if self.version < 1:
            msg = "rubric version must be at least 1"
            raise ValueError(msg)
        if not 1 <= len(self.criteria) <= _MAX_CRITERIA:
            msg = f"rubric must contain between 1 and {_MAX_CRITERIA} criteria"
            raise ValueError(msg)
        criterion_ids = [criterion.criterion_id for criterion in self.criteria]
        if len(set(criterion_ids)) != len(criterion_ids):
            msg = "rubric criteria must have unique identifiers"
            raise ValueError(msg)
        if not 1 <= self.max_iterations <= HARD_VERIFICATION_ITERATION_CAP:
            msg = f"rubric max_iterations must be between 1 and {HARD_VERIFICATION_ITERATION_CAP}"
            raise ValueError(msg)


def render_rubric(spec: RubricSpec) -> str:
    """Render the rubric into the middleware's ``rubric`` state contract.

    The grader is instructed to reuse the exact criterion identifiers so its
    per-criterion verdicts can be mapped back onto this rubric version.
    """
    lines = [
        "Evaluate the work against every criterion below. In each per-criterion "
        "verdict, set `name` to the exact criterion id shown before the colon.",
    ]
    lines.extend(
        f"- {criterion.criterion_id} "
        f"({'required' if criterion.required else 'advisory'}): {criterion.text.strip()}"
        for criterion in spec.criteria
    )
    return "\n".join(lines)


class CriterionResult(TypedDict):
    """Mapped grader outcome for one rubric criterion in one iteration."""

    criterion_id: str
    required: bool
    outcome: CriterionOutcome
    rationale_summary: str


class VerificationVerdict(TypedDict):
    """One grader iteration, preserved verbatim in order."""

    iteration: int
    verdict: GraderVerdictLabel
    summary: str
    results: list[CriterionResult]
    unmatched_criteria: list[str]


class VerificationRecord(TypedDict):
    """Complete verification outcome for one journey run.

    ``verdicts`` is the full append-ordered repair history; earlier failed
    iterations are never overwritten by a later pass.
    """

    rubric_id: str
    rubric_version: int
    verifier_ref: str
    max_iterations: int
    iterations_used: int
    status: VerificationStatus
    status_reason: str
    verdicts: list[VerificationVerdict]
    trust: Literal["untrusted"]


def _bounded_text(value: object, *, max_length: int) -> str:
    """Coerce untrusted grader text into a bounded printable summary."""
    text = value if isinstance(value, str) else ""
    text = text.strip()
    if len(text) > max_length:
        return text[:max_length]
    return text


def _map_criterion_entries(
    spec: RubricSpec,
    raw_criteria: object,
) -> tuple[list[CriterionResult], list[str]]:
    """Map grader per-criterion entries onto the rubric's criterion ids."""
    entries = raw_criteria if isinstance(raw_criteria, list) else []
    by_name: dict[str, Mapping[str, object]] = {}
    unmatched: list[str] = []
    known_ids = {criterion.criterion_id for criterion in spec.criteria}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        if not isinstance(name, str):
            continue
        if name in known_ids:
            by_name.setdefault(name, cast("Mapping[str, object]", entry))
        elif len(unmatched) < _MAX_UNMATCHED_NAMES:
            unmatched.append(_bounded_text(name, max_length=_MAX_IDENTIFIER_LENGTH))
    results: list[CriterionResult] = []
    for criterion in spec.criteria:
        entry = by_name.get(criterion.criterion_id)
        if entry is None:
            outcome: CriterionOutcome = "not_evaluated"
            rationale = ""
        else:
            outcome = "pass" if entry.get("passed") is True else "fail"
            rationale = _bounded_text(entry.get("gap", ""), max_length=_MAX_SUMMARY_LENGTH)
        results.append(
            {
                "criterion_id": criterion.criterion_id,
                "required": criterion.required,
                "outcome": outcome,
                "rationale_summary": rationale,
            }
        )
    return results, unmatched


def _map_verdict(
    spec: RubricSpec, index: int, evaluation: Mapping[str, object]
) -> VerificationVerdict:
    """Map one middleware evaluation into a bounded verdict record."""
    raw_result = evaluation.get("result")
    verdict: GraderVerdictLabel = (
        cast("GraderVerdictLabel", raw_result)
        if raw_result in ("satisfied", "needs_revision", "failed", "grader_error")
        else "grader_error"
    )
    raw_iteration = evaluation.get("iteration")
    iteration = raw_iteration if isinstance(raw_iteration, int) else index
    results, unmatched = _map_criterion_entries(spec, evaluation.get("criteria"))
    return {
        "iteration": iteration,
        "verdict": verdict,
        "summary": _bounded_text(evaluation.get("explanation"), max_length=_MAX_SUMMARY_LENGTH),
        "results": results,
        "unmatched_criteria": unmatched,
    }


def _terminal_status(
    spec: RubricSpec,
    verdicts: Sequence[VerificationVerdict],
) -> tuple[VerificationStatus, str]:
    """Derive the truthful terminal status from the ordered verdict history."""
    if not verdicts:
        return "error", "no-verdict-recorded"
    last = verdicts[-1]["verdict"]
    if last == "satisfied":
        return "passed", "satisfied"
    if last == "grader_error":
        return "error", "grader-error"
    if last == "failed":
        return "error", "rubric-unevaluable"
    if len(verdicts) >= spec.max_iterations:
        return "capped", "iteration-cap-reached"
    return "failed", "criteria-failing"


def build_verification_record(
    spec: RubricSpec,
    evaluations: Sequence[Mapping[str, object]],
) -> VerificationRecord:
    """Map the middleware's evaluation history into a verification record.

    Args:
        spec: The immutable rubric version the run dispatched with.
        evaluations: Ordered ``RubricEvaluation`` payloads observed through the
            middleware's public ``on_evaluation`` callback.

    Returns:
        A bounded record with the full repair history and a terminal status
        that can never report an automatic pass unless the final grader
        verdict was ``satisfied``.

    """
    verdicts = [
        _map_verdict(spec, index, evaluation) for index, evaluation in enumerate(evaluations)
    ]
    status, status_reason = _terminal_status(spec, verdicts)
    return {
        "rubric_id": spec.rubric_id,
        "rubric_version": spec.version,
        "verifier_ref": VERIFIER_REF,
        "max_iterations": spec.max_iterations,
        "iterations_used": len(verdicts),
        "status": status,
        "status_reason": status_reason,
        "verdicts": verdicts,
        "trust": "untrusted",
    }

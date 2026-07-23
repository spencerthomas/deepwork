"""Deterministic fake normalization runtime; this is not Deep Agents behavior."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .common import (
    IDENTITY_FIELDS,
    ValidationError,
    canonical_json,
    exact_identity,
    require,
    sha256_bytes,
)


TERMINAL = {"passed", "failed", "unsupported", "manually_reviewed", "cancelled", "capped"}
NON_PASSING_REQUIRED = {"fail", "uncertain", "not_evaluated"}


@dataclass(frozen=True)
class FakeModel:
    """Returns a fixed untrusted summary so evidence binding can overrule it."""

    summary: str = "Everything passed."

    def invoke(self, _messages: list[dict[str, str]]) -> str:
        return self.summary


def promote_artifact(working: dict[str, Any], promotion: dict[str, Any]) -> dict[str, Any]:
    exact_identity(working.get("identity"), label="working artifact")
    exact_identity(promotion.get("identity"), label="artifact promotion")
    if working["identity"] != promotion["identity"]:
        raise ValidationError("artifact promotion identity mismatch")
    if working["content_hash"] != promotion["candidate_hash"]:
        raise ValidationError("artifact promotion candidate mismatch")
    return {
        **working,
        "artifact_id": promotion["artifact_id"],
        "version": promotion["version"],
        "state": "promoted",
        "promotion_attestation": promotion["attestation_id"],
    }


def normalize_subagent_event(event: dict[str, Any], parent: dict[str, Any]) -> dict[str, Any]:
    exact_identity(event.get("identity"), label="subagent event")
    exact_identity(parent, label="subagent parent")
    for field in IDENTITY_FIELDS:
        if event["identity"].get(field) != parent.get(field):
            raise ValidationError(f"subagent parent mismatch: {field}")
    if "hidden_reasoning" in event or "prompt" in event:
        raise ValidationError("hidden subagent content is forbidden")
    allowed = {"spawned", "progress", "completed", "failed", "cancelled", "reconnected"}
    if event.get("state") not in allowed:
        return {
            "kind": "parent_timeline",
            "state": "unknown",
            "summary": "Source supplied an unsupported subagent event.",
        }
    return {
        "kind": "parent_timeline",
        "state": event["state"],
        "summary": event["display_summary"][:240],
        "subagent_id": event["subagent_id"],
        "namespace": event["namespace"],
    }


def evaluate_required_criteria(criteria: list[dict[str, Any]]) -> tuple[str, list[str]]:
    require(isinstance(criteria, list) and criteria, "criteria must be a non-empty list")
    allowed_states = {"pass", "fail", "uncertain", "not_evaluated"}
    allowed_semantics = {"required", "advisory"}
    for criterion in criteria:
        require(criterion.get("state") in allowed_states, "criterion state is invalid")
        require(criterion.get("semantics") in allowed_semantics, "criterion semantics is invalid")
        require(
            isinstance(criterion.get("criterion_id"), str) and criterion["criterion_id"],
            "criterion id is missing",
        )
    failed = [
        criterion["criterion_id"]
        for criterion in criteria
        if criterion["semantics"] == "required"
        and criterion["state"] in NON_PASSING_REQUIRED
    ]
    return ("failed" if failed else "passed", failed)


def bind_verdict(candidate: dict[str, Any], evidence: list[dict[str, Any]], model: FakeModel) -> dict[str, Any]:
    identity = exact_identity(candidate.get("identity"), label="verdict candidate")
    require(isinstance(evidence, list) and evidence, "verdict evidence must be non-empty")
    rationale = model.invoke([])[:240]
    required = [item for item in evidence if item["required"]]
    invalid = [item["evidence_id"] for item in required if item["state"] != "valid"]
    for item in evidence:
        exact_identity(item.get("identity"), label=f"evidence {item.get('evidence_id', '<missing>')}")
        require(isinstance(item.get("evidence_id"), str) and item["evidence_id"], "evidence id missing")
        require(isinstance(item.get("version"), str) and item["version"], "evidence version missing")
        require(item.get("state") in {"valid", "invalid", "missing", "fail"}, "evidence state invalid")
        for field in IDENTITY_FIELDS:
            if item["identity"].get(field) != identity.get(field):
                invalid.append(item["evidence_id"])
                break
    state = "failed" if invalid else "passed"
    return {
        "verdict_id": f"verdict-{candidate['attempt_id']}",
        "identity": identity,
        "template_id": candidate["template_id"],
        "rubric_version": candidate["rubric_version"],
        "candidate_hash": sha256_bytes(canonical_json(candidate)),
        "evidence_versions": {
            item["evidence_id"]: item["version"] for item in evidence
        },
        "state": state,
        "invalid_required_evidence": sorted(set(invalid)),
        "display_rationale": (
            rationale
            if not invalid
            else "Required source-owned evidence is missing, invalid, or mismatched."
        ),
    }


def append_repair(history: list[dict[str, Any]], next_entry: dict[str, Any]) -> list[dict[str, Any]]:
    identity = exact_identity(next_entry.get("identity"), label="repair entry")
    require(
        isinstance(next_entry.get("candidate_hash"), str)
        and len(next_entry["candidate_hash"]) == 64,
        "repair candidate hash missing",
    )
    require(
        isinstance(next_entry.get("evidence_versions"), dict)
        and next_entry["evidence_versions"],
        "repair evidence versions missing",
    )
    if history:
        previous = history[-1]
        exact_identity(previous.get("identity"), label="previous repair entry")
        if previous["identity"] != identity:
            raise ValidationError("repair identity mismatch")
        if next_entry["iteration"] != previous["iteration"] + 1:
            raise ValidationError("repair iteration must be contiguous")
        if next_entry["supersedes_verdict_id"] != previous["verdict_id"]:
            raise ValidationError("repair history must supersede the prior verdict")
        if (
            next_entry["candidate_hash"] == previous["candidate_hash"]
            and next_entry["evidence_versions"] == previous["evidence_versions"]
        ):
            raise ValidationError("repair must bind changed candidate or evidence")
    elif next_entry["iteration"] != 1:
        raise ValidationError("repair history must begin at iteration one")
    if any(item["verdict_id"] == next_entry["verdict_id"] for item in history):
        raise ValidationError("verdict history must be append-only and unique")
    return [*history, dict(next_entry)]


def substitution_rejected(expected: str, presented: str) -> bool:
    require(isinstance(expected, str) and expected, "expected binding missing")
    require(isinstance(presented, str) and presented, "presented binding missing")
    return expected != presented

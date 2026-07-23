"""Shared validation rules for the retained contract evidence."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

SPIKE_IDS = (
    "SPIKE-SOURCE-001",
    "SPIKE-CONFIG-001",
    "SPIKE-DEPLOY-001",
    "SPIKE-COMPOSE-001",
    "SPIKE-THREADS-001",
    "SPIKE-STREAM-001",
    "SPIKE-STREAM-002",
    "SPIKE-STREAM-003",
    "SPIKE-HITL-001",
    "SPIKE-CANCEL-001",
    "SPIKE-CHECKPOINT-001",
)

REQUIRED_ROW_KEYS = (
    "spike_id",
    "operation",
    "evidence_level",
    "environment",
    "request",
    "response_schema",
    "errors",
    "idempotency",
    "retry",
    "cancel",
    "reconnect",
    "result",
    "fallback",
    "sources",
    "downstream_acceptance_ids",
)

EVIDENCE_LEVELS = {
    "official-documented",
    "installed-public-contract",
    "sanitized-live-classic-sandbox",
    "unsupported-or-unknown",
}

RESULTS = {
    "documented",
    "accepted-installed",
    "accepted-live",
    "blocked-live-evidence",
    "rejected",
}


def validate_matrix_document(document: Mapping[str, Any]) -> list[str]:
    """Return deterministic validation errors for a matrix document."""
    errors: list[str] = []
    if document.get("schema_version") != "1.0":
        errors.append("schema_version must equal 1.0")
    rows = document.get("rows")
    if not isinstance(rows, list):
        return [*errors, "rows must be a list"]
    installed = document.get("installed_public_distributions")
    if installed != {}:
        errors.append("installed_public_distributions must be an empty object until inventory proves exact distributions")

    seen: set[str] = set()
    for index, row in enumerate(rows):
        label = f"rows[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{label} must be an object")
            continue
        for key in REQUIRED_ROW_KEYS:
            if key not in row:
                errors.append(f"{label} missing {key}")
        spike_id = row.get("spike_id")
        if spike_id not in SPIKE_IDS:
            errors.append(f"{label} has unknown spike_id {spike_id!r}")
        elif spike_id in seen:
            errors.append(f"{label} duplicates spike_id {spike_id}")
        else:
            seen.add(spike_id)
        if row.get("evidence_level") not in EVIDENCE_LEVELS:
            errors.append(f"{label} has invalid evidence_level")
        if not installed:
            if row.get("evidence_level") == "installed-public-contract":
                errors.append(f"{label} cannot claim installed evidence without an installed distribution inventory")
            if any(item.get("level") == "installed-public-contract" for item in row.get("evidence", [])):
                errors.append(f"{label} evidence cannot claim an unavailable installed distribution")
            if "installed" in row.get("response_schema", {}):
                errors.append(f"{label} response_schema cannot use installed without installed distribution evidence")
        result = row.get("result")
        if result not in RESULTS:
            errors.append(f"{label} has invalid result")
        if result == "accepted-live" and row.get("evidence_level") != "sanitized-live-classic-sandbox":
            errors.append(f"{label} accepted-live requires sanitized live evidence")
        if result == "blocked-live-evidence" and row.get("environment", {}).get("live_evidence") != "unavailable":
            errors.append(f"{label} blocked-live-evidence must declare unavailable live evidence")
        sources = row.get("sources")
        if not isinstance(sources, list) or not sources:
            errors.append(f"{label} sources must be a non-empty list")
        elif any(not isinstance(source, dict) or not source.get("revision") for source in sources):
            errors.append(f"{label} every source must include a revision")

    missing = sorted(set(SPIKE_IDS) - seen)
    if missing:
        errors.append(f"missing spike rows: {', '.join(missing)}")
    return errors


def validate_ordered_decisions(
    action_requests: Iterable[Mapping[str, Any]],
    review_configs: Iterable[Mapping[str, Any]],
    decisions: Iterable[Mapping[str, Any]],
) -> None:
    """Reject lossy or reordered HITL batches before any submission."""
    requests = list(action_requests)
    configs = list(review_configs)
    submitted = list(decisions)
    if not requests or len(requests) != len(configs) or len(requests) != len(submitted):
        raise ValueError("action_requests, review_configs, and decisions must have equal non-zero length")
    for index, (request, config, decision) in enumerate(zip(requests, configs, submitted, strict=True)):
        if set(request) - {"name", "args", "description"}:
            raise ValueError(f"unexpected action request keys at index {index}")
        if not {"name", "args"} <= set(request):
            raise ValueError(f"incomplete action request at index {index}")
        if set(config) - {"action_name", "allowed_decisions", "args_schema"}:
            raise ValueError(f"unexpected review config keys at index {index}")
        if not {"action_name", "allowed_decisions"} <= set(config):
            raise ValueError(f"incomplete review config at index {index}")
        if request.get("name") != config.get("action_name"):
            raise ValueError(f"ordered HITL alignment failed at index {index}")
        allowed = config.get("allowed_decisions", [])
        if decision.get("type") not in allowed:
            raise ValueError(f"decision {decision.get('type')!r} is not allowed at index {index}")
        decision_type = decision.get("type")
        allowed_keys = {
            "approve": {"type"},
            "edit": {"type", "edited_action"},
            "reject": {"type", "message"},
            "respond": {"type", "message"},
        }
        if decision_type not in allowed_keys or set(decision) - allowed_keys[decision_type]:
            raise ValueError(f"unexpected decision shape at index {index}")
        if decision_type in {"edit", "respond"} and len(decision) != 2:
            raise ValueError(f"incomplete decision shape at index {index}")
        if decision_type == "edit":
            edited = decision.get("edited_action")
            if not isinstance(edited, dict) or set(edited) != {"name", "args"}:
                raise ValueError(f"invalid edited action at index {index}")


def dedupe_protocol_events(events: Iterable[Mapping[str, Any]], since: int) -> list[Mapping[str, Any]]:
    """Project protocol-v3 replay using seq for position and event_id for identity."""
    output: list[Mapping[str, Any]] = []
    event_ids: set[str] = set()
    last_seq = since
    for event in events:
        seq = event.get("seq")
        event_id = event.get("event_id")
        if not isinstance(seq, int) or not isinstance(event_id, str):
            raise ValueError("protocol-v3 events require integer seq and string event_id")
        if seq <= since or event_id in event_ids:
            continue
        if seq < last_seq:
            raise ValueError("protocol-v3 seq must not move backwards")
        event_ids.add(event_id)
        last_seq = seq
        output.append(event)
    return output

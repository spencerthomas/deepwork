"""Generate the complete matrix from the immutable scope."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from attachment_contract_spikes.scope import (
    derive_identities,
    load_json,
    row_id,
    scope_lookup,
    scope_sha256,
)


TRANSFER_CORE = {"transfer-intent", "transfer-receipt"}
PROVIDER_LIFECYCLE = {
    "delete-after-transfer",
    "provider-deletion-failure",
}
HOSTED_OBJECT_OR_SCANNER = {
    "quarantine-create",
    "metadata-hash-detected-type",
    "scan-clean",
    "scan-unsafe",
    "scan-error",
    "scan-timeout",
    "scan-unavailable",
    "retention-expiry",
}
FIXTURE_BYTES = {
    "bounded-text-file": b"Synthetic bounded text attachment.\n",
    "image": b"\x89PNG\r\n\x1a\n",
    "pdf": b"%PDF-1.4\n% harmless synthetic fixture\n",
    "code": b"result = 2 + 2  # inert text fixture\n",
}
MAX_BYTES = {
    "bounded-text-file": 64 * 1024,
    "image": 2 * 1024 * 1024,
    "pdf": 5 * 1024 * 1024,
    "code": 128 * 1024,
}


def conclusion_for(identity: dict[str, str]) -> tuple[str, str, str | None]:
    """Return conclusion, primary evidence tier, and blocker."""
    operation = identity["lifecycle_operations"]
    boundary = identity["byte_boundaries"]
    representation = identity["transfer_representations"]

    if operation in TRANSFER_CORE and boundary == "deep-work-quarantine":
        if representation == "standard-content-provider-file-id":
            return (
                "unsupported",
                "deterministic-fake",
                "quarantined Deep Work bytes cannot already be provider-managed",
            )
        return (
            "rejected",
            "deterministic-fake",
            "quarantined bytes are never transferable or agent-visible",
        )
    if operation in TRANSFER_CORE:
        if representation == "standard-content-provider-file-id":
            return (
                "unknown",
                "unknown",
                "no public Classic provider-file creation or ownership contract",
            )
        return (
            "blocked-live-evidence",
            "official-documented",
            "sanctioned non-production Classic runtime profile not supplied",
        )
    if operation in PROVIDER_LIFECYCLE:
        if representation == "standard-content-provider-file-id":
            return (
                "unknown",
                "unknown",
                "provider-managed file deletion contract is not public Classic proof",
            )
        return (
            "blocked-live-evidence",
            "deterministic-fake",
            "provider deletion behavior requires sanctioned non-production proof",
        )
    if operation in HOSTED_OBJECT_OR_SCANNER:
        dependency = "scanner" if operation.startswith("scan-") else "object store"
        return (
            "blocked-live-evidence",
            "deterministic-fake",
            f"real {dependency} behavior requires sanctioned non-production proof",
        )
    return ("accepted-fixture-only", "deterministic-fake", None)


def transition_for(operation: str) -> list[str]:
    """Return the expected fail-closed state transition."""
    if operation.startswith("preflight-reject"):
        return ["selected", "rejected", "agent-visibility-denied"]
    if operation == "preflight-accept":
        return ["selected", "policy-validated", "quarantine-required"]
    if operation == "quarantine-create":
        return ["policy-validated", "quarantined", "agent-visibility-denied"]
    if operation == "metadata-hash-detected-type":
        return ["quarantined", "integrity-verified", "agent-visibility-denied"]
    if operation == "detected-type-mismatch":
        return ["quarantined", "rejected", "agent-visibility-denied"]
    if operation == "scan-clean":
        return ["quarantined", "clean-not-authorized", "agent-visibility-denied"]
    if operation.startswith("scan-"):
        return ["quarantined", operation.removeprefix("scan-"), "agent-visibility-denied"]
    if operation == "transfer-intent":
        return ["clean-not-authorized", "transfer-ready", "agent-visibility-denied"]
    if operation == "transfer-receipt":
        return ["transfer-ready", "transferred", "receipt-recorded"]
    if operation.startswith("transfer-reject"):
        return ["transfer-ready", "rejected", "agent-visibility-denied"]
    if operation == "remove-before-transfer":
        return ["quarantined-or-clean", "removed", "future-transfer-denied"]
    if operation == "delete-after-transfer":
        return ["transferred", "local-delete-recorded", "provider-delete-separate"]
    if operation == "retention-expiry":
        return ["retained", "expired", "cleanup-audited"]
    if operation == "provider-deletion-failure":
        return ["delete-requested", "provider-delete-unverified", "retry-pending"]
    if operation == "orphan-cleanup":
        return ["orphaned", "cleanup-audited", "idempotent-terminal"]
    if operation == "retry":
        return ["retryable-failure", "same-authority", "no-duplicate-visibility"]
    if operation == "restart-recovery":
        return ["persisted-verdict", "recovered-same-verdict", "no-visibility-broadening"]
    return ["available-or-pending", "unavailable-or-error", "fail-closed-with-fallback"]


def schemas_for(operation: str, representation: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return bounded sanitized request and response shapes."""
    request = {
        "required": [
            "actor_id",
            "workspace_id",
            "task_id",
            "object_id",
            "sha256",
            "size",
        ],
        "representation": representation,
        "operation": operation,
        "credentials": "server-side-reference-only",
    }
    response = {
        "required": ["state", "audit_event_id"],
        "never_contains": [
            "credentials",
            "raw_headers",
            "cookies",
            "reusable_grants",
            "unsafe_content",
        ],
    }
    if operation == "transfer-intent":
        request["required"].extend(["destination", "expires_at", "idempotency_key"])
    if operation == "transfer-receipt":
        response["required"].extend(["receipt_id", "verified_sha256", "verified_size"])
    return request, response


def build_row(
    scope: dict[str, Any],
    identity: dict[str, str],
    scope_hash: str,
) -> dict[str, Any]:
    """Build one complete source-qualified matrix row."""
    operation = identity["lifecycle_operations"]
    conclusion, tier, blocker = conclusion_for(identity)
    operation_scope = scope_lookup(scope, "lifecycle_operations", operation)
    media_scope = scope_lookup(scope, "media_classes", identity["media_classes"])
    request_schema, response_schema = schemas_for(
        operation, identity["transfer_representations"]
    )
    fixture_bytes = FIXTURE_BYTES[identity["media_classes"]]
    observations: list[dict[str, str]] = [
        {
            "evidence_tier": "deterministic-fake",
            "source_ref": "attachment_contract_spikes.state_machine",
            "observation": (
                "The network-denied fake enforces the declared fail-closed transition. "
                "It is not hosted-provider proof."
            ),
        },
        {
            "evidence_tier": "official-documented",
            "source_ref": "SRC-LC-MESSAGES@7b9215d708e0b57e6fbae7b5d0762c4118b8e309",
            "observation": (
                "The representation is a candidate standard content block. "
                "Graph, model, account, scanner, retention, and cleanup support remain unproved."
            ),
        },
        {
            "evidence_tier": "installed-public",
            "source_ref": "langgraph-sdk==0.4.2",
            "observation": (
                "Classic run creation accepts graph-defined JSON input and exposes no "
                "source-independent attachment upload schema in the examined public client."
            ),
        },
    ]
    if tier == "unknown":
        observations.append(
            {
                "evidence_tier": "unknown",
                "source_ref": "no-sanctioned-live-profile",
                "observation": "No higher-precedence evidence decides this row.",
            }
        )
    return {
        "row_id": row_id(identity),
        "identity": identity,
        "scope_sha256": scope_hash,
        "scope_revision": scope["scope_revision"],
        "packet_id": scope["packet_id"],
        "gate_id": scope["gate_id"],
        "versions": {
            "SRC-LC": scope["evidence_pins"]["SRC-LC"]["commit"],
            "SRC-DA": scope["evidence_pins"]["SRC-DA"]["commit"],
            "deepagents": scope["evidence_pins"]["SRC-DA"]["package_version"],
            "SRC-LG": scope["evidence_pins"]["SRC-LG"]["commit"],
            "langgraph-sdk": scope["evidence_pins"]["SRC-LG"]["package_version"],
            "object_store": "deterministic-fake-v1; live-version-unknown",
            "scanner": "deterministic-fake-v1; live-version-unknown",
            "classic_runtime": "public-client-0.4.2; live-server-version-unknown",
        },
        "live_context": {
            "account_tier": "unknown",
            "region": "unknown",
            "authentication_context": "not-supplied",
            "observation_date": "2026-07-23",
        },
        "expected_conclusion_class": operation_scope["expected_conclusion_class"],
        "source_observations": observations,
        "state_transitions": transition_for(operation),
        "request_schema": request_schema,
        "response_schema": response_schema,
        "policy": {
            "max_count": 4,
            "max_bytes": MAX_BYTES[identity["media_classes"]],
            "declared_media_type": media_scope["declared_media_type"],
            "detected_media_type_required": True,
            "empty_content": "reject",
            "unsafe_or_traversal_filename": "reject",
            "duplicate_or_hash_mismatch": "reject",
        },
        "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
        "integrity": {
            "sha256_required": True,
            "size_required": True,
            "declared_and_detected_type_required": True,
            "filename_normalization_required": True,
        },
        "authorization": {
            "actor_bound": True,
            "workspace_bound": True,
            "task_bound": True,
            "object_bound": True,
            "destination_bound": True,
            "expiry_required": True,
            "idempotency_required": True,
        },
        "evidence_tier": tier,
        "conclusion": conclusion,
        "blocker": blocker,
        "blocker_owner": (
            "coordinator-supplied-non-production-access" if blocker else None
        ),
        "fallback": scope["required_fallback"],
        "provider_proof": False,
        "precedence_conflict": False,
        "acceptance_contribution": [
            "AC-DW-TASK-002-03",
            "AC-DW-QUAL-001-03",
            "AC-DW-QUAL-001-04",
        ],
        "e2e_v1_01_effect": "neither-blocks-nor-satisfies",
    }


def generate(scope_path: Path, output_path: Path) -> dict[str, Any]:
    """Generate and retain a stable, complete matrix."""
    scope = load_json(scope_path)
    digest = scope_sha256(scope_path)
    rows = [build_row(scope, identity, digest) for identity in derive_identities(scope)]
    payload = {
        "schema_version": "1.0",
        "scope_sha256": digest,
        "row_count": len(rows),
        "generated_from": "matrix-scope.json",
        "rows": rows,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("scope", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    payload = generate(args.scope, args.output)
    print(f"generated {payload['row_count']} rows")


if __name__ == "__main__":
    main()

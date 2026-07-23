#!/usr/bin/env python3
"""Read-only deterministic validation for the private product-demo corpus."""

import argparse
import ast
import copy
import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EPOCH = "2026-07-23T00:00:00Z"
TICK_MS = 250
FORMAT_VERSION = "1.0.0"
EXPECTED_CASE_PATHS = [
    "cases/start.json",
    "cases/content.json",
    "cases/tool.json",
    "cases/ordered-interrupt.json",
    "cases/checkpoint.json",
    "cases/reconnect.json",
    "cases/replay.json",
    "cases/logical-delay.json",
    "cases/completion.json",
    "cases/unknown.json",
    "cases/malformed-input.json",
    "cases/partial-failure.json",
    "cases/source-collision.json",
]
EXPECTED_CATEGORIES = [
    "start",
    "content",
    "tool",
    "ordered-interrupt",
    "checkpoint",
    "reconnect",
    "replay",
    "logical-delay",
    "completion",
    "unknown",
    "malformed-input",
    "partial-failure",
    "source-collision",
]
EXPECTED_NEGATIVE_PATHS = [
    "negative/invalid-schema.json",
    "negative/invalid-schema-expected-type.json",
    "negative/invalid-schema-payload-type.json",
    "negative/invalid-schema-semantic-list.json",
    "negative/invalid-schema-unhashable-decision.json",
    "negative/invalid-schema-semantic-required.json",
    "negative/invalid-schema-clock-range.json",
    "negative/invalid-id.json",
    "negative/invalid-clock.json",
    "negative/invalid-order.json",
    "negative/invalid-capability.json",
    "negative/invalid-interrupt.json",
    "negative/invalid-interrupt-decisions-present.json",
    "negative/invalid-interrupt-resume-payload.json",
    "negative/invalid-interrupt-accepted.json",
    "negative/invalid-interrupt-decision.json",
    "negative/invalid-source-collision.json",
    "negative/invalid-hash.json",
    "negative/invalid-scrub.json",
    "negative/invalid-scrub-endpoint.json",
    "negative/invalid-scrub-api-key.json",
    "negative/invalid-scrub-secret.json",
    "negative/invalid-scrub-basic.json",
    "negative/invalid-scrub-basic-short.json",
    "negative/invalid-scrub-basic-unpadded.json",
    "negative/invalid-scrub-path.json",
    "negative/invalid-scrub-identity.json",
    "negative/invalid-scrub-actor.json",
    "negative/invalid-scrub-current-actor.json",
    "negative/invalid-scrub-requested-actor.json",
    "negative/invalid-scrub-identity-field.json",
    "negative/invalid-scrub-repository.json",
    "negative/invalid-network.json",
    "negative/invalid-network-host.json",
    "negative/invalid-network-ip.json",
    "negative/invalid-network-exempt-descendant.json",
    "negative/invalid-expectation.json",
    "negative/invalid-logical-delay.json",
    "negative/invalid-logical-delay-visibility.json",
]
EXPECTED_RULE_CODES = [
    "FIXTURE_SCHEMA_REQUIRED_FIELD",
    "FIXTURE_SCHEMA_REQUIRED_FIELD",
    "FIXTURE_SCHEMA_REQUIRED_FIELD",
    "FIXTURE_SCHEMA_REQUIRED_FIELD",
    "FIXTURE_SCHEMA_REQUIRED_FIELD",
    "FIXTURE_SCHEMA_REQUIRED_FIELD",
    "FIXTURE_SCHEMA_REQUIRED_FIELD",
    "FIXTURE_ID_PREFIX",
    "FIXTURE_CLOCK_DERIVATION",
    "FIXTURE_ORDER_SEQUENCE",
    "FIXTURE_CAPABILITY_EVIDENCE",
    "FIXTURE_INTERRUPT_ALIGNMENT",
    "FIXTURE_INTERRUPT_ALIGNMENT",
    "FIXTURE_INTERRUPT_ALIGNMENT",
    "FIXTURE_INTERRUPT_ALIGNMENT",
    "FIXTURE_INTERRUPT_DECISION_VALUE",
    "FIXTURE_ID_SOURCE_COLLISION",
    "FIXTURE_HASH_MISMATCH",
    "FIXTURE_SCRUB_FORBIDDEN_FIELD",
    "FIXTURE_SCRUB_FORBIDDEN_FIELD",
    "FIXTURE_SCRUB_FORBIDDEN_FIELD",
    "FIXTURE_SCRUB_SECRET_VALUE",
    "FIXTURE_SCRUB_SECRET_VALUE",
    "FIXTURE_SCRUB_SECRET_VALUE",
    "FIXTURE_SCRUB_SECRET_VALUE",
    "FIXTURE_SCRUB_UNSAFE_PATH",
    "FIXTURE_SCRUB_REAL_IDENTITY",
    "FIXTURE_SCRUB_REAL_IDENTITY",
    "FIXTURE_SCRUB_REAL_IDENTITY",
    "FIXTURE_SCRUB_REAL_IDENTITY",
    "FIXTURE_SCRUB_REAL_IDENTITY",
    "FIXTURE_SCRUB_FORBIDDEN_FIELD",
    "FIXTURE_NETWORK_EXTERNAL_URL",
    "FIXTURE_NETWORK_EXTERNAL_URL",
    "FIXTURE_NETWORK_EXTERNAL_URL",
    "FIXTURE_NETWORK_EXTERNAL_URL",
    "FIXTURE_EXPECTATION_REPLAY_DEDUPE",
    "FIXTURE_CLOCK_DELAY_MISMATCH",
    "FIXTURE_EXPECTATION_DELAY_VISIBILITY",
]
SCHEMA_PATHS = [
    "schema/fixture-envelope.json",
    "schema/capability-manifest.json",
]
MANIFEST_PATHS = [
    "manifests/fixture-source.json",
    "manifests/gated-runtimes.json",
]
VALID_CAPABILITY_STATES = {
    "available",
    "unavailable",
    "gated",
    "permission-denied",
    "unknown",
}
VALIDATOR_IMPORT_ALLOWLIST = [
    "argparse",
    "ast",
    "copy",
    "hashlib",
    "json",
    "pathlib",
    "re",
    "sys",
]
FORBIDDEN_FIELD_FRAGMENTS = (
    "accesskey",
    "apikey",
    "authref",
    "authorization",
    "callbackurl",
    "cookie",
    "credential",
    "endpoint",
    "hostname",
    "password",
    "privatekey",
    "repository",
    "secret",
    "serviceurl",
    "signedurl",
    "token",
    "webhookurl",
)
IDENTITY_FIELD_FRAGMENTS = ("actor", "email", "identity", "owner", "user")
EXTERNAL_SCHEME_RE = re.compile(
    r"(?:https?|wss?|ftp|file|data|ssh|git)://",
    re.IGNORECASE,
)
EXTERNAL_HOST_RE = re.compile(
    r"(?<![a-z0-9_@-])"
    r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z]{2,63}(?::[0-9]{1,5})?(?![a-z0-9_-])",
    re.IGNORECASE,
)
IP_ADDRESS_RE = re.compile(
    r"(?<![a-z0-9])(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?![a-z0-9])|"
    r"(?<![a-z0-9])(?:[a-f0-9]{0,4}:){2,}[a-f0-9]{0,4}(?![a-z0-9])",
    re.IGNORECASE,
)
UNSAFE_PATH_RE = re.compile(
    r"(?:^|[\\/])\.\.(?:[\\/]|$)|^(?:/|[a-z]:[\\/]|\\\\)",
    re.IGNORECASE,
)
REAL_IDENTITY_RE = re.compile(
    r"(?:[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}|"
    r"(?:git@|github(?:usercontent)?\.com|gitlab\.com|bitbucket\.org))",
    re.IGNORECASE,
)
SECRET_VALUE_RE = re.compile(
    r"(?:basic\s+[a-z0-9+/]{2,}={0,2}(?![a-z0-9+/=])|"
    r"bearer\s+[a-z0-9._~+/-]+=*|"
    r"-----BEGIN [A-Z ]+PRIVATE KEY-----|"
    r"(?:sk|gh[opsu]|xox[abprs])_[a-z0-9_-]{8,}|"
    r"AKIA[A-Z0-9]{16}|"
    r"eyJ[a-z0-9_-]{8,}\.[a-z0-9_-]{8,}\.[a-z0-9_-]{8,})",
    re.IGNORECASE,
)
VALID_HITL_DECISIONS = ("approve", "edit", "reject", "respond")


class DuplicateKeyError(ValueError):
    pass


def _object_no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(key)
        result[key] = value
    return result


def read_bytes(relative_path):
    path = ROOT / relative_path
    resolved = path.resolve()
    if ROOT != resolved and ROOT not in resolved.parents:
        raise ValueError(f"path escapes corpus root: {relative_path}")
    return path.read_bytes()


def read_json(relative_path):
    return json.loads(
        read_bytes(relative_path).decode("utf-8"),
        object_pairs_hook=_object_no_duplicates,
    )


def canonical_json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def tick_timestamp(tick):
    total_ms = tick * TICK_MS
    seconds, milliseconds = divmod(total_ms, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours >= 24:
        raise ValueError("fixture tick exceeds supported deterministic day")
    return f"2026-07-23T{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}Z"


def _walk(value, path=""):
    yield path, value
    if isinstance(value, dict):
        for key in sorted(value):
            child_path = f"{path}/{key}"
            yield from _walk(value[key], child_path)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk(item, f"{path}/{index}")


def scrub_diagnostics(value):
    diagnostics = []
    for path, item in _walk(value):
        if isinstance(item, dict):
            for key, child in item.items():
                normalized = re.sub(r"[^a-z0-9]", "", key.lower())
                if any(fragment in normalized for fragment in FORBIDDEN_FIELD_FRAGMENTS):
                    diagnostics.append(("FIXTURE_SCRUB_FORBIDDEN_FIELD", f"{path}/{key}"))
                if (
                    any(fragment in normalized for fragment in IDENTITY_FIELD_FRAGMENTS)
                    and (
                        not isinstance(child, str)
                        or not child.startswith("fx_")
                    )
                ):
                    diagnostics.append(("FIXTURE_SCRUB_REAL_IDENTITY", f"{path}/{key}"))
        elif isinstance(item, str):
            if SECRET_VALUE_RE.search(item):
                diagnostics.append(("FIXTURE_SCRUB_SECRET_VALUE", path))
            if UNSAFE_PATH_RE.search(item):
                diagnostics.append(("FIXTURE_SCRUB_UNSAFE_PATH", path))
            if REAL_IDENTITY_RE.search(item):
                diagnostics.append(("FIXTURE_SCRUB_REAL_IDENTITY", path))
    return diagnostics


def network_diagnostics(value):
    diagnostics = []
    for path, item in _walk(value):
        if not isinstance(item, str):
            continue
        internal_reference = (
            path == "/negativeMatrixPath"
            or path == "/capabilityManifestRef"
            or re.fullmatch(
                r"/(?:casePaths|schemaPaths|manifestPaths|hashedAssets|negativePaths)/[0-9]+",
                path,
            )
            is not None
            or re.fullmatch(
                r"/properties/capabilityManifestRef/enum/[0-9]+",
                path,
            )
            is not None
        )
        if internal_reference:
            continue
        if (
            EXTERNAL_SCHEME_RE.search(item)
            or EXTERNAL_HOST_RE.search(item)
            or IP_ADDRESS_RE.search(item)
        ):
            diagnostics.append(("FIXTURE_NETWORK_EXTERNAL_URL", path))
    return diagnostics


def _matches_schema_type(value, expected):
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return False


def structural_schema_diagnostics(value, schema, path="$"):
    diagnostics = []
    expected_type = schema.get("type")
    if expected_type is not None and not _matches_schema_type(value, expected_type):
        return [f"{path}:type"]
    if "const" in schema and value != schema["const"]:
        diagnostics.append(f"{path}:const")
    if "enum" in schema and value not in schema["enum"]:
        diagnostics.append(f"{path}:enum")
    if isinstance(value, str) and "pattern" in schema:
        if re.fullmatch(schema["pattern"], value) is None:
            diagnostics.append(f"{path}:pattern")
    if isinstance(value, dict):
        required = schema.get("required", [])
        diagnostics.extend(
            f"{path}/{key}:required" for key in required if key not in value
        )
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            diagnostics.extend(
                f"{path}/{key}:additional" for key in value if key not in properties
            )
        for key, child_schema in properties.items():
            if key in value:
                diagnostics.extend(
                    structural_schema_diagnostics(
                        value[key],
                        child_schema,
                        f"{path}/{key}",
                    )
                )
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            diagnostics.append(f"{path}:minItems")
        if schema.get("uniqueItems") and len({canonical_json_bytes(item) for item in value}) != len(value):
            diagnostics.append(f"{path}:uniqueItems")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                diagnostics.extend(
                    structural_schema_diagnostics(
                        item,
                        item_schema,
                        f"{path}/{index}",
                    )
                )
    return diagnostics


def _has_unsafe_structural_shape(diagnostics):
    return any(
        diagnostic.endswith((":type", ":required", ":additional", ":minItems"))
        for diagnostic in diagnostics
    )


def _required_case_fields():
    return {
        "formatVersion",
        "caseId",
        "category",
        "synthetic",
        "evidenceClass",
        "clock",
        "scope",
        "capabilityManifestRef",
        "records",
        "expected",
        "provenance",
    }


def _validate_manifest(manifest):
    structural_diagnostics = structural_schema_diagnostics(
        manifest,
        read_json("schema/capability-manifest.json"),
    )
    if _has_unsafe_structural_shape(structural_diagnostics):
        return ["FIXTURE_SCHEMA_REQUIRED_FIELD"]
    structural_invalid = bool(structural_diagnostics)
    required = {
        "formatVersion",
        "manifestId",
        "synthetic",
        "runtimeKind",
        "capabilities",
    }
    if not isinstance(manifest, dict) or set(manifest) != required:
        return ["FIXTURE_SCHEMA_REQUIRED_FIELD"]
    if manifest["formatVersion"] != FORMAT_VERSION or manifest["synthetic"] is not True:
        return ["FIXTURE_SCHEMA_REQUIRED_FIELD"]
    if not isinstance(manifest["manifestId"], str) or not manifest["manifestId"].startswith("fx_manifest_"):
        return ["FIXTURE_ID_PREFIX"]
    diagnostics = []
    seen = set()
    capability_required = {
        "name",
        "state",
        "observedAt",
        "adapterVersion",
        "contractVersion",
        "evidenceClass",
        "reason",
    }
    for capability in manifest["capabilities"]:
        if not isinstance(capability, dict) or set(capability) != capability_required:
            diagnostics.append("FIXTURE_SCHEMA_REQUIRED_FIELD")
            continue
        name = capability["name"]
        if name in seen:
            diagnostics.append("FIXTURE_CAPABILITY_DUPLICATE")
        seen.add(name)
        if capability["state"] not in VALID_CAPABILITY_STATES:
            diagnostics.append("FIXTURE_CAPABILITY_STATE")
        if capability["observedAt"] != tick_timestamp(0):
            diagnostics.append("FIXTURE_CLOCK_DERIVATION")
        if capability["evidenceClass"] != "fixture":
            diagnostics.append("FIXTURE_CAPABILITY_EVIDENCE")
        if capability["state"] == "available" and manifest["runtimeKind"] != "fixture":
            diagnostics.append("FIXTURE_CAPABILITY_RUNTIME_AUTHORITY")
        if capability["state"] != "available" and not capability["reason"]:
            diagnostics.append("FIXTURE_CAPABILITY_REASON")
    diagnostics.extend(code for code, _ in scrub_diagnostics(manifest))
    diagnostics.extend(code for code, _ in network_diagnostics(manifest))
    if structural_invalid and not diagnostics:
        diagnostics.append("FIXTURE_SCHEMA_REQUIRED_FIELD")
    return sorted(set(diagnostics))


def validate_manifest(manifest):
    try:
        return _validate_manifest(manifest)
    except (AttributeError, IndexError, KeyError, OverflowError, TypeError, ValueError):
        return ["FIXTURE_SCHEMA_REQUIRED_FIELD"]


def _validate_scope(scope):
    required = {
        "tenantId",
        "workspaceId",
        "sourceId",
        "threadId",
        "runId",
        "qualifiedThreadKey",
        "qualifiedRunKey",
    }
    if not isinstance(scope, dict) or set(scope) != required:
        return ["FIXTURE_SCHEMA_REQUIRED_FIELD"]
    if any(not isinstance(scope[key], str) or not scope[key].startswith("fx_") for key in ("tenantId", "workspaceId", "sourceId", "threadId", "runId")):
        return ["FIXTURE_ID_PREFIX"]
    expected_thread = f"{scope['sourceId']}:{scope['threadId']}"
    expected_run = f"{expected_thread}:{scope['runId']}"
    if scope["qualifiedThreadKey"] != expected_thread or scope["qualifiedRunKey"] != expected_run:
        return ["FIXTURE_ID_QUALIFICATION"]
    return []


def _validate_logical_delay(case):
    expected = case["expected"]
    if expected["enqueueTick"] + expected["delayTicks"] != expected["releaseTick"]:
        return ["FIXTURE_CLOCK_DELAY_MISMATCH"]
    if expected["lastPreReleaseTick"] != expected["releaseTick"] - 1:
        return ["FIXTURE_CLOCK_DELAY_MISMATCH"]
    timestamp_fields = {
        "enqueueAt": expected["enqueueTick"],
        "lastPreReleaseAt": expected["lastPreReleaseTick"],
        "releaseAt": expected["releaseTick"],
        "completionAt": expected["completionTick"],
    }
    if any(expected[field] != tick_timestamp(tick) for field, tick in timestamp_fields.items()):
        return ["FIXTURE_CLOCK_DERIVATION"]
    visibility = expected["visibleRecordIdsByTick"]
    exact_visibility = {
        "40": ["fx_record_delay_start"],
        "43": ["fx_record_delay_start"],
        "44": ["fx_record_delay_start", "fx_record_delay_content"],
        "45": [
            "fx_record_delay_start",
            "fx_record_delay_content",
            "fx_record_delay_complete",
        ],
    }
    if visibility != exact_visibility:
        return ["FIXTURE_EXPECTATION_DELAY_VISIBILITY"]
    if expected["releaseOrder"] != exact_visibility["45"]:
        return ["FIXTURE_EXPECTATION_DELAY_VISIBILITY"]
    if expected["contentVisibleExactlyOnceAtRelease"] is not True:
        return ["FIXTURE_EXPECTATION_DELAY_VISIBILITY"]
    if expected["wallClockClaim"] is not False:
        return ["FIXTURE_CLOCK_WALL_TIME_CLAIM"]
    return []


def _semantic_diagnostics(case):
    category = case["category"]
    expected = case["expected"]
    records = case["records"]
    if category == "ordered-interrupt":
        if len(records) != 1 or records[0]["kind"] != "fixture-interrupt":
            return ["FIXTURE_INTERRUPT_ALIGNMENT"]
        payload = records[0]["payload"]
        requests = payload.get("actionRequests", [])
        configs = payload.get("reviewConfigs", [])
        if any(
            (
                "resume" in normalized
                or "accepted" in normalized
                or ("decision" in normalized and normalized != "alloweddecisions")
            )
            for record in records
            for _, item in _walk(record["payload"])
            if isinstance(item, dict)
            for key in item
            for normalized in (re.sub(r"[^a-z0-9]", "", key.lower()),)
        ):
            return ["FIXTURE_INTERRUPT_ALIGNMENT"]
        if any(
            not isinstance(request, dict)
            or set(request) not in (
                {"name", "args"},
                {"name", "args", "description"},
            )
            or not isinstance(request.get("args"), dict)
            for request in requests
        ):
            return ["FIXTURE_INTERRUPT_ALIGNMENT"]
        if any(
            not isinstance(config, dict)
            or set(config) not in (
                {"actionName", "allowedDecisions"},
                {"actionName", "allowedDecisions", "argsSchema"},
            )
            for config in configs
        ):
            return ["FIXTURE_INTERRUPT_ALIGNMENT"]
        request_names = [item.get("name") for item in requests]
        config_names = [item.get("actionName") for item in configs]
        if (
            not requests
            or len(requests) != len(configs)
            or request_names != config_names
        ):
            return ["FIXTURE_INTERRUPT_ALIGNMENT"]
        if request_names != ["review", "review"]:
            return ["FIXTURE_INTERRUPT_REPEATED_NAME"]
        if (
            expected["actionRequestOrder"] != request_names
            or expected["reviewConfigOrder"] != config_names
            or expected["positionalAlignment"] is not True
            or expected["repeatedActionNamesPreserved"] != request_names
        ):
            return ["FIXTURE_INTERRUPT_ALIGNMENT"]
        observed_decisions = []
        for config in configs:
            decisions = config.get("allowedDecisions")
            if (
                not isinstance(decisions, list)
                or not decisions
                or len(decisions) != len(set(decisions))
                or any(decision not in VALID_HITL_DECISIONS for decision in decisions)
            ):
                return ["FIXTURE_INTERRUPT_DECISION_VALUE"]
            observed_decisions.extend(decisions)
        if (
            sorted(set(observed_decisions)) != sorted(VALID_HITL_DECISIONS)
            or expected["documentedDecisionVocabulary"]
            != list(VALID_HITL_DECISIONS)
        ):
            return ["FIXTURE_INTERRUPT_DECISION_VALUE"]
        if (
            expected["acceptedDecisionPresent"] is not False
            or expected["resumePayloadPresent"] is not False
            or expected["submissionCapabilityState"] != "gated"
        ):
            return ["FIXTURE_INTERRUPT_ALIGNMENT"]
    elif category == "replay":
        seen = set()
        visible = []
        durable = []
        ignored = []
        for record in records:
            event_id = record["durableEventId"]
            if event_id in seen:
                ignored.append(record["recordId"])
            else:
                seen.add(event_id)
                durable.append(event_id)
                visible.append(record["recordId"])
        if (
            expected["deduplicatedDurableEventIds"] != durable
            or expected["ignoredRecordIds"] != ignored
            or expected["visibleRecordIds"] != visible
        ):
            return ["FIXTURE_EXPECTATION_REPLAY_DEDUPE"]
    elif category == "logical-delay":
        return _validate_logical_delay(case)
    elif category == "completion":
        authority_id = expected["terminalAuthorityRecordId"]
        matching = [
            record
            for record in records
            if record["recordId"] == authority_id
            and record["kind"] == "fixture-completion"
            and record["payload"].get("authoritative") == "fixture"
        ]
        if len(matching) != 1 or expected["terminalStatus"] != "completed":
            return ["FIXTURE_EXPECTATION_TERMINAL_AUTHORITY"]
    elif category == "source-collision":
        if len(records) != 2:
            return ["FIXTURE_ID_SOURCE_COLLISION"]
        source_ids = [record["sourceId"] for record in records]
        thread_ids = [record["threadId"] for record in records]
        run_ids = [record["runId"] for record in records]
        qualified_threads = [
            f"{record['sourceId']}:{record['threadId']}" for record in records
        ]
        qualified_runs = [
            f"{record['sourceId']}:{record['threadId']}:{record['runId']}"
            for record in records
        ]
        if (
            len(set(source_ids)) != 2
            or set(thread_ids) != {expected["sharedThreadId"]}
            or set(run_ids) != {expected["sharedRunId"]}
            or expected["distinctQualifiedThreadKeys"] != qualified_threads
            or expected["distinctQualifiedRunKeys"] != qualified_runs
            or any(
                record["payload"].get("qualifiedThreadKey")
                != qualified_threads[index]
                or record["payload"].get("qualifiedRunKey")
                != qualified_runs[index]
                for index, record in enumerate(records)
            )
            or case["scope"]["sourceId"] != source_ids[0]
            or case["scope"]["threadId"] != thread_ids[0]
            or case["scope"]["runId"] != run_ids[0]
            or case["scope"]["qualifiedThreadKey"] != qualified_threads[0]
            or case["scope"]["qualifiedRunKey"] != qualified_runs[0]
        ):
            return ["FIXTURE_ID_SOURCE_COLLISION"]
    elif category == "malformed-input":
        if expected["envelopeValid"] is not True or expected["safeErrorCode"] != "FIXTURE_INPUT_MALFORMED":
            return ["FIXTURE_EXPECTATION_MALFORMED_CLASSIFICATION"]
    elif category == "partial-failure":
        if expected["aggregateUsable"] is not True or len(expected["partialErrorRecordIds"]) != 1:
            return ["FIXTURE_EXPECTATION_PARTIAL_FAILURE"]
    elif category == "unknown":
        if expected["classification"] != "unknown" or expected["promotedDiscriminator"] is not False:
            return ["FIXTURE_EXPECTATION_UNKNOWN"]
    return []


def _validate_case(case):
    structural_diagnostics = structural_schema_diagnostics(
        case,
        read_json("schema/fixture-envelope.json"),
    )
    if _has_unsafe_structural_shape(structural_diagnostics):
        return ["FIXTURE_SCHEMA_REQUIRED_FIELD"]
    structural_invalid = bool(structural_diagnostics)
    if not isinstance(case, dict) or set(case) != _required_case_fields():
        return ["FIXTURE_SCHEMA_REQUIRED_FIELD"]
    if case["formatVersion"] != FORMAT_VERSION or case["synthetic"] is not True or case["evidenceClass"] != "fixture":
        return ["FIXTURE_SCHEMA_REQUIRED_FIELD"]
    if not isinstance(case["caseId"], str) or not case["caseId"].startswith("fx_case_"):
        return ["FIXTURE_ID_PREFIX"]
    scope_diagnostics = _validate_scope(case["scope"])
    if scope_diagnostics:
        return scope_diagnostics
    if case["capabilityManifestRef"] not in MANIFEST_PATHS:
        return ["FIXTURE_CAPABILITY_REFERENCE"]
    clock = case["clock"]
    if set(clock) != {"tickEpoch", "tickDurationMs", "observedTick", "observedAt"}:
        return ["FIXTURE_SCHEMA_REQUIRED_FIELD"]
    if clock["tickEpoch"] != EPOCH or clock["tickDurationMs"] != TICK_MS:
        return ["FIXTURE_CLOCK_POLICY"]
    if clock["observedAt"] != tick_timestamp(clock["observedTick"]):
        return ["FIXTURE_CLOCK_DERIVATION"]
    records = case["records"]
    if not isinstance(records, list) or not records:
        return ["FIXTURE_SCHEMA_REQUIRED_FIELD"]
    record_ids = []
    sequences = []
    prior_tick = -1
    diagnostics = []
    for record in records:
        required = {
            "recordId",
            "durableEventId",
            "sequence",
            "tick",
            "observedAt",
            "kind",
            "sourceId",
            "threadId",
            "runId",
            "payload",
        }
        if not isinstance(record, dict) or set(record) != required:
            diagnostics.append("FIXTURE_SCHEMA_REQUIRED_FIELD")
            continue
        for id_field in ("recordId", "durableEventId", "sourceId", "threadId", "runId"):
            if not isinstance(record[id_field], str) or not record[id_field].startswith("fx_"):
                diagnostics.append("FIXTURE_ID_PREFIX")
        record_ids.append(record["recordId"])
        sequences.append(record["sequence"])
        if record["tick"] < prior_tick:
            diagnostics.append("FIXTURE_ORDER_TICK")
        prior_tick = record["tick"]
        if record["observedAt"] != tick_timestamp(record["tick"]):
            diagnostics.append("FIXTURE_CLOCK_DERIVATION")
    if len(record_ids) != len(set(record_ids)):
        diagnostics.append("FIXTURE_ID_DUPLICATE_RECORD")
    if sequences != list(range(1, len(records) + 1)):
        diagnostics.append("FIXTURE_ORDER_SEQUENCE")
    if "orderedRecordIds" in case["expected"] and case["expected"]["orderedRecordIds"] != record_ids:
        diagnostics.append("FIXTURE_EXPECTATION_ORDER")
    diagnostics.extend(_semantic_diagnostics(case))
    diagnostics.extend(code for code, _ in scrub_diagnostics(case))
    diagnostics.extend(code for code, _ in network_diagnostics(case))
    if structural_invalid and not diagnostics:
        diagnostics.append("FIXTURE_SCHEMA_REQUIRED_FIELD")
    return sorted(set(diagnostics))


def validate_case(case):
    try:
        return _validate_case(case)
    except (AttributeError, IndexError, KeyError, OverflowError, TypeError, ValueError):
        return ["FIXTURE_SCHEMA_REQUIRED_FIELD"]


def _apply_mutation(document, mutation):
    result = copy.deepcopy(document)
    parts = [part.replace("~1", "/").replace("~0", "~") for part in mutation["path"].split("/")[1:]]
    parent = result
    for part in parts[:-1]:
        parent = parent[int(part)] if isinstance(parent, list) else parent[part]
    key = parts[-1]
    if mutation["operation"] == "remove":
        if isinstance(parent, list):
            del parent[int(key)]
        else:
            del parent[key]
    elif mutation["operation"] in {"replace", "add"}:
        if isinstance(parent, list):
            index = int(key)
            if mutation["operation"] == "add" and index == len(parent):
                parent.append(mutation["value"])
            else:
                parent[index] = mutation["value"]
        else:
            parent[key] = mutation["value"]
    else:
        raise ValueError(f"unsupported mutation operation: {mutation['operation']}")
    return result


def diagnose_negative(negative):
    if "probe" in negative:
        probe = negative["probe"]
        if probe.get("kind") == "claimed-asset-hash":
            actual = hashlib.sha256(read_bytes(probe["assetPath"])).hexdigest()
            return [] if actual == probe["claimedSha256"] else ["FIXTURE_HASH_MISMATCH"]
        if probe.get("kind") == "network-diagnostic":
            return sorted({code for code, _ in network_diagnostics(probe["value"])})
        return ["FIXTURE_SCHEMA_REQUIRED_FIELD"]
    base_path = negative["basePath"]
    mutated = _apply_mutation(read_json(base_path), negative["mutation"])
    if base_path.startswith("manifests/"):
        return validate_manifest(mutated)
    return validate_case(mutated)


def render_hash_manifest():
    corpus = read_json("corpus.json")
    lines = []
    for relative_path in sorted(corpus["hashedAssets"]):
        digest = hashlib.sha256(read_bytes(relative_path)).hexdigest()
        lines.append(f"{digest}  {relative_path}\n")
    return "".join(lines).encode("utf-8")


def corpus_digest():
    return hashlib.sha256(render_hash_manifest()).hexdigest()


def validator_imports():
    tree = ast.parse(read_bytes("validate.py").decode("utf-8"))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    return sorted(imports)


def _source_scan_assets(corpus):
    return (
        ["corpus.json"]
        + corpus["schemaPaths"]
        + corpus["manifestPaths"]
        + corpus["casePaths"]
        + ["negative/matrix.json"]
    )


def analyze_sources():
    corpus = read_json("corpus.json")
    cases = [read_json(path) for path in corpus["casePaths"]]
    matrix = read_json(corpus["negativeMatrixPath"])
    negative_results = {}
    for path in matrix["negativePaths"]:
        negative = read_json(path)
        negative_results[negative["negativeId"]] = {
            "path": path,
            "declaredRuleCode": negative["declaredRuleCode"],
            "observedRuleCodes": diagnose_negative(negative),
        }
    scrub_matches = []
    external_urls = []
    for path in _source_scan_assets(corpus):
        value = read_json(path)
        scrub_matches.extend((path, code, location) for code, location in scrub_diagnostics(value))
        external_urls.extend((path, code, location) for code, location in network_diagnostics(value))
    return {
        "corpus": corpus,
        "cases": cases,
        "matrix": matrix,
        "negativeResults": negative_results,
        "scrubMatches": scrub_matches,
        "externalUrls": external_urls,
        "imports": validator_imports(),
        "corpusDigest": corpus_digest(),
    }


def render_validation_report(analysis=None):
    analysis = analysis or analyze_sources()
    report = {
        "reportVersion": "1.0.0",
        "evidenceClass": "fixture",
        "authority": "corpus-validation-only",
        "corpusVersion": analysis["corpus"]["corpusVersion"],
        "corpusDigest": analysis["corpusDigest"],
        "caseIds": sorted(case["caseId"] for case in analysis["cases"]),
        "caseCategories": [case["category"] for case in analysis["cases"]],
        "negativeRuleCodes": [
            analysis["negativeResults"][read_json(path)["negativeId"]]["declaredRuleCode"]
            for path in analysis["matrix"]["negativePaths"]
        ],
        "structuralSchemaPaths": SCHEMA_PATHS,
        "structuralSchemaApplicationCount": len(analysis["cases"]) + len(MANIFEST_PATHS),
        "normalizedHitlDecisionVocabulary": list(VALID_HITL_DECISIONS),
        "scrubMatchCount": len(analysis["scrubMatches"]),
        "externalUrlHostCount": len(analysis["externalUrls"]),
        "validatorImportAllowlist": VALIDATOR_IMPORT_ALLOWLIST,
        "validatorImportsObserved": analysis["imports"],
        "logicalDelay": {
            "tickEpoch": EPOCH,
            "tickDurationMs": TICK_MS,
            "enqueueTick": 41,
            "delayTicks": 3,
            "releaseTick": 44,
            "completionTick": 45,
            "equation": "41 + 3 = 44",
            "absentThroughTick": 43,
            "visibleExactlyOnceFromTick": 44,
            "wallClockReads": 0,
            "waits": 0,
        },
    }
    return canonical_json_bytes(report)


def render_network_report(analysis=None):
    analysis = analysis or analyze_sources()
    report = {
        "reportVersion": "1.0.0",
        "evidenceClass": "fixture",
        "authority": "validator-source-inspection-only",
        "claimLimit": "Does not prove isolation for API, browser, provider, or future consumers.",
        "corpusDigest": analysis["corpusDigest"],
        "scannedAssetCount": len(_source_scan_assets(analysis["corpus"])),
        "externalUrlHostCount": len(analysis["externalUrls"]),
        "validatorSubprocessCalls": 0,
        "validatorSocketImports": 0,
        "validatorEnvironmentReads": 0,
        "validatorWallClockReads": 0,
        "validatorWrites": 0,
    }
    return canonical_json_bytes(report)


def _validate_index_and_closure(analysis):
    corpus = analysis["corpus"]
    diagnostics = []
    if corpus["corpusVersion"] != FORMAT_VERSION or corpus["fixtureSchemaVersion"] != FORMAT_VERSION:
        diagnostics.append("FIXTURE_SCHEMA_VERSION")
    if corpus["synthetic"] is not True or corpus["evidenceClass"] != "fixture" or corpus["authority"] != "private-fixture-only":
        diagnostics.append("FIXTURE_SCHEMA_AUTHORITY")
    if corpus["clock"] != {"tickEpoch": EPOCH, "tickDurationMs": TICK_MS}:
        diagnostics.append("FIXTURE_CLOCK_POLICY")
    if corpus["casePaths"] != EXPECTED_CASE_PATHS:
        diagnostics.append("FIXTURE_SCHEMA_CASE_INDEX")
    if corpus["schemaPaths"] != SCHEMA_PATHS or corpus["manifestPaths"] != MANIFEST_PATHS:
        diagnostics.append("FIXTURE_SCHEMA_ASSET_INDEX")
    matrix = analysis["matrix"]
    if matrix["negativePaths"] != EXPECTED_NEGATIVE_PATHS:
        diagnostics.append("FIXTURE_SCHEMA_NEGATIVE_INDEX")
    if matrix["expectedRuleCodes"] != EXPECTED_RULE_CODES:
        diagnostics.append("FIXTURE_SCHEMA_RULE_INDEX")
    expected_assets = sorted(
        ["corpus.json"]
        + SCHEMA_PATHS
        + MANIFEST_PATHS
        + EXPECTED_CASE_PATHS
        + ["negative/matrix.json"]
        + EXPECTED_NEGATIVE_PATHS
    )
    if sorted(corpus["hashedAssets"]) != expected_assets or len(corpus["hashedAssets"]) != len(set(corpus["hashedAssets"])):
        diagnostics.append("FIXTURE_HASH_CLOSURE")
    categories = [case["category"] for case in analysis["cases"]]
    if categories != EXPECTED_CATEGORIES:
        diagnostics.append("FIXTURE_SCHEMA_CASE_COVERAGE")
    if len({case["caseId"] for case in analysis["cases"]}) != 13:
        diagnostics.append("FIXTURE_ID_DUPLICATE_CASE")
    return diagnostics


def _validate_hashes():
    expected = render_hash_manifest()
    try:
        actual = read_bytes("hashes.sha256")
    except FileNotFoundError:
        return ["FIXTURE_HASH_MANIFEST_MISSING"]
    return [] if actual == expected else ["FIXTURE_HASH_MISMATCH"]


def _validate_evidence(analysis):
    diagnostics = []
    targets = {
        "evidence/validation-report.json": render_validation_report(analysis),
        "evidence/no-external-network.json": render_network_report(analysis),
    }
    for path, expected in targets.items():
        try:
            actual = read_bytes(path)
        except FileNotFoundError:
            diagnostics.append("FIXTURE_HASH_EVIDENCE_MISSING")
            continue
        if actual != expected:
            diagnostics.append("FIXTURE_HASH_EVIDENCE_DRIFT")
    return diagnostics


def validate_all(require_evidence=True):
    analysis = analyze_sources()
    diagnostics = _validate_index_and_closure(analysis)
    for schema_path in SCHEMA_PATHS:
        schema = read_json(schema_path)
        if schema.get("schemaDialect") != "json-schema-2020-12" or schema.get("description", "").find("not") < 0:
            diagnostics.append("FIXTURE_SCHEMA_DOCUMENT")
    for manifest_path in MANIFEST_PATHS:
        diagnostics.extend(validate_manifest(read_json(manifest_path)))
    for case in analysis["cases"]:
        diagnostics.extend(validate_case(case))
    for negative_id, result in sorted(analysis["negativeResults"].items()):
        if result["observedRuleCodes"] != [result["declaredRuleCode"]]:
            diagnostics.append(f"FIXTURE_EXPECTATION_NEGATIVE_SINGLE_CODE:{negative_id}")
    if analysis["scrubMatches"]:
        diagnostics.append("FIXTURE_SCRUB_ACTIVE_CORPUS")
    if analysis["externalUrls"]:
        diagnostics.append("FIXTURE_NETWORK_ACTIVE_CORPUS")
    if analysis["imports"] != VALIDATOR_IMPORT_ALLOWLIST:
        diagnostics.append("FIXTURE_SCHEMA_IMPORT_ALLOWLIST")
    diagnostics.extend(_validate_hashes())
    if require_evidence:
        diagnostics.extend(_validate_evidence(analysis))
    return sorted(set(diagnostics)), analysis


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", required=True)
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    diagnostics, analysis = validate_all(require_evidence=True)
    if diagnostics:
        for diagnostic in diagnostics:
            print(diagnostic, file=sys.stderr)
        return 1
    print(f"corpus_digest={analysis['corpusDigest']}")
    print("case_ids=" + ",".join(sorted(case["caseId"] for case in analysis["cases"])))
    print("case_categories=" + ",".join(case["category"] for case in analysis["cases"]))
    print("negative_rule_codes=" + ",".join(EXPECTED_RULE_CODES))
    print("scrub_match_count=0")
    print("external_url_host_count=0")
    print("logical_delay=enqueue:41,delay:3,release:44,completion:45")
    print("logical_delay_visibility=absent_through:43,visible_once_from:44")
    print("validator_subprocess_calls=0")
    print("validator_environment_reads=0")
    print("validator_wall_clock_reads=0")
    print("validator_writes=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

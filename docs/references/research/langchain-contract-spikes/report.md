# LangChain contract-spike research report

Collected: 2026-07-23

Packet: `DW-EXT-W1-LANGCHAIN-CONTRACT-RESEARCH`

## Outcome

No capability is accepted or enabled by this research.

All eleven named spikes are `blocked-live-evidence`. The pinned official
documentation, generated Agent Server OpenAPI, and public package source
revisions establish useful candidate contracts and contradictions, but:

- no human-provided non-production classic sandbox profile was available; and
- public package-index egress was not authorized, so the candidate distribution
  versions were not locked, installed, or promoted to installed-public-contract
  evidence.

The deterministic fallback is therefore unchanged: classic sources, task
submission, streaming, decisions, cancellation, checkpoints, config mutation,
and deployment controls remain unavailable until independently accepted.

## Evidence precedence and pins

The review applied this precedence:

1. sanitized live classic-sandbox behavior;
2. installed public/generated package contract;
3. official primary documentation and generated public schema;
4. pinned public package source, used only to explain a candidate shape; and
5. unsupported, contradictory, or unknown behavior with a fail-closed fallback.

Exact local evidence was clean at:

| Source | Revision | Role |
|---|---|---|
| `SRC-LC` | `7b9215d708e0b57e6fbae7b5d0762c4118b8e309` | Official docs and Agent Server OpenAPI |
| `SRC-DA` | `7794b61a6e76230e8c7a49bdce808b3728305914` | Deep Agents public package source |
| `SRC-LCPY` | `592055e15e138f5369dce95dd049ce22430996e2` | LangChain HITL public package source |
| `SRC-LG` | `31f90df3e6b0268fa77fd2d118a917d420b84a68` | LangGraph SDK/package source |

Candidate package versions derived from those pinned sources are
`deepagents==0.6.12`, `langchain==1.3.14`, `langgraph==1.2.9`, and
`langgraph-sdk==0.4.2`. They are recorded as candidates, not installed
distribution evidence. The generated Agent Server OpenAPI identifies itself as
`0.1.0` and has SHA-256
`0b4d3d1e2da065a50a53838e7f63f5d90763a1dc759b165dd7a4409b5959888c`.

## Gate conclusions

| Spike | Documentary/package-source conclusion | Result | Deterministic fallback |
|---|---|---|---|
| `SPIKE-SOURCE-001` | Agent Server has `/ok`, optional `/info`, assistants, and per-operation routes; route presence and shallow health are not capability proof | `blocked-live-evidence` | Keep source unavailable and mutations disabled |
| `SPIKE-CONFIG-001` | Project manifest requires generated-schema plus runtime CLI validation; there is no universal serialized Deep Agent/provider settings schema | `blocked-live-evidence` | Opaque read-only config; no generic provider editor |
| `SPIKE-DEPLOY-001` | Control plane is separate, region-specific, and documented at `/v2/deployments`; exact pinned schema/idempotency/lifecycle is absent | `blocked-live-evidence` | Operator-owned CLI/console workflow only |
| `SPIKE-COMPOSE-001` | Thread create and run create are separate; run input is assistant-schema-defined and run create has no mutation idempotency key | `blocked-live-evidence` | Retain an application draft; disable dispatch |
| `SPIKE-THREADS-001` | Search is deployment-scoped, limit/offset based, and returns no cursor or stable-snapshot promise | `blocked-live-evidence` | Source-qualified projection plus direct refetch |
| `SPIKE-STREAM-001` | Legacy thread/run join and resumable run stream are distinct from protocol v3 | `blocked-live-evidence` | State polling/non-live snapshot |
| `SPIKE-STREAM-002` | Four Agent Server multitask strategies are documented; frontend queue APIs are not a Python/provider contract | `blocked-live-evidence` | Accept input only when idle; keep text as a draft |
| `SPIKE-STREAM-003` | Beta protocol v3 uses `/stream/events`, body cursor `since`, and `event_id` dedupe | `blocked-live-evidence` | Qualified legacy join if later accepted, else refetch |
| `SPIKE-HITL-001` | Python HITL is ordered snake_case arrays with positional decisions and no action IDs | `blocked-live-evidence` | Read-only interrupt; no force resolve or retry |
| `SPIKE-CANCEL-001` | Cancel accepts `interrupt` or destructive `rollback`; terminal/race behavior is unproven | `blocked-live-evidence` | Hide Stop and refresh source state |
| `SPIKE-CHECKPOINT-001` | Current/historical state and same-thread checkpoint branching are exposed; selected-checkpoint-to-new-thread fork is not proven | `blocked-live-evidence` | Read-only history; no restore/fork action |

Full request, response, error, idempotency, retry, cancel, reconnect, source, and
downstream acceptance details are retained in `matrix.json`.

## Material contradictions and unknowns

### Source and health

- Agent Server OpenAPI defines `/ok` and `/info`, but the CLI configuration can
  disable metadata routes and make `/ok` skip deeper checks. `/ok` alone is not
  readiness or capability evidence.
- The generated Agent Server OpenAPI declares neither a canonical server URL nor
  a security scheme. Exact base URL, mount prefix, redirects, authentication, and
  error bodies require live source evidence.
- SDK candidate code accepts arbitrary assistant ID strings while generated
  paths use UUID formats. Default graph/assistant identity cannot be inferred.
- Route groups can be disabled. OpenAPI presence is not proof that a deployed
  source enables assistants, threads, runs, or store operations.

### Configuration

- The generated CLI schema is under-strict: some runtime-required values are not
  schema-required, and unknown keys are warned rather than rejected.
- Pinned docs point `$schema` at a moving main-branch schema and contain fields or
  values that disagree with the pinned CLI candidate (`bullseye`,
  `checkpointer.backend`, and `$schema` warning behavior).
- `create_deep_agent` accepts Python objects and callables. It is construction-time
  dependency injection, not a portable serialized settings schema.
- LangChain's runtime-configurable model surface warns that
  `configurable_fields="any"` can expose sensitive provider options. A generic
  provider form is rejected; only separately pinned safe allowlists could qualify.

### Deployment

- Official control-plane docs require `X-Api-Key` and `X-Tenant-Id`, but the
  locally pinned docs link the exact OpenAPI from a moving live URL rather than
  retaining it. Request fields, complete status enums, errors, and idempotency
  are not pinned.
- CLI source is explanatory, not a public control-plane SDK. It retries transport
  errors around mutations without an idempotency key and can include raw response
  text in errors, so it cannot define safe application retry or logging behavior.
- CLI deployment-type values (`dev|prod`) conflict with documentation
  (`serverless|dedicated`). A zero CLI exit is not accepted deployment success;
  exact deployment and revision state must be checked.

### Compose and threads

- Thread creation supports a caller UUID plus `if_exists`, but run creation has no
  caller run ID or idempotency key. `if_not_exists` handles a missing thread; it
  does not deduplicate a run mutation.
- SDK candidate input types are narrower than generated REST JSON. The docstring
  says `input` and `command` are mutually exclusive, while candidate
  implementation/generated schema do not enforce exclusivity.
- Thread search uses `limit` and `offset`, not a cursor. No stable snapshot or
  tie-break behavior under concurrent writes is promised.
- SDK candidate and generated schemas disagree on thread select fields, required
  thread fields, graph schema optionality, and interrupt ID optionality.

### Streaming

- Current event streaming is protocol v3. Earlier audit prose calling the same
  `/threads/{thread_id}/stream/events` surface “protocol v2” is stale.
- Protocol v3 resumes with request-body `since`; it does not use
  `Last-Event-ID`. Legacy thread/run join remains a separate contract.
- `RunsClient.stream(version="v2")` changes the client projection for the legacy
  run-stream endpoint; it is not protocol v3.
- Candidate Python `run.start` has no multitask strategy or queue handle.
  Frontend `stream.submit`, queue entries, cancel/clear, and `stream.stop()` must
  not be inferred into the provider adapter.
- Official Deep Agents docs describe a product-level `subagents` projection, but
  candidate Python currently aliases `subagents` to `subgraphs`. Specialized
  subagent UI is therefore rejected until distribution/live evidence resolves it.
- Internal controller retry counts, backoff, in-memory dedupe, and overlap
  behavior explain implementation only; they are not hosted contract promises.

### HITL

The pinned Python shape is:

```text
HITLRequest:
  action_requests[] = {name, args, description?}
  review_configs[] = {action_name, allowed_decisions, args_schema?}

HITLResponse:
  decisions[] = approve | edit | reject | respond
```

There is exactly one decision per request, in source order. Upstream carries no
action ID in these arrays, so repeated tool names are distinguishable only by
position. A client must not invent IDs and then use them to reorder the provider
payload. The exact hosted stale, duplicate, keyed-resume, lost-response, and
permission behavior remains live-blocked.

### Cancel and checkpoints

- Candidate cancel returns no state object. After any ambiguous request the
  caller must refetch both run and thread; it must never assume stream closure
  means cancellation.
- `rollback` removes run progress/checkpoints and is materially different from
  `interrupt`.
- Checkpoint state is nested under a checkpoint object. Some time-travel prose
  shows flat checkpoint IDs and a GET history request, while the candidate SDK
  uses nested objects and POST history.
- Same-thread historical branching is documented. A public operation that copies
  a selected checkpoint to a new thread is unsupported/unknown.

## Recommended adapter boundary

This research recommends a future server-only boundary; it does not authorize its
implementation:

```text
Deep Work application service
  -> source registry with server-side credential reference
  -> classic Agent Server adapter
       - assistants/config schemas
       - deployment-scoped threads/runs/state
       - legacy stream capability
       - protocol-v3 stream capability
       - ordered HITL resume capability
       - cancel/checkpoint capability
  -> separate control-plane deployment service
```

Each operation must advertise its own dated evidence and capability. The browser
must never receive provider credentials or call the provider directly. Legacy
stream and protocol-v3 cursor envelopes stay separate. The control plane does not
share an adapter or assumed authentication policy with Agent Server.

## Probe and fixture qualification

The retained environment-bound probe scaffold:

- validates one complete matrix row for every named spike;
- rejects lossy/reordered HITL batches and invented upstream action IDs;
- tests protocol-v3 replay projection using `seq` for position and `event_id` for
  identity;
- fails closed when the live classic-sandbox profile is absent;
- records exact source, candidate package, generated schema, interpreter, and
  blocker inventory;
- scans retained evidence for secrets, credential references, tenant/customer
  identifiers, and unapproved hosts; and
- contains only synthetic transcripts with hashes and scrub attestations.

Because public-index access was blocked, the probe project deliberately has no
registry dependencies. Its dependency-free package installs an offline test
entrypoint that requires the workspace's exact `pytest 9.0.2`; this runner is
tooling evidence only and is not counted as an installed LangChain contract.
It is not a reproducible isolated test lock. Producing that lock remains blocked
on approved public-index access.

## Required future live evidence

An independent reviewer still needs a human-provided, non-production classic
sandbox and explicit account tier, region, authentication context, Agent Server
revision, SDK distribution lock, and synthetic cleanup scope. At minimum, the live
run must prove:

- `/ok`, `/info`, disabled-meta behavior, assistant identity, auth failures, and
  operation-specific capability detection;
- real graph config/context/input schemas and invalid/unknown field behavior;
- create-thread/run ambiguity, run idempotency reconciliation, and offset-search
  stability;
- protocol-v3 cross-disconnect replay, bounded-gap behavior, durable dedupe,
  reauthentication, and legacy fallback;
- multitask strategy ordering and status/error behavior;
- single, batched, repeated-name, invalid, stale, duplicate, lost-response, and
  post-resume HITL behavior;
- cancel for active, queued, interrupted, and terminal runs;
- checkpoint retention, stale/cross-thread errors, history ordering, and branch
  identity; and
- exact control-plane OpenAPI, lifecycle states, mutation idempotency, cleanup,
  region, tier, and redacted error behavior.

Until that evidence is sanitized, reviewed, and accepted, every affected
capability remains unavailable.

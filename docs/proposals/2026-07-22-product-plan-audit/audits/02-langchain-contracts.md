# LangChain and LangSmith Contract Audit

Status: staged audit; external contracts require live verification before implementation readiness
Documentation pin: `langchain-docs-reference@7b9215d708e0b57e6fbae7b5d0762c4118b8e309`
Plan comparison pin: `deepwork@06f051554bf938e919af5ab7855974098fbf3d2a`
Audit date: 2026-07-22

## Decision

Deep Work v1 must use **classic LangSmith Deployment / Agent Server as its supported public remote baseline**. Managed Deep Agents (MDA) is a separately detected, private-beta adapter and cannot be a release prerequisite. Fleet is a read/invoke source where authorized, not a proven public CRUD surface. Local development can be a third source adapter.

The current plans conflate at least four planes:

1. the Deep Work application service;
2. a deployment's Agent Server data plane for assistants, threads, runs, streams, state, and crons;
3. the LangSmith control plane for deployment lifecycle;
4. LangSmith platform services such as Context Hub, sandboxes, traces, workspaces, and Fleet bootstrap.

They also combine legacy streaming resume rules with protocol v2, flatten ordered HITL batches into a single action, and assume public MDA/Fleet endpoints that the primary prose does not support. These are release-blocking contract defects, not implementation details.

## Classification method

Every external assumption is classified as one of:

- **Documented**: explicitly described by pinned primary prose and/or generated contract.
- **Gated/beta**: explicitly private, beta, version-gated, region-gated, or otherwise not a universal baseline.
- **Inferred**: plausible synthesis that is not itself promised by the source.
- **Contradicted**: the current plan conflicts with pinned primary evidence.
- **Unknown**: available evidence is absent, ambiguous, or disagrees; a live-contract spike is mandatory.

Confidence is **high** when prose and generated contract agree, **medium** when a single primary source is clear, and **low** when evidence is incomplete or conflicting. All LC evidence references below are at commit `7b9215d708e0b57e6fbae7b5d0762c4118b8e309`; accepting this audit does not remove the live-spike requirement for mutable hosted services.

## External claim register

| ID | External claim or current assumption | Classification | Confidence | Pinned evidence and consequence |
|---|---|---|---|---|
| LC-01 | Classic LangSmith Deployment exposes an Agent Server data plane for assistants, threads, runs, state, streams, and deployment-scoped crons | Documented | High | `src/langsmith/agent-server-openapi.json`; use as v1 remote baseline |
| LC-02 | LangSmith control-plane deployment lifecycle uses `/v2/deployments` | Documented | High | `src/langsmith/api-ref-control-plane.mdx`, `src/langsmith/control-plane.mdx`; do not route thread/run calls here |
| LC-03 | Control-plane requests use `X-Api-Key` plus `X-Tenant-Id` | Documented | High | `src/langsmith/api-ref-control-plane.mdx`; store credentials server-side and attach per plane |
| LC-04 | A deployment's Agent Server is the same API as the LangSmith control plane | Contradicted | High | LC-01 and LC-02 define different authorities and base URLs |
| LC-05 | Event Streaming protocol v2 subscribes with `POST /threads/{thread_id}/stream/events` and resumes with body field `since` containing the last sequence | Gated/beta | High | `src/langsmith/event-streaming.mdx`, `agent-server-openapi.json`; requires version/capability check |
| LC-06 | Protocol v2 uses `Last-Event-ID` for reconnect | Contradicted | High | Protocol-v2 docs explicitly use `since`; `Last-Event-ID` belongs to other stream surfaces |
| LC-07 | Legacy `GET /threads/{thread_id}/stream` supports `Last-Event-ID` | Documented | High | `src/langsmith/streaming.mdx`, `agent-server-openapi.json`; keep adapter separate from v2 |
| LC-08 | Run-join streaming can use `Last-Event-ID` when `stream_resumable=true` | Documented | High | `agent-server-openapi.json`; do not generalize to protocol v2 |
| LC-09 | Protocol-v2 run start and event subscription are separate operations; commands include `run.start` and `input.respond` | Gated/beta | High | `src/langsmith/event-streaming.mdx`, `agent-server-openapi.json` |
| LC-10 | The frontend `useStream` helper's `stream.submit(...)` sends new input and can submit a resume command | Documented | High | `src/oss/deepagents/frontend/subagent-streaming.mdx`, `src/oss/langchain/frontend/human-in-the-loop.mdx`, `message-queues.mdx`; it is a client-helper API, not a universal wire endpoint |
| LC-11 | `stream.send()` and `stream.interrupt()` are supported mutation contracts | Contradicted | Medium | Pinned frontend docs consistently use `submit`; wire protocol uses `run.start`/`input.respond`; remove invented methods pending package spike |
| LC-12 | Agent Server supports `reject`, `rollback`, `interrupt`, and `enqueue` multitask strategies; default is `enqueue` | Documented | High | `agent-server-openapi.json`, `src/langsmith/double-texting.mdx` and strategy pages |
| LC-13 | Multitask strategies are a generic OSS Deep Agents capability | Contradicted | High | `src/langsmith/double-texting.mdx` scopes them to Agent Server/LangSmith Deployment |
| LC-14 | Deep Agents HITL interrupts preserve `action_requests[]` and `review_configs[]`; decisions have one entry per request in the same order | Documented | High | `src/oss/deepagents/human-in-the-loop.mdx` |
| LC-15 | Supported HITL decisions are approve, edit, reject, and respond, subject to each review config | Documented | High | `src/oss/deepagents/human-in-the-loop.mdx`; prototype “ignore” is not a decision type |
| LC-16 | A UI may safely flatten a multi-action interrupt to one approval action | Contradicted | High | LC-14 requires ordered batch fidelity |
| LC-17 | MDA is a public, stable API baseline | Contradicted | High | `src/langsmith/managed-deep-agents-overview.mdx` calls it private beta, Cloud US only, and says supported API is being finalized |
| LC-18 | MDA currently provides a CLI-first `mda dev`/`mda deploy` project lifecycle | Gated/beta | High | overview, deploy, CLI, and how-it-works MDA docs |
| LC-19 | Deep Work should recreate `mda deploy` by archiving/uploading source and calling guessed endpoints | Contradicted | High | MDA deploy docs assign compilation, Context Hub sync, secrets, source archive, deploy, and schedule reconciliation to the official workflow |
| LC-20 | Public stable `/v1/deepagents/*` CRUD is available for Deep Work | Unknown | Low | Official prose removes API-driven examples while contracts are being finalized; do not implement until beta/live contract proves exact routes |
| LC-21 | Arbitrary MDA connector CRUD or `/connectors/deepwork/sandbox/*` routes are public contracts | Unknown | Low | MDA project docs describe connector files and platform integrations, not these routes |
| LC-22 | MDA owns backend/store/checkpointer, hosted execution, skills/memory integration, and per-thread sandbox provisioning | Gated/beta | High | `managed-deep-agents-how-it-works.mdx`, deploy docs; adapter should not duplicate these responsibilities |
| LC-23 | MDA schedules are static project declarations reconciled by the official deploy workflow | Gated/beta | High | MDA deploy/how-it-works docs; do not silently mutate them as Agent Server crons |
| LC-24 | Agent Server cron endpoints are scoped to a deployment | Documented | High | `agent-server-openapi.json`; schedules must be aggregated per source |
| LC-25 | LangSmith platform sandboxes expose `/v2/sandboxes` lifecycle APIs | Documented | High | platform sandbox documentation and generated contract; separate from MDA per-thread sandbox semantics |
| LC-26 | Context Hub exposes versioned agent/skill repository operations through official SDK methods with optimistic parent-commit behavior | Documented | High | `src/langsmith/use-the-context-hub.mdx`, `manage-contexts-sdk.mdx` |
| LC-27 | `/v1/platform/hub/repos/*` is the supported Deep Work contract | Unknown | Low | Plan route is not established by the pinned primary workflow; use official SDK or prove live route/package |
| LC-28 | MDA instructions and skills are deployment/project-owned while runtime memories survive deploy and have different ownership | Gated/beta | Medium | MDA how-it-works plus Context Hub docs; model these as separate state classes |
| LC-29 | Fleet agents can be read/invoked through their Agent Server endpoint using an owner PAT | Gated/beta | High | `src/langsmith/fleet/code.mdx`; workspace non-owners are read-only |
| LC-30 | Fleet invocation with a raw header uses `X-Api-Key` plus `X-Auth-Scheme: langsmith-api-key` | Gated/beta | High | `src/langsmith/fleet/code.mdx` |
| LC-31 | Public Fleet create/update/delete is a supported app contract | Unknown | Low | Fleet prose documents read/invoke and permissions; generated platform schema includes Fleet surfaces that may not constitute a stable public product contract; spike exact package/account |
| LC-32 | `/threads/search` provides organization-global task search | Contradicted | High | `agent-server-openapi.json` exposes search on one Agent Server/deployment; Deep Work must aggregate per source |
| LC-33 | Agent Server data-plane requests universally use the same auth header | Unknown | Medium | Classic examples use `X-Api-Key`; custom deployment auth may use `Authorization: Bearer`; Fleet adds `X-Auth-Scheme`; select by source |
| LC-34 | One LangSmith OAuth token is proven to work across platform, control plane, arbitrary Agent Server deployments, Fleet, and MDA | Unknown | Low | OAuth exists for documented LangSmith clients/flows, but the pinned evidence does not establish a universal token/scope contract across all required planes |
| LC-35 | Event Streaming v2 is universally available on every deployment | Contradicted | High | `event-streaming.mdx` is Beta and declares minimum Agent Server/SDK versions |
| LC-36 | Durable `event_id` is the client dedupe key while `seq` orders one connection/replay session | Gated/beta | High | `event-streaming.mdx`; persist both with source/run identity |

## Supported source model

The product must normalize capabilities without pretending that sources share deployment, auth, schedule, sandbox, or configuration semantics.

| Source adapter | v1 status | Required evidence | Allowed responsibilities |
|---|---|---|---|
| Classic LangSmith Deployment | Supported baseline | Live deployment contract spike against pinned client/server versions | Read/invoke assistants; create/read/search threads within that deployment; runs, state, legacy or v2 stream by capability; deployment crons; trace deep-links |
| Local Agent Server | Supported development/demo adapter | Clean-install fixture and live local test | Same Agent Server data-plane subset; local auth/topology documented separately |
| Fleet | Flagged source | Authorized account and PAT contract test | Discover/read/invoke only; no CRUD promise |
| Managed Deep Agents | Private-beta adapter | Capability detection, region/account entitlement, official CLI/package and beta contract transcript | Invoke/read capabilities proven by beta; deploy only through supported official workflow; no guessed API |

A missing optional source must never block classic v1 acceptance. Capability detection must occur at connection time and be refreshable after server/package upgrades.

## Protocol v2, legacy streaming, and resume

The current plan must replace a single generic “resume cursor” with a source/protocol-specific cursor envelope:

| Mode | Subscribe/join | Resume input | Deduplication | Plan rule |
|---|---|---|---|---|
| Event Streaming v2 | `POST /threads/{thread_id}/stream/events` | JSON body `since: <seq>` | Durable `event_id`; `seq` orders replay/session | Capability-gated; open subscription independently from `run.start`/`input.respond` |
| Legacy thread stream | `GET /threads/{thread_id}/stream` | `Last-Event-ID` header | Contract-specific event IDs | Supported fallback; do not label protocol v2 |
| Run join stream | run-specific join endpoint | `Last-Event-ID` only when resumable is enabled | Contract-specific | Use only when source advertises join/resumable behavior |

Reconnect acceptance must prove:

1. no duplicate user-visible event after disconnect/replay;
2. no missed approval interrupt;
3. stale cursor handling and bounded-buffer gaps are explicit;
4. reauthentication does not discard the last confirmed cursor;
5. cancellation during reconnect has a deterministic outcome;
6. refresh/reopen reconstructs current thread state before replaying transient UI effects.

## HITL normalization

The normalized model must preserve the exact runtime batch rather than creating a friendlier but lossy object:

```text
InterruptBatch
  source_id
  thread_id
  run_id
  interrupt_id or stable source reference
  observed_at and source_version
  actionRequests[]       # ordered, unmodified source requests
  reviewConfigs[]        # ordered/source-complete configuration
  decisions[]            # exactly one per action request, same order
  status                 # pending | submitting | accepted | stale | failed | cancelled
```

Python sources use `action_requests` and `review_configs`; JavaScript surfaces may expose camelCase. Serialization adapters may translate casing, but must not reorder, merge, drop, or infer entries. `edit` must preserve the source schema and only be offered when allowed. `respond` is distinct from editing tool arguments. “Ignore” is not a runtime decision. V1 has no user-visible “Mark resolved” or force-resolve action: reconciliation removes a stale projection after refetch proves no interrupt remains, while pending work requires a valid decision or separately verified cancellation.

Decision submission requires an application idempotency record because a network failure can leave the source outcome ambiguous. On ambiguity, refetch the pending interrupt before retry. Never send a second decision merely because the first HTTP response was lost.

## `submit`, steering, and multitask strategy

`stream.submit(...)` is documented on the LangGraph frontend `useStream` helper for a user input and for a resume command [LC-10]. It does not prove that every source exposes an identically shaped wire API. The React hook calls a browser-safe normalized SDK mutation against FastAPI; FastAPI selects the source adapter and the verified underlying `run.start`, `input.respond`, legacy run call, or supported SDK method.

For steering while a run is active:

- `enqueue` is the safe default only on Agent Server sources that advertise multitask strategies;
- `reject` reports an actionable conflict and preserves the current run;
- `interrupt` cancels/interrupts the active run before the new one and must be an explicit user choice;
- `rollback` is destructive relative to current run progress and must not be used as a generic Cancel action;
- an OSS/local adapter without Agent Server multitask support must disable or queue in the application only if that queue's ownership, persistence, and ordering are specified.

The UI must not call guessed `stream.send()` or `stream.interrupt()` methods. Exact installed frontend/client package types and runtime calls are a Gate 0 spike.

## Plane and authentication matrix

| Plane | Representative responsibilities | Base identity | Authentication rule | Deep Work owner |
|---|---|---|---|---|
| Deep Work application API | Sessions, Agent Source registry, cross-source index, normalized approvals, notifications, app drafts/audit | Deep Work URL | Deep Work session; server resolves secret references | `apps/api`; browser/desktop never receive broad platform keys |
| Agent Server data plane | Assistants, threads, runs, state, streaming, deployment crons | Per deployment/source URL | Source-specific: classic key/custom auth/Fleet scheme | Source adapter in application service/shared contract |
| LangSmith control plane | Deployment create/update/status | LangSmith control-plane URL | `X-Api-Key` + `X-Tenant-Id` | Server-only deployment service |
| LangSmith platform | Context Hub, sandboxes, traces, workspace resources | Platform API/official SDK | Operation and key scope specific | Server-side integration service |
| MDA official workflow | Compile/sync/archive/deploy/reconcile schedules | Official CLI/package/account | Private-beta documented flow | Capability adapter/job wrapper, not a reimplementation |
| GitHub | Installation/repository/branch/PR/CI/merge | GitHub App/API | Installation token via server-side proxy | Coding integration service |

No credential may be stored in `localStorage`, serialized into task/thread
state, emitted in logs/traces, passed to sandbox tools, or bundled with Tauri.
The server-only `AgentSourceRecord` stores an opaque `authRef`; the application
service resolves it according to plane and actor authorization. Client-safe
`AgentSourceView` exposes credential state/capability evidence and never the
reference itself.

## Context Hub ownership

The plans currently use “memory,” “agent configuration,” “skills,” and “Context Hub” as if they were a single mutable object. They are not.

| State | Authority | Write path | Review rule |
|---|---|---|---|
| Agent instructions/skills source | Versioned project or Context Hub repository | Official SDK/project workflow | Draft and diff before publish |
| MDA deployment instructions/skills | MDA project/deploy workflow | `mda deploy` private-beta path | Do not mutate with guessed platform routes |
| Runtime thread state/checkpoints | Agent Server/runtime | Run/input/checkpoint APIs | Source-authoritative; app stores references/projections only |
| Runtime agent memory | Runtime/Context Hub semantics | Capability-specific | Preserve across deploy where documented; live spike exact ownership |
| Organizational memory proposal | Deep Work draft/audit plus versioned target | Human-reviewed publish operation | Approve/edit/reject required; never auto-publish synthesis |

Context Hub version identifiers, parent commits, and conflict results must be preserved. A lost optimistic-concurrency conflict must never overwrite newer content.

## Schedules, sandboxes, connectors, and Fleet

### Schedules

Classic Agent Server crons are deployment-scoped [LC-24]. MDA schedules are project declarations reconciled by the official deploy workflow [LC-23]. Therefore the application presents a per-source schedule index and routes create/edit/delete through the adapter supported for that source. It must not merge two schedule types into one mutation contract merely because their cards look the same.

### Sandboxes

Platform sandboxes and MDA per-thread sandboxes have different lifecycle owners [LC-22, LC-25]. A normalized coding-session model may expose provision/status/snapshot/terminate capabilities, but it cannot promise a manually created platform sandbox is the MDA thread sandbox. The mapping among task, thread, run, sandbox, snapshot, and repository checkout must be captured in live transcripts.

### Connectors

MDA documents project connector files and supported integrations, not arbitrary connector CRUD [LC-21]. Workspace credential installation, agent connector binding, and sandbox tool availability are separate concerns. MCP belongs in connector/source capabilities; ACP/A2A remain future discovery, not a generic v1 “Protocols” settings promise.

### Fleet

Fleet read/invoke is gated and has a special auth scheme [LC-29, LC-30]. The application must not offer Clone, Create, Save, Deploy, or Delete for a Fleet agent unless an accepted live contract specifically proves that operation and authorization. Workspace non-owner behavior must be read-only.

## Per-source aggregation

Because thread search is deployment-scoped [LC-32], Deep Work must not expose a fake global Agent Server query. The application service maintains a source registry and queries each authorized source independently, then normalizes, merges, and paginates results. The plan must specify:

- source-scoped cursors and partial failure;
- deterministic cross-source ordering and stable composite IDs;
- per-source freshness and last successful sync;
- authorization filtering before aggregation;
- collision behavior for identical thread/assistant IDs;
- whether a task is source-authoritative or an application projection;
- background indexing boundaries and retention;
- search result disclosure when one or more sources are unavailable.

Global search may be implemented over an app-owned projection in Postgres, but its freshness and source coverage must be visible. It is not a proxy for a nonexistent global runtime endpoint.

## Contract-invalid plan assumptions and required corrections

| Current plan assumption | Finding | Required correction |
|---|---|---|
| One resumable SSE rule based on `Last-Event-ID` | Contradicted for protocol v2 | Add protocol-specific cursor adapters and golden reconnect tests |
| `stream.send()` / `stream.interrupt()` | Not supported by pinned frontend contract | Use normalized input/cancel services backed by verified `submit`/Agent Server methods |
| Single approval object and “ignore” decision | Contradicts HITL batch model | Preserve ordered request/config arrays and allowed decisions |
| Multitask strategy on every runtime | Agent Server-specific | Advertise capability per source and provide disabled/fallback behavior |
| Control-plane thread search | Wrong plane | Query each Agent Server; aggregate in app service |
| MDA as required v1 deployment | Private beta | Make classic deployment baseline and MDA a non-blocking adapter |
| Handwritten MDA archive/deploy | Reimplements official workflow | Invoke/observe supported `mda` workflow only while beta |
| `/v1/deepagents/*` CRUD | Unknown/unsupported public promise | Remove from ready plans; reinstate only with accepted beta contract |
| Arbitrary MDA connector/sandbox routes | Unknown | Use documented project/platform paths or mark discovery gate |
| Fleet manager CRUD | Not established | Re-scope to read/invoke; capability gate every mutation |
| `/v1/platform/hub/repos/*` | Not validated as supported contract | Use pinned official SDK and verify exact installed package/live behavior |
| One API key/OAuth header policy | Contradicted by plane-specific auth | Credential matrix and source-specific header builder |
| Organization-global runtime thread search | Nonexistent | App-owned per-source index/projection |

## Mandatory Gate 0 live-contract spike

No plan depending on a mutable external API may be marked ready until a reproducible spike records the exact package versions, account/region, request/response schema, headers with secrets redacted, and a golden fixture. Where official prose and generated contracts disagree, the accepted live result outranks both for the pinned implementation version and must be recorded in the decision register.

Required spike scenarios:

1. **Classic bootstrap**: list/read/invoke an assistant, create a thread/run, read state, and link a trace.
2. **Protocol v2**: start a run, subscribe, disconnect, resume with `since`, dedupe with `event_id`, and observe bounded-gap behavior.
3. **Legacy fallback**: prove `Last-Event-ID` resume on the exact fallback endpoint/client.
4. **HITL**: receive a two-action batch, render exact review configs, submit mixed ordered decisions, reconnect before and after response, and reject a stale duplicate.
5. **Multitask**: capture `reject`, `rollback`, `interrupt`, and `enqueue`, including default behavior and unsupported-source fallback.
6. **Auth matrix**: classic data plane, custom auth if supported, control plane with tenant header, Fleet special scheme, and expired/revoked credentials.
7. **Schedules**: classic Agent Server cron CRUD/search; confirm MDA schedule workflow separately through official tooling.
8. **Context Hub**: official SDK push/pull/list, parent-commit conflict, version read, and permission failure.
9. **Sandbox**: platform lifecycle versus MDA per-thread provisioning, setup script, snapshot, egress, and cleanup ownership.
10. **MDA private beta**: entitlement detection, official deploy/invoke/read flow, version/region constraints, and failure when unavailable; it must remain outside release-critical acceptance.
11. **Fleet**: authorized read/invoke and non-owner read-only behavior; explicitly test whether any desired mutation is truly supported before planning it.
12. **OAuth**: verify exact scopes/audiences and whether one session can lawfully access every required plane; otherwise retain server-side API-key/key-proxy baseline.

Spike artifacts must include sanitized HTTP transcripts, generated/type definitions, a capability-manifest fixture, automated contract tests, and an expiry/revalidation trigger. Screenshots or successful prose walkthroughs alone are not acceptance evidence.

## Readiness gates

This contract audit is ready to integrate only when:

- every external operation in a v1 feature references an LC claim and accepted live contract artifact;
- no implementation plan embeds guessed paths, methods, headers, or response fields;
- classic deployment can complete the full first-task, stream, approval, reconnect, and recovery journey without MDA/Fleet;
- MDA and Fleet absence degrade to explicit capability states rather than blocking or breaking navigation;
- source, control-plane, platform, GitHub, and application credentials have separate ownership and audit rules;
- per-source aggregation handles partial failure and does not claim global runtime search;
- protocol v2 and legacy stream code paths have independent tests and cursor storage;
- HITL golden tests prove array fidelity, order, allowed decision types, idempotency, and stale handling;
- discrepancies between pinned prose, generated OpenAPI, installed package types, and live behavior are resolved in the decision register.

## Pinned source index

All sources are from `langchain-docs-reference@7b9215d708e0b57e6fbae7b5d0762c4118b8e309`:

- Agent Server generated contract: `src/langsmith/agent-server-openapi.json`;
- protocol v2: `src/langsmith/event-streaming.mdx`;
- legacy streaming: `src/langsmith/streaming.mdx`;
- concurrency strategies: `src/langsmith/double-texting.mdx`, `enqueue-concurrent.mdx`, `reject-concurrent.mdx`, `rollback-concurrent.mdx`, `interrupt-concurrent.mdx`;
- Deep Agents HITL: `src/oss/deepagents/human-in-the-loop.mdx`;
- frontend submission/resume: `src/oss/deepagents/frontend/subagent-streaming.mdx`, `src/oss/langchain/frontend/human-in-the-loop.mdx`, `message-queues.mdx`;
- control plane: `src/langsmith/api-ref-control-plane.mdx`, `src/langsmith/control-plane.mdx`;
- MDA status and lifecycle: `src/langsmith/managed-deep-agents-overview.mdx`, `managed-deep-agents-deploy.mdx`, `managed-deep-agents-how-it-works.mdx`, `managed-deep-agents-cli.mdx`;
- Fleet read/invoke: `src/langsmith/fleet/code.mdx`;
- Context Hub: `src/langsmith/use-the-context-hub.mdx`, `src/langsmith/manage-contexts-sdk.mdx`;
- generated platform evidence where prose may disagree: `src/langsmith/langsmith-platform-openapi.json`.

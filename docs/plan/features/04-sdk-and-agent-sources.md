# F04 · `packages/sdk` & agent sources

*Deep Work feature spec · 2026-07-22 · Status: draft · Milestone: M1 · Depth: implementation-ready*

Sources: [02 · Architecture §2/§6/§7](../02-architecture.md) · [03 · UI spec §5](../03-ui-spec.md) · [06 · Frontend plan Phase B](../06-frontend-implementation.md) · [04 · Roadmap M0–M1](../04-roadmap.md) · [research 21 (UI contract)](../../research/21-gapfill-ui-contract.md) · [research 20 (MDA API)](../../research/20-gapfill-mda-api.md) · [research 23 (runtime tiers)](../../research/23-gapfill-runtime-tiers.md) · [research 12 (lifecycle/auth)](../../research/12-lifecycle-auth-followup.md) · [research 13 (agent-inbox)](../../research/13-agent-inbox.md) · [research 04 (LangChain UIs)](../../research/04-langchain-uis.md) · [decisions](../decisions.md)

## 1. Scope

`packages/sdk` is the TypeScript client layer everything else consumes: the **AgentSource registry** (multi-runtime connection config), the **control-plane client**, the **wire-normalization layer** (D-011), **`useStream` option factories**, the **`DataProvider` seam** for `apps/web`, **cross-source thread aggregation**, and the **typed error taxonomy**. It is framework-agnostic TS (no React dependency in core; `apps/web` calls `useStream` itself with SDK-built options) so `packages/sdk` also serves Tauri and the post-v1 Expo app ([02 §11](../02-architecture.md)).

Out of scope here: inbox UX and its N+1/pagination policy (→ [./08-task-inbox.md](./08-task-inbox.md)), approvals UI, the Python FastAPI glue service `apps/server` itself (P-005 — this spec only defines what the SDK expects from it), the agent package, and the post-v1 pure-OSS tier's server (→ [./26-oss-selfhost-tier.md](./26-oss-selfhost-tier.md); the SDK only reserves the adapter seam). Contract-test fixtures originate in [./02-m0-spikes.md](./02-m0-spikes.md) Spike 3.

## 2. Dependencies & seams

| Dependency | Direction | Contract |
|---|---|---|
| `@langchain/react` **^1.0.28**, `@langchain/langgraph-sdk` **^1.9.x** (1.9.27 inspected), `@langchain/protocol` 0.0.18 types | consumes | Protocol-v2 stream client + `HttpAgentServerAdapter`; pinned + renovate-grouped ([05](../05-oss-setup.md)) |
| `apps/server` (Python FastAPI glue, P-005) | calls | Any request that must carry a secret (service keys, `X-MDA-Ingress-Secret`, GitHub tokens) routes via `apps/server` proxy endpoints; the SDK's plane router decides proxy-vs-direct per source auth mode |
| `apps/web` (Next.js, D-022) | consumed by | Components depend only on `DataProvider` + normalized types — never on raw wire shapes ([06 Phase B](../06-frontend-implementation.md)) |
| `packages/ui` fixtures (P-004) | consumed by | `FixturesProvider` wraps the fixture set kept from the v0 concept's `lib/data.ts` ([06 Phase A](../06-frontend-implementation.md)) |
| [./02-m0-spikes.md](./02-m0-spikes.md) Spike 3 | gated by | Golden protocol-v2 transcripts recorded against `langgraph dev` become this package's CI contract suite |
| [./08-task-inbox.md](./08-task-inbox.md) | consumed by | Uses `searchThreadsAcrossSources` primitive (§3.6); owns the UX-level pagination policy |
| [./26-oss-selfhost-tier.md](./26-oss-selfhost-tier.md) | seam only | `CustomAdapterOptions`/`AgentServerAdapter` branch reserved; no v1 implementation |

## 3. Design

### 3.1 AgentSource registry

An `AgentSource` describes one place agents live. Five types, one client ([02 §2](../02-architecture.md)):

| Type | What | v1 |
|---|---|---|
| `mda` | Managed Deep Agents deployment (hosted Agent Server at the deployment URL; identity via `trusted_backend`/`validated_token`) | ✅ |
| `deployment` | Any LangSmith Deployment URL (classic `langgraph.json` project) | ✅ |
| `fleet` | Fleet agent, invoke/read only (owner-gated; CRUD not public) | ✅ |
| `local` | `langgraph dev` on localhost — no API key, no license check ([research 23](../../research/23-gapfill-runtime-tiers.md)) | ✅ |
| `custom` | Post-v1 protocol server via `AgentServerAdapter` → [./26-oss-selfhost-tier.md](./26-oss-selfhost-tier.md) | 🔜 type reserved |

**Capability flags.** Components never branch on `source.type` — only on `source.capabilities`, computed as *type defaults → probe results (health/`GET /info`-class checks where available) → user overrides*. Matrix of type defaults (❓ = unresolved, see §9 question number):

| Capability | mda | deployment | fleet | local | custom |
|---|---|---|---|---|---|
| `invoke` (runs/commands/stream) | ✅ (beta: design-partner-gated → flag off + link-out, [02 §6](../02-architecture.md)) | ✅ | ✅ owner only; non-owner 404 | ✅ | via adapter |
| `streamResumable` (`Last-Event-ID`, join) | ✅ | ✅ | ✅ | ✅ | ❌ unless adapter reimplements replay ([research 23](../../research/23-gapfill-runtime-tiers.md)) |
| `webSocket` transport | ❓ Q1 | ❓ Q1 | ❓ Q1 | ❓ Q1 | adapter-defined |
| `doubleTexting` (server-honoured `multitask_strategy`) | ⚠️ Q2 (enqueue documented as default param; server honouring unverified) | ⚠️ Q2 | ⚠️ Q2 | ⚠️ Q2 | ❌ |
| `crons` (per-deployment `/runs/crons`) | ✅ (mda-reconciled; UI CRUD same API) | ✅ | ❓ Q3 | ❓ Q3 | ❌ |
| `assistantsCrud` / versioning | ✅ | ✅ | read-only | ✅ | ❌ |
| `deployMgmt` (`/v2/deployments`) | ✅ | ✅ | ❌ (Fleet CRUD not public) | n/a | n/a |
| `deepagentsApi` (`/v1/deepagents/*`) | ✅ | n/a | n/a | n/a | n/a |
| `webhooks` on run-create | ✅ | ✅ | ❓ Q3 | ❓ Q3 | ❌ |
| `mdaIdentity` (actor/tenant headers, guest tokens) | ✅ | ❌ (generated `langgraph_sdk.Auth` instead) | ❌ | ❌ | ❌ |

Degradation is UI-visible, not silent: a flag that is off renders the affordance disabled with a link-out (e.g. Fleet config → smith.langchain.com), per the manager's graceful-degradation rule ([02 §6](../02-architecture.md)).

**Config document.** User-editable multi-source registry per [03 §3.6](../03-ui-spec.md) — OAP's `NEXT_PUBLIC_DEPLOYMENTS` JSON-array pattern (`{id, deploymentUrl, tenantId, name, isDefault, defaultGraphId}`, [research 04](../../research/04-langchain-uis.md)) upgraded to runtime-editable. Precedent for client-side persistence: agent-inbox's `inbox:agent_inboxes` localStorage list ([research 13](../../research/13-agent-inbox.md)).

**Persistence decision (v1):** client-side. Deep Work has no database of its own in v1 ([02 §1](../02-architecture.md)); the registry is a versioned JSON doc (`version: 1`) in localStorage (`deepwork:agent-sources`), seeded at boot from an env JSON (`NEXT_PUBLIC_AGENT_SOURCES`, OAP-style) with `origin: 'env' | 'user'` merge semantics — user edits win, env removals tombstone. Export/import as JSON from settings. **Secrets are excluded by schema**: the config carries an auth *mode*, never key material (§6). Cross-device sync of the registry is deferred (§9 Q6).

### 3.2 Control-plane client

One client, two address families: the LangSmith **control plane** at `api.smith.langchain.com`, and **per-deployment Agent Server** endpoints at each source's URL. Note: crons are *data-plane per-deployment* — `mda deploy` reconciles schedules by calling the deployment's own Agent Server ([research 20](../../research/20-gapfill-mda-api.md)) — the SDK groups them here because the fleet-manager UI consumes them alongside control-plane surfaces.

| Surface | Endpoints (verified) | Base | Source |
|---|---|---|---|
| Deployments | `GET/POST /v2/deployments`, `POST /v2/deployments/{id}/upload-url` (signed PUT, 200 MB cap), revisions polling, redeploy | control plane | [research 20](../../research/20-gapfill-mda-api.md), [12](../../research/12-lifecycle-auth-followup.md) |
| Deep agents | `/v1/deepagents/*` — agents CRUD + health; `mcp-servers` CRUD + `/mcp/tools` + oauth-provider + auth-sessions | control plane | [research 20](../../research/20-gapfill-mda-api.md) |
| Crons | `POST /runs/crons`, `POST /runs/crons/search` | deployment URL | [research 20](../../research/20-gapfill-mda-api.md), [02 §6](../02-architecture.md) |
| Context Hub | `/v1/platform/hub/repos/` (file get/commit — instructions/skills/memories) | control plane | [research 12](../../research/12-lifecycle-auth-followup.md) |
| Sandboxes | `/v2/sandboxes` — snapshots, boxes, exec (incl. WS), files, tunnels, service URLs | control plane | [research 12](../../research/12-lifecycle-auth-followup.md), [02 §6](../02-architecture.md) |

**Auth-header injection per plane.** Every request is built by a plane router: `resolveAuth(source, plane) → {headers, via: 'proxy' | 'direct'}`.

| Plane | Headers | Injected where |
|---|---|---|
| Control plane, PAT | `X-Api-Key: <PAT>` | `apps/server` proxy by default; direct only in local mode |
| Control plane, org-scoped service key (`lsv2_sk_`) | `X-Api-Key` + **`X-Tenant-Id`** (required per request, [research 12](../../research/12-lifecycle-auth-followup.md)) | `apps/server` only (P-005 — service keys are secrets) |
| Fleet data plane | `x-api-key: <PAT>` + **`X-Auth-Scheme: langsmith-api-key`** | direct (agent-inbox precedent) or proxy |
| MDA data plane, `validated_token` | `Authorization: Bearer <token>` | direct from client (documented beta pattern, [research 20](../../research/20-gapfill-mda-api.md)) |
| MDA data plane, `trusted_backend` | `X-MDA-Ingress-Secret` + `X-MDA-Actor-Id` [+ `X-MDA-Tenant-Id`] | **`apps/server` only, never client-side** (P-005; [02 §5](../02-architecture.md)) |
| `langgraph dev` | none | direct |

The SDK ships both paths behind one interface: `direct` composes `defaultHeaders` on the client/`useStream` options; `proxy` rewrites the base URL to the `apps/server` passthrough route (the `langgraph-nextjs-api-passthrough` pattern relocated to FastAPI per P-005). Mode→route mapping is fixed (auth modes are [F05 §4 contract 4](./05-auth-and-identity.md)'s canonical enum, adopted 1:1 in §4): `oauth_session`/`key_proxy` → always `via: 'proxy'` (`apps/server` strips inbound auth/identity headers, then injects from the session — F05 contract 2); `key_local`/`validated_token` → `direct`, headers obtained from the source's header-provider callback, never from globals (F05 contract 4); `none_local` → `direct`, no headers. `trusted_backend` identity is reachable only through the proxy modes.

### 3.3 Normalization layer (D-011)

Wire fields are snake_case; normalization to camelCase canonical happens **once**, in one module (`packages/sdk/src/normalize/`), and nowhere else ([05 repo notes](../05-oss-setup.md): "HITL casing lives HERE, nowhere else"; [02 §7](../02-architecture.md)). Rules, all grounded in [research 21](../../research/21-gapfill-ui-contract.md):

- **General**: snake_case → camelCase at the SDK boundary; components never see casing variants.
- **The one exception**: `reviewConfigs[].actionName/action_name` and `argsSchema/args_schema` are *not* aliased by upstream `normalizeHitlInterruptPayload` — the SDK preserves **both** keys on the canonical object and exports `getActionName(rc)` / `getArgsSchema(rc)` accessors so UI code has exactly one way to read them.
- **HITL payloads**: Python middleware emits snake_case `{action_requests, review_configs}`, JS emits camelCase — both normalize to canonical `HITLRequest {actionRequests: [{name, args, description?}], reviewConfigs: [...]}`. Resume is `{decisions: [...]}` via `respond()/respondAll()`; on `edit` the SDK sends **both** `editedAction` and `edited_action` (upstream duplicates on send — we preserve that behavior).
- **FileData**: three wire variants — Python `{content: string, encoding: 'utf-8'|'base64'}`, JS v1 `{content: string[]}` (lines), JS v2 `{content: string|Uint8Array, mimeType}` — normalize to one `NormalizedFile` (§4). Variant detection: `Array.isArray(content)` → v1; `encoding` present → py; `mimeType` present → v2; else `ContractViolationError` (§5). `Record<path, FileData|null>` null-delete updates are honored.
- **Never normalize blindly**: unknown fields pass through under a `raw` escape hatch so schema-tolerant UI fallbacks ([03 §3.3](../03-ui-spec.md)) can render the original payload.

### 3.4 `useStream` integration

The SDK does not wrap the hook; it builds its options. `buildStreamOptions(source, threadId, overrides?) → UseStreamOptions` returns the `AgentServerOptions` branch for the four v1 tiers and the `CustomAdapterOptions` branch (with `HttpAgentServerAdapter` or a custom adapter) for the post-v1 tier ([research 21/23](../../research/21-gapfill-ui-contract.md)).

- **Transport**: SSE default; `'websocket'` only when `source.capabilities.webSocket` is confirmed (Q1) — opt-in on desktop ([03 §5](../03-ui-spec.md)).
- **Reconnection**: `maxReconnectAttempts` / `streamIdleReconnect` / `reconnectDelayMs` tuned per surface profile (mobile vs desktop presets exported as constants); on background/tab-hide the app calls `stream.disconnect()` and rejoins via resumable streams + `Last-Event-ID` ([03 §5](../03-ui-spec.md), [02 §7](../02-architecture.md)).
- **Pins**: `@langchain/react` ^1.0.28 · `@langchain/langgraph-sdk` ^1.9.x — weekly-release churn is absorbed here and only here ([04 risk register](../04-roadmap.md)).
- **Banned v0 anti-patterns** ([03 §5](../03-ui-spec.md), [research 21](../../research/21-gapfill-ui-contract.md)) — enforced by a lint rule in this package and in `apps/web`: `onCustomEvent`, `streamMode`, `joinStream`, `reconnectOnMount`, `fetchStateHistory`, `submit(null, {command: {resume}})` (resume is **only** `respond()/respondAll()`), `getMessagesMetadata`/`setBranch` (branching is `checkpoints` channel + `useMessageMetadata(...).parentCheckpointId` + `submit(input, {forkFrom})`).

### 3.5 `DataProvider` — the seam `apps/web` consumes

Per [06 Phase B](../06-frontend-implementation.md): components depend on a `DataProvider` interface with two v1 implementations — **`FixturesProvider`** (P-004; wraps the fixture set retained from `lib/data.ts`, zero credentials, powers demo mode/Storybook/tests) and **`LiveProvider`** (registry + control-plane client + stream factories). Both are constructed at the app boundary; swapping them changes no component code. Fixtures ship *canonical* (already-normalized) shapes so the fixtures path exercises the same types the live path produces after normalization.

### 3.6 Thread aggregation (inbox primitive)

`searchThreadsAcrossSources(query)` fans out `threads.search({metadata: {assistant_id | graph_id}, sortBy: 'updated_at', status?, limit, offset})` per source ([03 §3.1](../03-ui-spec.md); agent-inbox precedent caps `limit ≤ 100`, [research 13](../../research/13-agent-inbox.md)), then: tags every thread with `sourceId`, merge-sorts by `updated_at`, maintains an opaque per-source cursor map for stable pagination, dedupes by `(deploymentUrl, threadId)`, and attaches interrupt counts hydrated from `thread.getState().tasks[].interrupts` ([research 21](../../research/21-gapfill-ui-contract.md)). Partial failure returns `{threads, errors: DeepWorkError[]}` — one dead source never blanks the inbox. The N+1/pagination *UX policy* (page sizes, polling cadence, badge refresh) belongs to [./08-task-inbox.md](./08-task-inbox.md); this package owns only the deterministic primitive.

### 3.7 Typed error taxonomy & contract tests

All SDK failures throw `DeepWorkError` subclasses (§4) carrying `{sourceId?, plane, endpoint, status?, retryable}` with auth headers scrubbed. Mapping highlights: Fleet non-owner 404 and MDA beta-gated invoke → `GatedEndpointError` (a 404 that means "no access", not "missing" — [research 12](../../research/12-lifecycle-auth-followup.md)); org-scoped key without tenant → `TenantScopeError` thrown *before* any network call; 429 → `RateLimitError` (gateway table exists, e.g. 2000/10s general, [research 20](../../research/20-gapfill-mda-api.md)); post-normalization schema failures → `ContractViolationError` with the raw payload attached for the schema-tolerant UI fallback.

**CI pinning**: [./02-m0-spikes.md](./02-m0-spikes.md) Spike 3 records golden protocol-v2 transcripts against `langgraph dev` (content blocks, tools channel, HITL respond, subagent namespaces, `Last-Event-ID` resume — [04 M0](../04-roadmap.md)). Those transcripts live in-repo; this package's CI replays them through normalization + assembly and snapshot-asserts canonical outputs, plus casing fixtures (py & js HITL emitters) and all three FileData variants ([05 CI matrix](../05-oss-setup.md)). A renovate bump that changes upstream behavior fails here first, not in the app.

## 4. Contracts

```ts
// -- registry --------------------------------------------------------------
type AgentSourceType = 'mda' | 'deployment' | 'fleet' | 'local' | 'custom';
interface AgentSource {
  id: string;                      // stable uuid
  type: AgentSourceType;
  name: string;
  deploymentUrl: string;           // http(s) base; localhost for `local`
  assistantId?: string;            // default assistant; else graphId
  graphId?: string;
  tenantId?: string;               // workspace scoping (OAP precedent)
  isDefault?: boolean;
  origin: 'env' | 'user';
  // canonical enum = F05 §4 contract 4, adopted 1:1; route/header behavior per mode: §3.2
  auth: { mode: 'oauth_session' }                            // OAuth bearer in apps/server session; via proxy
       | { mode: 'key_proxy' }                               // PAT/service key in apps/server session; via proxy (default)
       | { mode: 'key_local'; keyRef: string }               // local mode only; direct; ref, never the key
       | { mode: 'validated_token' }                         // MDA bearer from auth flow; direct from client
       | { mode: 'none_local' };                             // langgraph dev; direct, no headers
  capabilities: Partial<SourceCapabilities>;                 // overrides on type defaults
}
interface SourceCapabilities {
  invoke: boolean; streamResumable: boolean; webSocket: boolean | 'unverified';
  doubleTexting: boolean | 'unverified'; crons: boolean | 'unverified';
  assistantsCrud: boolean | 'readonly'; deployMgmt: boolean;
  deepagentsApi: boolean; webhooks: boolean | 'unverified'; mdaIdentity: boolean;
}
interface AgentSourceRegistry {
  list(): AgentSource[]; get(id: string): AgentSource | undefined;
  upsert(s: AgentSource): void; remove(id: string): void;
  resolveCapabilities(id: string): SourceCapabilities;       // defaults ⊕ probe ⊕ overrides
  exportJson(): string; importJson(json: string): ImportResult;
}

// -- normalized types (canonical camelCase, D-011) ---------------------------
interface NormalizedFile { path: string; content: string | Uint8Array;
  mimeType?: string; encoding?: 'utf-8' | 'base64'; createdAt?: string; modifiedAt?: string;
  wireVariant: 'py' | 'jsV1' | 'jsV2'; }
interface HITLRequest { actionRequests: { name: string; args: Record<string, unknown>; description?: string }[];
  reviewConfigs: ReviewConfig[]; raw: unknown; }
// ReviewConfig keeps BOTH casings for the documented exception; use the accessors.
interface ReviewConfig { actionName?: string; action_name?: string;
  allowedDecisions: ('approve' | 'edit' | 'reject' | 'respond')[];
  argsSchema?: unknown; args_schema?: unknown; }
declare function getActionName(rc: ReviewConfig): string;
declare function getArgsSchema(rc: ReviewConfig): unknown | undefined;

// -- data provider -----------------------------------------------------------
interface DataProvider {
  sources: AgentSourceRegistry;
  threads: { searchAcrossSources(q: AggregateThreadQuery): Promise<AggregateThreadResult> };
  streamOptionsFor(sourceId: string, threadId?: string): UseStreamOptions;  // @langchain/react branch union
  controlPlane: { deployments: DeploymentsApi; deepagents: DeepagentsApi;
                  hub: ContextHubApi; sandboxes: SandboxesApi };
  crons(sourceId: string): CronsApi;              // data-plane, per source
}

// -- errors -------------------------------------------------------------------
abstract class DeepWorkError extends Error {
  sourceId?: string; plane: 'control' | 'data' | 'proxy'; endpoint: string;
  status?: number; retryable: boolean; }
class AuthError extends DeepWorkError {}            // 401/403
class TenantScopeError extends DeepWorkError {}     // org-scoped key, no X-Tenant-Id — pre-flight
class GatedEndpointError extends DeepWorkError {}   // Fleet non-owner 404, MDA beta gate
class RateLimitError extends DeepWorkError {}       // 429 + retry-after if present
class TransportError extends DeepWorkError {}       // SSE/WS drop, reconnect exhausted
class ContractViolationError extends DeepWorkError { raw: unknown; } // schema fail post-normalize
class NotSupportedError extends DeepWorkError {}    // capability flag off
```

## 5. Edge cases & failure modes

| Case | Behavior |
|---|---|
| FileData variant ambiguous (no `encoding`/`mimeType`, non-array `content`) | `ContractViolationError` with `raw`; UI degrades to raw view, never guesses binary-ness |
| Malformed interrupt payload | Normalize best-effort → canonical with `raw`; UI renders raw-JSON fallback card ([03 §3.3](../03-ui-spec.md)) — the SDK must not throw on render-path data |
| Fleet non-owner access | 404 → `GatedEndpointError` with "owner-gated" hint — never reported as "thread not found" |
| Org-scoped `lsv2_sk_` without `tenantId` | `TenantScopeError` before network I/O |
| One source down during aggregation | Partial result + per-source error; inbox renders what it has |
| Same deployment registered twice | Dedupe by `(deploymentUrl, threadId)`; registry warns on duplicate URL at upsert |
| `multitask_strategy` unsupported server-side (Q2) | Queue-vs-interrupt affordance downgrades to client-side enqueue (upstream already queues client-side, [research 21](../../research/21-gapfill-ui-contract.md)) |
| WS upgrade refused | Transparent fallback to SSE; capability flag self-corrects to `false` |
| Reconnect attempts exhausted / `Last-Event-ID` replay unavailable (custom tier) | `TransportError{retryable: true}`; UI offers manual rejoin; on rejoin, state re-hydrates from thread state |
| Key/token expires mid-stream | `AuthError` surfaced through stream error channel; source marked unhealthy until re-auth |
| Source deleted while its threads are open | Open streams closed; threads keep rendering from cached state, tagged "source removed" |
| localStorage unavailable (SSR pass, private mode) | Registry is client-only and hydration-safe: in-memory fallback + env seed |
| Env seed changes between boots | Merge by `id`: user edits win; removed env entries tombstoned, not resurrected |

## 6. Security & privacy

- **No secrets in the registry or localStorage** — enforced by type (auth is a mode + `keyRef`, never material) and by an import-time schema check that rejects key-shaped strings. Per P-005, service keys, `X-MDA-Ingress-Secret`, and anything org-scoped live in `apps/server`; the `key_local` mode exists only for local mode with the on-screen trust story ([03 §3.6](../03-ui-spec.md)).
- **Header hygiene**: `DeepWorkError` scrubs `Authorization`/`X-Api-Key`/`x-api-key`/`X-MDA-*` from anything it captures; no request/response logging of auth headers anywhere in the package.
- **Trusted-backend headers are server-only**: the SDK has no code path that attaches `X-MDA-Ingress-Secret` client-side; the `proxy` auth mode is the only route to trusted_backend identity ([02 §5](../02-architecture.md)).
- **Untrusted content passes through untouched**: normalization is structural only (no eval, no HTML handling); webhook/schedule payload rendering happens downstream inside untrusted-content boundaries ([02 §10](../02-architecture.md)).
- **Tenant isolation**: `X-Tenant-Id` is stamped per request from source config, never from ambient globals — two sources in different workspaces cannot cross-contaminate requests.
- Registry export files are shareable by design and therefore must stay secret-free (same schema check on export).

## 7. Acceptance criteria

1. Registry: CRUD + localStorage round-trip + env-seed merge semantics covered by tests; stored/exported JSON contains no key material (schema test with `lsv2_`-prefixed probe strings).
2. The same inbox and task-detail components render against `FixturesProvider` and `LiveProvider` with zero component-code changes (type-level: components import only `DataProvider` + canonical types).
3. Spike-3 golden-transcript suite green in CI: content blocks, tools-channel assembly, HITL respond, subagent namespaces, `Last-Event-ID` resume.
4. Normalization: Python and JS HITL fixture payloads produce deep-equal canonical objects except the documented `reviewConfigs` dual-casing keys; all three FileData variants map to `NormalizedFile`; unknown variant throws `ContractViolationError`.
5. Control-plane client covers every endpoint in §3.2's table; header injection matches §3.2's auth matrix per plane (asserted via recorded-request tests); `TenantScopeError` fires pre-flight.
6. `buildStreamOptions` yields valid `AgentServerOptions` for all four v1 source types and a `CustomAdapterOptions` branch for `custom`; lint rule bans every §3.4 v0 anti-pattern repo-wide and has at least one failing-fixture test.
7. Aggregation over ≥3 sources is deterministic (merge order stable across runs), tags `sourceId`, dedupes, reports partial failures without throwing.
8. Every network failure mode in §5 maps to a typed `DeepWorkError` subclass; no raw `fetch` errors escape the package boundary.
9. Package builds ESM + `.d.ts`, imports cleanly from `apps/web` and from a bare Node script (no React/Next dependency in core).
10. Fleet source smoke test (recorded fixtures): non-owner 404 → `GatedEndpointError`; PAT + `X-Auth-Scheme: langsmith-api-key` headers present on data-plane calls.

## 8. Task breakdown

| # | Task | Depends on | Definition of done |
|---|---|---|---|
| 1 | Package scaffold: ESM build, exports map, vitest, CI wiring per [05](../05-oss-setup.md) | — | Builds + tests run in CI from clean clone |
| 2 | Error taxonomy (`DeepWorkError` + subclasses, scrubbing) | 1 | §4 classes exported; scrub test passes (AC 8) |
| 3 | Normalization module + fixture corpus (py/js HITL, 3× FileData, snake→camel) | 1 | AC 4 green; accessors `getActionName`/`getArgsSchema` exported |
| 4 | `AgentSource` types, capability matrix defaults, registry with env-seed merge + persistence | 1 | AC 1 green; §5 merge/tombstone cases tested |
| 5 | Plane router + auth-header injection (proxy vs direct), `apps/server` passthrough contract stub | 2, 4 | §3.2 auth matrix asserted; `TenantScopeError` pre-flight (AC 5) |
| 6 | Control-plane client: deployments, `/v1/deepagents/*`, Context Hub, sandboxes | 3, 5 | AC 5 endpoint coverage; typed responses normalized |
| 7 | Per-source data-plane client: crons (`POST /runs/crons`, `/search`), `threads.search` wrapper | 5 | Recorded-request tests against `langgraph dev` |
| 8 | `buildStreamOptions` factories + reconnection presets + v0-anti-pattern lint rule | 4 | AC 6 green; presets documented |
| 9 | `DataProvider` interface + `FixturesProvider` over P-004 fixtures | 3, 4 | AC 2 (fixtures half); fixtures are canonical-shaped |
| 10 | `LiveProvider` composing registry + clients + stream factories | 6, 7, 8, 9 | AC 2 (live half) against `langgraph dev` |
| 11 | `searchThreadsAcrossSources` aggregation primitive | 7, 10 | AC 7 green; interrupt counts hydrated |
| 12 | Spike-3 golden-transcript contract suite wired as CI gate for this package | 3, 8, [./02-m0-spikes.md](./02-m0-spikes.md) | AC 3 green; renovate bumps run the suite |

## 9. Open questions

1. **WebSocket tier matrix** — is the WS upgrade on `/threads/{id}/stream/events` enabled on hosted Agent Server tiers (and `langgraph dev`) during the MDA beta? SSE is confirmed; WS is documented but untested per tier ([research 21](../../research/21-gapfill-ui-contract.md)). Until answered, `webSocket: 'unverified'` everywhere.
2. **`multitask_strategy` server-side honouring** — SDK types accept all four strategies but only `rollback` (plus client-side enqueue) is honoured client-side today ([research 21](../../research/21-gapfill-ui-contract.md)). Determines whether `doubleTexting` can ever be `true` in the matrix.
3. **Fleet/`langgraph dev` cron + webhook mutations** — are `POST /runs/crons` and run-create `webhook` accepted on Fleet agent servers with a PAT (owner-gated writes?) and on the in-mem dev server? No source verifies either.
4. **MDA invoke gating breadth** — thread/run invocation is design-partner-gated during beta ([research 20](../../research/20-gapfill-mda-api.md)); what does a non-partner org receive (404? 403?), so `GatedEndpointError` detection can key on it? Resolves with [./02-m0-spikes.md](./02-m0-spikes.md) Spike 2.
5. **Control-plane CORS** — agent-inbox proves data-plane browser calls work with `x-api-key`; whether `api.smith.langchain.com` control-plane endpoints allow browser origins is unverified. If not, *all* control-plane traffic routes via `apps/server` regardless of secrecy (P-005 already makes this the default; this question only affects local mode).
6. **Registry cross-device sync** — v1 is client-side per device; should post-v1 ride Context Hub (file-based, org-visible) or stay local? Interacts with the no-database rule ([02 §1](../02-architecture.md)).
7. **FileData convergence** — exact deepagents-JS version where V2 (`mimeType`) replaced V1 (lines), and whether Python converges on it ([research 21](../../research/21-gapfill-ui-contract.md)); affects how long the three-way normalization stays load-bearing.
8. **`managed_deep_agent` marker shape** on `POST /v2/deployments` (flag vs `deployment_type` enum, [research 20](../../research/20-gapfill-mda-api.md)) — needed before task 6 can create MDA deployments rather than only listing them.

## 10. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Weekly `@langchain/react`/`langgraph-sdk` 1.x churn breaks assembly or option types | High freq / low-med sev | Pins + renovate grouping ([05](../05-oss-setup.md)); Spike-3 contract suite as the tripwire; all upstream contact confined to this package ([04 risk register](../04-roadmap.md)) |
| Upstream fixes the `reviewConfigs` dual-casing gap and starts aliasing | Silent double-normalization | Accessors are the only read path; contract test asserts current upstream behavior and fails loudly on change |
| MDA invoke gating persists past beta | v1 primary tier degraded | Capability flag + link-out degradation already designed; `deployment` + `local` are fully public equivalents ([02 §12](../02-architecture.md)) |
| Capability matrix rots as the beta evolves (0.4.0-dev channel) | Wrong affordances shown | Probe-on-connect + user overrides; canary deployment in CI tracks the dev channel ([04](../04-roadmap.md)) |
| Fixtures drift from live shapes | "Works in demo, breaks live" | Fixtures typed against canonical types; AC 2's dual-provider rendering test in CI |
| Aggregation cost grows with source count (N searches per page) | Slow inbox | Primitive keeps per-source cursors + partial results; UX budget owned by [./08-task-inbox.md](./08-task-inbox.md) |
| Error taxonomy over-fits today's status codes (e.g. Fleet 404-as-gate) | Misclassified errors | Detection isolated in one mapping module with recorded fixtures per class; unknowns wrap as generic `DeepWorkError`, never guess |

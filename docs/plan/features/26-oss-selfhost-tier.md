# F26 · Pure-OSS self-host tier

*Deep Work feature spec · 2026-07-22 · Status: draft · Horizon: post-v1 · Depth: design-complete*

Sources: [02 · Architecture §2/§4/§7/§12](../02-architecture.md) · [01 · Vision (personas, cut line)](../01-vision.md) · [04 · Roadmap (post-v1 backlog)](../04-roadmap.md) · [05 · OSS setup (licensing)](../05-oss-setup.md) · [research 23 (runtime tiers & licensing)](../../research/23-gapfill-runtime-tiers.md) · [research 06 (execution backends)](../../research/06-execution-sandboxes.md) · [F04 · SDK & agent sources](./04-sdk-and-agent-sources.md) · [decisions](../decisions.md)

## 1. Scope

**Why this tier exists.** There is no free self-host path for Agent Server: `langgraph-api` is Elastic-2.0, standalone deployment requires `LANGSMITH_API_KEY` for dev and an Enterprise `LANGGRAPH_CLOUD_LICENSE_KEY` for production, and the historical free tiers (Self-Hosted Lite / Developer node quotas) have vanished from docs and pricing ([research 23](../../research/23-gapfill-runtime-tiers.md) facts 1–4; [02 §12](../02-architecture.md)). The **self-hoster persona** ([01](../01-vision.md)) — no LangSmith account, own infra — gets a **reduced-but-honest** tier: the full task loop against an MIT-stack backend, with every missing capability visibly disabled rather than silently broken. The licensing boundary is restated as a hard rule: Deep Work links only MIT packages and **never vendors or redistributes Elastic-2.0 code** — clients talk to Agent Server over HTTP where the user runs it; this tier exists precisely so that self-hosters never have to ([02 §2](../02-architecture.md); [05](../05-oss-setup.md); D-002, D-005).

**In scope:** backend-path selection (custom protocol server vs Aegra) with evaluation criteria and a provisional recommendation; the `custom` AgentSource type reserved in [F04 §3.1](./04-sdk-and-agent-sources.md); the concrete per-surface feature-loss matrix and its UI degradations; the execution story without LangSmith Sandboxes; the trace story without LangSmith; a docker-compose reference deployment; the optional "hybrid" configuration (pure-OSS backend + free-plan LangSmith extras layered back).

**Out of scope:** the v1 tiers (MDA/deployment/fleet/local — [F04](./04-sdk-and-agent-sources.md)); multi-user identity on the OSS backend (single-operator assumption, §9-Q7); GitLab (D-007 unchanged); re-implementing Agent Server features (crons, webhooks, double-texting) server-side beyond what the chosen path provides; any Deep Work-owned database beyond the tier's Postgres checkpointer (D-003 spirit: state lives in the checkpointer, not in a new app schema).

## 2. Dependencies & seams

| Dependency | Direction | Contract |
|---|---|---|
| [F04](./04-sdk-and-agent-sources.md) `custom` source type + capability flags | extends | `CustomAdapterOptions`/`AgentServerAdapter` branch reserved there; this spec fills in defaults (§4) and refines "custom" from one monolithic row to per-backend probe results |
| `@langchain/langgraph-sdk` `HttpAgentServerAdapter({apiUrl, paths?, defaultHeaders?, onRequest?, fetch?, webSocketFactory?})` + `ProtocolSseTransportAdapter` | consumes | MIT, speaks the CDDL-specified Agent Streaming Protocol ([research 23](../../research/23-gapfill-runtime-tiers.md) facts 6–7) |
| deployment-cookbook (MIT, LangChain-official) | pattern source | Documented minimum: `POST /threads/:id/commands`, `POST /threads/:id/stream` (SSE), `GET\|POST /threads/:id/state`, plus threads list/delete/history ([research 23](../../research/23-gapfill-runtime-tiers.md) fact 8). **Never invent routes beyond these** — gaps go to §9 |
| `langgraph` (MIT) + `langgraph-checkpoint-postgres` (MIT, py 3.1.0 / js 1.0.4) | consumes | Graph execution + durable state for the protocol server |
| Aegra (Apache-2.0, `aegra-api` 0.9.24) | candidate | FastAPI+Postgres reimplementation of the LangGraph Platform API ([research 23](../../research/23-gapfill-runtime-tiers.md) fact 15) |
| `packages/agent` (D-008, runtime-agnostic per D-004) | hosts | No backend/store/checkpointer in agent code is what lets this tier provision its own — the same rule that enables MDA ([02 §2](../02-architecture.md)) |
| `apps/server` ([F28](./28-backend-glue-service.md), P-005) | optional | GitHub App token minting (F12) still applies; OAuth/key-proxy/push routes are LangSmith-specific and idle on this tier |
| [F02](./02-m0-spikes.md) Spike-3 golden transcripts | reuses | The protocol contract suite doubles as this tier's conformance test |
| Feature-loss consumers: [F08](./08-task-inbox.md) · [F09](./09-task-detail-and-streaming.md) · [F10](./10-approvals-inbox.md) · [F17](./17-fleet-manager.md) · [F18](./18-schedules-and-activity.md) · [F19](./19-notifications-and-push.md) · [F20](./20-pwa-and-mobile.md) · [F27](./27-interop-acp-a2a.md) | degrades | Per-capability behavior in §3.4; all gating flows through `source.capabilities`, never `source.type` ([F04 §3.1](./04-sdk-and-agent-sources.md)) |

## 3. Design

### 3.1 Two candidate paths, compared

| Criterion | (a) Custom protocol server (cookbook pattern) | (b) Aegra |
|---|---|---|
| What it is | We implement the documented minimum routes + MIT Postgres checkpointer, hosting `packages/agent` in-process | Apache-2.0 drop-in reimplementation of the LangGraph Platform API (FastAPI + Postgres) |
| Protocol fit | Native Agent Streaming Protocol v2 → same `useStream` + Spike-3 transcripts, via `HttpAgentServerAdapter` (`paths` absorbs route naming) | Verified as "legacy langgraph-sdk Client compatibility" ([research 23](../../research/23-gapfill-runtime-tiers.md) fact 15); protocol-v2 support **unverified** (§9-Q3) — may need a bespoke adapter |
| Language fit | Python (FastAPI, same uv workspace as `packages/agent`/`apps/server`, P-005) — but cookbook examples are JS-first (Next.js/SvelteKit/Nuxt/Hono) and no MIT Python protocol-v2 emitter is verified (§9-Q1) | Python FastAPI — hosts the Python agent naturally |
| Surface owned | Minimal (~6 routes), ours forever | Large surface, third-party maintenance (single-maintainer risk; released 2026-07-05, active) |
| Feature recovery | Only what we build (background execution, maybe replay — §3.5, §9-Q6) | Potentially restores assistants CRUD and more, **unverified** (§9-Q3) |
| Policy fit (D-005, [02 §8](../02-architecture.md)) | "Build only where nothing upstream exists" — the cookbook is LangChain's official DIY pattern, so building here is sanctioned | "Consume, don't build" favors it — but it's community, not LangChain upstream, and pin-and-renovate discipline applies |

**Provisional recommendation: path (a)**, as a small FastAPI app in the existing uv workspace (own compose service, not merged into `apps/server` — run execution is a long-lived workload, glue is not). Rationale: protocol-v2 nativity keeps one stream contract for all tiers (the entire premise of [02 §2](../02-architecture.md)); the agent is hosted unchanged; the owned surface is minimal and conformance-tested by transcripts we already record. **Gate:** the §8 spike must first prove protocol-v2 framing is tractable from Python without `langgraph-api` (§9-Q1); if it is not, fall back to (b) behind a bespoke adapter, or a thin JS protocol shim in front of the Python graph — decided at spike exit, not now. Aegra is re-evaluated at the adoption trigger regardless: if it has gained protocol-v2 by then, its larger restored surface may win.

### 3.2 Client seam

Exactly the seam [F04](./04-sdk-and-agent-sources.md) reserves: `buildStreamOptions(source)` returns the `CustomAdapterOptions` branch for `type: 'custom'`, constructing `HttpAgentServerAdapter` from the source's adapter config (§4). What differs from the v1 tiers is **only transport config**: `apiUrl` = the protocol server, `paths` remaps route names (cookbook examples mount under `/api/threads/...`; [02 §7](../02-architecture.md) names `/threads/{id}/commands` + `/stream/events` — the `paths` option absorbs this discrepancy, pinned in the spike), `defaultHeaders` carries only **non-secret** reverse-proxy values (routing/tenant tags — never credentials: the registry seed is `NEXT_PUBLIC_AGENT_SOURCES`, baked into the browser bundle and readable by anyone who loads the page; authenticated exposure uses a session-bound mechanism or server-side proxy, §6), auth mode is `none` (§6). Registration: the same registry as every tier — env seed via `NEXT_PUBLIC_AGENT_SOURCES` or Settings UI, with `type: 'custom'`; the probe step hits the server's threads-list route as the health check and stamps capability results, so components downstream see flags, never tier names.

### 3.3 What is lost (server side)

Verbatim from [research 23](../../research/23-gapfill-runtime-tiers.md) fact 9 — a pure-OSS server loses: double-texting strategies, resumable `joinStream`/`Last-Event-ID` replay (unless the adapter replay contract is reimplemented), crons, run webhooks, assistants CRUD+versioning, the `/mcp` and `/a2a` endpoints, Studio integration, and the durable background-run task queue. Plus, because this persona has no LangSmith account: no control plane at all — no Context Hub, no `/v2/deployments`, no `/v2/sandboxes`, no tracing, no Insights.

### 3.4 Feature-loss matrix, per surface (all gated by `source.capabilities`, [F04 §3.1](./04-sdk-and-agent-sources.md))

| Capability off | Surface impact — spelled out |
|---|---|
| `doubleTexting` | [F09](./09-task-detail-and-streaming.md) steering composer drops the "queue vs interrupt" choice ([03 §3.3](../03-ui-spec.md)): messages **client-side enqueue** (the [F04 §5](./04-sdk-and-agent-sources.md) downgrade row) and deliver as the next turn after the run completes, labeled "delivers after this run". Mid-run injection via the steering middleware queue is unverified on this tier (§9-Q6); until proven, the UI must not promise it. Run cancel availability is also unverified (§9-Q2) — the Stop button renders only if the probe confirms it |
| `crons` | [F18](./18-schedules-and-activity.md) already specifies the behavior: capability probe returns `crons:false` → Schedules tab shows the "unsupported on this backend" row, no phantom empty state, CRUD hidden. F26 adds a **docs recipe, not a UI feature**: a host-level scheduler (e.g. system cron) invoking the same run-creation entrypoint the composer uses (exact thread-creation route: §9-Q2). F18's export-as-JSON eases migration off a hosted tier |
| `webhooks` | [F19](./19-notifications-and-push.md)'s run-completion pipeline keys on the run-create `webhook` param ([02 §7](../02-architecture.md)) → **no Web Push, no one-tap approve from a notification**. Degradation: in-app polling only (inbox refresh cadence owned by [F08](./08-task-inbox.md)); desktop ([F21](./21-desktop-tauri.md)) may optionally poll locally and raise native notifications while the app runs — an app-side loop, no server change |
| `assistantsCrud` / versioning | [F17](./17-fleet-manager.md): no assistants API and no Context Hub → the file-first editor, version history, and Auto/Ask matrix-to-assistant-version save path are all unavailable. The custom source renders as a reduced agent card (name, health, thread count) with F17's honest-degradation pattern pointed at docs instead of smith.langchain.com: "config lives in your deployment — edit `packages/agent` and restart". `interrupt_on`/templates are baked into the deployed agent; whether task-type templates ([F15](./15-task-templates.md)) survive as config passthrough or need per-template graphs is §9-Q5 |
| `streamResumable` | [F20](./20-pwa-and-mobile.md): backgrounding a PWA loses the live stream and there is **no `Last-Event-ID` replay**; on return the client re-hydrates from the state/history routes ([F04 §5](./04-sdk-and-agent-sources.md) rejoin row) — final state correct, missed narration not replayed, shown as a "stream gap" divider. Cross-device handoff mid-run degrades the same way. Recoverable if path (a) implements the adapter replay-buffer contract (§9-Q6) |
| `/mcp`, `/a2a` endpoints | [F27](./27-interop-acp-a2a.md) exposure paths simply absent on this tier; F27 documents the constraint |
| Studio | Not consumed by Deep Work surfaces; no UI impact ([02 §10](../02-architecture.md) deep-links LangSmith, not Studio) |
| Background-run task queue | Cookbook minimum executes runs within the streaming request's lifetime — "dispatch and walk away" needs the protocol server to decouple execution from the connection (background task + Postgres checkpoints). Path (a) treats this as **required**, not optional: a run must survive client disconnect. Verified at spike (§9-Q2/Q6) |

### 3.5 What still works fully

- **The task loop**: compose → dispatch → stream narration/tool cards/todos → HITL approve/edit/reject → done. Interrupts and checkpoint branching are core MIT `langgraph`; the v1 HITL contract (D-010) rides the commands/state routes — resume-command handling on the cookbook pattern verified at spike (§9-Q2). Inbox lists threads from the threads-list route; cross-source metadata filtering depends on that route's query support (§9-Q4, degrade to client-side filtering).
- **Execution without LangSmith Sandboxes** ([research 06](../../research/06-execution-sandboxes.md) facts 1, 6–7): (1) **StateBackend** (default) — thread-scoped virtual FS, no `execute`; research/writing templates fully work, files render via `values.files` ([F13](./13-files-diff-and-review.md), [02 §4](../02-architecture.md)). (2) **BYO provider sandboxes** — MIT packages `langchain-daytona`/`langchain-e2b`/`langchain-modal`/`langchain-runloop`/`langchain-vercel-sandbox` (+ AgentCore), sandbox-as-tool, user's own provider account. (3) **LocalShellBackend / FilesystemBackend(virtual_mode=True)** on the protocol-server host — no isolation; docs-gated to single-user machines (dcode-style local fallback, research 06 recommendation). [F11](./11-execution-and-environments.md)'s environment-snapshot UX (LangSmith `/v2/sandboxes`) does not apply; environments on this tier are the compose image + BYO provider config.
- **Traces**: no LangSmith → `TracePill` ([03 components](../03-ui-spec.md)) is capability-gated off (`traceLinks:false`, a flag this spec adds to F04's matrix). The run panel keeps **local provenance** from the state/history routes (checkpoints, run timeline). An optional per-source `traceUrlTemplate` re-enables the pill for users who wire their own tracing backend (§4).
- **Hybrid configurations, honestly labeled**: the tier boundary is the *backend*, not an all-or-nothing account wall. A self-hoster with a free Developer-plan account can layer back LangSmith tracing (5k traces/mo) and LangSmith Sandboxes (5 LCU + 1 LSU free, 10-box cap) — the `langsmith` SDK is MIT ([research 23](../../research/23-gapfill-runtime-tiers.md) fact 16). The docs present this as an opt-in upgrade, never a requirement.

### 3.6 Deployment shape

One `docker-compose.yml` at repo root (`deploy/selfhost/`), four services, reference config in §4: **postgres** (≥14, volume-backed), **protocol-server** (uv-workspace image: FastAPI routes + `packages/agent` + `langgraph-checkpoint-postgres`; model API keys in its env only), **server** (`apps/server`, optional profile — needed for the GitHub App flow of [F12](./12-github-and-git-flow.md), idle otherwise), **web** (`apps/web`, D-022, seeded with the custom source). No Elastic-2.0 image anywhere in the stack; no license-key egress (`beacon.langchain.com` is an Agent Server concern the stack never has — [research 23](../../research/23-gapfill-runtime-tiers.md) facts 1, 8).

## 4. Contracts

```ts
// F04 AgentSource, custom branch — concretized (extends F04 §4; additive only)
interface CustomAdapterConfig {
  kind: 'http-protocol'                       // path (a); 'aegra' added only if path (b) is chosen
  paths?: Partial<Record<'commands' | 'stream' | 'state' | 'threads' | 'history', string>>;
  defaultHeaders?: Record<string, string>;    // non-secret values only (routing/tenant tags) — never credentials/key material (F04 §6 rule; NEXT_PUBLIC_* is browser-visible, §6)
  traceUrlTemplate?: string;                  // e.g. "https://my-otel.example/trace/{runId}"; absent ⇒ TracePill hidden
}
// AgentSource gains: adapterConfig?: CustomAdapterConfig   (present iff type === 'custom')

// Capability defaults for type 'custom', path (a) — resolves F04 §3.1's ❓ row for this tier
const CUSTOM_DEFAULTS: SourceCapabilities = {
  invoke: true,                 // via HttpAgentServerAdapter
  streamResumable: false,       // true only if the replay-buffer contract is implemented (§9-Q6)
  webSocket: false,             // cookbook stream route is SSE; webSocketFactory exists if a server adds WS
  doubleTexting: false, crons: false, webhooks: false,
  assistantsCrud: false, deployMgmt: false, deepagentsApi: false, mdaIdentity: false,
  traceLinks: false,            // NEW flag (added to F04's SourceCapabilities post-v1); true iff traceUrlTemplate set
};
```

```yaml
# deploy/selfhost/docker-compose.yml — reference shape (illustrative)
services:
  postgres:        { image: "postgres:16", volumes: ["pgdata:/var/lib/postgresql/data"] }
  protocol-server: # uv workspace image; MIT deps only (langgraph, langgraph-checkpoint-postgres, deepagents)
    environment: [DATABASE_URL, ANTHROPIC_API_KEY]     # model keys server-side only
    ports: ["127.0.0.1:8123:8123"]                     # localhost-bound by default (§6)
  server:          { profiles: ["github"] }            # apps/server (F28) — optional GitHub App glue
  web:
    environment:
      # NEXT_PUBLIC_* is compiled into the browser bundle — public by definition; no credentials, no secret defaultHeaders (§6)
      NEXT_PUBLIC_AGENT_SOURCES: '[{"id":"selfhost","type":"custom","name":"Self-hosted",
        "deploymentUrl":"http://localhost:8123","auth":{"mode":"none"},
        "adapterConfig":{"kind":"http-protocol"}}]'
```

Protocol routes are **exactly** the documented cookbook set (§2); anything further the spike wants (thread create, cancel, resume specifics) is recorded in §9 first and added to this section only once verified.

## 5. Edge cases & failure modes

| Case | Behavior |
|---|---|
| Client disconnect mid-run | Run continues server-side (path-(a) background-execution requirement, §3.4); rejoin re-hydrates from state; no replay of missed tokens unless §9-Q6 lands |
| Protocol server restarted mid-run | Postgres checkpoints preserve the last durable state; UI shows the run as interrupted-by-restart with a resume-from-checkpoint affordance (mechanism per spike, §9-Q2) — never a silent hang |
| Probe cannot reach the server | Source marked unreachable in the registry; inbox partial-failure semantics per [F04 §3.6](./04-sdk-and-agent-sources.md) — one dead source never blanks the inbox |
| User registers an Agent Server URL as `type: 'custom'` | Works (protocol superset) but with pessimistic flags; registry warns and suggests `deployment` type instead |
| Aegra-style backend registered under `kind: 'http-protocol'` | Probe fails on protocol-v2 framing → source unhealthy with an explicit "backend does not speak protocol v2" error, not a generic timeout |
| Postgres down, server up | Commands fail server-side; SDK surfaces a typed retryable error ([F04 §3.7](./04-sdk-and-agent-sources.md) taxonomy); composer disables with an honest banner |
| Hosted-tier features attempted via deep link (old bookmarks, e.g. `/schedules`) | Screens render their capability-off states (F18's "unsupported on this backend" row is the pattern); no 404s |
| Hybrid: LangSmith key added later | Re-probe flips `traceLinks`/sandbox availability; no restart of the compose stack required for client-side flags |
| Templates picker on custom source | Renders only what the deployment exposes; until §9-Q5 resolves, a single default template is the honest floor |

## 6. Security & privacy

- **Authn is the deployer's**: the cookbook minimum ships no identity layer and MDA identity presets don't apply ([02 §5](../02-architecture.md) planes 2–3 are LangSmith machinery). Default posture: compose binds the protocol server to localhost; exposure beyond that goes behind the deployer's reverse proxy, carried via `adapterConfig.defaultHeaders`. Single-operator assumption documented; multi-user is out of scope (§9-Q7).
- **Secrets**: model API keys live in the protocol-server env, never in the browser or registry ([F04 §6](./04-sdk-and-agent-sources.md) no-secrets rule unchanged). GitHub: `apps/server` can still mint short-lived installation tokens ([F12](./12-github-and-git-flow.md)), but the LangSmith sandbox auth-proxy callback (D-015's zero-token mechanism) does not exist on BYO/local backends — tokens enter the execution environment. This is an **honest, documented deviation from D-015**, mitigated by short TTL and per-repo down-scoping; LocalShellBackend additionally means execution shares the server host (docs-gated, §3.5).
- **No phone-home**: the stack contains no Elastic-2.0 component, hence no license-key validation egress; data (threads, checkpoints, files) lives entirely in the user's Postgres — the strongest form of the D-003 trust story.
- **Untrusted-content boundaries unchanged** ([02 §10](../02-architecture.md)): external payload rendering rules from [F18](./18-schedules-and-activity.md)/[F09](./09-task-detail-and-streaming.md) apply identically; normalization stays structural ([F04 §6](./04-sdk-and-agent-sources.md)).
- **Licensing hygiene**: CI license-scan on the compose images asserts MIT/Apache-only linkage; README licensing section states the boundary plainly ([05](../05-oss-setup.md); [02 §12](../02-architecture.md)).

## 7. Acceptance criteria

1. Full task loop — dispatch → stream → steer (client-enqueued) → HITL approve → done — completes against the compose stack with **zero LangSmith credentials**, from a clean `docker compose up`.
2. Spike-3 golden transcripts (the subset covering commands, content blocks, tools channel, HITL respond) replay green against the protocol server; deviations are documented per-transcript, never silently skipped.
3. Every §3.4 matrix row renders its specified degraded state (disabled affordance + honest label), driven by capability flags — a grep for `source.type === 'custom'` in `apps/web` finds nothing.
4. A run survives client disconnect and server-observed browser refresh; state re-hydrates on rejoin.
5. Research and writing templates work on StateBackend; a BYO-provider sandbox (at least one of e2b/daytona/modal) executes `execute`-tool calls end-to-end.
6. `TracePill` absent by default; present and correctly templated when `traceUrlTemplate` is set; hybrid LangSmith tracing re-enables the standard pill.
7. License scan proves no Elastic-2.0 package in any shipped image; the self-host guide's feature-loss table is generated from (or asserted against) the same capability defaults the SDK ships.
8. Compose defaults are localhost-bound; the reverse-proxy recipe is documented and tested with header-based auth passthrough.

## 8. Adoption triggers & sequencing

**Demand signals that start this work** (checked at each post-v1 planning pass): sustained votes on the "self-host without LangSmith" tracking issue (the README's honest-tier note, [02 §12](../02-architecture.md), links to it); recurring self-hoster questions in issues/discussions; Aegra maturity signals (release cadence, protocol-v2 adoption — §9-Q3); and one **external negative trigger** — if LangChain restores a free standalone Agent Server tier ([research 23](../../research/23-gapfill-runtime-tiers.md) open question), this feature shrinks to a docs page and the trigger re-evaluates from scratch.

**High-level order** (not a task breakdown): **(1) Adapter-seam validation** — exercise F04's `CustomAdapterOptions` branch against recorded fixtures; confirms the client seam with zero server work. **(2) Cookbook spike** — minimal Python protocol server hosting `packages/agent` + Postgres checkpointer; resolves §9-Q1/Q2/Q6 and replays the transcript subset; Aegra evaluated side-by-side against §3.1 criteria; path decision recorded in [decisions.md](../decisions.md). **(3) Matrix implementation** — capability defaults into the SDK, degraded states across F08/F09/F10/F17/F18/F19/F20 surfaces, compose reference + self-host guide. **(4) Recovery items** — replay buffer (`streamResumable`), hybrid extras documentation — only after the base tier ships.

## 9. Open questions

1. **Q1 · Python protocol-v2 emission**: is there (or will there be) an MIT server-side library for Agent Streaming Protocol framing, or do we hand-implement the CDDL spec from `langchain-ai/agent-protocol`? Cookbook examples are JS-first ([research 23](../../research/23-gapfill-runtime-tiers.md) fact 8). Gates the path-(a) recommendation.
2. **Q2 · Cookbook route coverage beyond the documented minimum**: thread creation, run cancel, resume-`decisions` command handling, restart-recovery semantics — none verified; spike resolves from the cookbook reference implementations, never invented here.
3. **Q3 · Aegra capabilities**: does it speak protocol v2 or only the legacy platform API, and which Agent Server features does it actually restore (assistants CRUD? crons?)? Determines whether F04's monolithic `custom` ❌ column needs per-backend splitting.
4. **Q4 · Threads-list query power**: does the cookbook threads route support metadata/status filtering + sort for [F08](./08-task-inbox.md) aggregation, or is client-side filtering the ceiling?
5. **Q5 · Templates without assistants**: do task-type templates ([F15](./15-task-templates.md), D-014) pass as per-command config, or does this tier need per-template graph registration?
6. **Q6 · Replay-buffer contract**: is the `AgentServerAdapter` resumability contract documented enough to reimplement `Last-Event-ID` replay server-side ([research 23](../../research/23-gapfill-runtime-tiers.md) fact 9), restoring `streamResumable` and improving §3.4's mobile story? Related: can any command reach a run mid-flight (steering ceiling)?
7. **Q7 · Multi-user posture**: is single-operator acceptable for this persona long-term, or does the tier eventually need a pluggable identity hook (the cookbook "your own auth" stance)?
8. **Q8 · Elastic-2.0 hosted-service clause** (inherited legal question, [research 23](../../research/23-gapfill-runtime-tiers.md)): where the "hosted or managed service" line falls for users running Deep Work over Agent Server — needs LangChain confirmation; affects docs guidance, not this tier's architecture.

## 10. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Python protocol implementation heavier than expected (Q1) | Path (a) stalls | Spike gates the decision; fallbacks pre-named (§3.1): Aegra adapter or thin JS protocol shim |
| We own a mini-server forever | Maintenance drag on a small team | Owned surface capped at the documented route set; conformance = existing transcript suite; feature recovery deliberately deferred (§8 step 4) |
| Aegra abandonment or API drift (if path (b)) | Backend rots | Pin + renovate like any dep ([02 §8](../02-architecture.md)); path (a) remains the escape hatch since the client seam is identical |
| Feature-loss disappointment ("worse than the demo") | Reputation | "Reduced-but-honest" is the design center: capability-gated UI, generated loss table in docs (AC-7), no phantom affordances |
| Capability matrix drifts from server reality | Wrong affordances | Probe-on-connect + AC-7 doc/code single-sourcing; F04's override mechanism for corrections |
| Protocol churn despite CDDL stability claim | Transcript suite breaks | Same tripwire as v1: pinned clients, Spike-3 suite fails first ([F04 §10](./04-sdk-and-agent-sources.md)) |
| Zero-secrets deviation (D-015) misread as the norm | Security posture confusion | §6 documents it as tier-specific; hosted tiers unchanged; self-host guide leads with the trade-off |

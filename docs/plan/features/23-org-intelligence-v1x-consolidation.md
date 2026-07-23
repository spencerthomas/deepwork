# F23 · Org intelligence v1.x — memory consolidation & review loop

*Deep Work feature spec · 2026-07-22 · Status: draft · Horizon: v1.x · Depth: design-complete*

Sources: [07 · Org intelligence §1–2, Layer 2, §5–6](../07-org-intelligence.md) · [research 15 · org intelligence](../../research/15-org-intelligence.md) · [02 · Architecture §1/§7/§10](../02-architecture.md) · [03 · UI spec §3.3/§4](../03-ui-spec.md) · [04 · Roadmap (post-v1 backlog)](../04-roadmap.md) · [08 · deepagents feature map (Memory)](../08-deepagents-feature-map.md) · [research 20 · MDA API](../../research/20-gapfill-mda-api.md) · [research 13 · agent-inbox](../../research/13-agent-inbox.md) · [research 12 · lifecycle/auth](../../research/12-lifecycle-auth-followup.md) · [decisions](../decisions.md)

Stack facts: the webhook consumer is a route set in the Python FastAPI glue service `apps/server` (P-005, provisional; skeleton from [F01](./01-monorepo-and-oss-infra.md), service spec [F28](./28-backend-glue-service.md)). Deep Work keeps **no database of its own in v1** (D-003; [02 §1](../02-architecture.md)) — §3.3 designs around that deliberately.

## 1. Scope

In scope — [07 §Layer 2](../07-org-intelligence.md) productized, v1.x:

- **`consolidation_agent`**: a second graph in `packages/agent` implementing the documented deepagents background-consolidation ("sleep time compute") recipe — second deep agent + cron with **lookback == interval** ([research 15](../../research/15-org-intelligence.md), CONFIRMED). Equipped with an **episodic-memory tool** (`threads.search` + thread history over the org's Deep Work threads). It consolidates *conventions, recurring failures, environment quirks* into **proposed** `org-memory/` commits — never direct writes (writes-are-proposals, [07 §1.3](../07-org-intelligence.md); org memory is runtime-denied to agents anyway, [research 15](../../research/15-org-intelligence.md)).
- **The review loop end-to-end**: proposal commit → Context Hub commit webhook (`context_hub.commit.created.v1`, HMAC-signed — the only event name our research confirms) → `apps/server` webhook consumer → approvals inbox renders the diff as a new payload type → approve = merge into `org-memory/**`, reject = feedback routed back to the consolidation agent.
- **The webhook consumer** — Deep Work's first real inbound-service surface: HMAC verification, idempotency, retry posture, reconciliation sweep, and the D-003 state question.
- **Proposal quality controls**: dedupe, concurrent-human-edit conflicts, size/volume caps, rejection-feedback semantics.
- The **`memory_proposal` payload type** added to [F10](./10-approvals-inbox.md)'s contract surface (§4).

Out of scope: Layer 0/1 foundations — `org-memory/` template, tracing conventions, org-analyst digests, Insights provisioning ([F22](./22-org-intelligence-v1.md)); general approvals-inbox mechanics ([F10](./10-approvals-inbox.md)); the `apps/server` skeleton, hosting, and shared middleware ([F28](./28-backend-glue-service.md)); push fan-out delivery ([F19](./19-notifications-and-push.md)); Layers 3–5 (OKF/openwiki, data plane, Graphiti — v2/v3 per [07 §5](../07-org-intelligence.md)).

## 2. Dependencies & seams

| Direction | Spec | What crosses the seam |
|---|---|---|
| needs ← | [F22 · Org intelligence v1](./22-org-intelligence-v1.md) | The `org-memory/` starter-template tree (proposal targets), tracing-metadata conventions (`task_type`/`agent`/`actor`/`tenant`/`surface` — the episodic tool's filter vocabulary, [02 §10](../02-architecture.md)), org-analyst digests as secondary input |
| needs ← | [F10 · Approvals inbox](./10-approvals-inbox.md) | Inbox list/card framework, `DecisionForm`/`DiffViewer` components, schema-tolerant rendering; F23 adds one payload type + one non-interrupt item source (§4) |
| needs ← | [F28 · Backend glue service](./28-backend-glue-service.md) *(P-005)* | Deployed, publicly reachable FastAPI service (webhooks need a URL — [F01 §9-Q4](./01-monorepo-and-oss-infra.md) hosting must be resolved), secrets handling, route conventions |
| needs ← | [F05 · Auth & identity](./05-auth-and-identity.md) | Operator session for decision endpoints; Context Hub **write** scope under LangSmith OAuth is unresolved (O-001-adjacent; [07 §6-Q2](../07-org-intelligence.md)) — service-key fallback via `apps/server` |
| needs ← | agent-composition spec (see [catalog](./README.md)) | `packages/agent` project structure the second graph and its `define_schedule` cron live in ([02 §3](../02-architecture.md), [research 20](../../research/20-gapfill-mda-api.md)) |
| shares problem with | [F19 · Notifications & push](./19-notifications-and-push.md) | Both need durable server-side state under D-003; §3.3 resolves F23's copy by making the org's Context Hub the source of truth — align the answers |
| provides → | Layer 3 wiki review surface (v2, [07 §Layer 3](../07-org-intelligence.md)) | The diff-review payload type and the commit-webhook consumer generalize to openwiki/OKF page review |

## 3. Design

### 3.1 The consolidation agent

A second graph, `consolidation_agent`, in `packages/agent` — composition, not new machinery ([07 §Layer 2](../07-org-intelligence.md)): the deepagents recipe's second deep agent, deployed alongside the main graph (multi-graph `langgraph.json` is what `mda` generates, [research 20](../../research/20-gapfill-mda-api.md); single-project feasibility is §9-Q5). Cron via `schedules/` `define_schedule` (5-field cron + `prompt`, [research 20](../../research/20-gapfill-mda-api.md)); recipe default `0 */6 * * *`, **lookback window == cron interval** so consecutive runs tile the timeline without gaps or overlap ([research 15](../../research/15-org-intelligence.md)). Interval is admin-tunable through the F22/M3 schedules UI; the lookback derives from the *last successful run marker*, not the nominal interval, so a failed run widens the next window instead of dropping it (marker storage: §9-Q7).

**Episodic-memory tool**: `threads.search` (filtered on the Layer-1 metadata conventions + `updated_at` window) plus per-thread history fetch, over the org's Deep Work threads. Under MDA identity, thread/store access is scoped fail-closed to `metadata.owner` ([research 20](../../research/20-gapfill-mda-api.md)) — a schedule-fired agent cannot see other actors' threads through its own runtime identity. Design stance: the tool calls the deployment's threads API with a **workspace service key held in deployment secrets** (org tooling acting for the org, not a user); degraded path if that is rejected: consume the org-analyst digests + `langsmith-mcp-server` reads only ([07 §Layer 1](../07-org-intelligence.md)). §9-Q6. Keep windows ≤7 days to stay in the friendly `/runs/query` rate tier when LangSmith queries supplement thread reads (10/10s ≤7d, [research 15](../../research/15-org-intelligence.md)).

**What it consolidates → where**: conventions (recurring steering corrections), recurring failures (error patterns, HITL rejections — already collected into datasets by Layer-1 automation rules), environment quirks (setup/sandbox friction) — into the F22 starter-template sections of `org-memory/`. **Proposal mechanics**: the agent never touches `org-memory/**` (runtime-denied). A `propose_memory_update` tool commits, via the Hub API (`/v1/platform/hub/repos/`, [research 20](../../research/20-gapfill-mda-api.md)), into a dedicated **proposal area** (separate prefix or repo — Hub branching support unknown, §9-Q3; copy-commit into a proposal prefix is the degradable default). One commit per proposal: the target-file diff plus a manifest (rationale, evidence thread/trace links, lookback window, **base commit id** of `org-memory/` it was computed against). Evidence links are mandatory — "provenance everywhere" ([02 §10](../02-architecture.md)).

### 3.2 The review loop

```
consolidation run ──commit──▶ Hub proposal area ──context_hub.commit.created.v1──▶ apps/server
     ▲                                                                                │ verify HMAC · filter · notify
     │ reject feedback (next-run context)                                             ▼
     └───────────────── approvals inbox (F10) ◀── memory_proposal item ◀── clients fetch open proposals
                          approve = apps/server commits merge to org-memory/** · reject = feedback recorded
```

**Not an interrupt.** The consolidation run completes after committing proposals; the approval item is *webhook/state-born*, not `stream.interrupt`-born. Alternative considered and rejected — pausing the run via `interrupt_on` on the propose tool: cron-fired threads would sit interrupted for days, colliding with the lookback==interval tiling and piling up paused runs. Instead the payload **mirrors the v1 HITL shape** so F10 renders it with the same card machinery ([03 §3.3](../03-ui-spec.md)), but resolution routes to `apps/server`, not `stream.respond()` (§4).

**Decisions**: `approve` → `apps/server` applies the diff as a commit to `org-memory/**` via the Hub API (write credential: reviewer's OAuth token if Hub write scopes allow, else server-held service key — audit-trail difference tracked in §9-Q4) and closes the proposal (removes it from the proposal area in the same commit). `edit` → reviewer amends the diff, then approve-with-edits merges the amended content. `reject` (message optional but encouraged) → no memory change; the rejection + message are recorded in the proposal log (location unresolved — **blocked by §9-Q7**); the next consolidation run receives recent rejections in its prompt context so it stops re-proposing rejected content — the feedback loop of [07 §2](../07-org-intelligence.md), Q7-contingent. `respond` does not exist here (no live run to talk to).

**Human commits are not proposals**: the consumer filters — only commits in the proposal area authored by the consolidation identity become approval items; direct human edits to `org-memory/**` (the fleet manager already edits these files, [07 §Layer 0](../07-org-intelligence.md)) instead update the *base* against which open proposals are staleness-checked (§3.4).

### 3.3 The webhook consumer — first inbound-service surface

`POST /hooks/context-hub` on `apps/server` *(P-005)*. Verification first, always: constant-time HMAC check against the shared secret provisioned at webhook registration (registration API surface unprobed — §9-Q1); missing/invalid signature → 401, body never processed. Respond 2xx quickly; all processing is after-verification and cheap.

**D-003 resolution — the Hub is the database.** The consumer stores nothing durable. Open proposals are *fully derivable from Hub state*: proposal area contents = open items; absence = closed; `org-memory/` head = merge base. So the webhook is a **freshness signal only** — on receipt, `apps/server` invalidates/refetches and (later, via F19's fan-out) pushes a notification; clients list open proposals by reading the Hub through the existing proxy. Consequences: replayed or duplicated deliveries are naturally idempotent (state-derived, keyed by commit id); **lost deliveries cost freshness, never correctness** — a **reconciliation sweep** (poll the proposal area on inbox open + a coarse server-side interval) is the backstop. This is the same D-003 problem class as [F19](./19-notifications-and-push.md)'s push subscriptions; F19 needs genuinely non-derivable state and may land differently — keep the two answers explicitly reconciled. Residual server-side state here is config-class only: webhook secret + service key (deployment secrets, [F28](./28-backend-glue-service.md)), never a datastore.

Retry posture: Hub delivery/retry semantics are undocumented in our research (§9-Q2); assume at-least-once and design idempotent, which §3.3 already is.

### 3.4 Proposal quality controls

- **Dedupe**: before proposing, the agent greps existing `org-memory/` and the open proposal area (files it can read); dedupe against *recently rejected* content additionally requires the proposal log, whose location is unresolved — **blocked by §9-Q7**, contingent, not assumed. The manifest carries `relates_to`/`supersedes` references. Verbatim re-proposal of open content is a defect; of rejected content, once Q7 lands (AC-5).
- **Stale base / concurrent human edits**: approve-time guard in `apps/server` — if any touched file's head commit differs from the manifest's `base_commit`, the merge is **blocked as stale**; UI offers "request regeneration" (queues the fact into the next run's context) instead of a blind merge.
- **Size limits**: hard caps in the `propose_memory_update` tool (max proposals per run, max changed lines per proposal — defaults small, config-exposed); oversized proposals are split or dropped with a note in the run output.
- **Runaway volume**: circuit breaker — if open proposals exceed a threshold, the run records that fact and proposes nothing; the schedules UI shows the skip and turning the cron off is one click — the pause toggle where the backend's capability probe supports it, else [F18 §3.1](./18-schedules-and-activity.md)'s delete-with-export fallback ([03 §3.5](../03-ui-spec.md)).

### 3.5 UI surface

One new card in the approvals inbox ([F10](./10-approvals-inbox.md)): `DiffViewer` (already in the `packages/ui` inventory, [03 §4](../03-ui-spec.md)) inside the interrupt-card frame; capability chip "Memory proposal"; manifest rationale as the description; evidence rendered as thread/trace deep links; Approve / Edit / Reject controls via the existing `DecisionForm`. Mobile one-tap approve works unchanged — this is the flagship mobile flow ([03 §3.3](../03-ui-spec.md)). Diff content renders inside untrusted-content boundaries ([02 §10](../02-architecture.md)).

## 4. Contracts

**`memory_proposal` item** (extends F10's inbox item union; wire snake_case, SDK-normalized camelCase per [02 §7](../02-architecture.md)):

```
MemoryProposalItem {
  kind: "memory_proposal",            // vs "interrupt"
  id: string,                         // proposal commit id in the Hub
  repo: string, base_commit: string,
  files: [{ path, diff }],            // unified diff per touched org-memory file
  manifest: { rationale, evidence: [{thread_id, trace_url}], lookback: {from, to},
              agent: "consolidation_agent", relates_to?: string[] },
  allowed_decisions: ["approve", "edit", "reject"]   // no "respond": no live run
}
```

**Decision endpoint** (`apps/server`, operator session per [F05](./05-auth-and-identity.md)): `POST /approvals/memory-proposals/{id}/decision` with `{type: "approve"} | {type: "edit", edited_files: [{path, content}]} | {type: "reject", message?}`. Approve/edit returns the resulting `org-memory` commit id; stale base returns a typed `409 stale_base` with current head. Listing: `GET /approvals/memory-proposals` (server derives from Hub state, §3.3).

**Webhook**: `POST /hooks/context-hub`, event `context_hub.commit.created.v1`, HMAC-signed ([research 15](../../research/15-org-intelligence.md) — the only confirmed facts; header name, payload schema, registration API are §9-Q1). No other event names are assumed anywhere in this spec.

**Consolidation agent**: graph name `consolidation_agent`; `define_schedule` cron with lookback == interval invariant; `propose_memory_update(files, manifest)` is the only write-capable tool, and it can only write to the proposal area. Secrets: `CONTEXT_HUB_WEBHOOK_SECRET` + workspace service key, `apps/server`/deployment side only ([F01 §6](./01-monorepo-and-oss-infra.md)).

## 5. Edge cases & failure modes

- **Webhook delivery loss** → freshness-only design (§3.3); reconciliation sweep surfaces the proposal regardless; no correctness dependency on delivery.
- **Duplicate/replayed deliveries** → state-derived idempotency by commit id; replays of genuine old events are no-ops.
- **Consolidation hallucination** → the core reason every merge is human-gated (writes-are-proposals, [07 §1.3](../07-org-intelligence.md)): a hallucinated "convention", once merged, would steer *every future agent run*. Mandatory evidence links make review cheap; proposals whose evidence doesn't resolve are auto-flagged in the card.
- **Runaway proposal volume** → per-run caps + open-proposal circuit breaker + one-click cron disable (§3.4).
- **Stale base** → 409 at approve time, regenerate affordance; human edits always win races.
- **Rejected content re-proposed** → rejection feedback in next-run context (Q7-contingent, §3.4); verbatim recurrence is an AC-5 failure once the proposal log exists.
- **Hub write fails on approve** → decision is synchronous with the reviewer; typed error surfaces in the card, retry is safe only if Hub commits are idempotent-or-conflict (semantics unknown, §9-Q3) — until probed, retry re-reads head first.
- **Run overruns its interval** → `multitask_strategy` enqueue default ([research 20](../../research/20-gapfill-mda-api.md)); lookback-from-last-success (§3.1) absorbs the shifted schedule.
- **Cross-thread read denied** (MDA `metadata.owner` fail-closed) → service-key path §3.1; degrade to digest-driven proposals rather than silently proposing from an empty window.

## 6. Security & privacy

- **Inbound hardening**: HMAC verified constant-time before any parsing; fail closed 401; this route joins the small documented set of unauthenticated-ingress surfaces (MDA's own are listed in [research 20](../../research/20-gapfill-mda-api.md)) and gets the same review scrutiny in [F28](./28-backend-glue-service.md).
- **Prompt-injection laundering** is the headline threat: proposal text is agent-generated content that, once merged, becomes trusted context for all future runs. Defenses, layered: human approval gate (this spec), org memory mounted read-only at runtime ("prevents prompt injection via shared state", [research 15](../../research/15-org-intelligence.md)), untrusted-content rendering of diffs/manifests in the UI ([02 §10](../02-architecture.md); roadmap v1 criterion 5), provenance links so reviewers can check claims against traces.
- **Secrets**: webhook secret + service key live only in `apps/server`'s deploy target / deployment secrets ([F01 §6](./01-monorepo-and-oss-infra.md)); never in clients; the browser never performs Hub writes directly — decisions go through `apps/server` (P-005).
- **Privacy**: the episodic tool reads across actors' threads. Default posture: org-visible Deep Work threads only; per-user memory slices (`/memories/user/**`) and tenant-scoped end-user threads (multi-tenant identity preset) are **excluded from consolidation input by default** — org memory must not launder one user's private context into shared knowledge. Exact exclusion mechanics ride §9-Q6.
- **Least privilege**: workspace-scoped (not org-scoped) service key; Hub write access limited to the memory repo/prefix; approve-as-reviewer preferred over approve-as-service-key when scopes allow (§9-Q4) for a true audit trail.

## 7. Acceptance criteria

1. `consolidation_agent` deploys from `packages/agent` alongside the main graph; its cron appears in the schedules UI; lookback == interval holds across three consecutive runs (timeline tiling verified against fixtures).
2. A run over seeded fixture threads produces ≥1 proposal commit in the proposal area with diff + manifest + resolvable evidence links, and **zero writes under `org-memory/**`**.
3. A valid signed `context_hub.commit.created.v1` delivery yields the item in the approvals inbox with rendered diff; an invalid/missing signature yields 401 and no processing.
4. Approve merges exactly the reviewed diff into `org-memory/**` and closes the proposal; edit-then-approve merges the amended content; the next consolidation run observes the updated memory.
5. Reject-with-message produces no memory change (unconditional). The feedback halves — message in the next run's context, no verbatim re-proposal — are **contingent on §9-Q7** (proposal-log location) and activate when it resolves; until then they are blocked, not waived.
6. With webhook delivery disabled entirely, the reconciliation sweep still surfaces new proposals (correctness without webhooks).
7. Replayed deliveries create no duplicate items; decisions on already-closed proposals return a typed conflict.
8. A proposal whose base is stale (human edited a touched file post-proposal) is blocked with `409 stale_base` and a regenerate affordance.
9. Per-run proposal caps and the open-proposal circuit breaker demonstrably fire under a flood fixture.
10. Every proposal card shows evidence deep links; diffs/manifests render inside untrusted-content boundaries.

## 8. Adoption triggers & sequencing

**Triggers — what makes this worth building** (v1.x is deliberately post-v1, [04 backlog](../04-roadmap.md)):

- [F22](./22-org-intelligence-v1.md) Layers 0/1 show real adoption: `org-memory/` seeded and read in anger; org-analyst digests being opened weekly.
- **Manual memory-edit volume**: admins repeatedly hand-copying digest findings into `org-memory/` — the loop is already running by hand, which is exactly the signal to automate the propose half.
- Layer-1 automation datasets (HITL rejections/edits) accumulating — raw consolidation material exists.
- Team-persona orgs asking for it; a solo builder editing their own memory has little need for the review ceremony.

**High-level sequencing** (order, not a task breakdown):

1. Preconditions: F22 conventions + template stable; [F28](./28-backend-glue-service.md) deployed with a public URL ([F01 §9-Q4](./01-monorepo-and-oss-infra.md) resolved — a webhook consumer needs somewhere to run).
2. Probe pass: Hub webhook registration/signature/payload details, delivery semantics, branch-vs-prefix, write scopes (§9-Q1–Q4) — extends the F05 auth spike per [07 §6-Q2](../07-org-intelligence.md).
3. Loop-without-webhook: consolidation agent + proposal commits behind a flag; inbox reads proposals by polling Hub state. Proves the whole loop with **zero new inbound surface**.
4. Add the webhook consumer for freshness + notification (riding F19's fan-out when available).
5. Quality-control hardening (dedupe, stale-base, caps, circuit breaker) → default-on.

## 9. Open questions

1. **Hub webhook surface**: registration/management API, signature header name, payload schema — only the event name and HMAC signing are confirmed ([research 15](../../research/15-org-intelligence.md)). Probe with the beta account.
2. **Delivery semantics**: at-least-once? retry/backoff? ordering? Assumed at-least-once; design is idempotent either way.
3. **Hub branch/merge capabilities**: do proposals get real branches, or the copy-commit proposal prefix (§3.1 default)? Are Hub commits conflict-checked (compare-and-swap on head) — affects approve-retry safety (§5)?
4. **Context Hub write scopes under LangSmith OAuth** (O-001-adjacent; [07 §6-Q2](../07-org-intelligence.md)): can approval commit as the reviewing user, or must it use the service key (weaker audit trail)?
5. **Two graphs, one MDA project**: does `mda deploy` accept `consolidation_agent` alongside the main graph in one project ([research 20](../../research/20-gapfill-mda-api.md) shows multi-graph `langgraph.json` generation but doesn't confirm authoring)? Fallback: separate classic deployment.
6. **Org-wide episodic reads vs MDA identity scoping**: is the service-key-against-threads-API path acceptable, and how exactly are per-user/tenant threads excluded (§6)?
7. **Last-successful-run marker + proposal log location** under D-003: Hub file, thread state, or the same store F19 chooses for subscriptions? Align with F19's answer. Blocks: §3.4 rejected-content dedupe and the §3.2 rejection-feedback loop (the feedback halves of AC-5).
8. **F10 item-source seam**: does F10's inbox architecture accept a non-interrupt item source cleanly, or does `memory_proposal` force a refactor? Coordinate before F10 finalizes.
9. **Proposal identity for dedupe**: Hub commit id vs content hash — depends on Q3 commit semantics.

## 10. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Hub webhook surface thinner than assumed (only the event name is confirmed) | Review loop's push path blocked | Polling-first sequencing (§8 step 3) makes the webhook an enhancement, not a dependency |
| Low-quality/noisy proposals → reviewer fatigue → feature ignored | The loop dies socially, not technically | Evidence requirement, dedupe, small-size caps, rejection feedback, interval tuning; ship behind a flag until precision is acceptable on dogfood |
| Approved memory poisons future runs (injection laundering, hallucinated conventions) | High — compounding | Human gate on every merge + provenance links + runtime read-only mount + untrusted rendering (§6); never auto-merge, ever |
| D-003 erosion: server-side state creeps in via this feature | Glue service grows a database by accident | Hub-as-source-of-truth design (§3.3); any residual state shares F19's single answer, not a second mechanism |
| MDA identity scoping blocks org-wide thread reads | Agent consolidates from an empty window | Service-key path; explicit degrade to digest-driven proposals (§5), never silent |
| `apps/server` still has no hosting story when this starts ([F01 §9-Q4](./01-monorepo-and-oss-infra.md)) | Consumer has nowhere to run | Listed as a hard precondition in §8; resolved in [F28](./28-backend-glue-service.md) |
| LangSmith beta churn around Hub webhooks/API | Contract breakage | Versioned event name already in hand (`.v1`); contract tests + the F02 canary pattern ([F02](./02-m0-spikes.md)) |
| P-005 reversal (glue returns to Next.js routes) | Consumer relocates | Route logic kept transport-thin per [F01 §5](./01-monorepo-and-oss-infra.md) reversal path; contract in §4 is host-agnostic |

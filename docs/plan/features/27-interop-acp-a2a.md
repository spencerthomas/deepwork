# F27 · Interop — ACP & A2A/MCP exposure

*Deep Work feature spec · 2026-07-22 · Status: draft · Horizon: post-v1 · Depth: design-complete*

Sources: [08 · feature map (Protocols)](../08-deepagents-feature-map.md) · [architecture §2/§5/§10](../02-architecture.md) · [roadmap backlog](../04-roadmap.md) · [research 02 · harness](../../research/02-deepagents-harness.md) · [research 20 · MDA API](../../research/20-gapfill-mda-api.md) · [research 01 · MDA](../../research/01-managed-deep-agents.md) · [research 23 · runtime tiers](../../research/23-gapfill-runtime-tiers.md) · [research 14 · dcode](../../research/14-dcode.md) · [decisions](../decisions.md)

## 1. Scope

Two interop directions, both explicitly deferred to post-v1 by the [roadmap backlog](../04-roadmap.md):

- **ACP (outward to editors)**: putting the Deep Work agent inside Zed/JetBrains/any ACP client via the harness's own `deepagents-acp` (`libs/acp` in both monorepos, [research 02](../../research/02-deepagents-harness.md)) — "editor integrations for free … zero UI work from us" ([08 Protocols](../08-deepagents-feature-map.md)). This spec decides *what Deep Work actually ships* (docs vs config vs a packaged entry point) and how HITL surfaces in an editor without double-surfacing against the approvals inbox.
- **A2A/MCP (inward from other agents)**: every deployed agent on Agent Server already exposes `/a2a/{assistant_id}` and `/mcp` (each agent as an MCP tool) ([research 01](../../research/01-managed-deep-agents.md), [research 20](../../research/20-gapfill-mda-api.md)). Deep Work's job is **documentation + auth guidance** — who may call in, identity mapping per [F05](./05-auth-and-identity.md), trust boundaries — not new code ([08 Protocols](../08-deepagents-feature-map.md): "documented as an integration capability, no v1 work").

In scope: the docs-vs-glue ledger (§3.5), the interop guide pages, HITL postures for editor and machine callers, exposure warnings, and one optional read-only UI panel. Out of scope (neighbors): dcode's own ACP server and terminal handoff ([F25](./25-dcode-integration.md), D-013); MCP *consumption* as connectors (D-016; [F17](./17-fleet-manager.md)); outbound async-subagent delegation over Agent Protocol ([F14](./14-agent-package.md), [08 Delegation](../08-deepagents-feature-map.md)); the pure-OSS tier, which **loses `/mcp` and `/a2a` entirely** ([F26](./26-oss-selfhost-tier.md); [research 23](../../research/23-gapfill-runtime-tiers.md)); Slack/Linear task channels ([roadmap backlog](../04-roadmap.md)).

## 2. Dependencies & seams

| Neighbor | Seam |
|---|---|
| [F05 · auth & identity](./05-auth-and-identity.md) | Inbound callers are **plane 2** actors (end user ↔ deployment); this spec maps caller types onto F05's `trusted_backend`/`validated_token`/guest/classic-`Auth` mechanisms and inherits its threat model verbatim |
| [F10 · approvals inbox](./10-approvals-inbox.md) | Human-backstop posture: interrupts raised by machine-initiated threads hydrate through the same `threads.search(status:'interrupted')` path — the inbox is the HITL surface for A2A callers (§3.4) |
| [F14 · agent package](./14-agent-package.md) | Home of the optional ACP entry point and of any "interop" assistant config preset — composition/config, never protocol code (D-005) |
| [F17 · fleet manager](./17-fleet-manager.md) | Optional read-only "Interop" panel on agent detail (derived URLs + exposure warnings, §3.6); owns MCP connector CRUD (the *other* direction) |
| [F25 · dcode](./25-dcode-integration.md) | dcode already ships an ACP server locally ([research 14](../../research/14-dcode.md)) — the zero-work editor path Deep Work documents first |
| [F26 · OSS self-host](./26-oss-selfhost-tier.md) | Feature-loss matrix must state: no `/mcp`, no `/a2a` + agent card on the protocol-server tier ([research 23](../../research/23-gapfill-runtime-tiers.md)) |
| Upstream `deepagents-acp` | Consumed as a versioned package; API surface unverified (§9-1) |

Decisions cited: D-005 (compose, never fork), D-013 (no CLI; dcode is the local companion), D-016 (MCP-first connectors), D-004 (runtime tiers), D-010 (v1 HITL contract), P-005 (no new `apps/server` routes required here).

## 3. Design

### 3.1 ACP — what Deep Work ships

Three candidate shapes, resolved in order of D-005 discipline:

1. **Docs first (ships regardless)**: an integration guide that points editor users at **dcode's existing ACP server** ([research 14](../../research/14-dcode.md)) — already installed as the documented local companion (D-013), already Zed/JetBrains-ready, zero Deep Work code.
2. **Packaged entry point (ships if §9-1 confirms)**: an optional extra in `packages/agent` (e.g. `deepwork-agent acp` console script) that wraps the *composed Deep Work agent* — same tools, middleware, templates as the deployed one ([02 §3](../02-architecture.md)) — in `deepagents-acp`'s server. Value over path 1: the editor runs *your org's agent* (curated tools, rubrics, steering middleware), not generic dcode. This is an entry point + config, not protocol code; blocked until `deepagents-acp`'s wrap-an-arbitrary-agent API is verified (§9-1).
3. **Remote-attach bridge (not planned)**: proxying ACP sessions onto deployed cloud threads would be new gateway code — rejected under D-005 unless upstream grows it (§9-7). Cloud↔editor continuity remains dcode's `--sandbox-id` reattach ([F25](./25-dcode-integration.md)).

ACP sessions run **locally** (the entry point is a local process, like `langgraph dev` — [02 §2](../02-architecture.md)); they are not threads on any registered Deep Work agent source.

### 3.2 HITL in editors — the double-surfacing rule

Because ACP sessions are local and unregistered by default, **the editor client is the sole approval surface**: `interrupt_on` interrupts surface however `deepagents-acp` maps them to the client (exact mapping and decision-set parity with approve/edit/reject/respond is §9-2 — not invented here). The Deep Work approvals inbox never sees these sessions, so double-surfacing cannot occur in the default posture. If a user *chooses* to register the local server as an agent source (supported for `langgraph dev` today, [F04](./04-sdk-and-agent-sources.md)), the standard F10 semantics apply: one store keyed on `interrupt_id`, first decision wins, the other surface drops the row on rehydrate ([F10 §3.6](./10-approvals-inbox.md)). The guide documents this trade-off; no new dedupe machinery is built.

### 3.3 A2A/MCP inbound — documentation + auth guidance

Facts the guides pin: a deployed agent's Agent Server exposes `/a2a/{assistant_id}` and `/mcp` at the deployment URL ([research 01](../../research/01-managed-deep-agents.md)); MDA deployments are standard Agent Servers, but whether these endpoints are on by default there is unconfirmed (§9-3). Caller→credential mapping, reusing [F05 §3.4](./05-auth-and-identity.md) plane 2:

| Caller | Credential guidance |
|---|---|
| Another org's agent (cross-trust-boundary) | `validated_token` bearer (JWKS/OIDC/introspection) — caller carries its own verifiable identity; threads stamped `metadata.owner`, store fails closed outside the actor namespace ([research 20](../../research/20-gapfill-mda-api.md)) |
| Same-org internal service | `trusted_backend` headers from *that org's own* backend — the ingress secret is full impersonation power and is **never** shared across a trust boundary ([F05 §6](./05-auth-and-identity.md)) |
| Lightweight/anonymous experiment | HS256 guest tokens via public `POST /identity/guest` — documented as **effectively public exposure** (§6) |
| Bare classic deployment (no custom auth) | `X-Api-Key` — handing a caller a workspace key is over-privileged; guide labels it an anti-pattern and points at `langgraph_sdk.Auth` ([F05 §3.4](./05-auth-and-identity.md)) |

Interop scenario documented end-to-end: an external agent delegates a task over A2A → a thread is created under the caller's actor identity in *your* LangSmith org (data residency disclosed, §6) → the operator sees it as an ordinary thread in the task inbox with provenance metadata ([02 §10](../02-architecture.md)) → results return over the caller's stream. Inbound payloads render inside the untrusted-content boundaries adopted for webhook/schedule content ([02 §10](../02-architecture.md), [F18](./18-schedules-and-activity.md)).

### 3.4 HITL for machine callers — two postures

A machine caller cannot answer an `interrupt_on` prompt. The guides document both postures; both are assistant-config, not code (D-014 pattern):

- **Autonomous interop config**: a dedicated assistant config with a constrained tool set and no `interrupt_on` — nothing ever blocks. Recommended default for exposure.
- **Human backstop**: interrupts left on; they land in the operator's [approvals inbox](./10-approvals-inbox.md) via the normal interrupted-threads hydration, and the caller's request waits. Callers must handle latency and the Cloud **1-hour connection timeout** ([research 01](../../research/01-managed-deep-agents.md)); long approvals mean the caller re-joins or polls thread state.

### 3.5 Thin glue vs pure documentation — the ledger

| Deliverable | Kind | D-005 justification |
|---|---|---|
| Guide: *Use your Deep Work agent in an editor (ACP)* — dcode path + entry-point path | docs | — |
| Guide: *Call a Deep Work agent from another agent (A2A)* — auth table, scenario walkthrough, timeout/retry notes | docs | — |
| Guide: *Expose a Deep Work agent as an MCP tool (`/mcp`)* — for MCP-capable clients/agents | docs | — |
| Guide: *Interop security checklist* — exposure levels, credential anti-patterns, revocation | docs | — |
| ACP entry point in `packages/agent` (optional extra) | thin glue | wraps upstream `deepagents-acp`; entry point + config only; gated on §9-1 |
| "Interop" assistant config preset (autonomous posture) | config | assistant config over the same agent (D-014) |
| F17 agent-detail Interop panel (§3.6) | thin UI | read-only derivation, no new APIs |
| Anything speaking ACP/A2A wire protocol itself | **not built** | upstream owns protocols; gaps go upstream (D-005) |

Docs live in-repo under `docs/` per the v1 posture ([05 · OSS setup](../05-oss-setup.md)); guide pages are date-stamped and verified against live deployments (§7).

### 3.6 Fleet manager Interop panel (optional, last)

Read-only card on [F17](./17-fleet-manager.md) agent detail: derived `/a2a/{assistant_id}` and `/mcp` URLs with copy buttons, the source's identity mode, and an **exposure chip** (`key-gated` / `identity: validated_token` / `identity: trusted_backend` / `guest tokens enabled — public` / `unauthenticated`). Pure derivation from data F17 already fetches; degrades to hidden when the deployment URL or identity mode is unknown.

## 4. Contracts

1. **Endpoint facts** (verified, [research 01](../../research/01-managed-deep-agents.md)/[20](../../research/20-gapfill-mda-api.md)): `/a2a/{assistant_id}` and `/mcp` at the deployment URL on hosted Agent Server tiers; absent on the pure-OSS protocol-server tier ([research 23](../../research/23-gapfill-runtime-tiers.md)). A2A message schema and agent-card shape are **not** pinned here (§9-5) — guides link upstream docs rather than restating them.
2. **Credential attach points** are exactly [F05 contract 3](./05-auth-and-identity.md) — this spec adds no new auth mechanism and no plane-crossing exceptions.
3. **ACP entry point** (if shipped): consumes the same exported `agent` object as `mda`/`langgraph.json` deploys ([02 §3](../02-architecture.md)); no fork of `deepagents-acp`; version pinned + renovate-grouped ([02 §8](../02-architecture.md)).
4. **Guide-page contract**: every interop guide states (a) required credential and plane, (b) exposure level produced, (c) runtime tiers it applies to, (d) verification date.
5. **No new `apps/server` routes**: inbound callers hit the deployment directly; Deep Work is not in their data path (P-005 unchanged, D-003).

## 5. Edge cases & failure modes

| Case | Behavior |
|---|---|
| MDA deployment has `/a2a`/`/mcp` disabled or gated (§9-3) | Guides carry a tier matrix; probe documented (`GET /openapi.json` at the deployment); fallback: classic LangSmith Deployment of the same agent (D-004) |
| A2A caller hits an interrupt under the human-backstop posture and disconnects at the 1-h timeout | Run continues server-side; caller documented to re-join/poll thread state ([02 §7](../02-architecture.md) resumability) |
| Caller floods duplicate requests | Default `multitask_strategy: enqueue` per thread; per-caller quotas are platform-side and unpublished for MDA (§9-8) — guides say so honestly |
| ACP client lacks a decision type the interrupt allows (e.g. `edit`) | Degradation behavior owned upstream; documented once §9-2 resolves; until then the guide scopes editor use to approve/reject-style flows |
| Local ACP session registered as a source, decided in both surfaces | F10 semantics: second decision fails against an already-resumed thread; row drops on rehydrate ([F10 §3.6](./10-approvals-inbox.md)) |
| Pure-OSS tier user follows the A2A guide | Guide front-matter blocks this: endpoints do not exist there ([F26](./26-oss-selfhost-tier.md)) |
| Protocol revision churn (ACP or A2A) breaks a guide | Date-stamped guides + CI link checks; entry point pinned; breakage handled as upstream issue, never a local patch (D-005) |

## 6. Security & privacy

- **Accidental public exposure is the headline risk.** Defaults and warnings: identity-enabled deployments are fail-closed ([research 20](../../research/20-gapfill-mda-api.md)); the security checklist and the F17 exposure chip flag the two ways a deployment becomes effectively public — enabling **guest tokens** (anyone can mint an identity via the public `/identity/guest` route) and running **unauthenticated** (`langgraph dev`-style). No Deep Work guide ever instructs disabling identity to "make interop easier".
- **Credential anti-patterns called out**: never share the `trusted_backend` ingress secret outside your own backend (full impersonation, [F05 §6](./05-auth-and-identity.md)); never hand workspace API keys to third-party callers; prefer `validated_token` for anything cross-org.
- **Isolation**: thread/store scoping by `metadata.owner` with fail-closed 403 outside the actor namespace ([research 20](../../research/20-gapfill-mda-api.md)) is what makes multi-caller exposure tenable; the A2A guide's verification step demonstrates a second actor cannot read the first's threads (mirrors [F05 acceptance 8](./05-auth-and-identity.md)).
- **Prompt injection**: inbound delegated tasks are untrusted content — same boundary treatment as webhook/schedule payloads ([02 §10](../02-architecture.md), [F18](./18-schedules-and-activity.md)); autonomous interop configs use constrained tool sets for exactly this reason (§3.4).
- **Data residency**: inbound calls create threads, traces, and files in the *operator's* LangSmith org — disclosed in the guides so orgs can decide who may call in ("your org, your data" cuts both ways).

## 7. Acceptance criteria

1. The four guide pages of §3.5 exist, satisfy contract 4, and were executed verbatim against a live deployment on their stated date.
2. Following only the MCP guide, an external MCP client invokes a Deep Work agent via `/mcp` and receives a result.
3. Following only the A2A guide, a caller under a second actor identity completes a delegated task via `/a2a/{assistant_id}`; thread isolation verified (second actor sees only its own threads).
4. Human-backstop posture demonstrated: a machine-initiated thread's interrupt appears in the approvals inbox, is approved there, and the caller receives the completed result.
5. Editor path: the Deep Work agent (dcode path, and entry-point path if shipped) completes a session inside an ACP client per the guide, with approvals surfacing in exactly one place.
6. Security checklist review: exposure chip states match actual deployment auth config for all identity modes; guest-token warning renders.
7. D-005 audit: zero protocol implementation code in the repo; interop diff is docs + entry point + config + one read-only panel.

## 8. Adoption triggers & sequencing

*(Not a task breakdown — design-complete per D-021.)*

- **Trigger — A2A/MCP guides** (first; cheapest): a real external-delegation request from a user, or MDA GA confirming endpoint defaults (§9-3). Prereqs are v1 features only (F05 auth docs, F17 agent detail) — can land any time after M3.
- **Trigger — ACP dcode-path guide**: demonstrated editor-integration demand (issue votes, dcode-ACP usage among Deep Work users). Prereq: [F25](./25-dcode-integration.md) shipped (M3).
- **Trigger — ACP entry point**: §9-1 resolves green (upstream API wraps arbitrary composed agents) *and* the dcode path proves insufficient (users want the composed org agent, not generic dcode, in-editor).
- **Trigger — F17 Interop panel**: both guide sets published and generating support questions the chip would answer.
- **Sequencing**: docs → entry point → panel. Nothing here blocks, or is blocked by, other post-v1 specs; F26 only needs the one feature-loss line it already carries.

## 9. Open questions

1. `deepagents-acp` public API: can it wrap an arbitrary `create_deep_agent` composition as an ACP server (vs being dcode-internal), and which ACP protocol revision does it target? Gates §3.1 path 2. Resolution: inspect `libs/acp` + upstream docs when scheduling.
2. How `interrupt_on` HITL maps onto ACP clients' permission UX — decision-set parity with approve/edit/reject/respond (D-010), and degraded behavior when a client lacks a decision type. Resolution: same inspection + live Zed test.
3. Whether MDA deployments enable `/mcp` and `/a2a` by default or require env flags — open upstream question carried from [research 20](../../research/20-gapfill-mda-api.md). Resolution: probe on the beta deployment.
4. Do `/a2a` and `/mcp` honor MDA identity (`validated_token`/`trusted_backend`) identically to thread routes, and what does the agent card advertise (auth hints? capabilities)? Resolution: same probe; blocks the auth table's final wording.
5. Which A2A spec revision Agent Server implements and the agent-card schema — not covered by any research doc; guides must link upstream rather than restate.
6. Outbound direction: can `AsyncSubAgent` (Agent Protocol transport, [research 02](../../research/02-deepagents-harness.md)) consume a *third-party* A2A server, or is outbound A2A a new-glue question to send upstream? Currently out of scope; revisit with F14 v1.x work.
7. Is a remote-attach ACP bridge (editor → deployed cloud thread) ever justified, or does dcode `--sandbox-id` + this spec's local path cover the need permanently? Default answer: upstream feature request, not Deep Work code (D-005).
8. Inbound rate limiting/abuse controls per caller on MDA — quotas explicitly unpublished during beta ([research 20](../../research/20-gapfill-mda-api.md)); guides need real numbers at GA.
9. Should the guides recommend registering a local ACP server as an agent source (unified history, but reintroduces the double-surface trade-off of §3.2), or advise against it?

## 10. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Protocol maturity/churn — ACP young, A2A ecosystem thin; guides and entry point rot | High | Low-Med | Docs-first strategy keeps blast radius to prose; date-stamped guides + CI link checks; pinned upstream packages; §8 triggers delay investment until demand is real |
| HITL semantics mismatch across ACP clients (decision types silently dropped) | Med | Med | §9-2 resolved before the entry point ships; guide scopes supported flows until then; single-surface default posture (§3.2) |
| Accidental public exposure of a deployed agent (guest tokens, shared keys) | Med | High | Fail-closed identity default; security checklist + exposure chip; anti-pattern callouts in every guide (§6) |
| Machine callers wedged on interrupts (timeouts, orphaned threads) | Med | Low-Med | Autonomous config as the documented default; backstop posture documents timeout/re-join explicitly (§3.4) |
| Scope creep toward an "interop gateway" product | Med | Med | §3.5 ledger is the contract; anything protocol-shaped goes upstream (D-005); cut line binding per D-020 |
| MDA beta gating blocks validating the guides | Med | Low | Validate on a classic LangSmith Deployment of the same agent (D-004 fallback); tier matrix in guides |

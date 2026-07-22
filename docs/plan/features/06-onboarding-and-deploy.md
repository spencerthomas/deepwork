# F06 · Onboarding & deploy wizard

*Deep Work feature spec · 2026-07-22 · Status: draft · Milestone: M1–M3 · Depth: implementation-ready*

Sources: [decisions](../decisions.md) · [catalog](./README.md) · [01-vision](../01-vision.md) · [02-architecture](../02-architecture.md) · [03-ui-spec §3.6](../03-ui-spec.md) · [04-roadmap](../04-roadmap.md) · [06-frontend-implementation](../06-frontend-implementation.md) · [07-org-intelligence](../07-org-intelligence.md) · [research/12](../../research/12-lifecycle-auth-followup.md) · [research/20](../../research/20-gapfill-mda-api.md) · [research/23](../../research/23-gapfill-runtime-tiers.md)

## 1. Scope

Everything between a fresh browser session and a user's first dispatched task: the first-run flow (sign-in handoff → org/workspace picker → path chooser), the **deploy wizard** (MDA-style tarball deploy with classic-deployment fallback), **connect-existing-agent**, **demo mode** (P-004), the GitHub-App and environment nudges as sequenced onboarding steps, funnel instrumentation for the 15-minute north star ([vision success criterion 1](../01-vision.md)), and the M3 extensions (template gallery, org-memory seeding interview, PWA install nudge).

Out of scope (owned by neighbors): OAuth/PKCE/device-flow/API-key mechanics and session storage → [F05](./05-auth-and-identity.md); GitHub App internals, token proxy, repo picker → [F12](./12-github-and-git-flow.md); environment/snapshot editor and sandbox lifecycle → [F11](./11-execution-and-environments.md); ongoing agent configuration after onboarding (fleet manager, [03-ui-spec §3.4](../03-ui-spec.md)); PWA/manifest/push implementation → [F20](./20-pwa-and-mobile.md); org-memory template content and review loop → [F22](./22-org-intelligence-v1.md). Frontend is Next.js (D-022); the v0 concept's `/login` and `/config` screens are **visual references only**, not imported code ([06-frontend-implementation](../06-frontend-implementation.md)).

## 2. Dependencies & seams

| Dependency | Direction | Seam |
|---|---|---|
| [F05 auth](./05-auth-and-identity.md) | upstream | F06 starts from an established session: `{credential, org, workspace (tenant_id), mode: oauth\|key\|local}`. Org/workspace enumeration is F05's contract; F06 only renders the picker. |
| `apps/server` (FastAPI, P-005) | upstream | All control-plane calls (`api.host.langchain.com` → fallback `api.smith.langchain.com`, per [research/20](../../research/20-gapfill-mda-api.md)) go through server routes; keys never reach the browser by default ([03-ui-spec §3.6](../03-ui-spec.md) key-proxy pattern). Supersedes older doc text placing glue in Next.js server routes ([02-architecture §1](../02-architecture.md)). |
| `packages/sdk` AgentSource registry | downstream | Every onboarding path terminates by writing an `AgentSource` record ([06-frontend-implementation Phase B](../06-frontend-implementation.md)); the inbox/task-loop features consume it. |
| `packages/agent` | upstream | The deploy wizard packages this project as its tarball/repo source ([02-architecture §3](../02-architecture.md)). |
| `packages/ui` fixtures | upstream | Demo mode (P-004) renders entirely from the fixture set kept from the v0 concept ([06-frontend-implementation, decision 4](../06-frontend-implementation.md)). |
| [F12 GitHub](./12-github-and-git-flow.md) | downstream | F06 embeds F12's install step as a card and reads back `integration_id` (`GET /v1/integrations/github/install`, [research/12](../../research/12-lifecycle-auth-followup.md)). |
| [F11 environments](./11-execution-and-environments.md) | downstream | F06 shows a deferred "set up an environment" nudge; F11 owns the editor. |
| [F22](./22-org-intelligence-v1.md) / [F20](./20-pwa-and-mobile.md) | downstream | M3/M4 onboarding extension hooks (§3.7). |

## 3. Design

### 3.1 First-run flow (route group `/onboarding/*`)

```
O-1 /login ──F05──▶ O-2 workspace picker ──▶ O-3 path chooser ──▶ O-4 deploy wizard ─┐
                                                    │                                ├─▶ O-7 GitHub nudge ─▶ O-8 first task
                                                    ├─▶ O-5 connect existing ────────┘
                                                    └─▶ O-6 demo mode (bypasses O-7/O-8 gates)
```

Onboarding state (`step`, chosen path, `deployment_id`, funnel timestamps) persists in `localStorage` (`dw.onboarding.v1`) so refresh/browser-crash resumes at the same step; the `deployment_id` also lives server-side in the session so a second device can resume polling.

| Screen | Content | Loading | Error / retry |
|---|---|---|---|
| **O-1 Sign in** | "Sign in with LangSmith" + API-key fallback + trust-story copy ("your org, your data") — all per [03-ui-spec §3.6](../03-ui-spec.md); mechanics in [F05](./05-auth-and-identity.md) | F05-owned | F05-owned |
| **O-2 Org/workspace picker** | List of orgs → workspaces from F05 session; preselect single-workspace accounts and skip the screen | skeleton list | Enumeration failure → inline error + Retry; key-mode with org-scoped key but no tenant → prompt for workspace ID (`X-Tenant-Id` requirement, [research/20](../../research/20-gapfill-mda-api.md)) |
| **O-3 Path chooser** | Three cards: **(a) Deploy the Deep Work agent** (primary CTA), **(b) Connect an existing agent**, **(c) Try the demo** (P-004). Plus a fourth conditional card: if `GET /v2/deployments` already lists a deployment carrying the Deep Work marker (§3.2) in this workspace, show **Join existing** (team-member path, §3.5) | deployments list skeleton; chooser renders immediately, Join card streams in | Deployments-list failure degrades silently (chooser still works); toast with Retry |
| **O-4 Deploy wizard** | §3.2 | per-step | per-step (§3.2, §5) |
| **O-5 Connect existing** | §3.3 | validate spinner on submit | §3.3 |
| **O-6 Demo** | §3.4 | none (fixtures are local) | none |
| **O-7 GitHub + environment nudges** | §3.6 | F12-owned | F12-owned; both skippable |
| **O-8 First task** | New-task composer ([03-ui-spec §3.1](../03-ui-spec.md)) prefilled with a starter research/writing task (M1 templates have no sandbox, [04-roadmap M1](../04-roadmap.md)) | — | normal composer errors |

### 3.2 Deploy wizard (path a)

Steps run inside one `apps/server` orchestration; the client subscribes to progress. All external calls are verified control-plane surfaces ([research/12](../../research/12-lifecycle-auth-followup.md), [research/20](../../research/20-gapfill-mda-api.md)).

| Step | What happens | UI state |
|---|---|---|
| **D1 Capability probe** (O-003) | Server probes MDA beta availability for this workspace — candidate signal: `/v1/deepagents/*` agents/health responding vs 403/404 (exact gating semantics unverified → §9-1). Result cached per workspace. | "Checking what your workspace supports…" spinner ≤5 s; on probe failure, default to classic path with an info note |
| **D2 Template** | M1: single "Deep Work agent" template (= `packages/agent`). M3: template gallery — Deep Work SWE · Research · Writing · blank ([03-ui-spec §3.4 Create](../03-ui-spec.md), [04-roadmap M3](../04-roadmap.md)) | static |
| **D3 Name + secrets** | Deployment name; model-provider API key(s) collected and passed as `secrets[]` on the create call ([research/20](../../research/20-gapfill-mda-api.md)); reserved platform vars are never forwarded (mda rule, ibid.) | field-level validation |
| **D4a MDA-style deploy** | `POST /v2/deployments` (`source=internal_source`, `langgraph_config_path`, `secrets[]`, the `managed_deep_agent` marker — shape unverified → §9-2) → `POST /v2/deployments/{id}/upload-url` → signed PUT of the project tarball (**200 MB cap**) → poll revisions until `DEPLOYED` ([research/20](../../research/20-gapfill-mda-api.md)); then Context Hub sync (`/v1/platform/hub/repos/`) and cron reconciliation (`POST /runs/crons(/search)` on the deployment's own Agent Server) exactly as `mda deploy` does ([research/12](../../research/12-lifecycle-auth-followup.md), [research/20](../../research/20-gapfill-mda-api.md)) | Progress checklist: Created → Uploaded → Building → Deployed → Synced. Revision polling with backoff (gateway limits: 2000/10 s general, [research/20](../../research/20-gapfill-mda-api.md)) |
| **D4b Classic fallback** | Same `POST /v2/deployments` with `source=github` (`repo_url` + `integration_id`, `build_on_push` CD) against the user's fork/copy of the agent repo, or `internal_source` tarball without the MDA marker ([research/12](../../research/12-lifecycle-auth-followup.md)). Triggered by: D1 probe negative, **or** D4a create rejected (`deployment_type` refused for non-beta orgs — [04-roadmap risk register](../04-roadmap.md)) — in the rejection case the wizard offers the switch inline without restarting (name/secrets carried over) | same checklist; github-source adds "waiting for first build" |
| **D5 Done** | Write `AgentSource {type: mda\|deployment, deploymentUrl, assistantId}` (field names per [F04 §4](./04-sdk-and-agent-sources.md)); emit funnel checkpoint C2 (§3.8); advance to O-7 | success panel with deployment deep link to smith.langchain.com |

**Deep Work deployment marker (durable).** Both create branches (D4a and D4b) stamp the deployment as Deep Work-managed at create time, so detection never depends on wizard-local state: the create payload carries `{deepwork: {managed: 'v1', template, wizard_session_id}}` in the deployment's metadata/tags (distinct from the MDA `managed_deep_agent` marker, §9-2). O-3's Join-existing card (§3.1) and the idempotency reconcile (below) filter `GET /v2/deployments` on this marker — never on name heuristics. Whether `POST /v2/deployments` accepts such metadata/tags and `GET /v2/deployments` returns them is unverified → §9-12; until confirmed, the fallback convention is the same triple encoded in a reserved name prefix (`dw--`) stamped at create, retired the moment the metadata marker is verified (provisional — pending batch-1 review).

**Failure diagnostics** (each renders a distinct message + action, never a generic toast):

| Failure class | Detection | UX |
|---|---|---|
| Plan gating | create rejected for a Developer-plan workspace (cloud deploys require Plus; Developer includes no deployment — [research/23](../../research/23-gapfill-runtime-tiers.md)) | Explain plan requirement; offer: MDA path if D1 was positive (beta pricing unpublished → §9-6), `langgraph dev` local instructions, or demo mode |
| MDA marker rejected | 4xx on D4a create | inline switch to D4b |
| Tarball > 200 MB | client-side size check before upload | error before any network call |
| Upload failed / signed URL expired | PUT non-2xx | re-request `upload-url` for the **same** deployment id and retry (no duplicate create) |
| Revision failed | revision reaches a failed status (full status enum unpublished → §9-4) | show status + deep link to the deployment page on smith.langchain.com for build logs (log API existence → §9-4); Retry = new revision via redeploy, not a new deployment |
| Poll timeout (>10 min) | client timer | keep polling in background; "still building" state; user may leave — O-3's Join card picks the deployment up later |

**Retry semantics / idempotency:** the orchestration persists `deployment_id` immediately after create; every retry resumes from the last incomplete step. The crash window between `POST /v2/deployments` returning and `deployment_id` persisting is closed one of two ways: an upstream idempotency key on the create call if the control plane supports one (unverified → §9-13); otherwise, since the create payload carries `wizard_session_id` inside the Deep Work marker (above), any retry lacking a persisted `deployment_id` **reconciles first** — marker-filtered `GET /v2/deployments` for this wizard session, adopting a match as the persisted `deployment_id` — before it may issue a create. Invariant either way: `POST /v2/deployments` is never re-issued for the same wizard session; one wizard session never duplicates deployments.

### 3.3 Connect an existing agent (path b)

Form: deployment/server **URL** + **assistant id** (+ optional label). Validation = server-side fetch of the assistant via the standard Assistants API at that URL (available on every tier — [02-architecture §2](../02-architecture.md)):

- **LangSmith Deployment / MDA URL**: workspace key or bearer per F05 session.
- **Fleet agent**: PAT + `X-Auth-Scheme: langsmith-api-key`; owner-gated — non-owner gets 404, workspace members read-only ([research/12](../../research/12-lifecycle-auth-followup.md)). The 404 case gets a specific message ("Fleet agents are owner-gated — ask the owner or use your own PAT"), not "not found".
- **`langgraph dev` local**: `http://localhost:*` URL, no key ([research/23](../../research/23-gapfill-runtime-tiers.md)); only offered when the client can reach localhost (web app warns about mixed-content/https).

Success writes `AgentSource {type: deployment|fleet|local}` and jumps to O-8 (GitHub/environment nudges are skipped — connecting to an existing agent implies its execution story already exists; the nudges reappear contextually on first coding task, §3.6). Errors: unreachable URL, non-Agent-Server response, 401/403 (wrong credential plane), 404 (bad assistant id or Fleet gating) — each with field-level retry.

### 3.4 Demo mode (path c, P-004)

Zero-credential mode rendering the full app from `packages/ui` fixtures ([06-frontend-implementation, decision 4](../06-frontend-implementation.md)): populated inbox, one streaming-replay task detail, approvals samples. Persistent top banner "Demo data — nothing is connected" with a **Set up for real** CTA that returns to O-3 preserving nothing. Demo mode is reachable without sign-in (from O-1's footer) — it must not require an org context. No funnel checkpoints are emitted in demo mode.

### 3.5 Persona-fit: what each sees first

| Persona ([01-vision](../01-vision.md)) | First-run experience |
|---|---|
| **Solo builder** (v1 primary) | O-1 → O-2 auto-skip (single workspace) → O-3 with **Deploy** primary → wizard → GitHub nudge → first task. This is the 15-minute path. |
| **Team admin** | Same as solo, plus in D3 an "org agent" toggle that selects the multi-tenant identity preset baked into the template (`identity.py`, `preset="multi-tenant-saas"` vs `"private-assistant"` — [02-architecture §3/§5](../02-architecture.md)). Post-deploy panel shows a copyable invite link for teammates. |
| **Teammate** (per-user identity) | O-3 detects the org's existing deployment (marker-filtered `GET /v2/deployments`, §3.2) → **Join existing** card → source registered, no deploy, no GitHub step (admin's App install is org-level, [F12](./12-github-and-git-flow.md)) → straight to first task. Per-user identity (trusted_backend / validated_token) is F05's plane. |
| **Fleet user** | O-3 → **Connect existing** pre-toggled to Fleet mode (PAT + `X-Auth-Scheme` hint) → inbox/approvals loop without smith.langchain.com ([vision success criterion 3](../01-vision.md)). |

### 3.6 GitHub App install & environment nudge — sequencing

Principle: **nothing blocks the first non-coding task.** M1 task types are research/writing (no sandbox — [04-roadmap M1](../04-roadmap.md)), so both steps are deferrable cards, not gates.

- **O-7a GitHub App** (from M2, when coding tasks exist): card after D5 — "Connect GitHub to let the agent open draft PRs". Embeds F12's install flow; server resolves `integration_id` via `GET /v1/integrations/github/install` ([research/12](../../research/12-lifecycle-auth-followup.md)). *Skippable*; re-surfaced as a blocking prompt only when the user first dispatches a coding task without an installation. Note: the classic **github-source** deploy path (D4b) needs the integration *at deploy time* — in that branch the card moves before D4b and becomes required.
- **O-7b Environment nudge**: one line, not a screen — "Coding tasks run in a default environment; customize later in Settings → Environments" linking [F11](./11-execution-and-environments.md). The default is the template's built-in snapshot + `setup.sh` ([02-architecture §4](../02-architecture.md)); per-repo environments are a first-coding-task concern, never an onboarding gate.

### 3.7 M3+ onboarding extensions (hooks, not gates)

- **Org-memory seeding interview** (M3): after D5 on the team-admin path, optional card "Teach the agent about your org" launching the guided interview that seeds the `org-memory/` starter template ([07-org-intelligence Layer 0](../07-org-intelligence.md), [04-roadmap M3](../04-roadmap.md)); content and review loop in [F22](./22-org-intelligence-v1.md). Skippable, resumable from Settings.
- **PWA install nudge** (M4): after the user's first completed task (not during onboarding — earn it first), prompt home-screen install; iOS ≥16.4 requires it for push ([03-ui-spec §6](../03-ui-spec.md)). Mechanics in [F20](./20-pwa-and-mobile.md).

### 3.8 The 15-minute funnel (vision success criterion 1)

Checkpoints, each a `{name, ts}` appended to `dw.funnel.v1` in `localStorage`:

| # | Checkpoint | Trigger |
|---|---|---|
| C1 | `signin_complete` | F05 session established (first credential validated) |
| C2 | `agent_ready` | Deploy path: first revision `DEPLOYED` + source registered. Connect path: source validation success |
| C3 | `first_dispatch` | First run accepted for the user's first thread |
| C4 | `first_complete_pr` | That run finishes **and** a draft-PR URL is present in thread values (coding); non-coding variant: run finishes with an artifact |

Measurement, honoring the store-nothing stance ([01-vision non-goals](../01-vision.md)):

1. **Release measurement** (authoritative, [04-roadmap release criterion 1](../04-roadmap.md)): scripted Playwright E2E against a **fresh LangSmith account**, asserting C1→C4 < 15 min; run manually per release candidate (fresh accounts aren't CI-automatable → §9-8).
2. **In-product**: on C4, a one-time celebration surface shows the user their own C1→C4 time — the number stays on the device.
3. **Org-side**: runs carry the tracing-metadata convention (`task_type`, `surface`, … — [02-architecture §10](../02-architecture.md)) so C3→C4 is measurable in the org's own LangSmith. C1/C2 are not runs and exist only client-side.
4. **Central telemetry**: none by default; any opt-in aggregate reporting is an open question (§9-9).

### 3.9 Milestone mapping

| Piece | Milestone ([04-roadmap](../04-roadmap.md)) |
|---|---|
| O-1/O-2 (key-path; OAuth if Spike 1 green), O-5 connect, O-6 demo, single-template basic deploy (D1–D5), funnel C1–C3 | **M1** |
| O-7a GitHub card, coding-task gate prompt, C4/PR checkpoint, celebration surface | **M2** |
| D2 template gallery, org-agent toggle + Join-existing polish, org-memory interview hook | **M3** |
| PWA install nudge, device-flow sign-in surface, quickstart docs alignment | **M4** |

Note: the roadmap text places the "create/deploy wizard" wholly in M3; this spec pulls a **single-template basic wizard** into M1 (per the feature-catalog scope: M1 = sign-in + connect + basic deploy) and leaves the gallery/multi-template wizard in M3. Flagged as a roadmap delta (§9-10).

## 4. Contracts

**External (verified surfaces — never invented; casing/fields per [research/12](../../research/12-lifecycle-auth-followup.md), [research/20](../../research/20-gapfill-mda-api.md)):**

| Call | Use | Notes |
|---|---|---|
| `POST /v2/deployments` | D4a/D4b create | `source: internal_source\|github`, `langgraph_config_path`, `secrets[]`; MDA marker shape unverified (§9-2). Headers: `X-Api-Key` (+ `X-Tenant-Id` for org-scoped keys). Base `https://api.host.langchain.com`, fallback `https://api.smith.langchain.com` |
| `POST /v2/deployments/{id}/upload-url` → signed PUT | tarball upload | 200 MB cap; GCS PUT |
| `GET /v2/deployments` (+ revisions read; exact revision-path/response schema → §9-4) | Join-existing card; D4 polling | poll until `DEPLOYED` |
| `GET /v1/deepagents/*` (agents/health) | D1 MDA probe candidate | probe signal unverified (§9-1) |
| `GET /v1/integrations/github/install` | O-7a → `integration_id` | consumed via [F12](./12-github-and-git-flow.md) |
| `/v1/platform/hub/repos/` | post-deploy Context Hub sync | mirrors `mda deploy` |
| `POST /runs/crons`, `/runs/crons/search` (deployment's Agent Server) | post-`DEPLOYED` schedule reconciliation | delete-and-recreate, mda semantics |
| Assistants API at source URL | O-5 validation | Fleet: PAT + `X-Auth-Scheme: langsmith-api-key` |

**Internal (`apps/server`, FastAPI — P-005; Deep Work-defined, first pinned here, final shapes owned by the server package):**

| Route (proposed) | Purpose |
|---|---|
| `GET  /api/onboarding/capabilities` | D1 probe result `{mda: available\|unavailable\|unknown, plan_gate?: bool}` per workspace |
| `POST /api/onboarding/deploy` | start orchestration `{template, name, org_agent: bool, secrets, source_mode}` → `{deployment_id}` |
| `GET  /api/onboarding/deploy/{deployment_id}/events` | SSE progress (`created\|uploaded\|building\|deployed\|synced\|failed{class}`) |
| `POST /api/sources/validate` | O-5 `{url, assistant_id, auth_mode}` (`auth_mode` ∈ [F05 §4 contract 4](./05-auth-and-identity.md)'s enum) → normalized `AgentSource` or typed error |

**Client:** `AgentSource {id, type: mda|deployment|fleet|local, name, deploymentUrl, assistantId}` — field names canonical per [F04 §4](./04-sdk-and-agent-sources.md), which owns the full schema (incl. `auth` mode + `capabilities`); registry per [06-frontend-implementation Phase B](../06-frontend-implementation.md). `dw.onboarding.v1` and `dw.funnel.v1` localStorage shapes as in §3.1/§3.8.

## 5. Edge cases & failure modes

- **Developer-plan (free) workspace**: no classic deploy entitlement ([research/23](../../research/23-gapfill-runtime-tiers.md)) — D1 surfaces this *before* D3 so users don't type secrets into a dead end.
- **Org-scoped key without workspace**: control-plane calls need `X-Tenant-Id`; O-2 blocks until a workspace is chosen.
- **`deployment_type` rejected mid-wizard**: inline fallback (D4b) without data loss — the roadmap risk-register mitigation, verbatim.
- **Refresh / second device mid-deploy**: resume from persisted `deployment_id`; O-3 Join card is the catch-all if local state is lost.
- **Duplicate deploys**: Join-existing card + explicit "deploy another" confirmation when a Deep Work deployment already exists in the workspace.
- **Upload-URL expiry / flaky PUT**: fresh `upload-url` per retry, same deployment (expiry window undocumented → §9-5).
- **Rate limiting during polling**: exponential backoff; polling budget stays far under the 2000/10 s gateway limit.
- **Connect-existing to a non-Agent-Server URL**: typed validation error ("didn't answer the Assistants API"), never a raw fetch failure.
- **Fleet owner-gating 404**: specific copy (§3.3) — the most confusing failure in this flow.
- **GitHub App popup blocked / install cancelled**: card returns to idle with Retry; coding-task gate re-prompts later (F12 owns callback handling).
- **Demo → real transition**: fixtures never mix with live sources; leaving demo clears nothing but the banner (no credentials existed).
- **Workspace switch mid-wizard**: hard reset of wizard state (deployments are workspace-scoped); confirm dialog first.
- **`langgraph dev` source on hosted web app**: localhost unreachable/mixed-content → guidance to run the web app locally instead of a silent timeout.

## 6. Security & privacy

- **Keys stay server-side**: API keys are proxied by `apps/server` (P-005) by default; client-side storage only in local mode — with the on-screen trust story ([03-ui-spec §3.6](../03-ui-spec.md), [research/12 §2](../../research/12-lifecycle-auth-followup.md)). Control-plane ops use the org/workspace-scoped service key server-side.
- **Deployment secrets**: D3 secrets are forwarded once as `secrets[]` to the control plane and never persisted by Deep Work; reserved platform vars are never forwarded (mda rule, [research/20](../../research/20-gapfill-mda-api.md)).
- **No GitHub tokens in the client or sandbox**: the install step only yields an `integration_id`; token minting/proxying is [F12](./12-github-and-git-flow.md)'s zero-secret pattern ([02-architecture §4](../02-architecture.md)).
- **Funnel privacy**: checkpoints are device-local; no central collection without explicit opt-in (§9-9) — consistent with "Deep Work stores essentially nothing" ([01-vision](../01-vision.md)).
- **Demo mode**: zero credentials, zero network beyond static assets; safe for screenshots/conference demos.
- **Deploy diagnostics**: error surfaces must not echo secret values or signed URLs; deep links to smith.langchain.com carry no credentials.

## 7. Acceptance criteria

1. Fresh account → C1→C4 (draft PR) in **< 15 min**, measured by the scripted E2E of §3.8-1 (from M2; at M1 the criterion is C1→C3 plus a completed non-coding task).
2. All three O-3 paths reach a registered `AgentSource` (or demo shell) with zero dead ends; every step in §3.1's table has implemented loading, error, and retry states.
3. MDA-unavailable and `deployment_type`-rejected workspaces both land on a successful classic deploy without re-entering name/secrets.
4. Deploy wizard survives page refresh at every step; no duplicate deployment is ever created by retries — including a crash between create and `deployment_id` persistence (reconcile path, §3.2) — verified by test against a mock control plane.
5. A Developer-plan workspace sees the plan-gate explanation before entering secrets, with all three alternatives offered.
6. Fleet connect works end-to-end with a PAT (vision criterion 3); the owner-gating 404 shows its specific message.
7. Teammate path: joining an existing org deployment requires zero deploy/GitHub steps.
8. Demo mode runs with no credentials and emits no funnel events or network calls to LangSmith.
9. No secret material is observable in browser storage, URLs, or client bundles in proxy mode (release criterion 5 hygiene).

## 8. Task breakdown

| # | Task | Depends on | Definition of done |
|---|---|---|---|
| 1 | Onboarding route group + state machine (`dw.onboarding.v1`, resume logic) | F05 session contract | Refresh at any step resumes; unit tests for all transitions |
| 2 | O-2 workspace picker (render-only over F05 enumeration) | 1, F05 | Single-workspace auto-skip; org-key-without-tenant prompt |
| 3 | Demo mode (P-004): fixtures provider + banner + exit ramp | fixtures pkg | Full app browsable with zero credentials; no LangSmith calls (network assert in test) |
| 4 | `apps/server` route: `POST /api/sources/validate` + typed errors | P-005 scaffold | Deployment/Fleet/local all validated; Fleet 404 typed distinctly |
| 5 | O-5 connect-existing screen → AgentSource registry write | 1, 4, sdk registry | All §3.3 error states rendered; source usable by inbox |
| 6 | O-3 path chooser + Join-existing detection (marker-filtered `GET /v2/deployments`, §3.2) | 1, server proxy | Join card appears iff a marker-stamped Deep Work deployment exists; silent degrade on list failure |
| 7 | D1 capability probe route + caching (O-003) | server proxy | Returns available/unavailable/unknown; result drives D4a/D4b branch; probe signal documented against beta account findings |
| 8 | Deploy orchestration in `apps/server`: create → upload-url → PUT → revision poll → hub sync → cron reconcile, SSE progress | 7, packages/agent tarball build | Golden-path integration test vs mock; idempotent resume from every step incl. the create-crash reconcile (§3.2) |
| 9 | O-4 wizard UI (D2 single template, D3 secrets, D4 progress checklist, D5 done) | 1, 8 | All §3.2 failure classes render distinct copy + correct retry action |
| 10 | Classic fallback branch (github-source + plain tarball) incl. inline switch on rejection | 8, F12 `integration_id` read | Rejected-marker path completes a classic deploy carrying over D3 inputs |
| 11 | Funnel instrumentation C1–C3 + `dw.funnel.v1` | 1, 5, 8 | Events fire once each; absent entirely in demo mode |
| 12 | O-7a GitHub card embed + coding-task gate re-prompt | F12 flow | Skippable; deploy-time-required only in github-source branch |
| 13 | O-7b environment nudge line + O-8 prefilled first-task composer | 9, task-composer feature | Dispatch from O-8 emits C3 |
| 14 | C4 checkpoint + celebration surface (draft-PR detection from thread values) | 11, M2 coding loop | Shows device-local elapsed time; fires once |
| 15 | Scripted fresh-account E2E for the 15-min measurement | 1–14 | Documented runbook; produces C1→C4 timings per release candidate |
| 16 | M3: template gallery (D2 multi-template) + org-agent toggle + org-memory interview hook + teammate-join polish | 9, F22 | Gallery deploys all templates; interview skippable/resumable |

## 9. Open questions

1. **MDA availability probe (O-003)**: what is the authoritative signal that a workspace is MDA-beta-enabled — `/v1/deepagents/*` response codes, a capabilities endpoint, or only create-time rejection? Needs testing with the beta account (extends [research/20 open questions](../../research/20-gapfill-mda-api.md)).
2. **`managed_deep_agent` marker shape** in the `POST /v2/deployments` payload — boolean, object, or `deployment_type` enum ([research/20](../../research/20-gapfill-mda-api.md)); blocks D4a payload finalization.
3. Whether non-beta orgs can accept the MDA marker at all (roadmap risk) — determines how prominent D4b is in copy.
4. **Revision API specifics**: exact path/response schema for revision listing/polling, the full revision status enum beyond `DEPLOYED`, and whether build logs are retrievable via API (vs deep-link-only).
5. Signed upload-URL **expiry window** and documented retry contract.
6. **MDA beta pricing/quotas** (unpublished, [research/23](../../research/23-gapfill-runtime-tiers.md)) — affects the Developer-plan messaging in §5.
7. **Workspace/org enumeration endpoint** for O-2 — owned by F05, but F06's picker copy depends on whether OAuth scopes cover it (M0 Spike 1).
8. Can fresh-account creation be automated for the 15-min measurement, or does it stay a manual runbook?
9. Policy for **opt-in central funnel telemetry** (if any) — needs a project decision; default remains none.
10. Roadmap delta: confirm pulling the single-template basic deploy wizard into M1 (roadmap text has the create/deploy wizard at M3; the M1 exit criterion "against a real MDA deployment" currently assumes CLI deploys).
11. Whether O-8's prefilled starter task should be a fixed template or generated from repo/org context once F22 exists.
12. **Deep Work deployment marker (§3.2)**: does `POST /v2/deployments` accept arbitrary metadata/tags, and does `GET /v2/deployments` return them for Join-existing filtering? Blocks retiring the `dw--` name-prefix fallback; needs testing with the beta account alongside §9-2.
13. **Create idempotency key**: does `POST /v2/deployments` honor an idempotency key (header or payload)? Determines whether reconcile-by-wizard-session-marker (§3.2) is the permanent crash-window closure or a stopgap.

## 10. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| MDA gating persists / marker rejected broadly | Med | High | D4b classic fallback is a first-class equal path, not an afterthought; copy never promises MDA ([04-roadmap risk register](../04-roadmap.md)) |
| Free-tier users hit the plan gate and churn at D1 | Med | Med | Gate surfaced early with three real alternatives (MDA-if-available, local dev, demo); §5 |
| Deploy orchestration flakiness (upload, build times) blows the 15-min budget | Med | High | Idempotent resume, background polling, snapshot-fast template; measure per release (task 15) |
| Probe signal (§9-1) proves unreliable → wrong default branch | Med | Med | Create-time rejection always triggers the inline fallback regardless of probe result |
| GitHub step placed wrong (too early = friction, too late = failed first coding task) | Low | Med | Deferred-card + hard gate only at first coding dispatch (§3.6); revisit with funnel data |
| Onboarding scope creep toward the fleet manager | Med | Med | Wizard ends at first task; all post-onboarding config lives in Agents/Settings ([03-ui-spec §3.4/§3.6](../03-ui-spec.md)) |
| Funnel unmeasurable in practice (manual fresh accounts) | Med | Low-Med | Runbook + celebration-surface numbers from real users as a proxy |

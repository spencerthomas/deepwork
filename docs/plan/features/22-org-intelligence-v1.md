# F22 · Org intelligence v1 (Layers 0–1)

*Deep Work feature spec · 2026-07-22 · Status: draft · Milestone: M3 · Depth: implementation-ready*

Sources: [07 · Org intelligence §1–2, Layers 0–1, §4–6](../07-org-intelligence.md) · [research 15 · org intelligence](../../research/15-org-intelligence.md) · [04 · Roadmap M3](../04-roadmap.md) · [02 · Architecture §3/§5/§6/§10](../02-architecture.md) · [03 · UI spec §3.4–3.6](../03-ui-spec.md) · [research 20 · MDA API](../../research/20-gapfill-mda-api.md) · [research 10 · open-swe/Fleet](../../research/10-openswe-fleet.md) · [decisions](../decisions.md) · [catalog](./README.md)

Stack facts: frontend = Next.js (D-022); all keyed calls go through the Python FastAPI glue `apps/server` (P-005; service spec [F28](./28-backend-glue-service.md)). Layer 2 (consolidation + review loop) is [F23](./23-org-intelligence-v1x-consolidation.md), post-v1; Layers 3–5 are [F24](./24-org-intelligence-v2-v3.md). This spec owns the **v1 slice only**: Layer 0 + Layer 1, roadmap M3.

## 1. Scope

In scope ([07 Layers 0–1](../07-org-intelligence.md); [04-roadmap M3](../04-roadmap.md)):

- **Layer 0 — the configured work system**: the `org-memory/` starter template (concrete tree + frontmatter, §4.1), its read-only mount contract at `/memories/org`, the onboarding **seeding interview** as a guided curation task, and the human edit/commit path via `apps/server`.
- **Layer 1 — activity intelligence**: the **tracing-metadata convention as a contract** (exact keys, stampers — §4.2); the **LangSmith deep-link map** for every screen (§3.4); **Insights config provisioning** over the beta REST (+ Plus/Enterprise gating and free-tier degradation); the **org-analyst schedule template** (cron → langsmith-mcp-server → weekly digest → notify); **automation-rule recipes** (HITL rejections/edits → dataset; errors → webhook → push).
- Rate-limit posture for everything above (`/runs/query` tiers; Bulk Export as the documented later warehouse path — recipe only, never built).

**Scope guard — build vs consume ([07 §4](../07-org-intelligence.md), D-018, D-020).** Deep Work builds *templates, provisioning glue, and review surfaces* only. Consumed as-is: LangSmith Insights, automations, `/runs/query`, Bulk Export, langsmith-mcp-server, Context Hub repos + MDA memory slices. **No analytics infra, no charts (P-002), no vector store, no Deep Work-side database (D-003).** Anything analytical deep-links to LangSmith ([02 §10](../02-architecture.md)).

Out of scope (neighbors): agent-proposed memory commits + Hub-webhook review loop → [F23](./23-org-intelligence-v1x-consolidation.md); OKF/openwiki, data plane, Graphiti → [F24](./24-org-intelligence-v2-v3.md); Schedules/Activity surfaces and `CronEditor` → [F18](./18-schedules-and-activity.md); fleet config editor chrome → [F17](./17-fleet-manager.md); onboarding sequencing → [F06 §3.7](./06-onboarding-and-deploy.md); push delivery → [F19](./19-notifications-and-push.md); rubric/verification metadata semantics → [F16](./16-verification-and-rubrics.md).

## 2. Dependencies & seams

| Direction | Spec | What crosses the seam |
|---|---|---|
| needs ← | [F28](./28-backend-glue-service.md) / P-005 | FastAPI host for org-memory routes, Insights/automation provisioning routes, automation-webhook ingest; workspace service key (`lsv2_sk_` + `X-Tenant-Id`) held server-side |
| needs ← | [F17](./17-fleet-manager.md) | Hub read proxy + file-editor components; F17's memory section renders `/memories/org` **view-only** and defers writes to this spec's commit path |
| needs ← | [F18](./18-schedules-and-activity.md) | `CronEditor` (org-analyst template opens it prefilled), `UntrustedContent`, schedule-origin metadata (`surface:"schedule"`, `deepwork_schedule_id`) |
| needs ← | [F14](./14-agent-package.md) | `packages/agent` carries the tracing-convention middleware, the org-analyst skill + `define_schedule` entry, and the langsmith-mcp-server connector registration |
| provides → | [F08](./08-task-inbox.md) / [F04](./04-sdk-and-agent-sources.md) | Canonical metadata key table (§4.2) — F08 stamps it at `threads.create`; F04's SDK owns the stamping helper + `traceUrls` |
| provides → | [F16](./16-verification-and-rubrics.md) | Dataset automation consuming `rubric_verdict`/`verification_override`/HITL outcomes (F16 §3.7 hands the recipe here) |
| provides → | [F19](./19-notifications-and-push.md) | Error-automation webhook events normalized into F19's pipeline (`task.failed`); F19 dedupes against run webhooks by `(run_id, status)` |
| provides → | [F23](./23-org-intelligence-v1x-consolidation.md) | `org-memory/` tree as proposal targets; metadata convention as the episodic tool's filter vocabulary; digests as consolidation input |
| coordinates ↔ | [F06 §3.7](./06-onboarding-and-deploy.md) | "Teach the agent about your org" card launches the seeding interview; skippable, resumable from Settings |
| constrained by | O-007, O-011, O-008, O-009 | Insights readback; multi-workspace iteration; Hub write scope under OAuth; OKF drift (we ship OKF-*shaped*, not OKF-locked) |

## 3. Design

### 3.1 Layer 0 — Context Hub as the work system

The org's work configuration is Context Hub files, already edited by F17: `instructions.md`, `skills/`, and `memories/` slices on the MDA hot/cold model — hot `/memories/user/AGENTS.md` injected per turn (0.4.0-dev, beta-badged per F17), cold files read on demand; per-actor/tenant slices scoped by MDA identity ([research 15](../../research/15-org-intelligence.md), [research 20](../../research/20-gapfill-mda-api.md)). F22 adds the **org slice**: `org-memory/**` mounted read-only at `/memories/org`; agent writes are **runtime-denied by MDA** — the platform's own prompt-injection defense for shared state ([research 15](../../research/15-org-intelligence.md): "prevents prompt injection via shared state"). Deep Work never requests agent write access to that mount; all writes go through `apps/server` with operator credentials:

- **Human edits (v1)**: admins edit org-memory pages in the Settings surface (§3.5) → diff preview → `POST /api/org-memory/commit` (Hub directory commit, [research 20](../../research/20-gapfill-mda-api.md) fact 1). Writes-are-proposals ([07 §1.3](../07-org-intelligence.md)) governs *agents*; humans commit directly.
- **Agent proposals**: none in v1 — that is F23's review loop. F17's "propose change" affordance renders disabled with "coming in v1.x" copy until F23 ships.
- **Digests** (§3.3): the one machine-written path, server-filed into `digests/` only — never into curated pages.

### 3.2 Layer 0 — seeding interview (seam to F06)

A **guided curation task, not new infra** ([07 Layer 0](../07-org-intelligence.md)): a normal thread against the Deep Work agent using the shipped `skills/org-memory-interview/SKILL.md`, launched from F06's M3 card or Settings → Org intelligence. Flow:

1. **Interview** — the agent asks, one topic per turn, capturing answers into draft files on its thread filesystem (StateBackend; no sandbox): (a) who are you — company, product, mission one-liner → `who-we-are.md`; (b) teams — names, missions, owners → `teams/*.md`; (c) systems — repos, services, environments, where things run → `systems/*.md`; (d) policies — code review, deploy windows, security/data handling, tone of voice → `policies/*.md`; (e) glossary — internal terms, acronyms → `glossary.md`; (f) recent decisions worth recording → `decisions/log.md`. The skill enforces the frontmatter shape (§4.1) and marks unknowns `status: draft` rather than inventing.
2. **Review** — drafts render in the task files rail ([F13](./13-files-diff-and-review.md)); user edits inline or steers the agent.
3. **Commit** — "Commit to org memory" per file or in bulk → `POST /api/org-memory/commit` (operator session; server enforces the `org-memory/**` path prefix). The agent never commits; runtime-deny stays intact.
4. **Resume** — the thread persists; F06's card is skippable and the interview resumable from Settings (F06 §3.7). Partial commits are fine; the browser shows seeded vs template-stub pages.

Run stamped `task_type: curation` (extends F08's enum — coordinated delta, §9-14).

### 3.3 Layer 1 — org-analyst schedule template

"What did all our agents do this week," synthesized and filed ([07 Layer 1](../07-org-intelligence.md)). Shipped in `packages/agent`, provisioned from Settings via F18's `CronEditor` opened prefilled:

| Piece | Concrete shape |
|---|---|
| Schedule | `define_schedule(name="org-analyst-weekly", schedule="0 7 * * 1", timezone=<org TZ at provisioning>, prompt=ORG_ANALYST_PROMPT)` — 5-field cron + prompt, per the verified contract ([research 20](../../research/20-gapfill-mda-api.md) fact 11). Thread mode **ephemeral** (default): each digest independent; prior context = read last digest file, not thread history |
| Tools | langsmith-mcp-server (official; runs/traces, thread stats, experiments, usage — [research 15](../../research/15-org-intelligence.md)) registered as a remote HTTP MCP connector (`define_mcp_servers`, bearer = workspace key in deployment secrets, never in any sandbox); filesystem built-ins. No `execute`, no sandbox |
| Skill | `skills/org-analyst/SKILL.md`: digest template, rate budget, link mandate (below) |
| Prompt (shipped text, abridged) | *"You are the org analyst. Survey the last 7 days of Deep Work activity via the langsmith tools: run volume by `agent` and `task_type`, completion/error rates, HITL rejection hotspots, notable failures, usage/cost summary where available. Cross-reference `/memories/org` for team and system names. Write the digest to `digests/YYYY-WW.md` per the skill template. Every claim carries a trace or project link. Aggregate — never quote end-user content verbatim. Respect the rate budget in your skill."* |
| Rate budget (in-skill, hard rules) | Windows **≤7 days** (the 10/10s `/runs/query` tier — [07 Layer 1](../07-org-intelligence.md); F18 §9-8 notes a 15/10s gateway-table discrepancy → budget to 10/10s); queries sequential, never parallel fan-out; prefer thread-stats/aggregate tools over per-run pulls; cap total reads per sweep; on 429 back off (harness `ToolRetryMiddleware`, [02 §3](../02-architecture.md)). A missed week is covered as two sequential ≤7d windows, never one 14d window (that drops to the 3/10s tier) |
| Output | `digests/YYYY-WW.md` (ISO week) with `kind: digest` frontmatter + `run_id` |
| Filing | The agent writes to its **thread FS** (org mount is read-only). On the run-completion webhook ([F19](./19-notifications-and-push.md)) for `agent: org-analyst`, `apps/server` fetches the file from thread state and commits it under `org-memory/digests/` — idempotent on `run_id`. Default auto-file (digests are append-only, labeled machine output); a `require_review_for_digests` toggle turns the notification into "review & file" (§9-10) |
| Notify | F19 `task.completed` push deep-linking to the digest view |

**Warehouse path**: orgs outgrowing the sweep get a documented **Bulk Export** recipe (Plus/Enterprise; scheduled Parquet → S3-compatible — [research 15](../../research/15-org-intelligence.md)) in the docs; Deep Work builds nothing for it.

### 3.4 Layer 1 — tracing conventions & the deep-link map

Per-agent tracing projects (open-swe pattern, [02 §10](../02-architecture.md)): one LangSmith project per deployed agent; hosted deployments get a per-deployment project natively — naming/override control is §9-5; where controllable the convention is the deployment name. Deep Work **never re-implements observability** — every screen deep-links out; URL construction is centralized in one `packages/sdk` `traceUrls` helper (run URLs via the langsmith SDK; project/Insights URL templates verified at the M3-entry probe, never guessed — filter-param encoding §9-5):

| Deep Work screen | LangSmith view |
|---|---|
| Task detail run panel ([F09](./09-task-detail-and-streaming.md)) — `TracePill`, 100% of runs (release criterion 4) | Run/trace page |
| Task inbox row menu ([F08](./08-task-inbox.md)) | Latest run trace for the thread |
| Approvals card ([F10](./10-approvals-inbox.md)) | Interrupted run's trace |
| Agents index row · Agent detail Overview ([F17](./17-fleet-manager.md)) | The agent's tracing project |
| Agent detail Overview "Insights" row | Project's Insights reports view |
| Schedules run-history row ([F18](./18-schedules-and-activity.md)) | Fired-run trace |
| Activity filter context (F18 §3.7 "Open in LangSmith ↗") | Tracing project (filtered view when §9-5 confirms param encoding; plain project link otherwise) |
| Settings → Org intelligence (§3.5) | Insights configs · rules/automations page · Bulk Export docs |
| Digest view | Trace links authored inside the digest body (skill mandate: per-claim links) |

### 3.5 Layer 1 — Insights provisioning + Settings surface

**Settings → Org intelligence** (P-002: config folds into Settings) hosts: org-memory browser (seeded/stub state per page, edit → commit path, digest list rendered inside `UntrustedContent`), interview launch/resume, org-analyst provisioning card, Insights configs, automation recipes.

Insights flow, per tracing project (LangSmith *sessions* = tracing projects; beta REST per [research 15](../../research/15-org-intelligence.md)):

1. Optional NL start: `POST /api/v1/sessions/{id}/insights/configs/generate` → editable config draft.
2. Save + schedule: `POST /api/v1/sessions/{id}/insights/configs` with `schedule_cron` (default `0 6 * * 1`, before the org-analyst sweep so reports exist to reference).
3. **Cost confirm before scheduling**: ~$1–4 per 1,000 threads, 1,000-trace sample cap, model enum openai|anthropic ([research 15](../../research/15-org-intelligence.md)) — shown with the org's recent weekly thread count.
4. **Gating**: Insights is Plus/Enterprise. Provisioning attempts the call; a plan-gate rejection (signal §9-2) flips the panel to degraded copy — "Insights needs Plus/Enterprise; your weekly org-analyst digest keeps working" — the free-tier story ([07 Layer 1](../07-org-intelligence.md)).
5. **Readback (O-007)**: if the M1 probe confirms report payloads are API-readable, the panel adds an exec-summary card per report; if UI-only, deep link only. Both states designed; no report rendering is built until O-007 resolves.

### 3.6 Layer 1 — automation rules

Two shipped recipes ([07 Layer 1](../07-org-intelligence.md); automations = filter + sample + actions, backfill supported — [research 15](../../research/15-org-intelligence.md)). The rules REST surface is **unverified** → provisioning glue targets whatever the M3-entry probe finds (§9-3); until then each recipe renders as a card with exact filter strings + deep link to the rules page — never invented endpoints:

| Rule (per Deep Work tracing project) | Filter | Action |
|---|---|---|
| **Eval fuel** | root runs where `hitl_outcome ∈ {rejected, edited}` or `rubric_verdict` failing or `verification_override` present (F16 §3.7 signal set) | Add to dataset `deepwork-hitl-feedback` (created once per workspace), sample 1.0 |
| **Error push** | root runs, `error: true` | Webhook → `POST https://<server>/hooks/langsmith/{grant}` → normalized to F19 `task.failed`. Covers runs Deep Work didn't create (Studio, direct SDK); F19's `(run_id, status)` dedupe suppresses doubles for Deep Work-created runs |

## 4. Contracts

### 4.1 `org-memory/` starter template (Layer 0)

OKF-*shaped* — typed YAML frontmatter + relative-link relationships, greppable/readable by agents with filesystem tools, forward-compatible with F24's OKF adoption without claiming v0.1 conformance (O-009):

```
org-memory/
  README.md            # index + curation rules; agents read this first
  who-we-are.md        # kind: org — company, product, mission
  teams/<slug>.md      # kind: team    (+ _template.md stub)
  systems/<slug>.md    # kind: system  — repos, services, envs (+ _template.md)
  policies/<slug>.md   # kind: policy  — review, deploy, security, voice (+ _template.md)
  glossary.md          # kind: glossary — term sections with anchors
  decisions/log.md     # kind: decision-log — append-only table (id · date · decision · owner · links)
  digests/YYYY-WW.md   # kind: digest — machine-written (Layer 1); the only agent-originated content
```

Frontmatter (every page; lint warns, never blocks — §5):

```yaml
---
kind: team              # org|team|system|policy|glossary|decision-log|digest
title: Payments squad
owner: alice@acme.com   # accountable human
updated: 2026-07-22
status: active          # active|draft|deprecated
links: [../systems/billing-api.md]   # relative, link-based relationships
source: interview       # interview|human|org-analyst (F23 adds: consolidation)
---
```

### 4.2 Tracing-metadata convention (Layer 1) — the contract

Canonical table; F08/F16/F18/F23 tables must match this one (drift is a build failure — task 12). Keys ride in `metadata` at create time and are filterable in LangSmith:

| Key | Values | Stamped by | Where |
|---|---|---|---|
| `task_type` | `coding \| research \| writing \| curation` (F15 may extend) | `packages/sdk` stamping helper (composer) | `threads.create` + `runs.create` metadata ([F08 §4](./08-task-inbox.md)) |
| `agent` | assistant slug/id | SDK helper; cron payload for schedule fires ([F18 §4.3](./18-schedules-and-activity.md)) | thread + run |
| `actor` | actor id (email/subject) | **agent middleware** `tracing_convention.py` from MDA `runtime.identity` ([research 20](../../research/20-gapfill-mda-api.md) fact 13) — the client can't know it authoritatively; platform `metadata.owner` is the enforcement twin | run |
| `tenant` | workspace/tenant id | agent middleware, same source | run |
| `repo` | `owner/name` (coding tasks; supersedes doc 02 §10's `context` — §9-7) | SDK helper | thread + run |
| `surface` | `web \| desktop \| mobile \| schedule \| dcode \| webhook` | SDK helper; F18 cron payload stamps `schedule` | thread + run |
| `deepwork_task_id` / `deepwork_schedule_id` | UUID / cron id | SDK helper / cron payload | thread ([F08](./08-task-inbox.md), [F18](./18-schedules-and-activity.md)) |
| `rubric`, `rubric_source`, `rubric_verdict`, `verification_override` | per [F16 §4](./16-verification-and-rubrics.md) | composer + RubricMiddleware | run/thread (F16 owns semantics) |
| `hitl_outcome` | `approved \| edited \| rejected \| responded` (worst outcome wins per run) | **proposed**: agent middleware at interrupt resolution — feasibility §9-13, coordinate F10/F14 | run |

Split rationale: the **SDK stamps what the client knows** (task shape, origin), **middleware stamps what only the runtime knows** (identity, HITL outcomes); schedule fires get their stamps from the cron payload since no client is present. Verification that create-time metadata reaches trace-level filters for root + child runs is §9-6.

### 4.3 External calls (verified surfaces only)

| Call | Use | Status |
|---|---|---|
| `POST /api/v1/sessions/{id}/insights/configs` (`schedule_cron`) · `POST .../configs/generate` | Insights provisioning (§3.5) | Verified beta REST ([research 15](../../research/15-org-intelligence.md)); full payload schema + entitlement signal → §9-2/-4 |
| Context Hub directory get/commit (`/v1/platform/hub/repos/`) | org-memory read/commit | Verified ([research 20](../../research/20-gapfill-mda-api.md) fact 1); org-memory repo location + conflict semantics → §9-8 |
| `POST /runs/crons`(`/search`) on the deployment | org-analyst schedule | Verified; CRUD caveats owned by [F18](./18-schedules-and-activity.md) |
| Automations/rules CRUD | rule provisioning | **Unverified — recipe-card fallback until §9-3 resolves; do not guess in code** |
| `POST /runs/query` | org-analyst reads (via langsmith-mcp-server only) | Verified limits: 10/10s ≤7d · 3/10s >7d · 1/10s full-text/child ([research 15](../../research/15-org-intelligence.md)); **no Deep Work UI surface ever calls it** (F18 §3.5 shares this rule) |

### 4.4 `apps/server` routes (proposed here, owned by F28)

| Route | Purpose |
|---|---|
| `GET /api/org-memory/tree` · `GET /api/org-memory/file?path=` | Hub reads (shares F17's Hub proxy) |
| `POST /api/org-memory/commit` `{files[{path,content}], message, run_id?}` | Interview commits, human edits, digest filing; enforces `org-memory/**` prefix, size caps, `run_id` idempotency |
| `POST /api/insights/provision` · `POST /api/automations/provision` | Glue wrapping §3.5/§3.6 (cost confirm, gating detection, per-workspace iteration) |
| `POST /hooks/langsmith/{grant}` (grant ↦ workspace, [F28 §3.4](./28-backend-glue-service.md)) | Automation-webhook ingest → F19 pipeline (payload schema §9-11) |

## 5. Edge cases & failure modes

| Case | Behavior |
|---|---|
| **Free-tier org (no Insights)** | Provisioning panel degrades per §3.5-4; digest path unaffected; copy names the plan gate honestly — never a dead button |
| **org-memory repo missing** | Agents run fine (mount simply absent); Settings shows "not seeded" empty state + interview CTA; first commit creates the tree; org-analyst still files digests (commit creates `digests/`) |
| **Malformed org-memory file** (bad frontmatter) | Browser falls back to raw-markdown render with a lint banner — never crashes; commit route lint warns, doesn't block; org-analyst skill says skip-and-note malformed pages |
| **Digest agent run fails** | F19 `task.failed` push; no digest committed; next week's prompt covers the gap as two sequential ≤7d windows (§3.3 rate budget); digest notes the covered range |
| **Digest filing webhook lost/duplicated** | F19 treats webhooks at-least-once; filing is idempotent on `run_id`; a missed webhook is caught by the next Settings visit (panel reconciles digest list vs schedule history) |
| **Insights plan downgraded after scheduling** | Reports stop platform-side; panel shows last-report timestamp + degraded copy on next entitlement check |
| **Very large org** (sweep exceeds budget) | Skill caps reads, degrades to stats-level digest with a "sampled" banner; Bulk Export recipe is the documented escape hatch (§3.3) |
| **Multi-workspace org (O-011)** | Insights/automations/projects are per-workspace: provisioning iterates workspaces under the org-scoped key + `X-Tenant-Id`; one org-analyst + digest tree per workspace; whole-org rollup deferred (§9-12) |
| **Duplicate provisioning** (two admins) | Org-analyst create checks `POST /runs/crons/search` for `org-analyst-weekly` first; Insights save lists existing configs — both idempotent |
| **`mda deploy` clobbers the UI-provisioned cron** | Shared risk with F18 §10-R1: template also ships as `schedules/org_analyst.py` in `packages/agent` so project-origin deploys reconcile it; UI-provisioned instances carry F18's warning banner |
| **Interview abandoned mid-way** | Thread persists; resumable from Settings; committed pages stay, stubs remain `status: draft` |
| **Hub commit conflict** (concurrent edit) | Server re-fetches, re-diffs, prompts re-confirm (exact Hub conflict semantics §9-8); never silent overwrite |

## 6. Security & privacy

- **Read-only org memory is load-bearing**: MDA runtime-denies agent writes at `/memories/org` — the documented shared-state prompt-injection defense ([research 15](../../research/15-org-intelligence.md)). Deep Work never weakens it; every write path goes through `apps/server` with an operator session, path-prefix-restricted to `org-memory/**`.
- **Digests are derived from traces** (which contain task content): the skill mandates aggregation over verbatim quotes; digest bodies render inside `UntrustedContent` ([F18 §3.6](./18-schedules-and-activity.md)) — inert HTML, click-to-load images, no synthesized actions.
- **Keys**: the langsmith-mcp-server bearer is a workspace key in deployment secrets (config plane; the org-analyst has no sandbox, and zero-secrets-in-sandbox — D-015 — is untouched). Provisioning keys never reach the browser (P-005).
- **Automation webhook ingress**: per-workspace ≥32-byte secret, constant-time compare, fast 204, body-size caps — F19's ingress discipline verbatim; payload treated untrusted end-to-end.
- **Insights = an LLM over your traces** (openai|anthropic enum): the cost-confirm step doubles as the data-processing disclosure; per-project opt-in; everything stays in the org's LangSmith (D-003 trust story) except the org's own chosen model call platform-side.
- **Interview content is the org's crown jewels**: lives only in their Hub + their traces; Deep Work stores nothing (D-003). Commit diffs shown before every write; `owner:` frontmatter keeps a human accountable per page.

## 7. Acceptance criteria

1. Fresh org: interview → review → commit produces the §4.1 tree; files readable at `/memories/org` in a live deployment; an in-agent write attempt to the mount is runtime-denied (test).
2. Every Deep Work-created run carries the §4.2 keys and each is filterable in LangSmith; schedule fires carry `surface:"schedule"` without a client present.
3. Deep-link map fully wired: each §3.4 row resolves a working LangSmith URL from `traceUrls`; P-002 audit — zero chart/analytics components in Deep Work; no UI surface issues `/runs/query` (proxy-log assert, shared with F18 AC-8).
4. Org-analyst end-to-end on a real deployment: provision (prefilled CronEditor) → fire → digest at `digests/YYYY-WW.md` with per-claim trace links → push notification → digest visible in Settings inside `UntrustedContent`. Sweep issues only sequential ≤7d-window queries (asserted from trace of the sweep itself).
5. Digest filing is idempotent: replayed completion webhook produces no duplicate commit.
6. Insights on an entitled workspace: generate → edit → save with `schedule_cron` succeeds; cost confirm shown first. On a free workspace: degraded panel, digest path intact, no dead ends.
7. Both automation recipes active (API-provisioned or recipe-card + manual, per §9-3 outcome); an injected error run produces exactly one F19 push for a Deep Work-created run (dedupe verified).
8. Malformed org-memory fixture renders raw with lint banner; browser never crashes.
9. Multi-workspace org: provisioning iterates workspaces; each gets its own project links, configs, and digest tree.
10. Cross-spec metadata tables (F08 §4, F16 §4, F18 §4.3, this §4.2) are byte-identical on shared keys (task 12 check in CI).

## 8. Task breakdown

| # | Task | Depends on | Definition of done |
|---|---|---|---|
| 1 | **M3-entry probe**: Insights REST payloads + entitlement signal + O-007 readback; rules API existence/shape; org-memory Hub location + commit-conflict semantics; project-URL/filter-param templates | beta account | §9-2/-3/-4/-5/-8/-11 answered with citations; §4.3 table updated; no invented endpoint survives |
| 2 | `org-memory/` starter template + frontmatter lint (ships in `packages/agent` assets) | — | Tree + stubs per §4.1; lint catches missing kind/owner/updated; fixture set for UI tests |
| 3 | `apps/server`: org-memory tree/file/commit routes over the Hub API | F28 skeleton, 1 | Prefix enforcement, size caps, `run_id` idempotency, conflict re-diff; integration test vs live Hub |
| 4 | SDK stamping helper + `traceUrls` (F04 home) | F04 registry | All §4.2 client-stamped keys on threads+runs; run/project URLs resolve; unit tests |
| 5 | `tracing_convention.py` middleware in `packages/agent` (`actor`/`tenant`, `hitl_outcome` if §9-13 positive) | F14, 4 | Keys visible in LangSmith on live runs incl. schedule fires; child-run propagation verified (§9-6) |
| 6 | Settings → Org intelligence panel + org-memory browser (empty/degraded/malformed states; digest list in `UntrustedContent`) | 2, 3, F17 components | All §5 UI states rendered; demo-mode fixtures work credential-free (P-004) |
| 7 | Seeding interview: skill + `curation` task template + F06 §3.7 hook + commit flow | 2, 3, F06 | AC-1 passes end-to-end; resumable; per-file commit |
| 8 | Org-analyst: skill + prompt + `schedules/org_analyst.py` + MCP registration + CronEditor prefill + digest filing route + review toggle | 3, 5, F18 CronEditor, F19 webhook | AC-4/-5 pass on a real deployment; rate-budget assert green |
| 9 | Insights provisioning: server glue + panel flow (generate/edit/save/cost/gating/readback-if-O-007) | 1, 6 | AC-6; degradation path tested against a free workspace |
| 10 | Automation rules: recipes (dataset + error-webhook), provisioning glue or recipe cards per §9-3; `/hooks/langsmith` ingest → F19 | 1, F19 pipeline | AC-7; ingress auth + untrusted handling tested |
| 11 | Multi-workspace iteration + idempotent provisioning + hardening (§5 table each tested or waived) | 3, 8, 9, 10 | AC-9; duplicate-provisioning tests green |
| 12 | Cross-spec reconciliation: convention table synced into F08/F16/F18/F23; CI check for drift | 4, 5 | AC-10; docs delta PRs opened for §9-7 rename |

## 9. Open questions

1. **O-007** — Insights report payloads readable via API or UI-only? Gates the readback card (§3.5-5); M1 probe with the beta account ([decisions](../decisions.md)).
2. **Insights entitlement signal** — what does the configs POST return on a free/Developer workspace (402? 403? feature flag in payload)? Drives §3.5-4 detection; task 1.
3. **Automations/rules REST surface** — exists publicly? Exact paths/payloads/filter grammar unrecovered by research; resolve from live docs/OpenAPI at M3 entry; recipe-cards fallback ships regardless.
4. **`schedule_cron` semantics** — timezone, minimum interval, on-save first run? Affects the default `0 6 * * 1` and its relation to the org-analyst cron.
5. **Tracing-project control** — can authors name/override the per-deployment project on MDA/classic tiers; how to resolve project id for deep links; LangSmith filter-param URL encoding for filtered views (§3.4).
6. **Metadata propagation** — does `runs.create`/cron-payload metadata reach trace-level filters on root **and child** runs, and can middleware add keys mid-run (current-run-tree write)? Determines the §4.2 stamping split's exact implementation.
7. **`context` → `repo` rename** — doc [02 §10](../02-architecture.md) lists `context`; F08/F18/this spec stamp `repo`. Ratify `repo` and amend doc 02 in the same commit (decision-log process).
8. **org-memory Hub location** — dedicated Hub repo vs `org-memory/**` prefix inside the deployment's repo ([research 15](../../research/15-org-intelligence.md) says only "Hub `org-memory/**`"); plus Hub commit conflict semantics. Blocks route implementation details (task 3).
9. **O-008 adjacency** — Hub *write* scope under LangSmith OAuth for the commit route in OAuth mode; key-mode service key is the fallback either way (F05 seam).
10. **Digest filing default** — auto-file vs review-first (`require_review_for_digests`); Tom taste call. Also digest retention (keep all vs index + prune >1y).
11. **Automation webhook payload schema** — field shapes for the rules webhook (≠ the run webhook F19 verified); needed before ingest normalization is coded.
12. **O-011** — mechanics of per-workspace iteration under org-scoped keys (enumeration endpoint, key scoping); whether a "whole org" digest rollup is wanted post-M3.
13. **`hitl_outcome` feasibility** — can agent middleware observe interrupt resolutions reliably enough to stamp it, or must F10's client stamp on `respond()`? Coordinate F10/F14.
14. **`task_type: curation`** — ratify the enum extension with F08/F15 (their tables list three values today).

## 10. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Insights beta REST churns or stays gated | High | Med | Deep links always work; provisioning is additive glue; digest path is the floor for every tier |
| Rate limits break the weekly sweep for big orgs | Med | Med | Hard in-skill budget (≤7d, sequential, stats-first); sampled-digest degradation; Bulk Export recipe documented |
| Digest quality is noise (unread = dead feature) | Med | Med | Skill template + per-claim trace links + review toggle; digest content iterated during M3 dogfood; F23 consolidation later raises signal |
| Convention drift across specs/implementations | Med | High | One canonical table (§4.2) + CI byte-diff check (task 12); stamping centralized in one SDK helper + one middleware |
| org-memory rots (stale pages mislead agents) | Med | Med | `owner`/`updated`/`status` frontmatter; org-analyst flags pages untouched >90 days in the digest; F23 is the structural fix |
| Free-tier value gap disappoints OSS users | Med | Low-Med | Digest-only path is real value; copy never dangles paid features (AC-6) |
| OKF v0.1→v0.2 drift invalidates the shape (O-009) | Low | Low | OKF-*shaped* only — plain markdown + frontmatter degrades gracefully; conformance deferred to F24 |
| `mda deploy` cron clobbering (F18 R1) | Med | Med | Template lives in `schedules/` (project-origin, reconciled by deploy); UI-provisioned copies banner-flagged |

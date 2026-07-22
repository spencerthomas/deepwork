# F17 · Fleet manager

*Deep Work feature spec · 2026-07-22 · Status: draft · Milestone: M3 · Depth: implementation-ready*

Sources: [03 · UI spec](../03-ui-spec.md) (§3.4) · [02 · Architecture](../02-architecture.md) (§6, §2–3) · [06 · Frontend implementation](../06-frontend-implementation.md) (Phase E) · [04 · Roadmap](../04-roadmap.md) (M3) · [01 · Vision](../01-vision.md) (pillar 3, cut line) · [07 · Org intelligence](../07-org-intelligence.md) (Layer 0) · [08 · deepagents feature map](../08-deepagents-feature-map.md) · [research 20 · MDA API](../../research/20-gapfill-mda-api.md) · [research 10 · open-swe/Fleet](../../research/10-openswe-fleet.md) · [research 12 · lifecycle & auth](../../research/12-lifecycle-auth-followup.md) · [research 01 · MDA & Deployment](../../research/01-managed-deep-agents.md) · [research 23 · runtime tiers](../../research/23-gapfill-runtime-tiers.md)

Stack facts applied: frontend is Next.js (D-022); control-plane calls that need org/workspace keys go through the Python FastAPI `apps/server` glue (P-005, provisional — [F28](./28-backend-glue-service.md)). Fleet CRUD is not public ([research 12](../../research/12-lifecycle-auth-followup.md)) and MDA invocation acceptance for non-beta orgs is unverified (O-003) — the manager degrades gracefully and surfaces beta caveats honestly, never papering over them ([02 §6](../02-architecture.md)).

## 1. Scope

### In scope

- **Agents index** (`/agents`): one table (cards toggle) aggregating every agent source the org has — control-plane deployments (`GET /v2/deployments`), MDA config-first agents (`/v1/deepagents/*` CRUD + health), Fleet agents (LangGraph SDK + PAT, invoke/read only), assistants per deployment, and locally connected `langgraph dev` sources ([02 §6](../02-architecture.md)).
- **Agent detail** (`/agents/[id]`) with the five tabs of [03 §3.4](../03-ui-spec.md): Overview · Configuration · Schedules · Environment · Deploy.
- **Configuration editing** as a file-first editor over the canonical deepagents project layout ([02 §3](../02-architecture.md)), backed by Context Hub repos (`/v1/platform/hub/repos/`) — diffable, versioned, with explicit draft/saved/published semantics.
- **Per-tool Auto/Ask matrix** compiling to `interrupt_on`, including its documented limits (filesystem `permissions` rules do not cover `execute`/MCP tools — [02 §3](../02-architecture.md), [08](../08-deepagents-feature-map.md) §Permissions).
- **Create flow**: template gallery → form → deploy handoff; **import/export** in the Fleet-export deepagents ZIP format, round-trip tested (v1 release criterion 4, [04](../04-roadmap.md)).
- **Graceful degradation**: every action without a public API renders as a deep link to smith.langchain.com with an honest explanation ([02 §6](../02-architecture.md): "anything not creatable via API is linked out"; beta gaps per O-003).

### Out of scope

- Schedules UX (cron editor, run history, untrusted-payload rendering) — [F18](./18-schedules-and-activity.md); F17 only embeds F18's per-agent scoped view.
- Environment editor internals (snapshot picker, `setup.sh`, egress allow-lists) — [F11](./11-execution-and-environments.md); F17 hosts its tab.
- First-run deploy wizard and MDA-availability detection — [F06](./06-onboarding-and-deploy.md); F17's Deploy tab reuses F06's deploy engine for redeploys.
- Org-memory content conventions, the read-only mount, and the propose/review loop — [F22](./22-org-intelligence-v1.md); F17's memory editor obeys F22's rules.
- Template *content* (prompts, tool sets, rubric defaults per template) — [F15](./15-task-templates.md); F17 renders the gallery.
- Fleet agent create/update — no public API ([research 12](../../research/12-lifecycle-auth-followup.md)); link-out only. O-004 (self-config-via-chat over the public run API) is the tracked post-M3 probe that could soften this. Slack/Teams channels config — cut from v1 ([01](../01-vision.md) cut line); channel *display* only, beta-flagged. Chat-to-configure builder — post-v1 ([01](../01-vision.md)).
- Approvals inbox, task loop, and `packages/agent` composition itself.

## 2. Dependencies & seams

| Direction | Spec / decision | What crosses the seam |
|---|---|---|
| needs ← | [F04 · SDK & agent sources](./04-sdk-and-agent-sources.md) | `AgentSource` registry, control-plane client, normalized types; F17 adds the `AgentSummary`/`AgentConfigModel` types (§4) |
| needs ← | [F06 · Onboarding & deploy](./06-onboarding-and-deploy.md) | The deploy engine (tarball upload / github-source, revision polling) as a callable service; F17's Deploy tab and create flow invoke it, never reimplement it |
| needs ← | [F14 · Agent package](./14-agent-package.md) | The Deep Work agent must expose `interrupt_on` through its config schema so the Auto/Ask matrix saves per-assistant ([02 §6](../02-architecture.md)); verified in §9-Q7 |
| needs ← | [F15 · Task templates](./15-task-templates.md) | Template catalog entries (Deep Work SWE · Research · Writing · blank) with per-template assistant-config payloads (D-014: templates are assistant configs, not codebases) |
| provides → | [F18 · Schedules & activity](./18-schedules-and-activity.md) | Agent context (deployment URL, assistant id, tier, capability flags) for the embedded per-agent Schedules tab (F18 owns `ScheduleList`/`CronEditor`); F17's config editor is the deep-link target for project-origin `schedules/` files |
| provides → | [F11 · Execution & environments](./11-execution-and-environments.md) | Same context object for the Environment tab; F17 renders the tab shell only |
| coordinates ↔ | [F22 · Org intelligence v1](./22-org-intelligence-v1.md) | Memory editor: `/memories/org` is read-only in the editor (writes go through F22's review loop); per-user memory slices are editable, beta-flagged |
| depends on | P-005 (provisional) → [F28](./28-backend-glue-service.md) | Org/workspace service keys (`lsv2_sk_` + `X-Tenant-Id`) live server-side in `apps/server`; the browser never holds them ([research 12](../../research/12-lifecycle-auth-followup.md)) |
| depends on | D-022 · P-002 | Routes `/agents`, `/agents/[id]?tab=…` in the Next.js App Router; nuqs URL state ([03 §3.1](../03-ui-spec.md)). P-002 folds the v0 `/config` surfaces (connectors, Auto/Ask, skills) into this agent detail |
| constrained by | [research 12](../../research/12-lifecycle-auth-followup.md) · O-004 | Fleet CRUD not public — invoke/read only; export format is the bridge ([02 §12](../02-architecture.md)); O-004 (chat-based self-config) is the tracked potential unlock |
| constrained by | O-003 | `managed_deep_agent` acceptance for non-beta orgs unverified — create/deploy paths detect and fall back via [F06](./06-onboarding-and-deploy.md); dev-channel features (per-user memory, channels) are feature-flagged per the [04](../04-roadmap.md) risk register |
| seed | [06](../06-frontend-implementation.md) §1, Phase E (D-012/P-001) | v0 concept's `/agents`, `/agents/[id]`, and connector Auto/Ask screens are the visual seed; data layer replaced wholesale |

## 3. Design

### 3.1 Agents index

Aggregation runs in `packages/sdk` over the agent-source registry; each source contributes rows independently (per-source failure isolation, §5). Columns per [03 §3.4](../03-ui-spec.md):

| Column | MDA deployment | Classic Deployment | Fleet agent | Local (`langgraph dev`) |
|---|---|---|---|---|
| Name | `/v2/deployments` name (rows carrying the `managed_deep_agent` marker, [research 20](../../research/20-gapfill-mda-api.md)) | `/v2/deployments` name | connected-source label (user-supplied; see discovery note) | source label |
| Tier badge | **MDA** | **Deployment** | **Fleet** + lock glyph | **local** |
| Model | assistant config (`provider:model`, [02 §3](../02-architecture.md)) | assistant config | Fast/Pro/Max tier if readable from assistant metadata ([research 10](../../research/10-openswe-fleet.md)); else `—` | assistant config |
| Tools count | project tools + MCP tools (`/v1/deepagents/mcp-servers` + `/mcp/tools`) | assistant schemas where exposed; else `—` | `—` (config not readable) | assistant schemas |
| Channels | 0.4.0-dev Slack channels, **beta badge** ([research 20](../../research/20-gapfill-mda-api.md)); `—` on 0.3.1 | `—` | not readable via public API → `—` (§9-Q6) | `—` |
| Schedules | `POST /runs/crons/search` on the deployment ([research 20](../../research/20-gapfill-mda-api.md)) | same | same (invoke/read scope permitting) | `—` (cron support on `langgraph dev` unverified — [F18](./18-schedules-and-activity.md) §9) |
| Last run | `threads.search` sorted by `updated_at` ([03 §3.1](../03-ui-spec.md)) | same | same | same |
| Health | `/v1/deepagents/*` health where applicable; else `GET /ok` probe + latest revision status | revision status + `/ok` | `/ok` probe | `/ok` probe |

- **Lazy columns**: tools count, schedules, last run load asynchronously per row (skeleton, then value or `—`); the index never blocks on N×M fan-out. Cache stale-while-revalidate in `packages/sdk`; stay inside the gateway budget (2000 req/10s general, [research 20](../../research/20-gapfill-mda-api.md)).
- **Fleet discovery**: no public listing API exists ([research 12](../../research/12-lifecycle-auth-followup.md) — only `GET/PUT /v1/agent-builder/integrations` is public). v1 Fleet rows come from *manually connected* sources (URL + assistant id, the connect-existing-agent pattern of [03 §3.6](../03-ui-spec.md)); auto-discovery is §9-Q5.
- **Owner-gating display**: Fleet rows show an "Invoke-only · owner-gated" chip; a PAT that is non-owner gets 404 from the agent ([research 12](../../research/12-lifecycle-auth-followup.md)) — the row stays listed in "unreachable (owner-gated)" state with an explainer, never silently dropped.
- **Cards toggle**: same data, `AgentCard` grid ([03 §4](../03-ui-spec.md) component inventory); preference persisted per user. Sidebar = agent list filter (tier, health, workspace) per the contextual-sidebar rule ([03 §2](../03-ui-spec.md)).

### 3.2 Agent detail — tabs

**Overview.** Recent runs (`threads.search` scoped to `assistant_id | graph_id`, linking into task detail), health (per §3.1), **View trace ↗** per run (LangSmith run URL — the trace is ground truth, [02 §10](../02-architecture.md)), and a provenance card: deployment URL, current revision, tier, identity preset, Context Hub repo link.

**Configuration.** File-first editor over the canonical layout ([02 §3](../02-architecture.md)); each section states what backs it and whether it is editable *for this agent*:

| Section | Backing surface | Editability |
|---|---|---|
| Instructions | `instructions.md` in the per-deployment Context Hub repo (synced by `mda deploy`, [research 01](../../research/01-managed-deep-agents.md)) | Markdown editor; save = Hub commit |
| Tools | code-defined tools (`tools/`) — read-only listing; MCP connectors — `/v1/deepagents/mcp-servers` CRUD, tool inventory via `/mcp/tools`, OAuth via oauth-provider + auth-sessions endpoints ([research 20](../../research/20-gapfill-mda-api.md)) | MCP full CRUD; code tools link to repo |
| Sub-agents | code-defined `SubAgent`s → read-only cards; file-based `subagents/` (imported Fleet-export projects) → editable | Partial, per provenance |
| Skills | `skills/<name>/SKILL.md` browser + editor (Hub-synced) | Full |
| Memory | `/memories/AGENTS.md` (Hub); per-user `/memories/user/AGENTS.md` **only on the 0.4.0-dev channel — beta badge** ([research 20](../../research/20-gapfill-mda-api.md)); `/memories/org` read-only per [F22](./22-org-intelligence-v1.md) | Edit agent memory; org memory view-only with "propose change" → F22 loop |
| Schedules (project-defined) | `schedules/` in the project source — reconciled as MDA-owned crons at deploy; `mda deploy` deletes and recreates them, clobbering UI edits ([research 20](../../research/20-gapfill-mda-api.md)) | View + [F18](./18-schedules-and-activity.md) deep-link target; edits are code-level → pending-publish tray. UI-created crons live in the Schedules tab |
| Permissions | Per-tool **Auto/Ask matrix** → `interrupt_on` (below) | Full where the agent exposes it |

*Auto/Ask matrix.* Rows = all known tools (built-ins, `execute`, `commit_and_open_pr`, MCP tools). Auto = tool absent from `interrupt_on`; Ask = `{tool: {allowed_decisions: [approve, edit, reject, respond]}}` subset per row ([02 §3](../02-architecture.md)). Compiled into the assistant's config where the agent's config schema exposes an `interrupt_on` key ([02 §6](../02-architecture.md): "`interrupt_on` config on the agent + assistant config schema") — saving creates a new assistant version (assistants API supports versioning, [research 01](../../research/01-managed-deep-agents.md)). Two documented limits rendered inline in the UI: (1) filesystem `permissions` rules guard paths but **do not cover `execute`/MCP tools** — the matrix is the only gate for those; (2) code-level `when:` predicates are not expressible in the matrix — such entries render as "conditional (code-defined)" read-only rows. Foreign agents whose config schema lacks the key get a read-only matrix + explainer.

*Save/publish semantics* (the "Context Hub mechanics"): three states, surfaced in the editor header —
1. **Draft** — unsaved editor state, autosaved locally; never leaves the browser.
2. **Saved** — Hub commit (directory get/commit API, [research 20](../../research/20-gapfill-mda-api.md)) or control-plane write (MCP servers, assistant config). Hub commits are the version history; every save shows a diff-before-commit step (files are diffable by design, [02 §6](../02-architecture.md)).
3. **Published** — changes requiring a new deployment revision (code tools, middleware, secrets) are batched into a "pending publish" tray that hands off to the Deploy tab. Whether Hub-file saves (instructions/skills/memory) take effect live or only at next deploy is unverified → §9-Q3; until resolved the UI labels Hub saves "saved — takes effect per runtime policy" rather than promising liveness.

**Schedules.** Embeds [F18](./18-schedules-and-activity.md)'s view scoped to this agent (crons API on the agent's own Agent Server); F17 passes context only.

**Environment.** Embeds F11's editor (sandbox snapshot, `setup.sh`, egress allow-list); F17 passes context only.

**Deploy.** Revision history from the control plane (Deployments v2 exposes revisions + redeploy, [research 12](../../research/12-lifecycle-auth-followup.md)); current revision status; **Deploy** button → F06 engine: tarball flow (`POST /v2/deployments/{id}/upload-url` → signed GCS PUT, 200 MB cap → revision polling) or github-source with `build_on_push` CD ([research 20](../../research/20-gapfill-mda-api.md), [research 12](../../research/12-lifecycle-auth-followup.md)). Every revision row deep-links to the corresponding smith.langchain.com deployment page. Rollback renders as "redeploy previous revision" **only if** §9-Q4 confirms the API supports it; otherwise the row shows a link-out.

### 3.3 Create flow

Template gallery (Deep Work SWE · Research · Writing · blank — content from F15) → form (name, description, `provider:model`, workspace, sandbox on/off per template, identity preset) → one of two paths, chosen automatically:

1. **New assistant on an existing Deep Work deployment** (default, instant): templates are assistant configs on the same agent, not separate codebases ([02 §3](../02-architecture.md)) — create = assistants API call, no build.
2. **New deployment**: no Deep Work deployment yet, or user opts for isolation → hand off to the [F06](./06-onboarding-and-deploy.md) wizard (which owns MDA-availability detection and the classic fallback).

### 3.4 Import / export

Canonical interchange = the Fleet-export deepagents ZIP: `AGENTS.md`, `config.json`, `tools.json`, `subagents/`, `skills/` (MIT `fleet-deepagents-export`, [research 10](../../research/10-openswe-fleet.md); designated canonical in [02 §6](../02-architecture.md)).

- **Import**: upload ZIP → validate manifest → map onto a deepagents project (the export format is a runnable project, [research 10](../../research/10-openswe-fleet.md)) → preview diff → create via §3.3 path 2. Reverse import *into Fleet* does not exist ([research 12](../../research/12-lifecycle-auth-followup.md)) — the UI says so.
- **Export**: any Deep Work-managed agent → generate the same ZIP from Hub files + config. Consume the upstream package's format; never fork it ([02 §8](../02-architecture.md) policy).
- **Round-trip acceptance test** (§7-AC8): export → import → export is semantically identical (file set + normalized content equal).

### 3.5 Graceful degradation matrix

| Action | Public API? | Behavior |
|---|---|---|
| Fleet create/update/delete | ❌ (O-004) | "Manage in LangSmith ↗" deep link; export format offered as the migration path |
| MDA thread/run invoke | Design-partner-gated during beta ([research 20](../../research/20-gapfill-mda-api.md)) | Works for the beta org; otherwise beta badge + link-out (O-003) |
| `managed_deep_agent` deploy for non-beta orgs | Unverified ([02 §6](../02-architecture.md)) | F06 detects and falls back to classic deployment |
| Per-user memory, Slack channels | 0.4.0-dev only | Feature-detected; beta badge; hidden on 0.3.1 stable |
| Fleet channel/config display | ❌ | `—` + tooltip explaining the gap |

## 4. Contracts

All verified surfaces; anything else is §9. Control-plane base = `api.smith.langchain.com`, auth `X-Api-Key` (+ `X-Tenant-Id` for org-scoped keys); calls proxied via `apps/server` (P-005). Fleet data plane = LangGraph SDK/REST at the agent URL with PAT + `X-Auth-Scheme: langsmith-api-key` ([research 12](../../research/12-lifecycle-auth-followup.md)).

| Surface | Endpoints (verified in sources) | Used for |
|---|---|---|
| Deployments v2 | `GET/POST /v2/deployments`, `POST /v2/deployments/{id}/upload-url`, revisions + redeploy ([research 12](../../research/12-lifecycle-auth-followup.md), [research 20](../../research/20-gapfill-mda-api.md)) | Index rows, Deploy tab, create path 2 |
| MDA config plane | `/v1/deepagents/*`: agents CRUD + health; `mcp-servers` CRUD + `/mcp/tools` + oauth-provider + auth-sessions; Hub directory get/commit ([research 20](../../research/20-gapfill-mda-api.md)) | Health, MCP connector editor, config commits |
| Context Hub | `/v1/platform/hub/repos/` ([02 §6](../02-architecture.md)) | Instructions/skills/memory files, diffs, history |
| Agent Server (per deployment) | assistants (+versions/schemas), `threads.search`, `POST /runs/crons(/search)`, `GET /ok` / `/info` ([research 01](../../research/01-managed-deep-agents.md)) | Assistant configs, Auto/Ask save, last-run, schedules count, health probe |
| GitHub integration | `GET /v1/integrations/github/install` → `integration_id` ([research 12](../../research/12-lifecycle-auth-followup.md)) | github-source deploys (via F06 engine) |

**Normalized SDK types** (in `packages/sdk`; wire snake_case, normalized once at the boundary per [03 §5](../03-ui-spec.md)):

- `AgentSummary { id, sourceId, name, tier: 'mda'|'deployment'|'fleet'|'local', model?, toolsCount?, channels?, schedulesCount?, lastRunAt?, health: 'ok'|'degraded'|'unreachable'|'owner_gated'|'unknown', capabilities }`
- `capabilities: { configEdit, mcpEdit, autoAskEdit, deploy, export, invoke }` — computed per tier + key scope; every UI affordance gates on a capability flag, never on tier alone.
- `AgentConfigModel`: file tree (path, kind: instructions|skill|memory|subagent|other, editable, hubVersion) + `mcpServers[]` + `autoAskMatrix { tool, mode: 'auto'|'ask'|'conditional', allowedDecisions[] }`.
- Auto/Ask compile target: `interrupt_on = { [toolName]: { allowed_decisions: ('approve'|'edit'|'reject'|'respond')[] } }` written into assistant config ([02 §3/§6](../02-architecture.md)).
- Import/export manifest: ZIP containing `AGENTS.md`, `config.json`, `tools.json`, `subagents/`, `skills/` — exact field schemas of `config.json`/`tools.json` follow the upstream `fleet-deepagents-export` package, pinned as a dependency, not restated here.

## 5. Edge cases & failure modes

- **Concurrent Hub edits**: two editors commit the same path. Hub commit-conflict semantics are unverified (§9-Q2); until known, the editor does read-before-write (re-fetch + compare the version it loaded), and on mismatch shows a three-way diff prompt (keep mine / take theirs / merge manually) instead of blind overwrite. Never last-writer-wins silently.
- **Deploy revision failure**: polling ends in a failed revision → Deploy tab shows the failure state, keeps the previous revision marked live, offers retry; build-log retrievability via API is unverified (§9-Q4) → link-out to the smith.langchain.com revision page meanwhile.
- **Permission-denied on org keys**: 403 from control plane (org-scoped key missing `X-Tenant-Id`, PAT lacking workspace) → the affected source degrades to read-only rows with a "key lacks access — fix in Settings" banner; other sources unaffected.
- **Mixed-tier orgs / partial failures**: each source fetch is isolated; a down deployment yields an "unreachable" row group, not an empty index. Empty state teaches the next action ([03 §7](../03-ui-spec.md)).
- **Fleet owner-gating**: non-owner PAT → 404 ([research 12](../../research/12-lifecycle-auth-followup.md)) → `owner_gated` health state with explainer (workspace members may be read-only; the UI never retries aggressively).
- **Channel-version skew**: 0.3.1 stable vs 0.4.0-dev feature detection failure → beta features hidden, never broken controls (O-003).
- **Import hazards**: ZIP path traversal (zip-slip), oversized archives, missing manifest files → validated server-side (P-005) before any file is written; tarball builds exceeding the 200 MB cap fail pre-upload with a size report.
- **Foreign agents** (deployments Deep Work didn't create): unknown config schema → Configuration tab renders what the assistant schema exposes, read-only otherwise; no writes to agents we can't model.
- **Rate limiting**: index fan-out is batched + cached; on 429 the SDK backs off and the UI shows stale-data timestamps rather than spinners.

## 6. Security & privacy

- **Key custody**: org/workspace service keys server-side only in `apps/server` (P-005); per-user PATs stored via the server proxy by default, client-side only in local mode with the on-screen trust story ([03 §3.6](../03-ui-spec.md)). No key ever reaches the client bundle.
- **Owner-gating respected**: Fleet access is display + invoke within granted scope; Deep Work never attempts to enumerate or bypass gated resources (LangSmith RBAC/governance is respected, not managed — [01](../01-vision.md) non-goals).
- **MCP connector secrets**: bearer tokens and OAuth client secrets are write-only fields — submitted to `/v1/deepagents/mcp-servers`, never echoed back into the form; per-user third-party tokens are brokered by LangSmith Agent Auth and never stored by Deep Work ([02 §5](../02-architecture.md)).
- **Untrusted file content**: memory/instructions files can be agent-written ([research 10](../../research/10-openswe-fleet.md): Fleet agents self-update files) — rendered as inert markdown (no script/active content), consistent with the untrusted-content boundary stance ([02 §10](../02-architecture.md)).
- **Imported ZIPs are untrusted input**: validated, size-capped, path-sanitized server-side; imported `config.json` is schema-checked before any control-plane write.
- **Provenance everywhere**: every config surface shows its Hub version and every run links its trace; Deep Work stores no agent data of its own ([01](../01-vision.md), [02 §10](../02-architecture.md)).

## 7. Acceptance criteria

1. Index renders rows from all four tiers simultaneously against a mixed org (MDA + classic + connected Fleet + `langgraph dev`), with per-source failure isolation demonstrated by killing one source.
2. All eight columns populate per the §3.1 mapping; unknown values render `—` with tooltips, never fake data.
3. Fleet rows show the invoke-only/owner-gated chip; a non-owner PAT produces the `owner_gated` state, not a dropped row or a crash.
4. Editing `instructions.md` produces a Hub commit with a diff-before-commit step; the commit appears in the file's version history in the UI.
5. The Auto/Ask matrix round-trips: setting a tool to Ask produces the expected `interrupt_on` entry in a new assistant version, verified by an interrupt firing on the next matching tool call against a `langgraph dev` deployment; the `execute`/MCP-not-covered-by-`permissions` note is visible in the matrix UI.
6. MCP connector CRUD works end-to-end (add server → tools appear via `/mcp/tools` → OAuth session completes via the auth-sessions flow); secrets are never returned to the client (verified in network traces).
7. Deploy tab lists revisions, triggers a redeploy through the F06 engine, and surfaces a failed revision without disturbing the live one.
8. **Round-trip test**: export a Deep Work agent → import the ZIP → export again → file sets and normalized contents are equal (CI-automated).
9. Every non-API-creatable action (Fleet CRUD, gated MDA features) renders a smith.langchain.com deep link with an explanation; beta features carry visible badges (O-003/O-004 audit).
10. M3 exit holds: an org's agents are manageable from Deep Work without touching smith.langchain.com except gated Fleet CRUD ([04](../04-roadmap.md) M3); v1 criteria 3–4 (Fleet agent driven from Deep Work; config round-trips through Fleet-export) pass.

## 8. Task breakdown

| # | Task | Depends on | Definition of done |
|---|---|---|---|
| 1 | `packages/sdk`: `AgentSummary`/`AgentConfigModel` types + capability computation + per-source aggregation with isolation, caching, backoff | sdk data layer (catalog) | Unit tests cover all four tiers + failure isolation; AC-1 |
| 2 | Index page: `AgentTable`/`AgentCard` ([03 §4](../03-ui-spec.md)) wired to task 1; lazy columns; cards toggle; sidebar filters; nuqs URL state | 1 | AC-2, AC-3 |
| 3 | Overview tab: recent runs, health, provenance card, trace links | 1 | Trace link on every listed run |
| 4 | Hub file service in `apps/server` (P-005): directory get/commit proxy, version listing, conflict detection (read-before-write) | — | AC-4; conflict path unit-tested |
| 5 | Configuration tab shell + instructions markdown editor + skills SKILL.md browser/editor | 2, 4 | AC-4 |
| 6 | Memory section: `/memories/AGENTS.md` editor; per-user memory behind 0.4.0-dev feature detection + beta badge; org-memory read-only + F22 handoff | 5, F22 conventions | Beta gating verified against 0.3.1 and 0.4.0-dev deployments |
| 7 | MCP connectors editor: mcp-servers CRUD, `/mcp/tools` inventory, oauth-provider + auth-sessions flow | 4 | AC-6 |
| 8 | Auto/Ask matrix: schema detection, compile to `interrupt_on`, assistant-version save, limits messaging | 5 | AC-5 |
| 9 | Schedules + Environment tab shells passing agent context to F18/F11 embeds | 2, F18, F11 | Tabs render embedded views with correct scoping |
| 10 | Deploy tab: revision history, redeploy via F06 engine, failure surfacing, deep links | F06 engine | AC-7 |
| 11 | Create flow: gallery (F15 data) → form → assistant-config path; deployment path hands to F06 | 1, F15, F06 | Both §3.3 paths produce a working agent |
| 12 | Import/export: ZIP validation (server-side), project mapping, export generation, CI round-trip test | 4, 11 | AC-8 |
| 13 | Degradation + beta-badge audit across all surfaces (O-003/O-004) | 2–12 | AC-9; AC-10 checklist run |

## 9. Open questions

1. **MDA run/thread API shape** — the design-partner `/v1/deepagents` invoke endpoints are unpublished ([research 20](../../research/20-gapfill-mda-api.md)); does "last run" for MDA rows come from the deployment's Agent Server `threads.search` in all cases, or a gated surface for some?
2. **Hub commit concurrency** — does the Hub directory get/commit API expose a base-version/ETag conflict check, or must the client diff defensively (§5 mitigation)? Also: exact repo naming/layout of the per-deployment Hub repo beyond what `mda deploy` syncs.
3. **Hub-save liveness** — does the MDA runtime read `instructions.md`/skills from Context Hub live between revisions, or only at deploy-time sync ([research 01](../../research/01-managed-deep-agents.md) documents the sync direction only)? Determines whether "Saved" means live.
4. **Rollback & build logs** — Deployments v2 lists "redeploy" ([research 12](../../research/12-lifecycle-auth-followup.md)); can it target a *prior* revision (true rollback), and are revision build logs readable via API?
5. **Fleet enumeration** — is there any supported way to list a workspace's Fleet agents (the unpublished "Fleet API" behind smith.langchain.com, [research 12](../../research/12-lifecycle-auth-followup.md))? v1 ships connect-by-URL; also: could Fleet publish webhooks (config + base64 ZIP, [research 10](../../research/10-openswe-fleet.md)) drive auto-import?
6. **Fleet metadata readability** — are model tier/channels/tools visible to a reader via assistant metadata on the Fleet Agent Server, or fully opaque (§3.1 shows `—` today)?
7. **`interrupt_on` in assistant config** — confirm the Deep Work agent can expose `interrupt_on` through its config schema so the matrix is per-assistant (template-level) rather than requiring a revision; and how `/v1/deepagents` config-first agents overlap with `/v2/deployments` MDA rows in the index (dedup key).
8. **Decision registry** — `../decisions.md` was not yet in the tree when this spec was written; D-022/P-005/O-003/O-004 are cited per the catalog conventions and must be re-verified against the registry when it lands.

## 10. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| MDA beta churn (0.4.0-dev weekly shifts, [04](../04-roadmap.md) risk table) | Config editor breaks against dev-channel deployments | Feature detection everywhere; canary deployment in CI; beta badges make partial support honest (O-003) |
| Fleet CRUD stays closed past v1 (O-004) | "Fleet-like manager" perception gap | Export format as the bridge; link-outs; LangChain relationship as the unlock ([02 §12](../02-architecture.md)) |
| Hub API semantics differ from assumptions (Q2/Q3) | Save/publish model reworked | Semantics isolated in the `apps/server` Hub service (task 4); UI language stays non-committal until verified |
| Config drift: Hub files vs deployed revision vs assistant versions | Users edit files that don't affect the live agent | Provenance header on every editor (Hub version + live revision); pending-publish tray makes the gap explicit |
| Foreign-agent config diversity | Editor crashes or, worse, corrupts configs it doesn't understand | Capability flags gate every write; unknown schemas are read-only by default |
| Index fan-out vs gateway rate limits | Sluggish or throttled index for large orgs | Lazy columns, caching, batch scheduling; measured against the published limits ([research 20](../../research/20-gapfill-mda-api.md)) |
| Scope creep toward full Fleet parity ([04](../04-roadmap.md) risk table) | M3 overruns | The §1 cut list is the contract; anything more needs a catalog/decision entry |

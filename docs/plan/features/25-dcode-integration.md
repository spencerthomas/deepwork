# F25 · dcode integration

*Deep Work feature spec · 2026-07-22 · Status: draft · Milestone: M3 (hooks activity: v2, design-complete) · Depth: implementation-ready*

Sources: [02 · Architecture §9](../02-architecture.md) (also §3–§6, §10) · [04 · Roadmap M3 + backlog](../04-roadmap.md) · [research 14 · dcode](../../research/14-dcode.md) · [research 02 · deepagents harness](../../research/02-deepagents-harness.md) · [08 · feature map](../08-deepagents-feature-map.md) · [decisions](../decisions.md) (D-013, D-005, D-016, P-002, P-005)

## 1. Scope

Deep Work builds **no CLI** — `dcode` (`deepagents-code`, OSS, deepagents-based, LangSmith-traced) is the local companion, the way Claude Code CLI pairs with its web surface (D-013; [02 §9](../02-architecture.md)). This spec owns the integration surfaces on the Deep Work side:

| In scope (M3, v1) | Out of scope (neighbor) |
|---|---|
| **Continue-in-terminal handoff**: run-panel action → `dcode --sandbox langsmith --sandbox-id <thread-sandbox>` reattaches to the thread's LangSmith sandbox; preconditions, disabled states, divergence semantics | Sandbox lifecycle, env chip, `GET /api/threads/{id}/sandbox` → [F11](./11-execution-and-environments.md) (consumed here) |
| **Plugins screen**: browse/install Claude-/Codex-style plugin marketplaces (skills + MCP servers) into agent config; compat badges for cloud agents | Config-editor commit machinery (Hub commits, MCP CRUD, save/publish semantics) → [F17](./17-fleet-manager.md) (F25 drives it through F17's services) |
| **Shared conventions**: `.deepagents/AGENTS.md` + agentskills.io skills read identically by dcode and `packages/agent`; conformance fixture + docs (quickstart installs dcode) | `packages/agent` composition and AGENTS.md injection itself → [F14](./14-agent-package.md) |
| **Goals/rubrics seam** (pointer only, §3.4) | All rubric/goal machinery → [F16](./16-verification-and-rubrics.md) (D-017) |
| **v2, DESIGN-COMPLETE (§3.5, no §8 tasks)**: dcode `hooks.json` → session events POSTed to `apps/server` → Activity shows local + cloud work | Activity tab itself, `UntrustedContent`, feed aggregation → [F18](./18-schedules-and-activity.md) |

Roadmap anchor: [04 M3](../04-roadmap.md) — "`dcode` companion: *Continue in terminal* handoff (`--sandbox-id`), plugins screen wired to the Claude/Codex-compatible marketplace format."

Grounding rule for this spec: dcode facts come only from [research 14](../../research/14-dcode.md); no flag, config key, or payload beyond it is assumed — everything else is §9.

## 2. Dependencies & seams

| Dependency / seam | Direction | What crosses it |
|---|---|---|
| dcode (`deepagents-code` 0.1.x, `dcode` binary; install `curl -LsSf https://langch.in/dcode \| bash`) | consumes (D-005: never fork) | `--sandbox langsmith --sandbox-id` reattach; plugin manifests/marketplaces; `.deepagents/AGENTS.md` + SKILL.md conventions; `hooks.json` (v2) — [research 14](../../research/14-dcode.md) |
| `langchain-ai/langchain-plugins` | consumes | Cross-tool marketplace (dcode + Claude Code + Codex); preconfigured default source ([research 14](../../research/14-dcode.md); [research 02](../../research/02-deepagents-harness.md)) |
| [F11 · execution & environments](./11-execution-and-environments.md) | consumes | Thread provenance `sandbox_id`/`environment` (F11 §4.2), sandbox lifecycle states + `GET /api/threads/{id}/sandbox` (F11 §4.3–4.4) — the handoff's availability signal |
| [F09 · task detail](./09-task-detail-and-streaming.md) | provides → | *Continue in terminal* action rendered in the run-panel rail ([F07 §3.2](./07-app-shell-and-navigation.md): rail hosts run panel); F25 defines the popover content + `HandoffState` contract (§4.1) |
| [F17 · fleet manager](./17-fleet-manager.md) | drives → | Plugin installs land as Hub commits (skills) via F17's file service and `/v1/deepagents/mcp-servers` CRUD (MCP) via F17's connector editor plumbing; F17 §3.2 Configuration table gains a **Plugins** section row |
| [F07 · app shell](./07-app-shell-and-navigation.md) / P-002 | resolves | F07 §9-6 ("plugins screen placement — Settings vs Agent detail undecided") — §3.2 proposes the split; roll up to the decision log on review |
| [F12 · GitHub & git flow](./12-github-and-git-flow.md) | inherits | Proxy-injected GitHub credentials keep working for dcode-driven commands inside the reattached box (creds are per-box, not per-caller) |
| [F13 · files, diff & review](./13-files-diff-and-review.md) | interacts | Connector `tree\|file` routes read the **live** sandbox FS — dcode edits show up in the files rail/diff; stated honestly in §3.1 |
| [F16 · verification & rubrics](./16-verification-and-rubrics.md) | seam only | dcode `/goal`+`/rubric` = UX reference; engine is `RubricMiddleware` (D-017); §3.4 |
| [F18 · schedules & activity](./18-schedules-and-activity.md) | v2 seam | Local-session events render as an Activity lane inside `UntrustedContent`; `surface: "dcode"` already exists in the metadata convention ([F08 §metadata](./08-task-inbox.md)) |
| `apps/server` (P-005 → [F28](./28-backend-glue-service.md)) | build | Marketplace fetch/parse/validate routes (§4.3); v2 hooks ingest + push fan-out (§3.5) |
| [F04 · SDK & agent sources](./04-sdk-and-agent-sources.md) | extends | `HandoffState` + plugin types normalized in `packages/sdk`; marketplace registry stored like the agent-source registry (client-side per device; cross-device sync shares F04 §9-6) |

## 3. Design

### 3.1 Continue-in-terminal handoff

**Flow.** Task detail run panel shows **Continue in terminal** next to the env chip. Clicking opens a popover with: (1) the exact command in mono with a copy button, (2) the dcode install one-liner (`curl -LsSf https://langch.in/dcode | bash`, [research 14](../../research/14-dcode.md)) — always shown, since a web page cannot detect a local binary (desktop-app PATH probing is a follow-up, §9-4), (3) precondition notes (auth + divergence, below). The command is assembled from live data at popover-open time — never from page-load state — via F11's `GET /api/threads/{thread_id}/sandbox`:

```
dcode --sandbox langsmith --sandbox-id <sandbox_id>
```

Exactly the [02 §9](../02-architecture.md) command; `sandbox_id` = the thread's provenance stamp (F11 §4.2: backend `.id`, the LangSmith box name valid against `/v2/sandboxes`). Research 14 confirms `--sandbox-id` reattaches to an existing sandbox and the third-party provider protocol is `get_or_create(sandbox_id=...)`. v1 is **copy-command only** — no `dcode://` deep-link scheme is documented, so none is invented (§9-4).

**Preconditions & availability matrix** (drives `HandoffState`, §4.1):

| Condition | Action state | Popover copy |
|---|---|---|
| Non-sandbox task (research/writing templates on StateBackend, [02 §4](../02-architecture.md)) | **hidden** | — (no terminal to continue in) |
| Sandbox `ready` / `running` / `idle` (F11 §3.2 states) | enabled | normal |
| Sandbox `stopped` (filesystem kept, F11 §3.2) | enabled, flagged | "Sandbox is stopped — dcode reattach may restart it; behavior unverified (§9-2). If attach fails, send a follow-up here first to wake it." |
| Sandbox `expired` (deleted; past delete-after-stop) | **disabled** | "Sandbox expired — filesystem is gone. Send a follow-up to auto-recreate from the warm snapshot, then reattach. Unpushed work from before expiry is lost (see F11)." |
| `provisioning` / `recreating` / `setup_failed` / `unreachable` | **disabled** | state-specific: wait / retry setup in the Environment tab |
| Cloud run currently active on the thread | enabled, **warn-gated** (explicit "I understand" line in popover) | "A run is still executing in this sandbox. Terminal commands will interleave with agent commands (§5). Prefer waiting or stopping the run." |

**Auth.** dcode authenticates to LangSmith with the **user's own local credentials** — Deep Work never exports, embeds, or copies any key into the command or clipboard. Precondition copy states: "requires dcode signed in to LangSmith with access to workspace *W*" (workspace name from the agent source). Access control is the platform's: `/v2/sandboxes` is workspace-key-gated, so the sandbox id alone grants nothing (§6). dcode's exact credential surface (env var vs `config.toml` vs its credentials page, which research 14 confirms exists) is §9-1 — the popover links dcode's docs rather than guessing.

**What happens to the cloud thread — stated honestly.** Attaching dcode does not pause, fork, or notify the cloud thread. Concretely:

- The **filesystem converges, the transcript diverges**: F13's connector routes read the live box, so the files rail and diff takeover *will* show dcode's edits; the cloud thread's messages, todos, and verification state *will not* know about them. The next cloud follow-up runs against the mutated tree and discovers changes the way it discovers any external edit.
- The **branch is the merge point**: dcode-driven `git push` works through the same per-box egress proxy with F12's callback-minted tokens (credentials are injected per outbound request, not per caller), so "finish in terminal → push → review the PR in Deep Work" is the recommended round-trip, documented in the popover.
- **Deep Work cannot see the terminal session in v1** (no eventing until §3.5). On copy, the client stamps thread metadata `deepwork_handoff: {actor, at}` (threads carry metadata per [02 §5](../02-architecture.md); no Deep Work-side storage) and the thread shows an advisory "handed off to terminal" marker — labeled *advisory*: it records the copy, not the attach.
- **Observability continuity**: dcode traces its own sessions to LangSmith ([research 14](../../research/14-dcode.md)); the marker links to the workspace's tracing project as the place where terminal work is visible ([02 §10](../02-architecture.md): the trace is ground truth).

### 3.2 Plugins screen

**Format = the shared ecosystem's, consumed not invented** (D-005, D-016). dcode supports Claude- and Codex-style plugin manifests and marketplace catalogs packaging **skills + MCP servers**; sources are `gh owner/repo[@ref]`, https git URLs, marketplace JSON URLs, or local dirs; `langchain-ai/langchain-plugins` is the cross-tool registry ([research 14](../../research/14-dcode.md)). **Local-dir sources are dcode-only**: Deep Work fetches catalogs server-side (§4.3) and can never reach a directory on the user's machine, so local dirs are explicitly excluded from the Deep Work surface — not registrable in Settings, absent from `plugins.json` source kinds (§4.2); gh/git/URL is the Deep Work set (a desktop-app bridge could revisit this, §9-4). An **org marketplace is just a repo** — the same catalog installs into dcode locally (`dcode plugin install code-review@acme-tools`) and, where compatible, into cloud agents here. Exact field-level manifest/catalog schemas are resolved from the upstream format at M3 entry (task 1) — never restated or guessed here (§9-5).

**IA placement (P-002 proposal — resolves [F07 §9-6](./07-app-shell-and-navigation.md)).** P-002 folds Config into Settings + Agent detail; plugins have both an app-level and a per-agent aspect, so they split the same way:

- **Settings → Plugins & marketplaces**: manage marketplace *sources* (add gh/git/URL, remove, pin ref). `langchain-ai/langchain-plugins` ships preconfigured. Registry persists client-side per device alongside the agent-source registry (F04 pattern; no Deep Work DB per D-003); cross-device sync shares F04 §9-6.
- **Agent detail → Configuration → Plugins** (new row in [F17 §3.2](./17-fleet-manager.md)'s section table): the per-agent *installed* set — enable state, version/ref, artifact list, update/uninstall — plus the "Browse marketplace" entry point. Install always targets an agent, so the browse takeover is reachable from the agent context (and from Settings, which then asks "install into which agent?").

**What "install" means per artifact type** — the core semantic table:

| Artifact in plugin | Install action (cloud agent) | Backing surface | Cloud caveat |
|---|---|---|---|
| Skill (`SKILL.md` dir, agentskills.io spec) | Copy the skill directory into the agent's `skills/` — a Context Hub commit through F17's file service (diff-before-commit, version history) | `/v1/platform/hub/repos/` via F17 task-4 service | Same spec as harness + Context Hub skills ([research 14](../../research/14-dcode.md)) → generally compatible. Liveness after commit shares [F17 §9-Q3](./17-fleet-manager.md) ("saved — takes effect per runtime policy") |
| MCP server (remote HTTP/SSE) | Register via `/v1/deepagents/mcp-servers` CRUD; tool inventory via `/mcp/tools`; OAuth via auth-sessions ([F17 §3.2 Tools row](./17-fleet-manager.md)) | MDA config plane | Compatible — [02 §3](../02-architecture.md) connectors are remote HTTP/SSE with bearer |
| MCP server (stdio/local command) | **Not installable on cloud agents** — there is no local process to run ([02 §9](../02-architecture.md): plugins usable in cloud agents only "where remote-MCP/skills-compatible") | — | Badged **local-only (dcode)**; install button replaced by the dcode CLI command to run locally |

Every plugin card computes a **compat badge** from its manifest: `cloud` (all artifacts installable) · `partial` (e.g. skills yes, stdio MCP no — install proceeds with an explicit list of what is skipped) · `local-only`. Uninstall reverses the same writes (Hub delete commit + mcp-server delete). Install/uninstall provenance is recorded file-first in **`plugins.json`** at the agent-project root (§4.2) so installs deploy with the agent, diff in git, and round-trip through Fleet-export like all other config ([02 §6](../02-architecture.md)); alignment with dcode's own local install-state format is §9-6.

Browse flow: marketplace catalogs are fetched and parsed **server-side** (`apps/server`, §4.3) — never in the browser — for CORS, size caps, and schema validation (same untrusted-input posture as F17's ZIP imports). Screens: marketplace list → plugin cards (name, description, artifacts, compat badge, source ref) → detail (README rendered inert, artifact manifest) → install-into-agent picker → F17 diff-before-commit → done. Loading/empty/error states per catalog source, per the F17 per-source isolation pattern; demo mode runs on fixtures (P-004).

### 3.3 Shared conventions (dcode ↔ `packages/agent`)

- **`.deepagents/AGENTS.md` at the git root** is read by dcode and appended to its system prompt ([research 14](../../research/14-dcode.md)); `packages/agent` injects repo-level AGENTS.md for coding tasks ([02 §3](../02-architecture.md), owned by [F14](./14-agent-package.md)). F25's obligation is *conformance, not code*: a fixture repo + test asserting both sides read the identical file, and a docs page ("one AGENTS.md, three surfaces: cloud, terminal, editor") — the quickstart installs dcode as the companion ([research 14](../../research/14-dcode.md) decision 1).
- **Skills**: agentskills.io `SKILL.md` dirs are one spec across dcode (startup discovery by frontmatter, `/reload`), the harness, and Context Hub ([research 14](../../research/14-dcode.md); [08 · Skills row](../08-deepagents-feature-map.md)). The plugins screen (§3.2) is the shared distribution channel: an org marketplace repo is v1's supported way to get the same skills into both dcode and cloud agents.
- **Org skills/memory sync, both directions — v2 design task, flagged not designed** ([02 §9](../02-architecture.md)): mapping Context Hub layouts (`/memories/`, `skills/`) onto dcode's local layout (`~/.deepagents/<agent>/memories/`, `AGENTS.md`, skills dirs — [research 14](../../research/14-dcode.md)) needs a dedicated design pass. Both sides are markdown-file-first, so the mapping is tractable; nothing in v1 depends on it (§9-8). Until then, sync is manual/marketplace-mediated and the docs say so.

### 3.4 Goals & rubrics — seam only

dcode's `/goal` (agent drafts acceptance criteria → review → per-turn grading) and `/rubric` are the UX reference Deep Work adopts through [F16](./16-verification-and-rubrics.md): engine = harness `RubricMiddleware` (D-017), v1 rubric UX = F16 §3.2–3.4, v1.x goal lifecycle = F16 §3.6 (design-complete there). F25 adds nothing — this section exists so nobody re-specs it here. The only F25-adjacent fact: a goal/rubric graded in the cloud is invisible to a dcode session attached to the same sandbox (transcript divergence, §3.1) — a docs note, not a feature.

### 3.5 Local-session activity via `hooks.json` — v2 · DESIGN-COMPLETE, NO TASKS IN §8

> Status: designed here, deliberately unscheduled. Nothing in §8 implements this section. Origin: [02 §9](../02-architecture.md) "Activity (v2, optional)".

**Mechanism.** dcode `hooks.json` (`~/.deepagents/hooks.json`) subscribes external commands to lifecycle events (e.g. `session.start`, `task.complete`), passing a JSON payload on stdin, fire-and-forget ([research 14](../../research/14-dcode.md)). Deep Work ships a documented hook entry — a `curl` POST of that payload to `apps/server` (P-005 explicitly reserves "future webhook consumers") — configured by the user, from a copy-paste block in Settings. No Deep Work binary is installed; no dcode fork (D-005).

**Event shape** (`DcodeSessionEvent`, §4.4): versioned envelope carrying event name, session id, agent name, model, start/end timestamps, host label, optional title, optional LangSmith trace URL — and **nothing filesystem- or command-derived by default** (see privacy). The documented hook command forwards dcode's payload fields onto this envelope; fields dcode doesn't emit stay absent (the dcode-side payload schema per event is §9-9 — never guessed).

**Storage & display.** D-003 (no Deep Work database) is respected: `apps/server` does **not** persist events. It validates, then fans them out over the existing push/notification pipeline ([02 §7](../02-architecture.md)) to connected clients, where the Activity tab renders a **"Local sessions (live)"** lane — rows appear in real time, previews inside `UntrustedContent` ([F18 §3.6](./18-schedules-and-activity.md); external-origin content by definition), `surface: "dcode"` per the existing enum ([F08](./08-task-inbox.md)). Sessions carrying a trace URL deep-link to LangSmith, which remains the *durable* record of local work; a client that was offline simply missed live rows — stated in the UI. If durable local-session history is ever wanted, that is a decision-log change to D-003, not silent scope growth.

**Auth.** Settings mints a **hook token**: signed by `apps/server`, bound to the operator identity + workspace, shown once, revocable (server keeps only a revocation list, in config/memory). The hook command sends it as a bearer header. Rejected/absent token → 401, no event.

**Privacy — opt-in, minimized.** Local paths, prompts, and command lines are the user's machine's business: the integration is **off by default**, enabled per device by the user pasting the hook block; the default envelope excludes cwd, file paths, prompt text, and command content; an "include session titles" toggle is the only enrichment offered. The Settings screen shows a sample payload before enabling — informed consent, not fine print.

**Adoption trigger.** Build when all three hold: (1) F18's Activity tab is shipped and stable, (2) dcode's hook event catalog + payload schema are documented upstream (§9-9), (3) real demand — users asking "why doesn't Activity show my terminal work" — is observed. Sequencing: design review of the envelope with the dcode team first (OSS-first: if dcode grows a native "report to URL" hook config, prefer it and delete our curl block).

## 4. Contracts

### 4.1 `HandoffState` (`packages/sdk`, camelCase per D-011)

```ts
type HandoffState = {
  available: "hidden" | "enabled" | "enabled_warn" | "disabled";
  reason?: "no_sandbox" | "stopped" | "expired" | "provisioning" | "recreating"
         | "setup_failed" | "unreachable" | "run_active";
  command?: string;            // "dcode --sandbox langsmith --sandbox-id <id>"; assembled fresh (§3.1)
  sandbox?: { id: string; state: string; idleExpiresAt?: string }; // from F11 §4.4
  workspace: string;           // for the auth precondition copy
};
```

Derived entirely from F11's lifecycle route + thread provenance metadata; no new server state. Copy action stamps thread metadata `deepwork_handoff: {actor, at}` (advisory, §3.1).

### 4.2 `plugins.json` (agent-project root — new, owned here; file-first per [02 §6](../02-architecture.md))

| Field | Type | Notes |
|---|---|---|
| `marketplaces` | `[{id, source: {kind: "gh"\|"git"\|"url", ref}}]` | sources this agent's installs came from (subset of the device registry) |
| `installs` | `[{plugin, marketplace, version/ref, installedAt, actor, artifacts: {skills: [path], mcpServers: [name]}, skipped: [artifact]}]` | provenance for update/uninstall; `skipped` records `partial` installs honestly |

Exact plugin/manifest field names inside `artifacts` follow the upstream format once pinned (task 1, §9-5).

### 4.3 `apps/server` routes (hosted by [F28](./28-backend-glue-service.md), P-005)

| Route | Purpose |
|---|---|
| `POST /api/marketplaces/resolve` | fetch + parse + schema-validate a catalog (gh/git/URL); size-capped; returns normalized plugin list with compat computation inputs |
| `GET /api/marketplaces/{id}/plugins/{name}` | plugin detail: manifest, README (returned as text; rendered inert client-side) |
| `POST /api/agents/{agentId}/plugins/install` \| `.../uninstall` | orchestrates Hub commits (skills) + `mcp-servers` CRUD + `plugins.json` update as one reported sequence; partial-failure report per artifact (§5) |
| *(v2, design-complete)* `POST /hooks/dcode/{grant}` | authenticated event ingest → push fan-out; no persistence (§3.5) |

### 4.4 `DcodeSessionEvent` (v2, design-complete — not built in M3)

```ts
type DcodeSessionEvent = {
  v: 1; event: string;                       // dcode lifecycle event name, forwarded verbatim
  sessionId: string; agent?: string; model?: string;
  ts: string; host: string;                  // user-chosen device label
  title?: string;                            // only with the opt-in toggle
  traceUrl?: string;                         // LangSmith deep link when dcode provides it
};   // deliberately NO cwd, paths, prompts, or command text (§3.5 privacy)
```

## 5. Edge cases & failure modes

| Case | Behavior |
|---|---|
| **Stale sandbox id at copy time** (box recreated between page load and click) | Command assembled at popover-open from the live F11 route; if state changed to a disabled state, the popover re-renders the matrix row instead of a dead command |
| **Reattach race — cloud run still active** | F11's enqueue only serializes *cloud* runs; dcode exec is out-of-band, so commands can interleave in one box. v1 answer: warn-gate (§3.1 matrix), docs recommend stop-or-wait; platform-level concurrent-exec semantics are §9-3 |
| **Sandbox idle-stops mid-terminal-session** | dcode exec activity is expected to reset the idle timer like agent exec (activity-based, F11 §3.2) — assumed, verified by task 1 (§9-2); long think-time can still stop the box; whether dcode transparently restarts is §9-2 |
| **dcode version drift vs sandbox tooling** | The box was provisioned by the *cloud* environment's `setup.sh`; dcode's LLM loop runs locally and only execs remotely ([research 14](../../research/14-dcode.md) sandbox-as-tool), so drift surfaces as failing shell commands, not protocol breakage; provider capability flags live in dcode's config. Docs pin a known-good `deepagents-code` version per Deep Work release; no runtime version negotiation is invented |
| **Plugin with unsatisfiable cloud dependencies** (stdio MCP, local binaries) | Never a silent partial install: compat badge up front (§3.2); `partial` installs list skipped artifacts in the confirm step and record them in `plugins.json.skipped`; `local-only` shows the dcode command instead of an install button |
| **Skill name collision** (`skills/<name>` exists) | Install pauses with rename-or-overwrite choice; overwrite goes through F17's diff-before-commit so the loser is visible in Hub history |
| **Malformed / oversized / hostile catalog** | Server-side validation (§4.3) rejects with a per-source error row; other marketplaces unaffected (F17 per-source isolation pattern); catalogs are untrusted input end-to-end |
| **Install partial failure** (Hub commit ok, MCP registration fails) | Sequence reported per artifact; completed artifacts stand, failed ones marked with retry; `plugins.json` records actual end state, never intent |
| **Marketplace ref moved / plugin yanked** | Installed agents keep working (artifacts are copied/registered, not referenced live); update check shows "source ref gone" and offers pin-to-installed |
| **Handoff on a foreign thread** (no Deep Work provenance stamps) | No `sandbox_id` metadata → action hidden (`no_sandbox`), same as non-sandbox tasks; never guess a box name |

## 6. Security & privacy

- **No credential ever crosses the handoff**: the command contains a sandbox id only; dcode uses the user's own local LangSmith credentials, and `/v2/sandboxes` access is enforced by workspace auth — the id is not a bearer capability. Deep Work's keys stay in `apps/server` (P-005) and are never rendered client-side.
- **Attach = the box's proxy scope, human-driven**: whoever attaches can make outbound calls with proxy-injected credentials (e.g. push via F12's installation tokens) — acceptable because attach requires workspace-level LangSmith access the user already holds; noted in docs so orgs understand terminal attach ≈ sandbox-level trust. dcode-driven work is traced by dcode to LangSmith, preserving auditability outside the cloud thread.
- **Plugins are third-party supply chain**: catalogs/manifests validated server-side, size-capped, schema-checked before any write (F17 §6 import posture); README/skill content renders inert (no script/active content); MCP registration shows the exact remote URL + auth mode before install; org marketplaces are repos, so org review = a PR review. Refs are pinned (`@ref`) in `plugins.json`; "latest" is an explicit user choice, never a default.
- **Hooks (v2)**: opt-in per device, minted revocable token, TLS via the standard `apps/server` ingress, payload minimized by construction (§3.5, §4.4) — local paths/commands leave the machine only if a future envelope version adds them behind a new explicit opt-in.
- No new storage anywhere in M3 scope: handoff stamps ride thread metadata; plugin state is files in the agent project; marketplace registry is device-local (D-003 intact).

## 7. Acceptance criteria

1. A coding task with a live sandbox shows *Continue in terminal*; the copied command reattaches a locally-authenticated dcode to the **same** box (verified: file created via dcode `execute` is visible in the F13 files rail without any cloud run).
2. The §3.1 availability matrix is fully exercised: hidden on research/writing tasks and foreign threads; disabled with correct copy on `expired`/`setup_failed`/`unreachable`/`provisioning`; flagged on `stopped`; warn-gated while a run is active.
3. Copy stamps `deepwork_handoff` metadata and the advisory marker renders with a tracing-project link; no LangSmith key or token appears in the popover, clipboard, or DOM (network/DOM audit).
4. After dcode-side edits + push, the Deep Work thread's next follow-up proceeds against the mutated tree and the PR reflects terminal commits — the documented round-trip works end-to-end.
5. Plugins: `langchain-ai/langchain-plugins` browses out of the box; an org marketplace added by gh ref browses identically; a skills-only plugin installs into an agent as a Hub commit visible in F17's version history; a remote-MCP plugin registers and its tools appear via `/mcp/tools`.
6. A plugin containing a stdio MCP server is badged `local-only`/`partial` and cannot reach a cloud install; skipped artifacts are listed in the confirm step and recorded in `plugins.json`.
7. Uninstall reverses installs cleanly; export → import of the agent (F17 round-trip) preserves installed skills and `plugins.json`.
8. Placement audit: marketplaces manageable only in Settings; per-agent installs only in Agent detail → Configuration → Plugins (P-002 proposal as built).
9. Conformance fixture: one repo's `.deepagents/AGENTS.md` is demonstrably read by both dcode and a `packages/agent` coding task (assert prompt injection on both sides).
10. Demo mode: plugins screens and the handoff popover fully render from fixtures with zero credentials (P-004).
11. v2 boundary audit: no hooks ingest route, token minting, or Activity lane ships in M3 (§3.5 is design-complete only).

## 8. Task breakdown

M3 items only — §3.5 (hooks activity) deliberately has no tasks.

| # | Task | Depends on | Definition of done |
|---|---|---|---|
| 1 | **M3-entry dcode probe**: verify `--sandbox-id` semantics against live LangSmith boxes (stopped/expired behavior, idle-timer reset, working-dir on attach), dcode's LangSmith credential surface, and pin the plugin manifest/catalog schema from `langchain-ai/langchain-plugins` — never invent | dcode installed; beta workspace | §9-1/2/3/5/6 answered with citations or upstreamed as issues ([02 §8](../02-architecture.md)); schema pinned as a versioned dependency note |
| 2 | `packages/sdk`: `HandoffState` derivation (F11 route + provenance metadata), fixtures for every matrix row | 1; F11 §4.3 route | Unit tests cover all §3.1 states incl. foreign-thread hidden case |
| 3 | Run-panel action + popover (F09 seam): live command assembly, copy + metadata stamp, install nudge, auth/divergence copy, warn-gate | 2; F09 rail exists | AC 1–3; a11y pass; states driven solely by `HandoffState` |
| 4 | `apps/server` marketplace routes: fetch/parse/validate (gh, git, URL), size caps, normalized plugin list + compat inputs | 1 (schema pinned) | §4.3 routes green with hostile-catalog test fixtures (§5) |
| 5 | Plugins UI: Settings marketplace registry (device-local, default source preconfigured) + Agent detail Plugins section + browse takeover with compat badges | 4; F17 tabs exist | AC 5 browse paths, AC 8 placement audit, demo fixtures (AC 10) |
| 6 | Install/uninstall orchestration: skills → F17 Hub file service commits; MCP → `mcp-servers` CRUD; `plugins.json` writes; partial-failure reporting | 4, 5; F17 tasks 4/7 | AC 5–7; collision + partial-failure cases from §5 tested |
| 7 | Shared-conventions conformance fixture + docs: AGENTS.md/SKILL.md fixture repo test; companion docs page; quickstart installs dcode | F14 AGENTS.md injection | AC 9; docs merged; F16 seam pointer (§3.4) cross-linked, nothing duplicated |
| 8 | Hardening: §5 fixture matrix, supply-chain audit against §6, stale-id race test, AC 11 v2-boundary audit | 3, 6 | Every §5 row has a test or explicit waiver; AC 2, 6, 11 |

## 9. Open questions

1. **dcode LangSmith credential surface for reattach** — env var, `config.toml`, or the credentials page ([research 14](../../research/14-dcode.md) confirms the page exists, not the precedence)? Determines the popover's auth copy. Task 1.
2. **`--sandbox-id` vs stopped/expired boxes** — does `get_or_create(sandbox_id=...)` restart a stopped box, error, or create fresh? Does dcode exec reset the idle TTL like agent exec? Gates the `stopped` matrix row's copy. Task 1.
3. **Concurrent exec semantics** — platform behavior when dcode and a cloud run exec into one box simultaneously (interleave? lock? undefined?). Determines whether warn-gate can relax or must hard-block. Task 1 + F11 §9-4 overlap.
4. **Deep link / desktop integration** — no `dcode://` scheme is documented; should the Tauri app (F21) shell out to dcode or probe PATH for the install nudge? Same bucket: whether the desktop app could bridge dcode-local marketplace dirs (excluded from the web surface, §3.2). Post-M3, coordinate with F21.
5. **Plugin manifest/catalog exact schemas** — Claude-style vs Codex-style field differences and the `langchain-plugins` catalog format; pinned by task 1, never restated in this spec.
6. **`plugins.json` alignment with dcode's local install state** — can one format serve both (or a documented mapping), so an org marketplace install shows identically in `dcode plugin --json` and Deep Work? Upstream conversation.
7. **Skill-install liveness** — Hub commit → running agent pickup; shared verbatim with [F17 §9-Q3](./17-fleet-manager.md).
8. **Org skills/memory bidirectional sync (v2)** — the [02 §9](../02-architecture.md) memory-layout mapping design task (`~/.deepagents/<agent>/` ↔ Context Hub); blocks nothing in M3.
9. **hooks.json event catalog + payload schemas (v2)** — research 14 documents the mechanism and two example events only; the §3.5 envelope forwards, it does not guess. Adoption trigger condition 2.
10. **Marketplace registry sync across devices** — shared with [F04 §9-6](./04-sdk-and-agent-sources.md) (client-side registries vs file-first org visibility under D-003).

## 10. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| dcode is 0.1.x and moves weekly — flags/plugin/hooks surfaces shift under us | High | Med | Only two flags consumed (§3.1); task-1 probe at M3 entry; docs pin a known-good version; gaps go upstream, never forked (D-005, [02 §8](../02-architecture.md)) |
| Handoff dead-ends (expired sandbox, auth confusion) sour the flagship "zero new infrastructure" story | Med | Med | Availability matrix never shows a dead command; every disabled state teaches the recovery action; auth precondition named before copy |
| Transcript/filesystem divergence confuses users ("the agent ignored my terminal work") | Med | Med | Honest popover copy, advisory handoff marker, branch-as-merge-point docs (§3.1); v2 hooks close the visibility gap if demand confirms |
| Plugin-format churn upstream (Claude/Codex manifest evolution) | Med | Med | Schema consumed as a pinned dependency (task 1), parsed server-side behind one route; UI reads normalized types only |
| Marketplace supply chain — a hostile plugin lands skills/MCP config into an org agent | Med | High | Server-side validation, ref pinning, diff-before-commit on every skill write, explicit MCP URL/auth confirmation, org-marketplace-as-repo puts review in git (§6) |
| P-002 placement proposal rejected in review | Low | Low | §3.2 split is two thin mounts over one shared browse component; relocation is routing, not rework (same posture as [F07 §3.2](./07-app-shell-and-navigation.md)'s P-002 reversal note) |
| v2 hooks perceived as surveillance of local machines | Low | High | Off by default, per-device opt-in, minimized envelope, sample-payload consent screen, revocable token — designed in §3.5 before any code exists |

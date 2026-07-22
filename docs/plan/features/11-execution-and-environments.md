# F11 · Execution & environments
*Deep Work feature spec · 2026-07-22 · Status: draft · Milestone: M2 · Depth: implementation-ready*
Sources: [02 · Architecture §4](../02-architecture.md) · [04 · Roadmap M2](../04-roadmap.md) · [research 06 · Execution sandboxes](../../research/06-execution-sandboxes.md) · [research 20 · MDA API gap-fill](../../research/20-gapfill-mda-api.md) · [research 23 · Runtime tiers](../../research/23-gapfill-runtime-tiers.md) · [research 12 · Lifecycle & auth](../../research/12-lifecycle-auth-followup.md) · [research 03 · Competitor teardown](../../research/03-competitor-teardown.md) · [research 10 · open-swe/Fleet](../../research/10-openswe-fleet.md) · [03 · UI spec §3.2/§3.4](../03-ui-spec.md) · [decisions](../decisions.md)

## 1. Scope

**Owns:** the environment model (environment = named LangSmith Sandbox snapshot), the sandbox lifecycle (create/reuse/expire/recreate, `scope="thread"`), the `/v2/sandboxes` usage map (who calls what from where), `define_sandbox` wiring in `packages/agent` and its mapping to the composer's environment picker, the non-sandbox StateBackend path, environment management UX (agent detail → *Environment* tab per [UI spec §3.4](../03-ui-spec.md)), lifecycle/failure surfacing (env chip, diagnostics), and idle-TTL/cost guidance.

**Does not own** (neighbors — see [catalog](README.md)): GitHub App, installation-token minting, and the zero-token auth-proxy callback route → [F12](./12-github-and-git-flow.md); file tree, diff review, and the connector `tree|file` routes → [F13](./13-files-diff-and-review.md); task-detail thread/run-panel chrome that *hosts* the env chip → [F09](./09-task-detail-and-streaming.md); the overall `packages/agent` composition → [F14](./14-agent-package.md) (F11 owns only its `sandbox/` module); sandbox-on/off per task template → [F15](./15-task-templates.md); the `apps/server` service itself → [F28](./28-backend-glue-service.md) (F11 defines the environment/lifecycle routes it hosts); HITL approval semantics (F11 only defines what happens to a sandbox *while* an approval waits).

Milestone anchor: [Roadmap M2](../04-roadmap.md) — "thread-scoped LangSmith Sandbox backend, environment = snapshot + `setup.sh` editor".

## 2. Dependencies & seams

| Dependency / seam | Direction | What crosses it | Grounding |
|---|---|---|---|
| `langsmith[sandbox]` SDK (`SandboxClient`, `LangSmithSandbox`) | consume | create/exec/files/snapshots; GA, MIT SDK | [research 06](../../research/06-execution-sandboxes.md) facts 7, 9 |
| `/v2/sandboxes` REST (base `/v2/sandboxes/boxes`) | consume | see §3.3 usage map | [research 06](../../research/06-execution-sandboxes.md) fact 9; [research 12 §1](../../research/12-lifecycle-auth-followup.md) |
| `managed-deepagents` `define_sandbox` | consume | per-thread managed sandbox on MDA; kwargs pass verbatim to `create_sandbox` | [research 20](../../research/20-gapfill-mda-api.md) facts 12, 19 |
| `deepagents` backends (StateBackend default; sandbox backends add `execute`) | consume | non-sandbox tasks; `execute` tool | [research 06](../../research/06-execution-sandboxes.md) facts 1, 19 |
| `apps/server` (Python FastAPI glue, P-005 → [F28](./28-backend-glue-service.md)) | build | env registry API, snapshot build pipeline, lifecycle status; holds the workspace API key — the browser never calls `/v2/sandboxes` directly | P-005; [02 §6](../02-architecture.md) |
| `apps/web` (Next.js, D-022) | build | Environment tab screens, composer picker, env chip | D-022; [03 §3.4](../03-ui-spec.md) |
| F12 GitHub & git flow | seam | proxy `callbacks` config referenced from env `proxy_config`; clone/push with zero tokens in-box | [02 §4](../02-architecture.md); [F12](./12-github-and-git-flow.md) |
| F13 files & diff | seam | files channel (`values.files`) for StateBackend tasks; connector `tree|file` routes for sandbox tasks | [02 §4](../02-architecture.md); [F13](./13-files-diff-and-review.md) |
| [F09](./09-task-detail-and-streaming.md) task detail | seam | env chip data contract (§4.4) rendered in the run panel | [03 §3.2](../03-ui-spec.md) rail: "environment/sandbox chip (id, TTL)" |
| D-015 | decision | thread-scoped sandboxes, environments = named snapshots + `setup.sh`, zero secrets in-sandbox — this spec elaborates it; warm start via `capture_snapshot` (Codex's 12 h container cache cut follow-up latency ~90%) | D-015; [02 §4](../02-architecture.md); [research 03](../../research/03-competitor-teardown.md) fact 8 |

## 3. Design

### 3.1 Environment model

A Deep Work **environment** is a named recipe that resolves to LangSmith Sandbox **snapshots** — the Codex-environments mental model ([02 §4](../02-architecture.md)):

- **Base**: a Docker image reference *or* a Dockerfile (snapshots build from either — [research 06](../../research/06-execution-sandboxes.md) fact 9).
- **`setup.sh`**: provisioning script run once at sandbox provisioning (Codex-style; MDA uploads it to `/tmp/mda-setup.sh` — [research 20](../../research/20-gapfill-mda-api.md) fact 19).
- **Egress policy**: per-environment level compiling to proxy rules, surfaced in the editor as levels mirroring Claude Code's None/Trusted/Full/Custom ([research 06](../../research/06-execution-sandboxes.md) fact 10; [research 03](../../research/03-competitor-teardown.md) fact 9). Effective policy per level — `trusted` (platform default): HTTP/S to any host via the proxy, all raw TCP denied; `custom`: HTTP/S only to allow-listed hosts, raw TCP only to explicitly listed `host:port` rows (`allow_list` opens host:port), everything else denied; `full`: HTTP/S open **and** raw TCP open. Traffic matching no rule is always denied (fail-closed), and the editor requires an explicit confirmation step before saving `full` or any level broader than `trusted`. A `none` level (deny-all) is desired but unverified (§9-Q7).
- **Env vars**: plain (non-secret) key/values only. **Secrets never enter the sandbox** — credentials are injected into outbound requests by the sandbox auth proxy (`workspace_secret`/opaque header rules, and F12's callback pattern for GitHub). This is a v1 release criterion ([04 · roadmap](../04-roadmap.md) criterion 5).
- **Repo pairing**: one or more `owner/repo` the environment is built for; filters the composer picker and tells F12 which installation tokens the proxy callback may mint.

**Two snapshots per environment** (D-015 warm start):

| Snapshot | Built when | Contains | Used for |
|---|---|---|---|
| *base* | on save/"Build" in the editor | image + Dockerfile layers | cold provisioning; warm-snapshot rebuilds |
| *warm* | after a successful provisioning run (base box → `setup.sh` → `capture_snapshot`) | base + setup.sh results (toolchains, dependency caches; optionally a repo clone cache) | thread sandbox creation — follow-ups and new tasks skip setup cost |

`setup.sh` templates ship an idempotent warm-guard header (`[ -f /.deepwork-warm ] && exec true` style) so per-thread provisioning on MDA — which always runs `setup.sh` — is a no-op on a warm snapshot. Repo freshness never depends on the snapshot: threads always `git fetch`/clone at start (via the F12 proxy), so a stale warm snapshot costs time, not correctness.

**Storage (working assumption, see §9-Q8):** environment definitions are files in the agent project — `packages/agent/sandbox/environments/<name>/{env.json, setup.sh}` — so they deploy with the agent, diff in git, and round-trip through the Fleet-export format like all other config ([02 §6](../02-architecture.md) file-first principle). Snapshot IDs are workspace-side state referenced from `env.json`. Deep Work keeps its no-database v1 stance (D-003; [02 §1](../02-architecture.md)).

### 3.2 Sandbox lifecycle (`scope="thread"`)

One sandbox per thread: `define_sandbox(LangSmithSandbox, scope="thread", idle_ttl_seconds=600)`; MDA resolves it lazily per scope key `thread:{thread_id}` and caches it ([research 06](../../research/06-execution-sandboxes.md) fact 8; [research 20](../../research/20-gapfill-mda-api.md) fact 19). Parallel tasks = parallel threads = separate sandboxes ([02 §4](../02-architecture.md)); classic tiers name boxes `thread-{thread_id}` and look them up via `list_sandboxes()` ([research 06](../../research/06-execution-sandboxes.md) fact 17).

State machine (env chip states, seam to F09):

| State | Entered by | Filesystem | Exit |
|---|---|---|---|
| `provisioning` | first `execute` in a thread → `create_sandbox(snapshot_id=warm‖base, idle_ttl_seconds, proxy_config)` + `setup.sh` + repo clone | fresh from snapshot | → `ready` / `setup_failed` |
| `ready` / `running` | exec activity | live | idle timer resets on activity |
| `idle` | no activity; TTL counting down | live | → `stopped` at TTL |
| `stopped` | `idle_ttl_seconds` (default 600) elapsed | **kept** until `delete_after_stop_seconds` (~14 d default) | restart on next follow-up → `ready` |
| `expired` | delete-after-stop elapsed, or box deleted | **gone** | → `recreating` on next follow-up |
| `recreating` | auto-recreate: new box from warm snapshot + re-clone + checkout `deepwork/<task>` branch from remote | fresh | → `ready` |
| `setup_failed` / `unreachable` | provisioning or exec failure | n/a | user retry / auto-retry (§5) |

Values from [research 06](../../research/06-execution-sandboxes.md) fact 9. **What survives what:** a *stop* keeps the filesystem (uncommitted work included); a *deletion* loses everything not pushed. The recreate story leans on F12's git flow — work lives on the `deepwork/<task>` branch and the auto-draft-PR middleware pushes early ([02 §3–4](../02-architecture.md)) — so recreation is re-clone + checkout, and the UI labels the recreation event in the thread with a "work since last push was lost" warning when the agent detects a dirty-tree mismatch. Long approval waits interact with TTL; see §5.

### 3.3 `/v2/sandboxes` usage map

Surfaces per [research 12 §1](../../research/12-lifecycle-auth-followup.md) and [research 20](../../research/20-gapfill-mda-api.md) fact 20; callers per P-005 (server glue) and [02 §3](../02-architecture.md) (agent runtime).

| Surface | Called from | Purpose |
|---|---|---|
| snapshots: build from image/Dockerfile, list, delete | `apps/server` | environment editor Build/duplicate/delete |
| `capture_snapshot` (running box → snapshot) | `apps/server` (warm-build pipeline §3.1) | D-015 warm start |
| boxes: create/start/stop, list | agent runtime (via `define_sandbox`/backend) for thread boxes; `apps/server` for warm-build + "Test build" boxes | lifecycle |
| exec (`sb.run()`, streaming CommandHandle, reconnect; WebSocket variant) | agent runtime (`execute` tool) | task work; `apps/server` uses it only to run `setup.sh` during warm builds |
| files: upload/download, glob/grep | agent runtime backend (`write/read/glob/grep`) | agent filesystem tools; the *client* reads files via F13 connector routes, never directly |
| `PATCH /v2/sandboxes/boxes/{name}` proxy rules | **not used in v1** — F12 uses the `proxy_config.callbacks` mechanism instead (MDA box names are runtime-generated; [research 20](../../research/20-gapfill-mda-api.md) facts 12, 27) | — |
| TCP tunnels, service URLs (`sb.service(port)` → `browser_url`), registries, service access tokens | deferred (v1.x web-app preview feature) | listed for completeness |

The workspace API key stays in `apps/server`/agent runtime; the browser never holds it ([02 §5](../02-architecture.md) key-proxy pattern).

### 3.4 `define_sandbox` and composer mapping

`packages/agent/sandbox/__init__.py` exports the managed-sandbox declaration ([02 §3](../02-architecture.md) layout):

```python
# sandbox/__init__.py — kwargs pass verbatim to SandboxClient.create_sandbox (research 20, fact 12)
define_sandbox(
    LangSmithSandbox,
    scope="thread",
    idle_ttl_seconds=600,
    snapshot_id=...,      # resolved from the selected environment — see mapping below
    proxy_config=...,     # egress allow-list + F12 callback rules, from env.json
)
```

**Composer → sandbox mapping.** The New-task composer's environment picker ([03 §3.1](../03-ui-spec.md)) writes `configurable.environment` (env name) into the run config. On **classic tiers** the async graph factory receives the `RunnableConfig` and resolves snapshot/proxy per run ([research 06](../../research/06-execution-sandboxes.md) fact 17) — full per-task environment choice. On **MDA**, whether `define_sandbox` kwargs can vary per run is unverified (§9-Q1); v1 fallback: one environment per MDA deployment (selection collapses to agent selection), with per-run choice lighting up if the beta answer is yes. Task templates without sandboxes (research/writing — assistant configs over one agent, D-014, [F15](./15-task-templates.md)) simply have no `execute` tool and run on the default **StateBackend** — zero infra, thread-scoped virtual FS, files still visible through the `values.files` channel in [F13](./13-files-diff-and-review.md) ([02 §4](../02-architecture.md); [research 06](../../research/06-execution-sandboxes.md) fact 1).

### 3.5 Environment management UX

IA: **Agents tab → agent detail → *Environment* tab** ([03 §3.4](../03-ui-spec.md): "sandbox snapshot picker, `setup.sh` editor, egress allow-list"). Screens:

- **List**: name · base image · paired repos · warm snapshot age · last build status · boxes now running. Empty state teaches "create your first environment".
- **Create/edit**: base image pick (curated defaults + custom ref/Dockerfile) · `setup.sh` editor (mono, 14 px per [03 §1.2](../03-ui-spec.md)) · egress level control (§3.1) with host:port allow-list rows · env-vars table with a pinned notice: *"Secrets never enter the sandbox — grant credentials via the auth proxy"* linking to [F12](./12-github-and-git-flow.md) · repo pairing multi-select (from F12's installed repos) · resource fields (vCPU/mem/disk; defaults 2 vCPU / ~8 GB / 32 GB per open-swe — [research 06](../../research/06-execution-sandboxes.md) fact 11).
- **Build & test**: "Build" runs base build + warm provisioning with streamed logs; failure shows the log tail + retry (§5). This is the antidote to the #1 documented competitor pain — generic env-setup failures and dead ends ([research 03](../../research/03-competitor-teardown.md) fact 16).
- **Duplicate / delete**: duplicate copies `env.json` + `setup.sh` (snapshots rebuild); delete is blocked while any live thread references the environment, and orphaned snapshots are garbage-collected.
- **Cost & TTL surfacing**: environments list shows a usage strip — sandbox-hours are metered in LCU/LSU (unit prices published; sandbox metering formula is not — O-005), free tier = 5 LCU + 1 LSU/mo and a 10-sandbox cap on Developer ([research 23](../../research/23-gapfill-runtime-tiers.md) fact 16). Until O-005 resolves, show box counts + deep-link to LangSmith usage. **Idle-TTL guidance** (docs + inline help): keep 600 s default; raise only for tight interactive review loops (cost rises linearly with idle time); never raise it to survive approval waits — restart-on-resume is free-ish because *stopped* boxes keep their filesystem (§3.2).

## 4. Contracts

### 4.1 `env.json` (environment definition, v1 — new, owned here)

| Field | Type | Notes |
|---|---|---|
| `name` | string, unique per agent | picker + chip label |
| `base` | `{image: ref}` \| `{dockerfile: path}` | snapshot source ([research 06](../../research/06-execution-sandboxes.md) fact 9) |
| `setup` | path (default `./setup.sh`) | provisioning script |
| `egress` | `{level: "trusted"\|"custom"\|"full", allow: ["host[:port]"]}` | compiles to proxy `allow_list`/access rules; effective per-level policy in §3.1 (`trusted` = HTTP/S via proxy + all raw TCP denied; `custom` = allow-listed HTTP/S + listed `host:port` raw TCP only; `full` = HTTP/S **and** raw TCP open — save requires explicit confirmation); unmatched traffic denied (fail-closed). A "none" level is desired but unverified (§9-Q7) |
| `env` | `{KEY: value}` | non-secret only; validated against a secret-pattern denylist at save |
| `credentials` | `[{host_glob, source: "workspace_secret"\|"callback"}]` | proxy-injected; values never stored here (F12 owns callback minting) |
| `repos` | `["owner/repo"]` | pairing; composer filter |
| `resources` | `{vcpu, memory_gb, disk_gb}` | defaults 2/8/32; ceilings unknown (§9-Q3) |
| `snapshots` | `{base_id, warm_id?, warm_captured_at?}` | written by the build pipeline, read-only in the editor |
| `idle_ttl_seconds` | int, default 600 | passed to `create_sandbox` |

### 4.2 Run-config & provenance

- Composer → run: `config.configurable.environment: <name>` (absent ⇒ template's non-sandbox StateBackend path).
- Agent → thread metadata (provenance, [02 §10](../02-architecture.md)): `sandbox_id` (= backend `.id`, the LangSmith box name usable against `/v2/sandboxes` — [research 20](../../research/20-gapfill-mda-api.md) fact 19), `environment`, `snapshot_id`.

### 4.3 `apps/server` endpoints (new, owned here; hosted by [F28](./28-backend-glue-service.md) per P-005)

| Route | Purpose |
|---|---|
| `GET/POST /api/environments`, `GET/PUT/DELETE /api/environments/{name}` | registry CRUD over the agent-project files (commit via the same flow F-agent-config uses) |
| `POST /api/environments/{name}/build` → `GET /api/environments/{name}/build/logs` (SSE) | base build + warm provisioning + `capture_snapshot`; streamed logs |
| `GET /api/threads/{thread_id}/sandbox` | lifecycle status for the env chip (state, `idle_expires_at`, ids); polled/SSE |

### 4.4 Env chip (seam to F09)

`{environment, sandbox_id, state: provisioning|ready|running|idle|stopped|expired|recreating|setup_failed|unreachable, idle_expires_at?}` — rendered as `EnvChip` ([03 §4](../03-ui-spec.md)) with TTL countdown while `idle`, pulse while `provisioning|recreating`, error styling on `setup_failed|unreachable`.

## 5. Edge cases & failure modes

| Case | Behavior |
|---|---|
| Snapshot build failure | Build logs streamed and retained; last-good snapshots kept (environment stays usable); Retry + "edit setup.sh" CTA. Never the generic "Failed to create task" dead end ([research 03](../../research/03-competitor-teardown.md) fact 16) |
| `setup.sh` failure at thread provisioning | Codex-parity diagnostics: exit code + log tail rendered as a thread event and in the env chip popover (`setup_failed`); actions: retry, retry from base (skip warm), open Environment tab |
| TTL expiry mid-approval-wait | Expected, not an error: HITL interrupts persist in thread state independent of the box; on resume, stopped box restarts with filesystem intact; if past delete-after-stop (~14 d), auto-recreate + re-clone (§3.2) with a visible recreation notice |
| Sandbox unreachable mid-run | `execute` errors flow through `ToolRetryMiddleware`/`ToolErrorMiddleware` ([02 §3](../02-architecture.md)) — transient retries, then an error ToolMessage the model can react to; chip → `unreachable`; run fails soft with trace link |
| Egress denial | Proxy blocks non-allow-listed traffic (fail-closed); the command's stderr reaches the agent as tool output (it can adapt/report), and the UI detects proxy-denial signatures in the tool card and hints "blocked by environment egress policy — edit allow-list" |
| Auto-recreate with unpushed work | Dirty-tree mismatch vs remote branch → warning banner in thread; F12's push-early policy minimizes the window |
| Follow-up while a run is active | `multitask_strategy` enqueue (default) serializes access to the single thread sandbox ([02 §7](../02-architecture.md)) — no concurrent-provision race |
| Developer-plan 10-sandbox cap / quota exceeded | Creation error surfaced with plan context + list of running boxes to stop ([research 23](../../research/23-gapfill-runtime-tiers.md) fact 16) |
| Warm snapshot stale vs repo | Correctness unaffected (always fetch at start); editor nudges rebuild when warm snapshot age exceeds a threshold |
| Snapshot deleted out-of-band | `create_sandbox` failure → fall back to base snapshot, flag environment "needs rebuild" |

## 6. Security & privacy

- **Zero secrets in the sandbox** — D-015 and release criterion 5 ([04](../04-roadmap.md)), verified by an automated test (§7-A5). All credentials are injected into *outbound* requests by the sandbox auth proxy; GitHub (D-007) uses F12's TTL-bound, fail-closed callback pattern (proxy POSTs `{host,port}`, server returns `{headers}`; TTL 60–3600 s — [research 20](../../research/20-gapfill-mda-api.md) fact 13). `setup.sh` gets no secret phase at all (stricter than Codex, which exposes secrets during setup — [research 03](../../research/03-competitor-teardown.md) fact 8): private registries/hosts are reached via proxy credential rules instead.
- **Egress is the exfiltration boundary**: per-level policy per §3.1 — `trusted` default is HTTP/S-only via proxy with all raw TCP denied, `custom` narrows to allow-listed hosts/ports, `full` opens raw TCP too and requires explicit user confirmation at save; traffic matching no rule is denied (fail-closed); rules render in the editor, never free-form in the sandbox ([research 06](../../research/06-execution-sandboxes.md) fact 10).
- **Key custody**: workspace API key lives server-side (`apps/server`) only; browser → server → `/v2/sandboxes` (P-005; [02 §5](../02-architecture.md)).
- **Isolation as safety**: risky commands run full-permission *inside* the disposable sandbox rather than via per-action prompts (open-swe lesson — [research 10](../../research/10-openswe-fleet.md)); `interrupt_on` still gates `execute` where the user configures Ask ([02 §3](../02-architecture.md)).
- **Provenance**: sandbox id + snapshot id + environment name in the task rail and run metadata ([02 §10](../02-architecture.md)); env-var values are plain config committed to the agent project — the save-time secret-pattern check (§4.1) keeps credentials out of git.

## 7. Acceptance criteria

- **A1** Creating an environment (image + `setup.sh`) in the Environment tab produces a base snapshot and, after a green provisioning run, a warm snapshot; build logs are visible live and retained on failure, with retry.
- **A2** A coding task dispatched with environment *E* provisions its thread sandbox from *E*'s warm snapshot; a follow-up within TTL reuses the same box with no re-provisioning (assert same `sandbox_id`).
- **A3** Two tasks dispatched in parallel get two distinct sandboxes; neither blocks the other.
- **A4** After idle stop, a follow-up restarts the box with the working tree intact; after forced deletion, the thread auto-recreates from the warm snapshot, re-clones, checks out the task branch, and shows the recreation notice.
- **A5** Automated zero-secret test: enumerate env + filesystem in a provisioned sandbox; no configured secret value appears anywhere, while `GH_TOKEN=dummy gh api user` succeeds through the proxy (with F12 in place).
- **A6** A request to a non-allow-listed host from the sandbox fails; the tool card shows the egress hint; adding the host in the editor and retrying succeeds.
- **A7** Env chip renders all §4.4 states with TTL countdown; `setup_failed` exposes exit code + log tail without leaving task detail.
- **A8** Research/writing tasks create no sandbox (assert zero `/v2/sandboxes` box calls) and their files render via the F13 files rail from `values.files`.
- **A9** Deleting an environment with live threads is blocked with an actionable message; duplicate produces an independent, buildable copy.
- **A10** Environments list shows running-box counts and links to LangSmith usage; TTL guidance is present in the editor help.

## 8. Task breakdown

| # | Task | Depends on | Definition of done |
|---|---|---|---|
| 1 | `packages/agent` sandbox module: `sandbox/__init__.py` (`define_sandbox` per §3.4) + warm-guard `setup.sh` template; StateBackend path for non-sandbox templates | — | `mda dev` + `langgraph dev` provision a thread sandbox for the coding template; research template makes no sandbox calls (A8) |
| 2 | `apps/server` sandbox client wrapper + environment registry (env.json schema §4.1, file storage, validation incl. secret-pattern check) | 1 | CRUD endpoints (§4.3) green with unit tests; invalid egress/env rejected |
| 3 | Snapshot build pipeline: base build → provision box → `setup.sh` → `capture_snapshot` → persist ids; SSE log streaming | 2 | A1; last-good retention; base-fallback on missing warm snapshot |
| 4 | Composer environment picker wiring: repo-filtered list, `configurable.environment`, classic-tier factory resolution | 1, 2 | Dispatch with chosen env verified end-to-end on classic tier; MDA fallback (one env/deployment) documented in-code |
| 5 | Lifecycle manager: `GET /api/threads/{id}/sandbox`, restart/recreate logic, recreation thread-event | 1, 2 | A2–A4 pass against a real workspace |
| 6 | Environment tab UI: list/create/edit/duplicate/delete, `setup.sh` editor, egress level + allow-list editor, repo pairing, build screen | 2, 3 | A1, A9; a11y per [03 §7](../03-ui-spec.md) |
| 7 | `EnvChip` + run-panel integration (F09 seam) | 5 | A7; states driven solely by the §4.4 contract |
| 8 | Failure diagnostics: setup-fail event card, egress-denial detection in tool cards, unreachable handling through the retry/error middleware | 5, 7 | A6, A7; no generic failure toasts remain |
| 9 | Zero-secret + egress CI tests (run against a live sandbox in a nightly job) | 1, 3, F12 route | A5, A6 automated |
| 10 | Cost/TTL surfacing: usage strip, LangSmith usage deep-link, TTL guidance copy | 6 | A10; revisit when O-005 resolves |

## 9. Open questions

1. **Per-run environment selection on MDA**: can `define_sandbox` kwargs (esp. `snapshot_id`) resolve from run config, or are they static per deployment? Static ⇒ v1 fallback in §3.4 stands. (Extends [research 20](../../research/20-gapfill-mda-api.md) OQ on managed sandbox customization.)
2. **MDA sandbox name discovery / `proxy_config` runtime patching** — callback design avoids it, but confirm `backend.id` is reliably exposed to authored middleware for provenance ([research 20](../../research/20-gapfill-mda-api.md) fact 19 vs OQ 27).
3. **Resource ceilings & exact create-time field names** for vCPU/memory/disk, and the concurrent-sandbox limit on Plus (only Developer's 10-box cap is documented) ([research 06](../../research/06-execution-sandboxes.md) OQ; [research 23](../../research/23-gapfill-runtime-tiers.md) OQ).
4. **Stop/restart semantics**: exact behavior at `idle_ttl` (stop vs delete), restart API call, and what `preserve_memory_on_stop` covers — §3.2's kept/lost table needs verification against the sandbox SDK.
5. **Dockerfile snapshot builds**: is there a build-log streaming surface, and what are the registries endpoints' roles? (Needed for A1's live logs; otherwise poll + tail.)
6. **Sandbox cost/quota** (extends O-005, "MDA quotas/pricing at GA"): the LCU/LSU metering formula for sandboxes and any usage-read API to render real numbers instead of deep links ([research 23](../../research/23-gapfill-runtime-tiers.md) OQ).
7. **"None" egress level**: can the proxy be configured to deny *all* HTTP/S (empty allow-list ⇒ deny-all), matching Claude Code's "None"? Docs only state the HTTP/S-open default.
8. **Environment metadata home**: agent-project files (working assumption, §3.1) vs a Context Hub repo vs `apps/server` state — decide before task 2; file-first is favored by [02 §6](../02-architecture.md).
9. **`capture_snapshot` limits**: size/rate limits, retention, and cross-region availability of captured snapshots.
10. **Non-secret env-var injection**: the exact `create_sandbox` mechanism for plain env vars (bake at capture vs create-time param) is unverified in our research.

## 10. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| MDA restricts sandbox config to static `define_sandbox` (kills per-run env choice on the primary tier) | Med | Med | §3.4 fallback: env-per-deployment on MDA; full choice on classic tiers; beta contact per [02 §6](../02-architecture.md) caveats |
| Sandbox pricing opacity → user bill shock (O-005 unresolved at M2) | Med | Med | Conservative 600 s TTL default, running-box visibility, usage deep links, docs guidance (§3.5) |
| Environment setup friction — the #1 documented pain across competitors — reproduced here | Med | High | Test-build with streamed logs, Codex-parity diagnostics, curated base images, warm-guard templates (§3.5, §5) |
| Beta churn: sandbox/MDA surfaces shift under us (0.4.0-dev channel) | High | Low-Med | Thin `apps/server` wrapper isolates the SDK; canary CI per [04 · risk register](../04-roadmap.md) |
| Snapshot sprawl / storage cost from warm captures | Med | Low | Keep only last-good + latest per environment; GC on delete (§3.5) |
| Thread-sandbox sprawl hits plan caps (10 boxes on Developer) | Med | Low-Med | Surface cap errors with stop-actions (§5); TTL keeps fleets small |
| Auto-recreate loses unpushed work | Low | Med | Push-early policy (F12), dirty-tree warning, recreation notice (§3.2, §5) |

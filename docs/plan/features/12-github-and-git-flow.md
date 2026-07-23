# F12 · GitHub integration & git flow
*Deep Work feature spec · 2026-07-22 · Status: draft · Milestone: M2 · Depth: implementation-ready*
Sources: [02 · Architecture §4/§5](../02-architecture.md) · [04 · Roadmap M2 + release criteria](../04-roadmap.md) · [decisions](../decisions.md) · [research 06 · sandboxes/auth proxy](../../research/06-execution-sandboxes.md) · [research 10 · open-swe/Fleet](../../research/10-openswe-fleet.md) · [research 20 · MDA API gap-fill](../../research/20-gapfill-mda-api.md) · [research 12 · lifecycle & auth](../../research/12-lifecycle-auth-followup.md) · [research 03 · competitor teardown](../../research/03-competitor-teardown.md) · [feature catalog](./README.md)

## 1. Scope

**Owns:** the GitHub App design (permissions, install flow, repo picker semantics, multi-org/multi-installation handling); short-lived installation-token minting and per-repo down-scoping; the zero-token-in-sandbox credential path end-to-end ([D-015](../decisions.md)); git flow conventions (branch naming, commit identity, force-push policy); the `commit_and_open_pr` tool contract and PR provenance conventions; CI-status readback *data contract*; and the "zero secrets in sandboxes (verified by test)" release criterion ([04 · release criteria #5](../04-roadmap.md)).

**Does not own:** apps/server service plumbing — routing, middleware, deploy, config loading — which belongs to [F28 · backend glue service](./28-backend-glue-service.md). The seam: **this spec defines the semantics and payloads of the GitHub routes; F28 defines where and how they run** (FastAPI app layout, auth middleware, env/secret loading, per [P-005](../decisions.md)). Also out: sandbox lifecycle/provisioning and the files/diff UI (separate specs — see [catalog](./README.md)), settings/onboarding page layout (F06), task-rail rendering (F09), notifications/push (F13), diff review UX ([03 · UI spec §3.2](../03-ui-spec.md)).

**Explicitly out (product):** GitLab and all non-GitHub providers ([D-007](../decisions.md); open-swe's most-requested and declined feature, same call — [01 · vision cut line](../01-vision.md)). §3.6 records the seam that would change.

**Do-not-conflate note:** LangSmith's own control-plane GitHub integration (`GET /v1/integrations/github/install` → `integration_id`, used for *deployment sources* — [research 12](../../research/12-lifecycle-auth-followup.md)) and LangSmith Agent Auth (brokered per-user third-party OAuth — [02 §5](../02-architecture.md)) are different systems from the Deep Work GitHub App specified here, which exists so *task sandboxes* can act on repos.

## 2. Dependencies & seams

| Neighbor | Direction | Seam |
|---|---|---|
| [F28 · backend glue](./28-backend-glue-service.md) | F12 → F28 | F12 specifies route semantics/payloads (§4.3); F28 owns the FastAPI service they mount in ([P-005](../decisions.md)). Token mint + proxy-callback endpoints are apps/server responsibilities. |
| F06 · onboarding & settings ([catalog](./README.md)) | F06 → F12 | Settings "GitHub" panel and onboarding step render the install flow + repo picker defined in §3.2; F12 supplies data endpoints and states (connected / not installed / suspended / revoked). |
| F09 · task detail & run rail ([catalog](./README.md)) | F09 → F12 | Rail shows branch, draft-PR link, CI status ([03 §3.2](../03-ui-spec.md)); F12 supplies the normalized CI-status shape (§4.4) and polling contract; rendering is F09's. |
| F13 ([catalog](./README.md)) | F12 → F13 | Push/webhook-driven CI updates are a F13 concern post-v1; v1 readback is poll-only (§3.5) to honor the no-DB constraint ([02 §1](../02-architecture.md)). |
| Sandbox/environment spec ([catalog](./README.md)) | F12 → | `proxy_config` (host rules, callback URL, egress allow-list) is set at sandbox creation by `define_sandbox` kwargs passed verbatim to `create_sandbox` ([research 20 fact 12](../../research/20-gapfill-mda-api.md)). |
| `packages/agent` | F12 → | `commit_and_open_pr` tool (§4.1), git conventions in instructions, `interrupt_on` gate on the tool ([02 §3](../02-architecture.md)). |
| Decisions | — | [D-015](../decisions.md) zero-token-in-sandbox; [D-007](../decisions.md) GitLab out; [D-022](../decisions.md) Next.js frontend; [P-005](../decisions.md) FastAPI glue. Note: P-005 supersedes the "Next.js server routes" phrasing in [02 §1/§11](../02-architecture.md) and [05 repo tree](../05-oss-setup.md) for these endpoints. |

## 3. Design

### 3.1 GitHub App

Per-operator app: each Deep Work install registers **its own GitHub App** (open-swe's model: `GITHUB_APP_ID` / `GITHUB_APP_PRIVATE_KEY` / installation ids — [research 06 fact 11](../../research/06-execution-sandboxes.md)). No Deep Work-hosted shared app in v1 (§9-Q8). To keep the <15-min criterion ([04](../04-roadmap.md)), onboarding uses GitHub's app-manifest flow (one-click app creation from a posted manifest; the returned credentials are written to apps/server config by the operator — flow details in F06/F28).

**Permission set** ([02 §4](../02-architecture.md), matching open-swe — [research 10](../../research/10-openswe-fleet.md)):

| Permission | Level | Why |
|---|---|---|
| Contents | RW | clone/fetch, push task branches |
| Pull requests | RW | open/update draft PRs, read PR state |
| Issues | RW | task↔issue linking, PR comments on issue-threads |
| Checks | RW | read CI for the rail (§3.5); write reserved for post-v1 "Deep Work verification" check runs |
| Metadata | R | implicit/mandatory on all Apps |

Not requested in v1: `workflows` (agent edits to `.github/workflows/**` will be rejected on push — documented failure mode §5, revisit in §9-Q7), org `members` (open-swe used it for its own dashboard ACLs; Deep Work access control is LangSmith-side — [02 §5](../02-architecture.md)). Webhook subscriptions: none in v1 (poll-based CI readback; webhooks are the F13 seam).

**Install flow & repo picker (UX seam to F06):** Settings → GitHub → "Install" deep-links to the app's `installations/new` page on github.com; the user picks account/org + all-repos-or-selected there (GitHub's native picker is the source of truth for repo selection); GitHub redirects back to the apps/server setup route with the new installation id. Deep Work then shows: installations list (account, repo-selection mode, status) and, per installation, the selectable repo list used by the task composer's repo picker ([03 §3.1](../03-ui-spec.md)).

**Statelessness:** Deep Work persists **no** installation/repo registry ([02 §1](../02-architecture.md): no DB; [01](../01-vision.md): "stores essentially nothing"). GitHub is the source of truth: installations are enumerated with the app JWT, repos per installation with an installation token, on demand with short-lived server-side caching. The only stored material is the app credential set (app id, private key, client id/secret) in apps/server secrets (F28).

**Multi-org / multi-installation:** one app, N installations (personal account + any number of orgs). All GitHub calls are keyed by `installation_id`; the repo picker groups by installation; a task binds `{installation_id, owner, repo}` at creation (stored in thread metadata, which we already stamp — [02 §10](../02-architecture.md)). Token cache key: `(installation_id, repo, permissions-hash)` with expiry-aware invalidation (open-swe's token cache + per-repo down-scoping — [research 06 fact 11](../../research/06-execution-sandboxes.md)).

### 3.2 Token minting & down-scoping

apps/server signs a short-lived app JWT (RS256) and calls GitHub's installation access-token endpoint (`POST /app/installations/{id}/access_tokens` — [research 06 fact 11](../../research/06-execution-sandboxes.md)), passing the task's single repo and the minimal permission subset for the operation, so every minted token is **down-scoped to one repo** even when the installation covers many. Installation tokens are GitHub-side short-lived (~1 h); Deep Work additionally treats them as disposable — minted on demand per proxy callback (§3.3) or per server-side GitHub API call, never stored beyond the in-process cache, never sent to the browser.

### 3.3 Zero-token-in-sandbox, end-to-end (D-015)

The sandbox contains **no secret at any time**. Chosen mechanism: the LangSmith sandbox auth-proxy **callback** pattern, not open-swe's PATCH-opaque-rules pattern, because MDA generates the per-thread sandbox name at runtime and never exposes it to author code — the callback design sidesteps that entirely ([research 20 fact 12 + open Q](../../research/20-gapfill-mda-api.md)).

```
sandbox (git / GH_TOKEN=dummy gh)
   │  outbound HTTPS to github.com / api.github.com
   ▼
LangSmith auth proxy ── POST {host, port} ──► apps/server callback route
   ▲                                              │ mint down-scoped installation token (§3.2)
   └──────────── 200 {headers} (TTL-bound) ◄──────┘        non-200 / timeout → proxy fails closed (502)
   │  injects headers into the outbound request
   ▼
github.com / api.github.com
```

- Proxy POSTs `{host, port}`; we return `{headers}`; response is TTL-bound (platform bounds 60–3600 s); any callback failure ⇒ proxy returns 502 to the in-sandbox client — **fail-closed** ([02 §4](../02-architecture.md), [research 20 fact 12](../../research/20-gapfill-mda-api.md); exact wire field names to be pinned against the sandbox-auth-proxy docs before implementation, §9-Q2).
- Host→header mapping (returned per callback, since the proxy tells us the host): `github.com` (git smart-HTTP) gets Basic auth encoding `x-access-token:<token>`; `api.github.com` (gh CLI) gets a bearer header. `codeload.github.com`/`uploads.github.com` included in the proxy host rules for archive/release fetches; LFS coverage is §9-Q9.
- In-sandbox setup (baked into environment snapshot / `setup.sh`): `GH_TOKEN=dummy` (gh refuses to run unauthenticated; the proxy replaces the header — the documented LangSmith pattern and open-swe's production pattern: [research 06 fact 10](../../research/06-execution-sandboxes.md), [research 10](../../research/10-openswe-fleet.md)), plain `https://github.com/{owner}/{repo}.git` remotes with **no userinfo**, no credential helper, no `~/.git-credentials`.
- Egress stays default-deny beyond HTTP/S with per-environment allow-lists ([02 §4](../02-architecture.md)) — the proxy is also the egress chokepoint, so "token only ever exists proxy-side" and "sandbox can only reach allow-listed hosts" are the same mechanism.
- `proxy_config` (host rules + callback URL) is passed statically via `define_sandbox` kwargs, which MDA forwards verbatim to `create_sandbox` ([research 20 fact 12](../../research/20-gapfill-mda-api.md)); no runtime PATCH needed.

### 3.4 Git flow conventions

1. **Clone** in sandbox over HTTPS (through the proxy). Default `--depth=50`; repos above a size threshold use `--filter=blob:none` (mitigates §5 TTL-mid-clone row).
2. **Branch**: all agent work happens on `deepwork/<task>` ([02 §4](../02-architecture.md)). Naming rule: `deepwork/{slug}-{tid}` where `slug` = kebab-cased task title, charset `[a-z0-9-]`, truncated so the full ref ≤ 60 chars, and `tid` = first 6 chars of the thread id. The `tid` suffix makes names collision-free across tasks and deterministic within one (resume/retry of the same thread reuses its branch). Prefix-based scoping mirrors Claude Code's `claude/`-prefixed autonomous-branch restriction ([research 03](../../research/03-competitor-teardown.md)).
3. **Never touch base**: the agent never commits to or pushes the default/base branch. Enforced at tool level (`commit_and_open_pr` only pushes the task branch), in instructions, and by HITL gating — not by the token (installation tokens are repo-scoped, not branch-scoped; residual risk in §10).
4. **Force-push policy**: allowed only on the task's own `deepwork/*` branch and only as `--force-with-lease` (used after history-rewriting steering, e.g. "squash that"); any force-push is reported in the tool result so the rail can show it.
5. **Commit identity**: commits authored as the app's bot identity (`<app-slug>[bot]` with its GitHub noreply address, configured via `git config` in setup); pushes already attribute to the app via the token. Human co-authorship trailer is §9-Q6.
6. **PR**: created **draft by default** via `gh` inside the sandbox (open-swe's production pattern — [research 06 fact 11](../../research/06-execution-sandboxes.md)), gated by `interrupt_on` (Auto/Ask) per [02 §3](../02-architecture.md).

**PR body/provenance conventions (proposal):** model writes the summary body; the *tool* appends an unforgeable footer below a reserved, tool-owned sentinel marker:

```
<!-- deepwork:provenance -->
---
Opened by Deep Work · Task: <deep-work task URL> · Branch: deepwork/{slug}-{tid}
Trace: <LangSmith run URL — included only for private repos, org-configurable; default off on public>
```

The HTML-comment sentinel makes the footer idempotent and unspoofable: before writing, the tool strips everything from the first sentinel occurrence onward (including any model-written impostor sentinels), preserving the model-authored body above it, then appends the fresh footer — so existing-PR updates (§4.1 step 5) replace the prior footer instead of stacking duplicates. Task link always; trace link is org-internal information (URL embeds org context) so default-on only for private repos (§9-Q5). Trace remains always visible in the task rail regardless ([02 §10](../02-architecture.md) provenance principle).

### 3.5 CI status readback (seam to F09/F13)

After a PR exists, apps/server exposes a normalized check summary for the PR head SHA (§4.4), computed server-side from GitHub's check-runs listing using a freshly minted read-scoped token — **no token or raw GitHub payload reaches the browser**. The task rail (F09) polls it while visible (suggested 30 s active / stop when tab hidden; final states cached). Webhook-driven push into the rail and notifications ride F13 post-v1; v1 is poll-only because apps/server has no store for webhook state ([02 §1](../02-architecture.md)).

### 3.6 GitLab seam (out, D-007)

Kept cheap, not built: (a) branch naming, commit rules, and the `commit_and_open_pr` *interface* are provider-neutral (PR⇄MR mapping is inside the tool); (b) all GitHub specifics live in one apps/server module (`github/`) behind a provider interface F28 can register alternatives into; (c) the proxy callback already receives `{host}` — a GitLab provider would add host rules + its own token mint. What would change: App/JWT/installation model → GitLab OAuth/project access tokens, `gh` → `glab` in snapshots, Checks → pipelines. No v1 code paths branch on provider.

## 4. Contracts

### 4.1 `commit_and_open_pr` tool (in `packages/agent`, name per [02 §3](../02-architecture.md))

```
commit_and_open_pr(
  title: str,                   # PR title
  body: str,                    # PR body; provenance footer appended by the tool (§3.4)
  commit_message: str | None,   # default: title
  base: str | None,             # default: repo default branch
  draft: bool = True,
  force: bool = False           # --force-with-lease on the task branch only (§3.4 rule 4)
) -> {
  pr_url: str, pr_number: int, branch: str, head_sha: str,
  base: str, draft: bool, created: bool,   # created=False ⇒ existing PR for branch was updated
  forced: bool, warnings: list[str]        # e.g. "draft unavailable on this plan; opened ready-for-review"
}
```

Behavior (ordered): (1) ensure on `deepwork/{slug}-{tid}`, creating from base if needed; (2) stage + commit all sandbox working-tree changes (empty diff ⇒ structured tool error, no PR); (3) push via proxy (fail-closed path §3.3); (4) if an open PR for this head already exists, update title/body and return it (`created=false`) — idempotent under retries; else create (draft per arg, with §5 draft-fallback); (5) write provenance footer: strip from the sentinel marker onward, append fresh footer (§3.4) — replace-not-append, so retries never duplicate it and the model-authored body is preserved; (6) return. Errors surface as error ToolMessages via `ToolErrorMiddleware` ([02 §3](../02-architecture.md)). The tool is listed in `interrupt_on` defaults (Ask) — approvals UX per [03 §3.3](../03-ui-spec.md).

### 4.2 Proxy callback (apps/server; plumbing F28)

- Request (from LangSmith proxy): `POST {callback_url}` body `{host, port}`.
- Response: `200` `{headers: {…}}`, TTL-bound (60–3600 s platform bounds); headers per host mapping §3.3. Unknown host, unauthenticated caller, mint failure, or timeout ⇒ non-200 ⇒ proxy fail-closed 502. ([research 20 fact 12](../../research/20-gapfill-mda-api.md); field-name confirmation §9-Q2, caller authentication §9-Q1.)
- The callback must resolve *which task/repo* it serves: the callback URL registered in each sandbox's `proxy_config` is unique per sandbox and encodes an opaque server-generated grant id bound to `{installation_id, owner, repo}` at sandbox creation — so a sandbox can never obtain a token for a repo its task wasn't bound to.

### 4.3 apps/server route surface (semantics here; paths/plumbing owned by [F28](./28-backend-glue-service.md))

| Route (indicative) | Semantics (this spec) |
|---|---|
| `GET  …/github/install-url` | Begin install: URL of the app's GitHub install page |
| `GET  …/github/setup` | GitHub post-install redirect target (receives installation id / setup action); bounces to settings |
| `GET  …/github/installations` | List installations: `{id, account, repository_selection, status}` |
| `GET  …/github/installations/{id}/repos` | Repo-picker data: `{owner, repo, private, default_branch}` per repo |
| `POST …/github/proxy-callback/{grant}` | §4.2 |
| `GET  …/github/checks?repo&pr` | §4.4 normalized CI status |

### 4.4 Normalized CI status (consumed by F09)

```
{ state: "pending"|"passing"|"failing"|"neutral"|"unknown",
  total: int, completed: int,
  failed: [{name, url}], updated_at: iso8601, html_url: str }
```

`unknown` covers revoked-access/rate-limited reads so the rail can render a degraded chip instead of lying.

## 5. Edge cases & failure modes

| Case | Behavior |
|---|---|
| Branch already exists | Same thread ⇒ reuse (deterministic name, §3.4). Different ref colliding (manual creation) ⇒ suffix `-2`, warn in tool result. |
| PR already open for branch | Idempotent update-and-return, `created=false` (§4.1) — also absorbs GitHub's "PR already exists" rejection under racing retries. |
| Draft PR unsupported (private repo on free plan) | Fall back to ready-for-review + `do-not-merge` label; `warnings[]` entry; rail badges it. |
| Force-push | Only task branch, only `--force-with-lease`, only `force=true`; reported via `forced` (§3.4). |
| Repo permissions revoked mid-run | Next mint fails ⇒ callback non-200 ⇒ proxy 502 ⇒ in-sandbox git/gh fail ⇒ error ToolMessage; task rail shows actionable "GitHub access lost"; settings shows installation health (F06). |
| Installation removed/suspended | Installations listing reflects it; new tasks can't bind the repo; running tasks fail as above. No webhook needed — state is re-derived from GitHub (§3.1). |
| Token TTL expiring mid-clone (large repo) | Token minted fresh at callback time; auth is evaluated when the request starts, and clone defaults (`--depth`, blobless for big repos, §3.4) keep transfers short. Multi-hour single-request transfer behavior: §9-Q4. |
| Private-fork / no-write-access flows | v1 requires the App installed with write on the target repo. Fork-based contribution (push to fork, cross-repo PR) is out of v1 — installation tokens don't reach repos outside their installation, so it needs a second installation on the fork owner; deferred (§9-Q10 not needed — recorded here as a cut). |
| Push touching `.github/workflows/**` | Rejected by GitHub (no `workflows` permission, §3.1); tool surfaces the specific remedy text; §9-Q7. |
| Nothing to commit | Structured tool error before any push/PR (§4.1). |
| Base branch deleted / repo archived, renamed or transferred | PR create fails ⇒ error ToolMessage with GitHub's reason; renames follow GitHub redirects server-side, task metadata is updated to the new `owner/repo`. |
| Callback endpoint down | Proxy fail-closed 502; git/gh error inside sandbox; retries via `ToolRetryMiddleware` ([02 §3](../02-architecture.md)); never fail-open. |
| GitHub rate limits (per-installation) | Server-side mint/read caching (§3.1); CI polling backs off on 403-rate-limit and reports `state: "unknown"`. |

## 6. Security & privacy

- **No secret in the sandbox, ever** ([D-015](../decisions.md)): tokens exist only in apps/server memory and in proxy-injected headers outside the sandbox boundary. Verified by test (§7).
- **App private key** lives only in apps/server secret config (F28); never in the client, agent code, sandbox, or repo. Key rotation = replace secret + restart; no other state to migrate (stateless design §3.1).
- **Callback hardening**: per-sandbox unguessable grant URL bound to one `{installation_id, repo}` (§4.2); reject unknown hosts; short TTLs; platform-side caller authentication is §9-Q1 — until pinned, the grant-URL + host allow-list is the floor, not the ceiling.
- **Down-scoping**: every token is one-repo, minimal-permission (§3.2). Blast radius of any single leaked token: one repo, ≤1 h.
- **Fail-closed everywhere**: mint failure, revocation, callback outage all end in 502-to-sandbox, never a fallback credential.
- **Browser never sees GitHub tokens or raw GitHub responses**; CI readback is normalized server-side (§3.5, §4.4).
- **Provenance vs. leakage**: trace URLs kept out of public-repo PR bodies by default (§3.4, §9-Q5); provenance footer appended by the tool so model output can't spoof it.
- **Prompt-injection boundary**: repo content read in-sandbox is untrusted input to the model, but it can never exfiltrate credentials (there are none) and egress is allow-listed ([02 §4](../02-architecture.md)); PR bodies rendered in Deep Work UI follow the untrusted-content boundary rules ([02 §10](../02-architecture.md)).
- **Audit**: every mint logged `{task/thread id, installation_id, repo, permissions, ttl}` — never token values; LangSmith traces remain the run-level audit ([02 §10](../02-architecture.md)).

## 7. Acceptance criteria

1. Install flow: from Settings, a user installs the App on ≥2 accounts (personal + org), and both installations' repos appear in the picker with no Deep Work-side persistence (server restarted between steps).
2. A coding task binds one repo; in-sandbox `git clone`, `git push`, `GH_TOKEN=dummy gh pr create --draft` all succeed via the proxy with zero secrets inside (criterion 5 test below green).
3. `commit_and_open_pr` produces a **draft** PR on `deepwork/{slug}-{tid}` with the provenance footer; re-invocation updates the same PR (`created=false`) and leaves exactly one footer (sentinel replace, §3.4); empty worktree yields a structured error, no PR.
4. Rail shows branch, PR link, and live CI status transitioning pending→passing/failing on a repo with real Actions (data via §4.4; rendering asserted with F09).
5. Revoking repo access mid-run produces a failed tool call with an actionable message and a degraded settings state — no hang, no fail-open.
6. Down-scoping proven: a minted token for repo A returns 404 on repo B of the same installation (integration test).
7. **Zero-secrets verification test** (release criterion 5, [04](../04-roadmap.md)) — `test_zero_secrets_in_sandbox`, CI-gated on real LangSmith sandboxes (nightly + on changes to token/proxy/tool code): the mint path records every token minted during a scripted clone→branch→commit→push→`gh pr create --draft` run — the harness never retains raw token values: it keeps one-way hashes, holding raw values only in short-lived memory for the sweep itself, and redacts them from assertion messages, logs, test reports, and CI artifacts — then asserts **inside the sandbox**: (a) no minted token appears in any process environment (`/proc/*/environ` sweep) — `GH_TOKEN` equals literally `dummy`; (b) a filesystem sweep for each minted token across the sandbox (incl. `~/.config/gh`, `~/.gitconfig`, `~/.git-credentials`, `<repo>/.git/config`, shell history) finds nothing; (c) `git remote get-url origin` contains no userinfo; and asserts **outside**: (d) fail-closed — with the callback returning 500, `git ls-remote` exits non-zero (proxy 502) and no git operation succeeds; (e) TTL-bound — callback responses carry a TTL within platform bounds and a fresh mint (counter ≥2) occurs across a TTL boundary during a long-running session.

## 8. Task breakdown

| # | Task | Depends on | Definition of done |
|---|---|---|---|
| 1 | GitHub App registration: manifest template + operator guide + settings copy | F28 scaffold | Fresh operator gets app id/key into apps/server config in <5 min following docs |
| 2 | apps/server `github/` module: app JWT, installation client, mint + down-scope + expiry-aware cache | 1 | Unit tests: scoping (§7-6), cache expiry, mint failure paths |
| 3 | Install/setup redirect routes + installations & repos listing endpoints | 2 | §4.3 rows 1–4 pass integration tests against a real test App; stateless across restart |
| 4 | Settings + composer repo picker wiring | 3, F06 | Multi-installation grouping renders; task binds `{installation_id, owner, repo}` into thread metadata |
| 5 | Proxy-callback endpoint: grant binding, host→header mapping, TTL, fail-closed | 2 | §4.2 behaviors under test incl. unknown-host reject and 500-on-mint-failure |
| 6 | `define_sandbox` proxy_config wiring in `packages/agent` (+ snapshot `setup.sh`: gh, GH_TOKEN=dummy, git identity) | 5 | Sandbox clone + gh auth-less flow works on MDA and classic tiers |
| 7 | Branch-naming util + git conventions in agent instructions | 6 | Property tests: charset/length/determinism; instructions reviewed against §3.4 rules 1–5 |
| 8 | `commit_and_open_pr` tool + provenance footer + `interrupt_on` default | 7, 2 | §4.1 contract tests; draft default; footer unforgeable + sentinel-replace idempotent |
| 9 | Idempotency & edge-case handling (existing branch/PR, draft fallback, empty commit, force policy) | 8 | Each §5 row with a deterministic trigger has a test |
| 10 | CI-status endpoint + normalization | 8 | §4.4 shape golden-tested against recorded check-run fixtures; rate-limit → `unknown` |
| 11 | Rail wiring for branch/PR/CI (with F09) | 10, F09 | §7-4 demo green |
| 12 | Failure surfacing: revoked/suspended/removed states in settings + task errors | 3, 9 | §7-5 scenario scripted and green |
| 13 | `test_zero_secrets_in_sandbox` in CI (nightly + path-triggered) | 6, 8 | §7-7 assertions all automated; wired as release gate |

## 9. Open questions

1. **Callback caller authentication**: how does the LangSmith proxy authenticate its POST to our callback (signature header? shared secret in `proxy_config`?) — not covered in [research 20](../../research/20-gapfill-mda-api.md); pin from sandbox-auth-proxy docs before task 5.
2. **Exact callback wire schema**: field names for `{host, port}` / `{headers}` / TTL are paraphrased in research ([20 fact 12](../../research/20-gapfill-mda-api.md)); confirm verbatim.
3. **MDA runtime pin**: does the Python `langsmith` version pinned by the MDA runtime accept `proxy_config` (incl. callbacks) verbatim? Confirmed from TS types + docs only ([research 20 open Q](../../research/20-gapfill-mda-api.md)).
4. Does GitHub re-validate auth mid-stream on very long single-request transfers (multi-hour clone)? Determines whether blobless-clone guidance (§3.4) is convenience or requirement.
5. Trace links in PR bodies: acceptable to include on private repos by default (URL embeds org context)? Org-level toggle shape.
6. Commit `Co-authored-by` for the dispatching human requires a LangSmith-identity→GitHub-identity mapping that doesn't exist in v1 — drop, or capture GitHub handle in user settings (F06)?
7. Add `workflows` permission (agent can edit CI) vs. keep least-privilege with the documented push rejection (§5)? Leaning least-privilege; revisit on user demand.
8. Shared Deep Work-hosted GitHub App (one install UX for everyone) vs. per-operator app — hosted app conflicts with the "wrapper, stores nothing" posture ([01](../01-vision.md)) but would cut onboarding minutes; decide before M4 docs.
9. Git LFS / `uploads.github.com` + `codeload.github.com` coverage in proxy host rules — which hosts does a full gh + git workflow actually touch?
10. Where does F06 persist per-agent default repo/environment prefs given no-DB ([02 §1](../02-architecture.md)) — LangGraph Store on the deployment (open-swe precedent, [research 10](../../research/10-openswe-fleet.md)) or Context Hub? (Shared with F06; F12 only needs `{installation_id, owner, repo}` in thread metadata.)

## 10. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Callback auth mechanism weaker than assumed (§9-Q1) | Token-mint oracle exposed | Grant-URL binding + host allow-list floor (§4.2); block task 5 exit on Q1 answer; fail-closed default |
| MDA rejects/strips `proxy_config` callbacks at some runtime version (§9-Q3) | Zero-token path broken on primary tier | Verified-on-classic-tier fallback exists (same `create_sandbox` args, [research 06](../../research/06-execution-sandboxes.md)); pin runtime versions; canary deployment already tracks the dev channel ([04 risk register](../04-roadmap.md)) |
| Installation tokens are repo- not branch-scoped | Compromised/confused agent could push non-task branches | Tool-level enforcement + HITL + `deepwork/*` convention (§3.4); document recommending branch protection on default branches; residual risk accepted for v1 |
| Sandbox-proxy platform API churn (beta-adjacent surface) | Rework in callback plumbing | Single `github/` module boundary (§3.6); contract tests against recorded proxy interactions |
| Per-operator App registration friction hurts the <15-min criterion ([04](../04-roadmap.md)) | Onboarding drop-off | Manifest-flow one-click creation (§3.1); measure in M4 dogfood; §9-Q8 fallback decision |
| Draft-PR plan limits on private free repos surprise users | Confusing "draft" behavior | Explicit fallback + warning + rail badge (§5) |
| CI poll-only readback lags or hits rate limits on busy orgs | Stale rail status | Backoff to `unknown` (§4.4), F13 webhook upgrade path reserved |

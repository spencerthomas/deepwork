---
title: Deep Work vision-alignment roadmap
status: review-artifact
kind: roadmap
last_reviewed: 2026-07-27
reviewed_commit: d852bee
owners: [product, architecture]
canonical: false
---

> **This is a point-in-time ROADMAP, not a canonical specification.** It grades the
> repository against the stated vision at commit `d852bee` and proposes milestones to
> raise each grade. It does not supersede `docs/PLANS.md`; where the two disagree, PLANS.md
> should be reconciled to reality (that reconciliation is itself milestone **X0** below).

# Deep Work — Vision-Alignment Roadmap

## The vision (as stated)

Deep Work should be **two things at once**:

1. **An open-source Claude Cowork / OpenAI Codex** — a control surface for delegating,
   supervising, approving, and verifying long-running agent work, whose coding outcome is
   a reviewable draft PR with tests and evidence.
2. **A living exposition of the LangChain ecosystem** — both the *hosted* services
   (LangGraph Platform deployment, LangSmith sandboxes, agent deployment, LangSmith Fleet /
   agent builder, Crons) and the *OSS* stack (langchain-core, langgraph, deepagents) and its
   *spin-offs* (Open SWE, open-deep-research, the open-agent-platform lineage / open-wiki).

## Baseline grades (commit `d852bee`)

| # | Axis | Grade | Gap to A+ |
|---|---|---|---|
| A1 | Cowork/Codex — supervision shell | B | Ambient triggers, multi-run fleet view, richer evidence |
| A2 | Cowork/Codex — the coding deliverable | D+ | No real draft-PR outcome; unsafe/loopless execution |
| B1 | Ecosystem — OSS core (langchain/langgraph/deepagents) | B+ | Middleware/observability not wired; useStream not used |
| B2 | Ecosystem — hosted services | C– | Only classic deployment works; Fleet/Crons/sandbox-UX absent |
| B3 | Ecosystem — OSS spin-offs (Open SWE / deep-research / OAP) | D | Researched, not leveraged |

Overall: a well-supervised shell around a single hosted-LangGraph path, with a coding agent
that cannot yet reliably produce the coding artifact, and a reuse-first thesis undermined by
two homegrown reimplementations (web streaming; the SDK/domain packages left unused).

The grade scale below extends the repo's own 0–4 quality scale into letter grades so "A+"
has a concrete, checkable meaning:

- **C** = the capability exists and runs.
- **B** = it runs, is tested, and is honest about its limits.
- **A** = it is production-safe (bounded, observable, recoverable) and end-to-end proven.
- **A+** = all of A, *and* it is a legible, reusable exposition of the ecosystem primitive —
  a reference other people learn the ecosystem from — with executable proof in CI.

---

## X0 — Truth baseline (prerequisite for every axis)

An exposition project is only as credible as the gap between what it *shows* and what is
*true*. Before grades can rise, the docs must stop over-claiming (see the companion
`CODE_REVIEW-2026-07-27.md`).

- Reconcile `SECURITY.md` (multi-tenant claim), `RELIABILITY.md` (Postgres/outbox/worker),
  `PLANS.md` ("no runtime implemented"), `QUALITY_SCORE.md`, and `README.md:109-111`.
- Fix `main` (architecture-checker + ruff failures) and require the `verify` job via branch
  protection.
- **Acceptance:** every canonical doc claim maps to executed evidence or is explicitly marked
  target-not-implemented; `main` is green; no direct-to-main feature pushes.

---

## Axis A1 — Supervision shell → A+

**Now (B):** delegate → plan → approve → stream → evidence → result works, with genuinely
honest states (no fabricated "completed"/"cancelled"). This is the strongest part of the
product and a real differentiator.

**Milestones**

- **A1.1 (→A) Cancel & recover everywhere.** Implement real-agent cancellation via
  `langgraph_sdk` `runs.cancel`; adopt (not fail) interrupt-waiting tasks on restart.
  *Acceptance:* a running real-agent task stops within one poll and its sandbox is torn down;
  a task parked at approval survives restart and resumes.
- **A1.2 (→A) Adopt the SDK/domain packages in the web app.** Replace the homegrown
  `tasks-store`/`sse` with `packages/sdk` stream service + `packages/domain` reducer.
  *Acceptance:* `apps/web` depends on `@deepwork/{sdk,domain}`; the duplicate-event and
  reconnect-gap bugs (audit B2/B3) are gone; one store, one type system.
- **A1.3 (→A+) Multi-run fleet view + ambient triggers.** Stream more than one active run;
  drive runs from GitHub webhooks (issue / @-mention / PR events) the way Open SWE does, so
  Deep Work becomes an ambient collaborator, not just a launcher.
  *Acceptance:* an `@deepwork` mention on an issue dispatches a run with a stable thread id and
  streams back into the Activity feed.

---

## Axis A2 — The coding deliverable → A+  *(highest priority)*

**Now (D+):** the sandbox executes, but there is no safe path to a real draft PR: the GitHub
credential is a static, model-readable env token (audit **C1**, CRITICAL), execution has no
loop/cost caps (audit **H3**), it can't be cancelled (**H4**), and the shipped system prompt
describes tools that don't exist and drops the untrusted-content clause (**H1**).

**Milestones**

- **A2.1 (→C, EXECUTED THIS PASS) Bound execution.** Wire the LangChain reliability middleware
  stack — `ModelCallLimitMiddleware`, `ToolCallLimitMiddleware`, `ModelRetryMiddleware`,
  `ToolRetryMiddleware` — plus a `recursion_limit` on the executor invoke and an optional
  `max_tokens`. This is exactly the stack `docs/plans/features/06-agent-project.md` says was
  "adopted wholesale… addresses Open SWE's top failure class." *Acceptance:* configurable caps
  enforced; graph still green; unit tests assert the middleware set and limits. **Done — see M1.**
- **A2.2 (→C, EXECUTED THIS PASS) Safe credential injection.** Remove the shell-injection vector
  (audit **C2**): quote the token and stop building credential shell strings by interpolation.
  *Acceptance:* token never interpolated unquoted; tests assert safe construction and that the
  token never appears in logs/repr. **Done — see M2.**
- **A2.3 (→A, NEXT) GitHub App tokens (the C1 fix, Open SWE pattern).** Replace the static
  `DEEPWORK_GITHUB_TOKEN` with per-run GitHub **App installation tokens**: RS256 JWT →
  `POST /app/installations/{id}/access_tokens`, **down-scoped to the single target repo**, ~1h
  TTL, cached, revoked on task end, and fetched by a credential helper that runs **outside** the
  agent's reach (askpass / short-lived injection) so `cat ~/.git-credentials` yields nothing
  durable. Mirrors `langchain-ai/open-swe` `agent/integrations` exactly.
  *Acceptance:* no long-lived secret on the sandbox filesystem; a prompt-injection test cannot
  exfiltrate a reusable credential; token is repo-scoped and expires.
- **A2.4 (→A) Real draft-PR outcome.** Agent produces branch + tests in the sandbox and opens a
  **draft** PR (via `gh`/App token), surfaced as evidence with a diff preview and the LangSmith
  trace. *Acceptance:* the e2e coding journey ends at a draft PR URL with tests, reproducibly.
- **A2.5 (→A+) Runtime-native system prompt.** Replace `system_prompt.txt` (a foreign
  Codex-CLI harness prompt) with one written for *this* runtime — deepagents toolset, the
  plan-approval interrupt, LangSmith sandbox semantics — and **restore the untrusted-content
  clause**. *Acceptance:* the prompt references only tools that exist; an eval asserts injection
  resilience.

---

## Axis B1 — OSS core exposition → A+

**Now (B+):** faithfully built on `create_deep_agent`, LangGraph interrupt/checkpoint,
`init_chat_model`, `langgraph-sdk`. Reuse-first is honored in the agent package.

**Milestones**

- **B1.1 (→A) Wire middleware + declare deps honestly.** (A2.1 delivers the middleware.) Add
  `langchain-openai` and `httpx` as direct deps (audit M1/M-dep) so the OpenRouter and trace
  paths aren't dead-on-arrival in deployment. *Acceptance:* a clean install from the lockfile
  serves an `openrouter:*` model.
- **B1.2 (→A) LangSmith-native observability.** Turn on tracing end-to-end and add structured
  logging in the API (audit's largest enterprise gap). *Acceptance:* every run is traceable in
  LangSmith and correlatable to an API request id.
- **B1.3 (→A+) Legible reference.** A short "how Deep Work uses the ecosystem" doc + annotated
  graph that a reader can lift: middleware choices, interrupt pattern, SDK stream mapping.
  *Acceptance:* the doc's code snippets are extracted from real source and checked in CI.

---

## Axis B2 — Hosted services exposition → A+

**Now (C–):** only the classic LangGraph Platform deployment path works end-to-end (which is
itself the most valuable single ecosystem proof). Sandboxes are invisible/flawed; Fleet, MDA,
Crons, and a deploy UX are gated stubs (`agents`, `schedules` are honest placeholders).

**Milestones**

- **B2.1 (→C) Schedules via the Crons API.** Wire the `schedules` destination to LangGraph
  Platform Crons — cheapest marquee win. *Acceptance:* a scheduled run fires and appears in
  Activity.
- **B2.2 (→A) Sandboxes as a first-class feature.** Surface live sandbox identity, resource use,
  lifecycle, and artifacts in the UI; set explicit resource ceilings and a verified TTL (audit
  M4). *Acceptance:* a user watches a sandbox start, run, and tear down; limits are enforced.
- **B2.3 (→A) Deploy experience.** A versioned deploy view over the classic deployment
  (assistant/version/health) instead of env-only configuration. *Acceptance:* deployment state
  is visible and switchable from the UI within the capability contract.
- **B2.4 (→A+) The open Fleet.** Since LangSmith Fleet is now hosted/closed-source, the OSS play
  is to be the *open* agent-builder/registry surface over LangGraph deployments (the niche the
  deprecated open-agent-platform vacated) — capability-detected, degrading honestly where a
  hosted CRUD API is unavailable. *Acceptance:* create/inspect/deploy an agent definition
  against a real deployment, with every unsupported route shown as `gated`, not faked.

---

## Axis B3 — OSS spin-offs → A+

**Now (D):** Open SWE, open-deep-research, and the OAP lineage are cited in `docs/references`
but leveraged in code approximately nowhere.

**Milestones**

- **B3.1 (→C) Stand on Open SWE for coding.** A2.3/A2.4 *are* this — adopt its GitHub-App +
  thread-named-sandbox + draft-PR patterns rather than re-deriving them.
- **B3.2 (→A) open-deep-research backbone for the research journey.** Back the research task
  type with LangChain's OSS deep-research agent instead of a generic loop. *Acceptance:* the
  research journey produces a cited report with verification, reproducibly.
- **B3.3 (→A+) open-wiki / OKF org-knowledge journey.** Deliver the org-intelligence direction
  already scoped in `docs/plan/07-org-intelligence.md` on the same task loop. *Acceptance:* an
  org-knowledge artifact is produced and versioned end-to-end.

---

## Sequencing

1. **X0** (truth baseline) and **A2.1 + A2.2** — executed / in progress this pass; convert
   "Codex-lite" toward "Codex" and clear the injection vector.
2. **A2.3 (GitHub App tokens)** — the CRITICAL fix; unlocks the safe draft-PR outcome. Next up.
3. **A2.4 + A2.5** — deliver and secure the actual coding artifact.
4. **A1.2 (adopt SDK) + B1.1/B1.2** — make the exposition honest and observable.
5. **B2.1 → B2.4** and **B3.2 → B3.3** — breadth across hosted services and spin-offs.
6. **A1.3, B1.3, B2.4, B3.3** — the A+ legibility/breadth tier.

## Execution log

| Milestone | Status | Evidence |
|---|---|---|
| A2.1 Bound execution (reliability middleware + caps) | **executed** | `7489c35`; +13 agent unit tests (config bounds, middleware wiring, bounded-run integration); agent suite 90 passed, ruff/ty at baseline |
| A2.2 Safe credential injection | **executed** | `473d7a7`; `build_git_credential_setup_command` + 3 injection-safety tests; ruff debt 19→16 in the touched file |
| A2.3 GitHub App tokens | planned (next) | — |
| all others | planned | — |

> Verification note: `packages/agent` ran green under its own CI commands
> (`ruff`, `ruff format --check`, `ty`, `pytest --disable-socket`) via a Python 3.12
> venv. The pre-existing 16 `ruff` / 5 `ty` findings in `packages/agent` predate this
> work and belong to milestone **X0** (fix `main`); the executed milestones add none.
> `apps/api` and the web/TS suites were **not** run here (they need the repo's
> Node ≥24.14 toolchain, unavailable in this environment).

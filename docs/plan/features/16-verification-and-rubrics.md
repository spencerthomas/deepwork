# F16 · Verification & rubrics

*Deep Work feature spec · 2026-07-22 · Status: draft · Milestone: M2 (goal lifecycle: v1.x, design-complete) · Depth: implementation-ready*

Sources: [08 · feature map (Grading rubrics row, corrections)](../08-deepagents-feature-map.md) · [02 · architecture §3/§9/§10](../02-architecture.md) · [04 · roadmap M2 + backlog](../04-roadmap.md) · [01 · vision (pillar 1)](../01-vision.md) · [03 · UI spec §3.1–3.3](../03-ui-spec.md) · [07 · org intelligence Layer 1](../07-org-intelligence.md) · [research 14 · dcode](../../research/14-dcode.md) · [research 02 · deepagents harness](../../research/02-deepagents-harness.md)

## 1. Scope

This spec owns **outcome verification end-to-end**: rubric authoring (composer field format, template defaults), the server-side grading loop (`RubricMiddleware` wiring in `packages/agent`), and the verification panel in the task-detail rail — verdicts, per-criterion feedback, iteration count, failure/override UX. It also carries the **v1.x goal lifecycle** (dcode `/goal` pattern) as a design-complete section with **no tasks** (§3.6; roadmap backlog per [04](../04-roadmap.md)).

Engine fact (D-017): the grader is the harness's own **`RubricMiddleware` (beta, deepagents ≥0.6.5)** — an LLM-as-judge grader subagent that reviews the transcript against a rubric, injects per-criterion feedback, and loops until `satisfied` / `max_iterations` / `failed` ([08 · Steering row](../08-deepagents-feature-map.md)). This is **an include in `packages/agent`, not new machinery** — audit correction #1 in doc 08 exists precisely because earlier docs implied otherwise.

**Not owned here** (neighbors): the new-task composer chrome and field plumbing — [F08 · task inbox](./08-task-inbox.md); rail layout/slotting — [F09 · task detail & streaming](./09-task-detail-and-streaming.md); plan-approval / HITL interrupt machinery (the *upfront* verification moment, §3.5) — [F10 · approvals inbox](./10-approvals-inbox.md) (D-010); the overall `packages/agent` composition — [F14 · agent package](./14-agent-package.md); the template catalog that carries rubric defaults — [F15 · task templates](./15-task-templates.md) (D-014); dcode companion surfaces — [F25](./25-dcode-integration.md) (D-013); dataset automation consuming verification signals — [F22 · org intelligence v1](./22-org-intelligence-v1.md).

## 2. Dependencies & seams

| Dependency / seam | Direction | Contract |
|---|---|---|
| `deepagents ≥0.6.5` RubricMiddleware (D-017) | consumes | Grading loop, terminal states `satisfied`/`max_iterations`/`failed`, configurable grader model ([08](../08-deepagents-feature-map.md)); exact constructor params **unverified** → §9-1, resolved by task 1 |
| [F14 · `packages/agent`](./14-agent-package.md) composition ([02 §3](../02-architecture.md), D-005: compose, never fork) | extends | Rubric compile step: `RubricSpec` (this spec, §4) → middleware config; middleware override-by-`.name` (≥0.7.0a3) if wrapping is needed |
| [F08 · task inbox](./08-task-inbox.md) (new-task composer) | provides surface | F16 defines the rubric field's format, helper copy, and advanced controls (§3.2); F08 owns placement/behavior of the composer itself |
| [F09 · task detail & streaming](./09-task-detail-and-streaming.md) (run-panel rail) | provides surface | F16 defines the verification panel's states and content (§3.3); F09 owns the rail slot order and responsive collapse |
| [F15 · task templates](./15-task-templates.md) (D-014: templates = assistant configs) | seam | Each template ships `rubric_default: RubricSpec \| null` (§3.2 table is the seam contract; F15 owns final catalog wording) |
| `packages/sdk` stream/state layer ([F04](./04-sdk-and-agent-sources.md); [03 §5](../03-ui-spec.md), D-011) | extends | `VerificationState` normalized at the SDK boundary (snake_case wire → camelCase, same rule as everything else) |
| Tracing metadata conventions ([02 §10](../02-architecture.md)) | extends | Adds `rubric`, `rubric_source`, `rubric_verdict` stamps (§4) |
| F22 org intelligence / [07 Layer 1](../07-org-intelligence.md) | downstream consumer | Verification verdicts + overrides feed the HITL-rejections→dataset automation rule (§3.7) |
| M2 milestone ([04](../04-roadmap.md)) | schedule | "RubricMiddleware wired into templates (rubric field in composer; verdicts/iterations in the run panel)" is an M2 exit line item |

## 3. Design

### 3.1 The grading loop (server side)

`packages/agent` includes `RubricMiddleware` in the template middleware set ([02 §3 Verification bullet](../02-architecture.md)). Per doc 08: the grader subagent reviews the transcript against the rubric after the worker finishes a pass, injects per-criterion feedback back into the loop, and the worker iterates until the grader returns `satisfied`, the iteration cap is hit, or the loop terminates `failed`. Deep Work adds only a **compile step**: a runtime-context-carried `RubricSpec` (per-run config propagates to subagents per [02 §3 context row](../02-architecture.md)) is translated into middleware configuration inside `packages/agent`. Whether the middleware accepts per-run rubrics natively or needs a thin named-override wrapper is §9-1; either way the UI contract (§4) is unaffected.

Grader visibility: doc 08 calls the grader a *subagent*, so grading passes are expected to surface in the `subagents` stream projection ([03 §3.2](../03-ui-spec.md)) — the panel derives its "grading in progress" state from that namespace (exact namespace/name is §9-2). Grader passes are traced like everything else; the panel links each pass to its LangSmith trace ([02 §10](../02-architecture.md): the trace is ground truth).

### 3.2 Rubric authoring

**Composer field (surface owned by F08).** Proposal — optimize for dcode-`/rubric`-grade simplicity ([research 14](../../research/14-dcode.md): "known criteria as quality gate"):

- A collapsed **Verification** section in the composer; expanding shows a plain-text criteria editor — **one criterion per line**, each nonblank line becomes one structured criterion. No nested syntax in v1; freeform-lines→structured-list is the format decision.
- Template defaults pre-fill the editor (visible + editable, never invisible magic).
- **Advanced** accordion: *Verification passes* (1–5, default 2) and *Grader model* (`provider:model` string per [02 §3](../02-architecture.md); default = template's task model).
- **Cost helper copy** (the cost surfacing, part 1): "Each verification pass runs a judge model over the full transcript and can trigger another working pass. More passes → higher confidence, more tokens." Deep Work does not do local cost accounting — token spend lives in LangSmith traces ([02 §10](../02-architecture.md); [01 non-goals](../01-vision.md)).

**Template defaults (seam contract to F15).** Templates ship rubric defaults per the [08 use-case-guides mapping](../08-deepagents-feature-map.md) ("each template = prompt + tools + middleware set (… rubric defaults …)"). Proposed catalog — F15 owns final wording:

| Template | Default | Criteria sketch | Passes | Rationale |
|---|---|---|---|---|
| Research | **on** | every load-bearing claim cited; all sub-questions answered; ≥2 independent sources for key claims; uncertainty stated | 2 | narrative output has no CI — the rubric is the only machine check |
| Writing | **on** | brief followed; requested structure present; consistent tone; no placeholders/TODOs | 2 | same |
| Data-analyst *(v2 — not wired in M2)* | **on** *(future default)* | every reported number traceable to executed code; charts labeled; caveats stated | 2 | pairs with the interpreter template ([08](../08-deepagents-feature-map.md)); id is v2-reserved in F15 §3.2 — design/sequencing in [F24](./24-org-intelligence-v2-v3.md) |
| Coding | **off** (available) | if enabled: tests actually run in transcript; diff scoped to task; PR description accurate | 1 | sandbox tests + diff review + CI already verify; don't double-pay a judge on top |

### 3.3 Verification panel (renders in F09's rail)

A rail section below the status block ([03 §3.2 run panel](../03-ui-spec.md)), states:

| State | Rendering |
|---|---|
| **No rubric** | Panel collapsed to one ghost row: "Verification: none · Add for next run →" (opens composer prefill; satisfies the [03 §7](../03-ui-spec.md) teach-the-next-action rule). Never a large empty panel. |
| **Grading (in progress)** | "Verifying — pass *n* of *max*", pulsing blue (running = primary-dark per [03 §1.1](../03-ui-spec.md)); grader subagent card visible in-thread like any subagent |
| **Satisfied** | Green **Verified** chip; criteria list all ✓; iteration count "passed on pass *n*/*max*". External-source rubrics: chip stays *Needs review* until human confirm (§3.4) |
| **Max iterations** | Amber; unmet criteria pinned to top with grader feedback expanded; actions per §3.4 |
| **Failed** | Amber (not red — see §3.4); grader's terminal reason shown |
| **Grader error** | Gray "Verification unavailable" + error row + *Retry verification* + trace link |
| **Overridden** | "Accepted by *actor* on *date* — 2 criteria unmet" badge, criteria list preserved |

Each criterion row: pass/fail/pending glyph (✓ green / ✕-style unmet amber / ○ pending — reusing subagent glyph conventions from [03 §3.2](../03-ui-spec.md)) + criterion text + chevron-expandable grader feedback (mono-quoted). Header shows grader model chip and per-pass **View trace ↗** links (cost surfacing, part 2: iteration count + trace links are how users see what grading cost — consistent with the never-re-implement-observability rule).

### 3.4 Failure semantics & overrides

Governing principle: **grader failure ≠ task failure, and rubric verdicts never flip a run to Failed.** Red is reserved for run errors ([03 §3.1 status chips](../03-ui-spec.md)); an unverified-but-complete task is *Needs review* (amber) — exactly the state the approvals-oriented inbox grouping (*Needs you*) is built for.

| Terminal state | Task status chip | User actions |
|---|---|---|
| `satisfied` (rubric `source` `template`/`user`/`template+user`) | Done (green) + Verified badge in inbox row | — |
| `satisfied` (`external` rubric source — §6 trust boundary) | Needs review (amber) — **never auto-Verified** | **Confirm Verified** (one click; records actor + timestamp like Accept anyway, then flips to Done + Verified) · Send back |
| `max_iterations` | Needs review (amber) | **Accept anyway** · **Send back** (steering message pre-filled with unmet criteria + grader feedback — rides the [03 §3.2](../03-ui-spec.md) composer, queue semantics) · **Raise cap & continue** (if per-thread cap raise is supported — §9-3) |
| `failed` | Needs review (amber) | Accept anyway · Send back (exact `failed` semantics vs `max_iterations` — §9-4) |
| grader model/infra error | task's own status stands; gray chip | Retry verification · trace link. Whether the reliability stack (`ModelRetryMiddleware` etc., [02 §3](../02-architecture.md)) already wraps grader calls is §9-5 |

**Accept anyway** is a first-class override: one click, records actor + timestamp as thread metadata (threads already carry metadata, e.g. `metadata.owner` per [02 §5](../02-architecture.md); Deep Work stores nothing itself — D-003, [01 non-goals](../01-vision.md)), flips chip to Done with the *Overridden* badge (§3.3), and emits the eval-fuel signal (§3.7). No confirmation dialog — the panel's unmet-criteria list *is* the informed-consent surface.

### 3.5 Why this exists: the cheap-verification thesis

Vision pillar 1 ([01](../01-vision.md)): trust in unverified agent output is collapsing (29% trust; 66% cite "almost right" as top frustration) — *verification UX is the product*. Deep Work brackets every task with two complementary checks:

- **Plan approval (upfront, human)** — verify *intent* before tokens are spent ([03 §3.2 PlanCard](../03-ui-spec.md); owned by [F10](./10-approvals-inbox.md)/[F09](./09-task-detail-and-streaming.md)).
- **Rubric grading (outcome, machine)** — verify the *result* before human attention is spent. The rubric converts "read the whole transcript to check if it's right" into "read k criterion verdicts, then spot-check via trace/diff".

The grading loop costs real tokens; the thesis is that judge tokens are cheaper than human review minutes — but only if the cost is visible and capped, hence: low default cap (2), cap and grader model user-configurable per task, iteration count + per-pass trace links always displayed, helper copy at authoring time (§3.2). Coding tasks default rubric-off because they already have cheaper verifiers (tests, CI, diffs — §3.2 table).

### 3.6 Goal lifecycle — v1.x · DESIGN-COMPLETE, NO TASKS IN §8

> Status: designed here, deliberately unscheduled ([04 backlog](../04-roadmap.md): "goal lifecycle (dcode-style draft→review→amend on top of RubricMiddleware)"). Nothing in §8 implements this section.

dcode's `/goal` pattern ([research 14](../../research/14-dcode.md); dcode is the companion per D-013, integration surfaces in [F25](./25-dcode-integration.md)): objective → **agent drafts acceptance criteria** → inline human review (accept / edit / revise / cancel) → goal persists across turns, **each turn graded** against the criteria until completion is approved; amend/pause/resume; per-goal grader model and max-iterations (`/goal model`, `/goal max-iterations`). [02 §9](../02-architecture.md) adopts this as "Deep Work's richer plan-approval", with RubricMiddleware as the engine (D-017) and dcode's lifecycle as the UX reference.

How it layers on F16's machinery — a goal **is** a rubric with three deltas:

1. **Authorship inverts**: the agent drafts the criteria; the human approves. The draft arrives as a standard HITL interrupt ([03 §3.3](../03-ui-spec.md) v1 contract, D-010) with decisions approve / edit / reject — the same `InterruptCard`/`PlanCard` surfaces ([F10](./10-approvals-inbox.md)), a new payload type. No new approval machinery.
2. **Grading cadence changes**: per *turn* (every follow-up graded against the goal) instead of per *task run*. Requires the rubric to persist in thread state across turns — dcode proves the pattern; the cloud-side mechanism is a v1.x design point flagged in [02 §9](../02-architecture.md) (memory-layout mapping class of work).
3. **Lifecycle states**: `drafting → in_review → active → paused → amending (re-review) → done (completion approved) | cancelled`. *Pause* suspends grading without discarding criteria; *amend* edits criteria mid-goal and re-enters review; *done* requires explicit human completion-approval even when the grader says satisfied (dcode: "until completion approved").

UI it adds (and only this): a **goal card** pinned at the top of the thread — the criteria checklist with live per-criterion state across turns, Amend/Pause/Resume actions; the §3.3 verification panel re-badges as goal progress (same `VerificationState`, plus `lifecycle` field); the composer gains a "Draft acceptance criteria first" toggle; inbox rows show a goal-progress fraction where a goal is active. Everything else — grading loop, criteria rows, verdict chips, override semantics — is §3.1–3.4 unchanged.

### 3.7 Eval-fuel seam (downstream: F22)

[07 Layer 1](../07-org-intelligence.md) already plans "HITL rejections/edits → dataset (eval fuel for later)" as an automation rule. F16 widens the funnel with strictly higher-signal outcome labels: `satisfied` verdicts (positive examples), **Accept anyway** overrides (grader-said-no-human-said-yes — grader-calibration gold), `max_iterations` exhaustions (hard cases), and Send-back messages (human-authored feedback paired with a failing transcript). F16's only obligation: stamp the metadata (§4) so [F22](./22-org-intelligence-v1.md)'s automation rules and the org-analyst digest can filter on it. Dataset creation itself is F22's territory; evals integration is explicitly post-v1 ([04 backlog](../04-roadmap.md)).

## 4. Contracts

**`RubricSpec`** — authoring format, produced by the composer (F08), stored in run config/runtime context, compiled by `packages/agent`:

```ts
type RubricSpec = {
  criteria: { id: string; text: string }[];   // id = stable slug, generated client-side
  maxIterations: number;                      // default 2, UI range 1–5
  graderModel?: string;                       // "provider:model"; default = template task model
  source: "template" | "user" | "template+user"   // template default, authored, or edited default
        | "external";                             // carried in a schedule/webhook payload (§6) — gates the Verified mapping (§3.4)
};
```

**`VerificationState`** — read contract for the panel, normalized in `packages/sdk` (camelCase canonical per D-011, [03 §5](../03-ui-spec.md)):

```ts
type VerificationState = {
  status: "none" | "grading" | "satisfied" | "maxIterations" | "failed"
        | "graderError" | "overridden";
  iteration: number;                          // current (streaming) or final pass count
  maxIterations: number;
  graderModel: string;
  criteria: { id: string; text: string;
              verdict: "pass" | "unmet" | "pending"; feedback?: string }[];
  override?: { actor: string; at: string };   // set by Accept anyway
  passTraceUrls: string[];                    // one per grading pass
};
```

Upstream source of this state (dedicated state channel vs. subagent projection vs. thread values) is §9-2; the SDK normalization layer is the seam that keeps the panel stable while that resolves.

**Metadata stamps** — extends the [02 §10](../02-architecture.md) run-metadata convention (`task_type`, `agent`, `actor`, …):

| Key | Values | Consumer |
|---|---|---|
| `rubric` | `true`/absent | LangSmith filters, F22 partitions |
| `rubric_source` | `template` · `user` · `template+user` · `external` (v1.x: `goal`) | grader-calibration analysis; §3.4 Verified gating |
| `rubric_verdict` | terminal `VerificationState.status` | F22 automation rules (§3.7) |
| `verification_override` | `{actor, at}` on thread metadata | audit, eval fuel |

## 5. Edge cases & failure modes

| Case | Behavior |
|---|---|
| Rubric with zero criteria after parse (blank lines only) | Composer refuses to attach; treated as "no rubric" — never ship an empty rubric to the middleware |
| Compacted transcript (Summarization middleware ran) | Grader may see summarized history — accuracy caveat; whether the middleware grades pre- or post-compaction transcript is §9-6. Panel shows the [03 §3.2](../03-ui-spec.md) summarized-history marker context regardless |
| Grading loop meets `ModelCallLimitMiddleware`/`ToolCallLimitMiddleware` caps ([02 §3](../02-architecture.md)) | Limit event already surfaces in the rail; verification ends `graderError`-equivalent, task status stands |
| Steering message arrives mid-grading | Default double-texting `enqueue` ([02 §7](../02-architecture.md)) — queued behind the grading loop; the queue-vs-interrupt affordance stays available |
| User re-runs / forks from checkpoint ([03 §3.2](../03-ui-spec.md)) | Each branch grades independently; `VerificationState` is per-run, panel follows the active branch |
| Rubric attach on follow-up turn (mid-thread) | Out of v1 scope pending §9-7; v1 rule: rubric fixed at task creation, the ghost row (§3.3) prefills the *next* task |
| Malformed/unrecognized verdict payload | Panel degrades to raw-JSON card with trace link — same schema-tolerant rule as interrupts ([03 §3.3](../03-ui-spec.md)); never crash the rail |
| Grader loops on an impossible criterion (e.g. "make CI pass" with no sandbox) | Cap bounds the damage (≤ maxIterations); Send back / Accept anyway resolve; template defaults avoid tool-dependent criteria in tool-less templates |

## 6. Security & privacy

- **Trust boundary unchanged**: the grader runs inside the deployment as a subagent — the transcript never leaves the user's org runtime + tracing ([01](../01-vision.md): "everything runs in your org"). One nuance: a *different grader model provider* means transcript content flows to that provider too — which is why the grader model chip is always visible in the panel (§3.3), never silent config.
- **Rubric text is prompt input to the judge.** User- and template-authored rubrics share the trust level of the task prompt itself. Rubrics arriving via schedule/webhook-fired tasks are untrusted-payload content (`source: "external"`, §4): they render inside untrusted-content boundaries ([02 §10](../02-architecture.md)) **and their `satisfied` verdict never maps to Done + Verified on its own** — external-rubric tasks land *Needs review* until a human clicks Confirm Verified (§3.4). A hostile rubric can therefore pass the judge it authored, but cannot mint a Verified badge or skip the human surfaces (diff review, PR) before anything merges. Whether an authenticated payload origin may bypass the confirm is §9-10.
- **Override attribution**: Accept anyway stamps the acting identity from the MDA identity plane ([02 §5](../02-architecture.md)) — auditable via thread metadata + trace, stored in the org, not by Deep Work.
- No new secrets, no new storage, no new egress; grading inherits sandbox zero-secret rules untouched ([02 §4](../02-architecture.md)).

## 7. Acceptance criteria

1. A research-template task created with the default rubric runs the grading loop against a real deployment; the panel shows per-criterion verdicts, feedback, and iteration count matching the LangSmith trace.
2. Composer: template default pre-fills and is editable; one-line-per-criterion parse verified; passes cap and grader model configurable; cost helper copy present.
3. A task exhausting `maxIterations` lands as **Needs review** (amber, *Needs you* inbox group) — never Failed/red; Accept anyway flips it to Done + Overridden badge and stamps `verification_override` metadata; Send back prefills the steering composer with unmet criteria.
4. A forced grader model error leaves the task's own status untouched and renders the gray "Verification unavailable" state with retry.
5. Tasks without a rubric show only the one-line ghost row — no empty panel.
6. `rubric`, `rubric_source`, `rubric_verdict` appear in run metadata and are filterable in LangSmith (F22 seam verified).
7. Golden-transcript tests (M0 Spike 3 pattern, [04](../04-roadmap.md)) cover all seven panel states in §3.3.
8. Coding template ships rubric-off; enabling it via composer works without template changes.

## 8. Task breakdown

v1/M2 only — goal lifecycle (§3.6) is deliberately absent.

| # | Task | Depends on | Definition of done |
|---|---|---|---|
| 1 | **Harness probe**: pin `deepagents ≥0.6.5`, exercise RubricMiddleware against `langgraph dev`; document constructor params, verdict/state surface, grader-subagent stream visibility, per-run config path | M0 spikes ([F02](./02-m0-spikes.md)) done | §9 items 1–6 answered or upstreamed as issues (D-005, [02 §8](../02-architecture.md) no-fork rule); contract notes committed |
| 2 | **`packages/agent` wiring**: RubricSpec compile step (runtime context → middleware config), research/writing defaults on, coding off (data-analyst is v2 → [F24](./24-org-intelligence-v2-v3.md)) | 1; [F14](./14-agent-package.md) v0 (M1) | Rubric-graded run completes on MDA + `langgraph dev`; template defaults per §3.2 table land as F15 seam data |
| 3 | **SDK layer**: `VerificationState` normalization + casing hygiene, per-branch state | 1 | Typed state hydrates from live stream and from thread reload; unit tests on wire fixtures |
| 4 | **Composer rubric field** (in F08's surface) | 3; [F08](./08-task-inbox.md) composer exists | §3.2 field: parse, prefill, advanced controls, helper copy; RubricSpec attached to run config |
| 5 | **Verification panel** (in F09's rail) | 3; [F09](./09-task-detail-and-streaming.md) rail exists | All §3.3 states rendered incl. ghost row; criterion rows with expandable feedback; per-pass trace links |
| 6 | **Failure & override UX**: status-chip mapping, Accept anyway (+ metadata stamp), Send back prefill, Retry verification | 5 | §3.4 table behaviors demonstrable; override attributed to actor identity |
| 7 | **Metadata stamps + eval-fuel hook**: run metadata keys, documented F22 automation-rule recipe | 2, 6 | §4 stamps present on real runs; recipe doc handed to [F22](./22-org-intelligence-v1.md) |
| 8 | **Golden-transcript tests** for the seven panel states + edge cases (§5 rows 1, 5, 7) | 3, 5, 6 | CI-green fixtures against `langgraph dev`; acceptance §7-7 satisfied |

## 9. Open questions

1. **RubricMiddleware exact API** (constructor params; rubric schema — string vs structured criteria; whether per-run rubrics are native or need a named-override wrapper reading runtime context; `max_iterations` default). Never guessed in this spec; task 1 resolves.
2. **Verdict/state exposure**: which stream projection / state channel carries per-criterion verdicts and iteration count — dedicated values channel, the grader subagent's namespace, or neither (trace-only)? Determines how thin `VerificationState` normalization can be.
3. Can the iteration cap be raised on a live thread ("Raise cap & continue"), or only per-run at creation?
4. Exact semantics of terminal `failed` vs `max_iterations` (grader-declares-unsatisfiable vs cap-hit?) — doc 08 names the three states without defining `failed`.
5. Does the reliability stack ([02 §3](../02-architecture.md)) wrap grader model calls, or does the grader need its own retry/fallback config?
6. Does the grader see the full transcript or the post-Summarization compacted one?
7. Mid-thread rubric attach (dcode `/rubric` is sticky-or-one-turn mid-session) — supported by the cloud middleware per-turn, or creation-time only? Gates the follow-up-composer affordance.
8. JS parity: RubricMiddleware availability in `deepagents` JS (research 02 flags unverified JS divergences) — matters only if `packages/agent` ever mirrors to JS; Python-first per D-008 / [02 §11](../02-architecture.md).
9. Goal lifecycle (v1.x): where do approved criteria persist across turns (thread state channel vs `/memories/` file) — the [02 §9](../02-architecture.md) "needs design" flag; blocks nothing in M2.

## 10. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| RubricMiddleware is beta and shifts under us (harness releases ~weekly, [research 02](../../research/02-deepagents-harness.md)) | High | Med | Pin + renovate group ([02 §8](../02-architecture.md)); RubricSpec/VerificationState seams isolate UI from middleware churn; golden-transcript tests catch drift |
| Verdict state turns out not to be streamable (trace-only) | Med | Med | Fallback: panel renders terminal state from thread values on completion + "grading…" from run status only; degraded but shippable; upstream issue filed |
| Grading loops silently burn tokens on vague user criteria | Med | Med | Low default cap (2), hard UI max (5), cost copy at authoring, iteration count + trace links always visible (§3.5) |
| Judge quality: false "Verified" badges erode the exact trust the pillar targets | Med | High | Verified badge always paired with criteria list + trace links (verify the verifier); Accept-anyway/override telemetry (§3.7) measures grader calibration; template criteria kept concrete/checkable |
| Users conflate rubric failure with task failure | Low | Med | Amber-not-red rule (§3.4) enforced in `StatusChip`; copy says "completed, not verified" |
| F08/F09 land later than task 4/5 need | Med | Low | Panel and field are self-contained components (`packages/ui`); can develop against static `VerificationState` fixtures like the M0 shell |

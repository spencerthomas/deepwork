# U5 · M0 Spike 3 — Stream contract

*Feature deep-dive · 2026-07-23 · Milestone M0 · Status: planning*
*Parent: [../2026-07-22-001-feat-deepwork-v1-delivery-plan.md](../2026-07-22-001-feat-deepwork-v1-delivery-plan.md) · Spec: [../../plan/02-architecture.md](../../plan/02-architecture.md) §7 (streaming & data plane), [../../plan/04-roadmap.md](../../plan/04-roadmap.md) M0 Spike 3*

---

## Objective

Capture **golden transcripts** of the Agent Streaming Protocol v2 as produced by a real runtime, and turn them into contract tests. These transcripts become the **frozen contract** every `useStream`-consuming unit (U7 types, U10 streaming, U11 HITL, U14 subagents) is built and tested against — so the UI is never built on an assumed shape, and weekly `@langchain/react` bumps are regression-guarded.

## Why this is risky

- `@langchain/react` 1.0.x releases **weekly** (roadmap: "High likelihood, low-med impact" churn). Building UI directly against the live SDK shape means every bump can silently break projections.
- The prototype's `ThreadEvent` union is an **invention** — the real projections (`messages`, `toolCalls`, `values.todos`, `values.files`, `subagents` map, `interrupts`, checkpoints) have shapes that must be observed, not guessed.
- **Casing hygiene** is a known bug class (arch §7): wire fields are snake_case; JS middleware emits camelCase HITL payloads, Python emits snake_case; the SDK normalizes to camelCase canonical **except** `reviewConfigs.actionName/argsSchema`, which the UI must read in **both** casings. Getting this into the golden tests up front eliminates the bug class.

## Probe methodology

1. **Runtime.** Run `langgraph dev` against the minimal agent from U4 (reuse it). No API key / license needed; state in `.langgraph_api/`. Where a projection only appears on MDA (e.g. certain subagent/memory channels), also capture against the MDA deployment from U4.
2. **Capture raw SSE/WS frames** for each projection type, saving to `.jsonl` golden files:
   - **Content blocks** (`messages` / narration) — streaming text deltas + final.
   - **`AssembledToolCall`** (`toolCalls`) — tool call open → streaming args → output → close.
   - **HITL** — `interrupt` emission (`HITLRequest` shape) + `respond()`/`respondAll()` round-trip, including `reviewConfigs.allowedDecisions` / `actionName` / `argsSchema`.
   - **Subagent namespaces** — the `subagents` map; frames attributed to a nested subagent.
   - **`values.todos`** — todo list state channel updates.
   - **`values.files`** (`FileData` variants) — file tree / content channel.
   - **Checkpoints** — checkpoint channel for branching / `submit(input, {forkFrom})` time-travel.
   - **Resume** — `stream_resumable` + `Last-Event-ID` replay and thread-level join stream.
3. **Casing capture.** Deliberately capture HITL payloads from **both** a JS-middleware tool and a Python tool to observe the camelCase/snake_case split, and confirm exactly which fields the SDK leaves dual-cased.
4. **Write contract tests.** `packages/sdk/tests/stream-contract.test.ts` parses each golden `.jsonl` through the SDK's normalization layer (built in U7) and asserts the normalized projection shape. Tests fail loudly if a future SDK bump changes the shape.

## What the golden set must cover (checklist)

- [ ] content-block stream (delta + final)
- [ ] tool call full lifecycle (open → args stream → output → close)
- [ ] `values.todos` updates
- [ ] `values.files` / `FileData` variants
- [ ] HITL interrupt (single tool)
- [ ] HITL interrupt (batched — multiple tool calls in one interrupt)
- [ ] HITL `respond` / `respondAll` round-trip
- [ ] `reviewConfigs` casing (camelCase canonical + dual-cased `actionName`/`argsSchema`)
- [ ] subagent namespace attribution
- [ ] checkpoint channel (for fork/time-travel)
- [ ] `Last-Event-ID` resume / thread join stream

## Artifacts

- `packages/sdk/tests/golden/*.jsonl` — the captured transcripts (the contract).
- `packages/sdk/tests/stream-contract.test.ts` — assertions (initially may be red/skipped until U7 builds the normalizer; the transcripts themselves are the deliverable here).
- `docs/spikes/2026-07-23-spike-stream-contract.md` — memo documenting: which projections were observed, any divergence from the `@langchain/react` published types, the exact casing map, and which frames required MDA (vs `langgraph dev`).

## Relationship to U7

This spike **produces the golden files and the empty test harness**; U7 (`packages/sdk`) **builds the normalizer that makes the tests pass** and defines `src/types.ts` from the observed shapes. Splitting it this way means the contract is frozen from a real runtime *before* any normalization code is written — the code conforms to the transcripts, not the other way around.

## Exit criteria

- Every checklist item above has at least one golden `.jsonl` transcript captured from a real runtime.
- The casing map is documented precisely (canonical camelCase + the dual-cased exceptions).
- The contract-test harness exists and references the golden files (passing or pending-U7).
- Any protocol-vs-published-types divergence is written down.

## Test scenarios

- **Validation:** each golden transcript is valid, replayable `.jsonl` captured from `langgraph dev` (or MDA where required).
- **Validation:** a batched HITL interrupt with ≥2 tool calls is captured (U11 depends on this shape).
- **Validation:** `Last-Event-ID` resume produces a replay that reconstructs stream position (U10 reconnection depends on this).
- **Edge case:** the dual-cased `reviewConfigs.actionName`/`argsSchema` appears in the captured payload and is noted for the U11 casing-tolerant reader.
- **Regression intent:** a deliberately hand-edited "changed shape" transcript makes the contract test fail — proving the guard works.

## Downstream units gated

- **U7** (`packages/sdk`) — `src/types.ts` and the stream normalizer are authored against these transcripts.
- **U10** (live task detail streaming) — every projection→renderer mapping is validated against the golden set.
- **U11** (approvals / HITL) — the `HITLRequest` shape, batching, and casing come from here.
- **U14** (subagent cards, fork-from-checkpoint) — subagent namespace + checkpoint channel shapes come from here.

## Dependencies

- **Upstream:** U1 (workspace, `packages/sdk` stub to hold golden files + tests). Reuses the minimal agent from U4.
- **Downstream:** U7, U10, U11, U14. Run alongside U4 (same deployment/agent).

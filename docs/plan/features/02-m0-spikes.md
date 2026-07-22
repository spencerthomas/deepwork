# F02 · M0 de-risking spikes

*Deep Work feature spec · 2026-07-22 · Status: draft · Milestone: M0 · Depth: implementation-ready*

Sources: [../04-roadmap.md](../04-roadmap.md) (M0) · [../02-architecture.md](../02-architecture.md) (§5–§7) · [../05-oss-setup.md](../05-oss-setup.md) · [../07-org-intelligence.md](../07-org-intelligence.md) (§open questions) · [../../research/12-lifecycle-auth-followup.md](../../research/12-lifecycle-auth-followup.md) · [../../research/20-gapfill-mda-api.md](../../research/20-gapfill-mda-api.md) · [../../research/21-gapfill-ui-contract.md](../../research/21-gapfill-ui-contract.md) · [../../research/23-gapfill-runtime-tiers.md](../../research/23-gapfill-runtime-tiers.md) · [../decisions.md](../decisions.md)

## 1. Scope

F02 turns the three riskiest unknowns in the plan into recorded facts before M1 code depends on them ([roadmap M0](../04-roadmap.md): "Exit: the three riskiest unknowns are facts"). Each spike is a real experiment: hypothesis → exact probes → artifacts → exit criteria → timebox → red-path fallback.

| Spike | Question it settles | Resolves | Primary artifact |
|---|---|---|---|
| **S1 — OAuth** | Can Deep Work be OAuth-first ("Sign in with LangSmith"), or key-first at launch? | O-001, O-002, O-008 | Auth decision memo |
| **S2 — MDA loop** | Does the full `mda init/dev/deploy` + external-client loop work end-to-end, and can we reproduce deploy via raw API (no CLI)? | O-003 | MDA loop memo + deploy-replay script |
| **S3 — stream contract** | Does Agent Streaming Protocol v2 behave as researched, pinned as executable golden-transcript tests? | protocol assumptions in [research 21](../../research/21-gapfill-ui-contract.md) | Permanent contract-test harness + fixtures |

In scope: spike code layout (throwaway `spikes/` vs permanent `packages/sdk` test dirs), the decision-memo format, and the handoff of S3's harness into permanent CI. Out of scope (neighbors — link, don't build): monorepo scaffold and the CI pipeline that *runs* the contract tests → F01 ([./01-monorepo-and-ci.md](./01-monorepo-and-ci.md)); the production SDK layer that *consumes* the pinned contract → F04 ([./04-sdk-and-agent-sources.md](./04-sdk-and-agent-sources.md)); production auth routes, agent package, and all UI.

## 2. Dependencies & seams

| Dependency | Direction | Notes |
|---|---|---|
| Beta MDA account (tom@) | S1/S2 need it | MDA invocation API is design-partner-gated during beta; the user has access ([../02-architecture.md](../02-architecture.md) §6, [research 20](../../research/20-gapfill-mda-api.md)) |
| F01 scaffold (`packages/sdk` workspace, CI jobs) | S3's permanent home | S1/S2 run pre-scaffold from `spikes/`; S3 harness lands in `packages/sdk` as its first real code. CI job wiring is F01's contract (see §4) |
| F04 SDK | consumes S3 | Golden fixtures + casing invariants become F04's regression net for `@langchain/react` 1.0.x churn (risk table, [../04-roadmap.md](../04-roadmap.md)) |
| Version pins | all spikes | `@langchain/react` ^1.0.28, `@langchain/langgraph-sdk` ^1.9.23+, `@langchain/protocol` 0.0.18, `managed-deepagents` 0.4.0-dev channel, `langgraph-cli` (MIT), deepagents py 0.6.12 / js 1.11.1 ([../05-oss-setup.md](../05-oss-setup.md)) |
| D-022 (Next.js frontend) | context | Spike clients stay throwaway Node/TS scripts; production wiring per D-022 is not spike work |
| **P-005 (provisional)** — Python FastAPI `apps/server` glue | S1/S2 memo recommendations | Supersedes older doc text placing OAuth/key-proxy glue in Next.js server routes ([../02-architecture.md](../02-architecture.md) §1, [../05-oss-setup.md](../05-oss-setup.md) repo tree). Memos must phrase "where the callback/proxy lives" as `apps/server`. If P-005 flips, only memo recommendations change, not spike evidence |
| O-001/O-002/O-003/O-008 | resolved by F02 | Memo step files decision-log updates (see §3.4) |

## 3. Design

Spike discipline: every probe is scripted (re-runnable), every HTTP exchange is captured to a transcript, every claim in a memo cites a transcript line. A spike that hits its timebox without a green result **defaults to its red-path fallback as the decision** — no open-ended extensions inside M0.

**Code layout.** Top-level `spikes/` directory, excluded from pnpm workspaces and CI, deleted at M1 entry (memos and fixtures survive):

```
spikes/
  s1-oauth/       # shell + small TS scripts: discovery, DCR, PKCE, device flow, bearer matrix
  s2-mda/         # minimal mda project + deploy-replay script + capture configs
  s3-stream/      # scratch recordings only — the real harness lives in packages/sdk (below)
  */transcripts/  # raw captures, GITIGNORED (see §6)
packages/sdk/tests/contract/
  server/         # deterministic fixture graph (tiny langgraph project run under `langgraph dev`)
  harness/        # recorder, normalizer, asserters, adapter-replay runner
  fixtures/       # committed golden transcripts, one .jsonl per scenario
  scenarios/      # per-scenario test specs (vitest)
```

Rationale: S1/S2 produce *knowledge*, so their code is throwaway; S3 produces a *permanent regression net* (roadmap M1–M4 all lean on it), so it starts in its forever-home. [../05-oss-setup.md](../05-oss-setup.md) sketches contract tests under the agent package's CI lane; we place the harness in `packages/sdk` because it tests the **client** contract (HITL casing normalization already lives in `packages/sdk` per that doc) — F01 owns reconciling the CI wording.

### 3.1 Spike 1 — OAuth ("Sign in with LangSmith")

**Hypothesis.** LangSmith's OAuth 2.1 server (RFC 8414 metadata, public DCR, PKCE, RFC 8628 device flow — confirmed to exist, [research 12](../../research/12-lifecycle-auth-followup.md)) issues bearer tokens whose scopes cover (a) control-plane reads/writes on `api.smith.langchain.com` and (b) data-plane calls on `*.langgraph.app` deployments — enough to ship OAuth-first with API-key paste as fallback ([../02-architecture.md](../02-architecture.md) §5).

**Probe steps** (scripted in `spikes/s1-oauth/`):

1. **Discovery**: GET `/.well-known/oauth-authorization-server` on candidate hosts (`smith.langchain.com`, `api.smith.langchain.com`; the exact issuer host is recorded, not assumed). Record full metadata: `scopes_supported`, grant types, registration/revocation endpoints, PKCE methods.
2. **DCR**: POST `/oauth/register` (RFC 7591) a public client with a loopback redirect. Record accepted redirect classes, client lifetime, any allowlist behavior.
3. **PKCE code flow**: `/oauth/authorize` with S256 (required per [research 12](../../research/12-lifecycle-auth-followup.md)) → token. Record token type, lifetime, refresh behavior, scope granted vs requested.
4. **Device flow**: `/oauth/device/code` (RFC 8628) with the same client → token. (Desktop/Tauri sign-in path, [../02-architecture.md](../02-architecture.md) §5.)
5. **Bearer matrix** — run each token (PKCE bearer, device bearer) and each key type (PAT; workspace service key `lsv2_sk_`; org-scoped key + `X-Tenant-Id`) against:

| Target | Call | Verifies |
|---|---|---|
| Control plane | `GET /v2/deployments` | O-001: control-plane read |
| Control plane | `GET /v1/platform/hub/repos/` | Context Hub read |
| Context Hub **write** | commit to a scratch hub repo (Hub directory get/commit surface, [research 20](../../research/20-gapfill-mda-api.md)) | **O-008**: review-loop commits under OAuth ([../07-org-intelligence.md](../07-org-intelligence.md) open q. 2) |
| Data plane (`*.langgraph.app`) | `langgraph_sdk get_client(url, headers={Authorization: Bearer …})` → assistants search + thread create on the S2 deployment | O-002: bearer acceptance at deployment URL (documented for beta users, [research 20](../../research/20-gapfill-mda-api.md)) |

   Ordering note: the data-plane leg needs S2's deployment (or any pre-existing deployment in the beta org) — schedule S1.5 after S2.2.
6. **Teardown**: revoke tokens via the metadata-advertised revocation endpoint; deregister/abandon the DCR client.

**Artifacts**: `docs/plan/memos/M0-S1-auth.md` (auth decision memo: **OAuth-first vs key-first**, per §3.4 format) + bearer-matrix table + redacted transcripts. **Exit criteria**: every cell of the bearer matrix has a recorded yes/no; memo states the launch posture and the O-008 verdict. **Timebox**: 2 dev-days. **Red path**: any blocking cell fails (no `scopes_supported` coverage, DCR refused, data plane rejects bearers) → **key-first at launch** — PAT/service-key paste + server-side proxy is a complete fallback ([../04-roadmap.md](../04-roadmap.md) risk table); OAuth ships later behind the same seam. Partial green (control plane yes, data plane no) is a legitimate memo outcome: OAuth for control plane, deployment identity (S2) for data plane.

### 3.2 Spike 2 — MDA loop

**Hypothesis.** With the beta account, a minimal agent goes `mda init → mda dev → mda deploy` to a live `*.langgraph.app` deployment; an external `useStream` client works against it under both identity presets; and the deploy is reproducible with raw control-plane calls (`POST /v2/deployments` → signed-URL tarball upload → revision polling) without the CLI — so Deep Work's deploy wizard (M3) can be built on the public control plane ([../02-architecture.md](../02-architecture.md) §6, [research 20](../../research/20-gapfill-mda-api.md)).

**Probe steps** (`spikes/s2-mda/`):

1. **Init/dev**: `mda init` a minimal project (`agent.py`, `instructions.md`, `identity.py` with `define_identity(preset=…)`); `mda dev` (sets `MDA_LOCAL_DEV=1`, synthetic actor `mda:local-dev`); confirm the local loop streams.
2. **Deploy with capture**: `mda deploy` behind an HTTP-capturing proxy. Record verbatim: the `POST /v2/deployments` payload — including the actual shape of the undocumented `managed_deep_agent` marker (flag vs `deployment_type` enum vs object; open in [research 20](../../research/20-gapfill-mda-api.md)) — `POST /v2/deployments/{id}/upload-url` → signed PUT (200 MB cap), `/revisions` polling cadence, and the post-DEPLOYED cron reconcile against the deployment's own `/runs/crons(/search)`. Also record key resolution (`LANGGRAPH_HOST_API_KEY → LANGSMITH_API_KEY → LANGCHAIN_API_KEY`) and the `api.host.langchain.com` / `api.smith.langchain.com` host split as observed.
3. **External client**: throwaway `@langchain/react` `useStream` script against the deployment URL, both identity modes: (a) `trusted_backend` — forward `X-MDA-Ingress-Secret` + `X-MDA-Actor-Id` (+ `X-MDA-Tenant-Id`); (b) `validated_token` — mint an HS256 guest token via public `POST /identity/guest` (signed with `MDA_GUEST_SIGNING_KEY`) and send as Bearer. Assert streaming works and thread scoping stamps `metadata.owner` per actor ([research 20](../../research/20-gapfill-mda-api.md) identity internals).
4. **Deploy replay without CLI**: a standalone script re-implements step 2's captured sequence (create → upload-url → tarball PUT → revision poll) and produces a second working deployment. Diff its transcript against the CLI's.
5. **Teardown**: delete scratch deployments; rotate ingress/guest secrets.

**Artifacts**: `docs/plan/memos/M0-S2-mda.md` + redacted CLI-vs-replay transcript diff + the replay script (throwaway; its knowledge feeds F04's control-plane client). **Exit criteria**: dev loop, deploy, both identity modes, and CLI-free replay each demonstrably green (or documented red with the exact failing call); `managed_deep_agent` marker shape recorded. **Timebox**: 3 dev-days. **Red path**: `mda deploy` or replay rejected (beta gating) → escalate to the LangChain beta contact **and** immediately fall back to a classic `langgraph.json` deployment of the same minimal agent (fully public path, feature-equivalent for v1 scope — [../04-roadmap.md](../04-roadmap.md) risk table) so S1's data-plane leg and S3's fallback recorder target still exist.

### 3.3 Spike 3 — stream contract (golden transcripts → permanent CI tests)

**Hypothesis.** The protocol-v2 behaviors Deep Work's UI depends on ([research 21](../../research/21-gapfill-ui-contract.md)) hold against a live `langgraph dev` server and can be frozen as replayable fixtures, so `@langchain/react` 1.0.x weekly churn is caught by CI instead of by users.

**Harness** (`packages/sdk/tests/contract/`):

- **Fixture server**: a deterministic graph project run under `langgraph dev` (no API key, no license check, `LANGGRAPH_CLI_NO_ANALYTICS=1`, state in `.langgraph_api/` — [research 23](../../research/23-gapfill-runtime-tiers.md)). Scripted canned outputs, **no live LLM** in replay or CI; scenarios needing model-shaped output (e.g. reasoning deltas) are recorded once against a real model, normalized, frozen.
- **Recorder**: drives `POST /threads/{id}/commands` and reads `POST /threads/{id}/stream/events` (SSE), capturing verbatim events (id/event/data) per scenario.
- **Normalizer**: replaces UUIDs/thread ids/checkpoint ids/timestamps with stable placeholders (`{{uuid:1}}` …), preserving order, field names, and **casing** exactly. Output: `fixtures/<scenario>.jsonl` with a metadata header (server + `@langchain/protocol` 0.0.18 + SDK versions, record date).
- **Asserters**, two layers: (1) *shape* — every event parses against `@langchain/protocol` 0.0.18 types; (2) *semantics* — per-channel state-machine invariants (not byte equality), plus a client-level pass feeding fixtures through `useStream` via the `AgentServerAdapter` custom-transport seam ([research 23](../../research/23-gapfill-runtime-tiers.md)) and asserting the projections (`messages`, `toolCalls`, `subagents`, `interrupts`).
- **Two CI modes** (seam to F01): `replay` — fixtures only, no server, runs on every PR; `live` — boots `langgraph dev`, re-records, diffs against fixtures; scheduled weekly with the renovate cadence ([../05-oss-setup.md](../05-oss-setup.md)).

**Scenario matrix** (each = one fixture + one test spec):

| # | Scenario | Channels | Invariants asserted |
|---|---|---|---|
| 1 | Plain text stream | messages | `message-start → content-block-start/delta/finish → message-finish`; `text-delta` accumulation; snake_case wire fields |
| 2 | Reasoning deltas | messages | `reasoning-delta` blocks stream and finish before/alongside text blocks |
| 3 | Tool call lifecycle | messages, tools | `block-delta` partial-JSON args; `tool_call_chunk` → `tool_call` upgrade at `content-block-finish`; `tool-started → tool-output-delta* → tool-finished`; `AssembledToolCall` status `running→finished` |
| 4 | Tool error | tools | `tool-error {message}` → status `error`, `output` stays null |
| 5 | HITL round-trip | input, values | Interrupts hydrate from `getState().tasks[].interrupts` + live `input.requested {interrupt_id, payload}`; `respond()/respondAll()` emit `input.respond {namespace, interrupt_id, response}`; all four `decisions` (`approve`/`edit`/`reject`/`respond`); reject → ToolMessage `status='error'`; casing invariant: `reviewConfigs.actionName/argsSchema` readable in **both** casings (the un-aliased exception) |
| 6 | Subagent namespaces | tools, values | `SubagentDiscoverySnapshot` fields; namespace `tools:<toolCallId>` (+ legacy `task:` tolerance); lazy namespaced subscription delivers child messages |
| 7 | Resume | SSE ids | Kill mid-stream, reconnect with `Last-Event-ID` (`stream_resumable`): no gap, no duplicates |
| 8 | Double-texting | commands | Second `submit` mid-run with `multitask_strategy: enqueue` → queued run executes after; **observed** server behavior is recorded as the contract ([research 21](../../research/21-gapfill-ui-contract.md) flags enqueue as possibly client-side only) |
| 9 | Checkpoints/fork | checkpoints | Envelopes `{id, parent_id, step, source}`; `submit(input, {forkFrom})` branches |

**Artifacts**: committed harness + 9 fixtures + `docs/plan/memos/M0-S3-stream.md` recording every divergence between research and observation. **Exit criteria**: all 9 scenarios recorded and green in replay mode locally; harness handed to F01 with the two CI modes specified. **Timebox**: 4 dev-days. **Red path**: per-scenario — if `langgraph dev` lacks a feature (candidates: `checkpoints` channel acceptance, `Last-Event-ID` replay — open in [research 21](../../research/21-gapfill-ui-contract.md)), record that fixture against S2's MDA deployment instead and tag it `target: deployment`; if a behavior contradicts research (e.g. enqueue), the fixture pins *observed* behavior and an upstream issue is filed (no-forks policy, [../02-architecture.md](../02-architecture.md) §8).

### 3.4 Decision-memo format (all spikes)

One file per spike at `docs/plan/memos/M0-S<n>-<topic>.md`:

```
# M0-S<n> · <topic> — decision memo
Date · spike id · timebox spent · verdict: green | partial | red
1. Hypothesis (verbatim from F02)
2. Method (commands, env, exact package/CLI versions)
3. Evidence table: claim | observed | transcript/fixture ref
4. Decision & consequences (what flips in the plan docs)
5. Decision-log updates (resolves O-00x → proposed D-/P- entries for ../decisions.md)
6. Follow-ups / upstream issues filed
```

Raw transcripts stay out of git (§6); memos embed only redacted excerpts.

## 4. Contracts

What F02 hands to neighbors — these are the interfaces; everything else in `spikes/` is disposable:

| Artifact | Consumer | Contract |
|---|---|---|
| `M0-S1-auth.md` | auth implementation (M1), F04, [../07-org-intelligence.md](../07-org-intelligence.md) review loop | Launch posture (OAuth-first / key-first / hybrid) + bearer matrix + O-008 verdict; decision-log entries resolving O-001/O-002/O-008 |
| `M0-S2-mda.md` + replay knowledge | F04 control-plane client, M3 deploy wizard | Verified request/response sequence for CLI-free deploy incl. `managed_deep_agent` marker shape; identity-mode results; resolves O-003 |
| `packages/sdk/tests/contract/**` | F01 CI, F04 SDK | Harness + 9 fixtures; fixture format: `.jsonl`, one normalized protocol-v2 event per line, metadata header line 1; test entry points runnable via the workspace test task in `replay` mode with zero credentials |
| CI-mode spec (§3.3) | F01 | `replay` on every PR; `live` weekly against `langgraph dev` with `LANGGRAPH_CLI_NO_ANALYTICS=1`; `live` failure = SDK/server drift alarm, not merge-blocking |
| Memo template (§3.4) | all future spikes | Stable format so decision-log grooming is mechanical |

## 5. Edge cases & failure modes

| Case | Handling |
|---|---|
| RFC 8414 metadata 404 on both candidate hosts | OAuth unusable as researched → S1 red path (key-first), file the discrepancy against [research 12](../../research/12-lifecycle-auth-followup.md) |
| Metadata omits `scopes_supported` (optional per RFC 8414) | Proceed empirically: request empty/default scope, record what the issued token can actually reach |
| DCR returns 403 / allowlist error | Red path + ask beta contact whether manual client provisioning exists; ToS question stays open (§9) |
| Device flow refused for DCR public clients | OAuth-first web-only; desktop keeps key-paste; memo records the split |
| Bearer accepted on control plane, rejected on data plane | Not a failure — hybrid outcome; memo specifies OAuth (control) + MDA identity (data) |
| Context Hub write 403 under bearer | O-008 red: review-loop commits go server-side via service key (P-005 `apps/server`); OAuth remains read-only there |
| `mda deploy` rejected (`managed_deep_agent` gating) | S2 red path: classic `langgraph.json` deployment of the same agent; escalate; S1/S3 dependencies keep a live deployment either way |
| Upload/replay flow deviates from research (non-GCS URL, extra params) | Transcript is the authority; memo corrects [research 20](../../research/20-gapfill-mda-api.md) |
| Revision polling stuck (>30 min) | One retry, then beta contact; timebox guard applies |
| Guest-token mint fails (`/identity/guest`) | Record `trusted_backend` result alone; `validated_token` verdict moves to §9 as unresolved |
| `langgraph dev` lacks checkpoints channel / `Last-Event-ID` replay | Per-scenario fallback recorder target = S2 deployment (fixture tagged `target: deployment`) |
| Enqueue handled client-side only | Fixture pins observed semantics; upstream issue filed; UI spec note for F04 |
| Reasoning deltas unproducible from scripted graph | Record-once from a live model, normalize, freeze; replay never needs the model again |
| Nondeterminism leaks into fixtures (ids, timing) | Normalizer placeholder rules (§3.3); re-record must produce a zero-diff fixture twice before freezing |
| Gateway rate limits (2000/10s general) during probes | Irrelevant at spike volume; replay-script retries with backoff anyway |

## 6. Security & privacy

- **Secrets never enter git**: API keys, bearer tokens, `X-MDA-Ingress-Secret`, `MDA_GUEST_SIGNING_KEY` live in untracked `.env`; `spikes/*/transcripts/` is gitignored.
- **Redaction rules for memo excerpts**: strip `Authorization` headers, all `lsv2_*` keys, ingress/guest secrets, signed upload URLs (their query strings are credentials), and tenant/org IDs unless load-bearing.
- **Private-beta discretion**: the MDA invocation surface is design-partner-gated and deliberately unpublished ([research 12](../../research/12-lifecycle-auth-followup.md)); this repo is public from day one ([../05-oss-setup.md](../05-oss-setup.md)). Rule: memos may summarize behavior; verbatim gated payload shapes not already in public docs stay out of the repo until the beta contact OKs publication (tracked in §9).
- **Test identities only**: identity probes use throwaway actor/tenant ids; no real user data in threads, fixtures, or memos.
- **Teardown is part of done**: revoke OAuth tokens + DCR client, rotate ingress/guest secrets, delete scratch deployments and hub repos (task 15, §8).
- **Fixtures are credential-free by construction**: recorded against no-auth `langgraph dev` on localhost (deployment-target fixtures pass the same redaction rules before commit).

## 7. Acceptance criteria

1. S1: bearer matrix fully populated (every token type × target cell yes/no with transcript ref); `M0-S1-auth.md` states OAuth-first vs key-first vs hybrid and the O-008 verdict; ≤ 2 dev-days.
2. S2: `mda dev` loop, captured deploy, both identity modes, and CLI-free replay each green or documented-red; `managed_deep_agent` marker shape recorded; `M0-S2-mda.md` resolves O-003; ≤ 3 dev-days.
3. S3: 9 scenarios frozen as fixtures; replay suite green locally with zero credentials; harness + CI-mode spec handed to F01; `M0-S3-stream.md` lists every research-vs-observed divergence; ≤ 4 dev-days.
4. All three memos follow §3.4 and propose concrete `../decisions.md` entries resolving O-001/O-002/O-003/O-008.
5. Red paths honored: any spike ending its timebox without green has its fallback recorded *as the decision* (no undecided states leave M0).
6. Teardown complete (§6); `spikes/` deletion scheduled for M1 entry; no secret or gated verbatim payload committed.
7. M0 exit line from [../04-roadmap.md](../04-roadmap.md) satisfied for F02's share: "the three riskiest unknowns are facts."

## 8. Task breakdown

| # | Task | Depends on | Definition of done |
|---|---|---|---|
| 1 | Create `spikes/` layout + gitignore rules + memo template | — | Layout of §3 exists; `transcripts/` ignored; template matches §3.4 |
| 2 | S1: discovery + DCR scripts | 1 | Metadata JSON + registered public client recorded for the real issuer host |
| 3 | S1: PKCE + device flows | 2 | Both flows yield tokens; lifetimes/refresh/scopes recorded |
| 4 | S1: bearer matrix vs control plane + Context Hub write (O-008) | 3 | All control-plane/Hub cells populated with transcript refs |
| 5 | S2: `mda init` + `mda dev` minimal agent | 1 | Local stream works; project pinned to the 0.4.0-dev channel |
| 6 | S2: captured `mda deploy` | 5 | Deployment live; full transcript incl. marker shape, upload flow, revision polling, cron reconcile |
| 7 | S1: bearer matrix vs data plane | 3, 6 | Data-plane cells populated against the S2 deployment URL |
| 8 | S2: external `useStream` under both identity modes | 6 | Streaming green (or documented red) for `trusted_backend` and `validated_token`/guest; `metadata.owner` scoping verified |
| 9 | S2: CLI-free deploy replay script | 6 | Second deployment created by raw API calls; transcript diff vs CLI ≈ empty |
| 10 | S3: fixture server + harness skeleton in `packages/sdk/tests/contract/` | F01 scaffold | Deterministic graph boots under `langgraph dev`; recorder/normalizer produce a stable fixture twice in a row |
| 11 | S3: record + freeze scenarios 1–9 | 10 (8 for any `target: deployment` fixture) | 9 fixtures committed with metadata headers, redaction-checked |
| 12 | S3: shape + semantic + adapter-replay assertions | 11 | Replay suite green; casing invariants (incl. `reviewConfigs` exception) covered |
| 13 | S3: CI-mode spec handed to F01 (`replay` per-PR, `live` weekly) | 12 | Documented in the harness README section; F01 issue opened |
| 14 | Write 3 memos + decision-log PR resolving O-001/O-002/O-003/O-008 | 4, 7, 8, 9, 12 | Memos merged; `../decisions.md` entries proposed; plan-doc contradictions flagged |
| 15 | Teardown + schedule `spikes/` deletion at M1 entry | 14 | §6 teardown checklist executed |

## 9. Open questions

- Actual `scopes_supported` contents and whether any scope maps to Context Hub **write** (O-008) — the spike answers this; unknown until run.
- DCR terms-of-service/allowlist posture for consumer apps (docs forbid nothing; unconfirmed — [research 12](../../research/12-lifecycle-auth-followup.md)).
- Exact issuer host for the OAuth metadata (research records paths, not host).
- Shape of the `managed_deep_agent` marker in the `/v2/deployments` payload (flag vs enum vs object — [research 20](../../research/20-gapfill-mda-api.md)).
- Shape of the design-partner `/v1/deepagents/*` run/thread/invoke endpoints — not needed for M0 (standard Agent Server API suffices) but worth capturing if visible in transcripts.
- Whether `langgraph dev` (in-mem runtime) supports `stream_resumable`/`Last-Event-ID` and accepts the `checkpoints` channel — determines which fixtures need the deployment target ([research 21](../../research/21-gapfill-ui-contract.md)).
- Server-side status of `multitask_strategy` enqueue/interrupt/reject vs client-side queueing ([research 21](../../research/21-gapfill-ui-contract.md)).
- WebSocket availability on `/threads/{id}/stream/events` across deployment tiers during beta (S3 records SSE; WS is a stretch check).
- MDA beta quotas (deployments, crons) — unpublished; ask the beta contact during S2.
- Whether LangChain permits publishing redacted transcripts of gated MDA surfaces in this public repo (§6 rule holds until answered).
- Catalog note: `../features/README.md` and `../decisions.md` were absent from the repo when this spec was drafted; neighbor filenames (`./01-monorepo-and-ci.md`) and D-/P-/O- IDs follow the coordinator's catalog and must be reconciled when those files land.

## 10. Risks

| Risk | L | I | Mitigation |
|---|---|---|---|
| OAuth scopes insufficient (O-001/O-002 red) | Med | Med | Key-first fallback is complete and already spec'd ([../04-roadmap.md](../04-roadmap.md) risk table); the seam (auth posture behind memo) isolates the flip |
| MDA gating blocks deploy or replay (O-003 red) | Med | High | Classic Deployment + `langgraph dev` are public and feature-equivalent for v1 scope; beta relationship as escalation path |
| Spike overrun eats M0 | Med | Med | Hard timeboxes; red-path-is-the-decision rule (§3); S3 scenarios independently shippable |
| `@langchain/react` 1.0.x churn breaks harness mid-spike | High | Low-Med | Pins from [../05-oss-setup.md](../05-oss-setup.md); replay mode isolates churn to the weekly `live` job |
| Public-repo leak of gated beta API details | Low | Med | §6 discretion rule; transcripts gitignored; redaction checklist in task 11/14 DoD |
| Beta account is a single point of failure | Med | Med | Everything scripted and re-runnable; transcripts make results reproducible as evidence even if access lapses |
| P-005 (provisional) flips, moving glue off FastAPI | Low | Low | Spikes are server-less by design (loopback redirects, throwaway scripts); only memo recommendations reference `apps/server` |

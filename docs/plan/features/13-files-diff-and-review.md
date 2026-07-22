# F13 · Files, diff & review
*Deep Work feature spec · 2026-07-22 · Status: draft · Milestone: M2 · Depth: implementation-ready*
Sources: [../03-ui-spec.md](../03-ui-spec.md) (§1.3, §3.2, §4, §7) · [../06-frontend-implementation.md](../06-frontend-implementation.md) (Phase D) · [../02-architecture.md](../02-architecture.md) (§4, §5, §7, §10) · [../04-roadmap.md](../04-roadmap.md) (M2) · [../../research/21-gapfill-ui-contract.md](../../research/21-gapfill-ui-contract.md) · [../../research/22-gapfill-ui-tokens.md](../../research/22-gapfill-ui-tokens.md) · [../../research/20-gapfill-mda-api.md](../../research/20-gapfill-mda-api.md) · [../../research/06-execution-sandboxes.md](../../research/06-execution-sandboxes.md) · [../../research/03-competitor-teardown.md](../../research/03-competitor-teardown.md) · [../decisions.md](../decisions.md) · catalog: [./README.md](./README.md)

## 1. Scope

The review surfaces of the task loop: everything between "the agent changed something" and "a human verified it". Verification UX is the product (01-vision §3: 29% trust, 66% "almost right").

| Owns | Does not own (neighbor) |
|---|---|
| Files-changed rail block (tree + counts) | Sandbox lifecycle, TTL, provisioning, `setup.sh` → [./11-execution-and-environments.md](./11-execution-and-environments.md) |
| `FileViewer` incl. multimodal + binary/large-file UX | Branch naming, `commit_and_open_pr`, PR/CI status block, merge → [./12-github-and-git-flow.md](./12-github-and-git-flow.md) |
| Diff-review full-width takeover, per-line comments, batched review message *format* | Composer mechanics, queue-vs-interrupt submit, optimistic states → [F09](./09-task-detail-and-streaming.md) |
| Artifact definition, rail list, artifact viewer | `FileData` → normalized-type conversion → [F04](./04-sdk-and-agent-sources.md) |
| Read-only terminal pane (P-003, provisional) | HITL/approvals rendering of gated tools → [F10](./10-approvals-inbox.md) |
| Loading/empty/error/degraded states + perf budget for all of the above | Trace views (LangSmith deep links only, 02 §10) |

Frontend is Next.js `apps/web` (D-022); any server-side proxying of connector calls rides the FastAPI glue service `apps/server` (P-005, [F28](./28-backend-glue-service.md)). In-repo target: `packages/ui` components (`FileTree` / `FileViewer` / `DiffViewer` per 03 §4) + `apps/web` wiring; the connector route *implementation* lands in `packages/agent/connectors/deepwork.py` (02 §3 — [F14](./14-agent-package.md) territory, sandbox access via F11) — this spec owns its HTTP contract because it exists solely to feed these surfaces.

## 2. Dependencies & seams

| Dependency | Direction | Contract at the seam |
|---|---|---|
| [F04](./04-sdk-and-agent-sources.md) data layer | consumes | `NormalizedFile` (§4.1) from `values.files`; F04 normalizes all three `FileData` variants once at the SDK boundary (03 §5, D-011); components never see variants |
| `useStream` root channels | consumes | `values` (files/todos), `tools` (`AssembledToolCall` + `tool-output-delta`) per research 21; no extra subscriptions needed |
| Sandbox connector routes | consumes/defines | `/connectors/deepwork/sandbox/:threadId/tree|file` (02 §4) — identity-enforced (`secure by default`, research 20); response schemas defined here (§4.2), implemented in [F14](./14-agent-package.md) with F11 |
| [F09](./09-task-detail-and-streaming.md) steering | produces | one plain-text human message per review batch (§4.3), submitted through the composer's queue-vs-interrupt affordance (02 §7, enqueue default) |
| F12 GitHub flow | produces | `Approve & open PR` intent (§3.4); F12 owns what happens after the click (tool call, HITL gate, PR/CI display) |
| F11 environments | consumes | sandbox presence/id/TTL from the env chip state; `SANDBOX_EXPIRED` handling + "resume environment" action |
| `packages/ui` tokens | consumes | catppuccin-latte/mocha framed code blocks, 14px mono, unified diff default (03 §1.3) |

## 3. Design

### 3.1 Files-changed rail block

Two data sources, selected per thread (03 §3.2 lists both):

| Task shape | Source | Counts shown |
|---|---|---|
| Sandbox-backed (coding) | connector `tree` route — git-derived vs the task's base branch inside the sandbox | per-file `+adds/−dels`, roll-up in header |
| State-backed (research/writing, StateBackend virtual FS, 02 §4) | `values.files` via F04 | file-level only: added / modified / deleted counts (no line baseline exists) |

Detection: env/sandbox chip present in thread state → connector; else `values.files`. Tree renders as a collapsible path tree (ui-patterns deep-agent-ide reference: 160px tree, depth×14+8px indent, amber modified dots — research 22), status dot per file (green added / amber modified / red deleted), monospace paths, header shows `N files · +A −D`. Clicking a file opens `FileViewer` (state-backed) or the diff takeover scoped to that file (sandbox-backed). Connector data revalidates on `tool-finished` events for mutating tools (`write_file`, `edit_file`, `delete`, `execute`) with a 2s debounce; `values.files` is live by nature.

### 3.2 FileViewer

- **Highlighting: Shiki (recommended decision).** 03 §1.3/§4 leaves Prism vs Shiki open. Choose Shiki: TextMate-grammar accuracy, first-party catppuccin-latte/mocha themes (exactly the pinned code palette), dual-theme CSS-variable output, async-friendly for worker offload. Prism (used by deep-agents-ui `oneDark`, agent-chat-ui `coldarkDark` — research 22) loses on theme fidelity and grammar quality. Record in [../decisions.md](../decisions.md); consequence: diffs (`@pierre/diffs`) and code blocks have separate token pipelines — theme alignment is R3.
- **Text**: framed code block (16px outer + 2px gutter + 14px inner, 03 §1.3), line numbers, path header with copy-path + download; markdown files render as sanitized rich markdown with a "raw" toggle (deep-agents-ui `FileViewDialog` precedent, research 22).
- **Multimodal** (`read_file` is multimodal — research 02; 03 §4 requires image/PDF/audio/video): rendered from `NormalizedFile.mimeType` + bytes as blob URLs — `image/*` → `<img>` (zoom/fit), `application/pdf` → sandboxed `<iframe>`, `audio/*`/`video/*` → native elements. Unknown/binary → metadata card (name, size, mime) + download only.
- **Large files** (defaults, tunable): highlight ≤ 256 KB *and* ≤ 10k lines, else plain text; render ≤ 1 MB, else first 64 KB + truncation banner "Showing first 64 KB — download full file"; connector `file` route hard cap 2 MB (413 over). Never block the main thread to decide: caps checked on metadata before content fetch.
- Presentation: 60vw×80vh dialog from rail/tool-call contexts; full pane inside the takeover (03 §4 "60vw dialog or takeover").

### 3.3 Diff review takeover

Full-width takeover from the Files-changed header ("Review changes") or any file row (03 §3.2). Layout: left virtualized file list (same tree component, condensed), main pane `@pierre/diffs` **unified view default** (03 §1.3), per-file collapse, split-view toggle behind a preference. Sticky header: `N files · +A −D`, comment counter, `Send N comments` primary action, `Approve & open PR` secondary, close returns to task detail preserving scroll.

**Per-line comments** — gutter `+` on hover (new side; deleted lines comment on the old side), inline composer per line, multiple drafts accumulate locally (nuqs/URL keeps takeover state shareable; drafts in memory + `sessionStorage`). Nothing is sent until `Send N comments`: comments are **batched into exactly one steering message** (03 §3.2; the Codex/Claude convention, research 03) in the §4.3 format, submitted via F09 (enqueue by default; the composer's queue-vs-interrupt affordance applies unchanged). After send, the takeover clears drafts and the thread shows the message; the UI re-renders sent batches as review cards by re-parsing the deterministic format (no side-channel storage in v1).

### 3.4 Approve & open PR

Visible only for sandbox-backed coding tasks. Click emits the F12 "open PR" intent; v1 realization (owned by F12): a steering directive instructing `commit_and_open_pr`, or — when that tool is HITL-gated (`interrupt_on`, 02 §3) and an interrupt is already pending — an approve decision. Button states: hidden / enabled / in-flight (disabled, spinner in label) / done (swaps to the PR link chip rendered by F12's rail block). Disabled with tooltip while review comments are unsent ("Send or discard comments first") to keep the message order deterministic.

### 3.5 Artifacts (non-coding tasks)

*What counts*: files the agent writes under `/artifacts/**` on the thread FS — a convention added to the research/writing task-template instructions (02 §3, D-014; owned by [F15](./15-task-templates.md), flagged in §9). Fallback heuristic while templates converge: root-level files with deliverable types (`.md .pdf .csv .docx .png .html`). Deliverables, not scratch: `/large_tool_results/`, `/conversation_history/` and other harness-internal paths (research 06) are always excluded.

*Rail list*: name, type icon, size, modified time; sorted by modified desc. *Viewer*: the same takeover chrome hosting `FileViewer` — markdown as rich text (primary case: research reports/documents, 01-vision §3 "land (draft PR, document, report)"), copy-as-markdown + download on all types. Artifacts come from `values.files` (state-backed threads) so they render even with every connector down.

### 3.6 Read-only terminal pane (P-003, provisional)

A run-panel pane (concept app already has one — 06 §1) fed entirely by `execute` tool streams on the `tools` channel: `tool-started {tool_call_id, tool_name, input}` → append `$ <command>` prompt line; `tool-output-delta` → append output; `tool-finished/tool-error` → status line (research 21). Append-only log across the thread's `execute` calls, newest at bottom, stick-to-bottom with pause-on-scroll-up. ANSI SGR colors rendered via a lightweight converter (not xterm.js — there is no PTY and **no stdin in v1**, 06 §4 decision 3); all other escape sequences stripped. Scrollback ring buffer 10k lines; per-block and select-all copy. Steering while a command runs happens in the composer, not here. Interactive terminal (stdin/PTY over sandbox exec) is post-v1; *Continue in terminal* → `dcode --sandbox-id` (02 §9, D-013, [F25](./25-dcode-integration.md)) is the escape hatch and renders next to this pane.

### 3.7 States

| State | Detection | Rendering |
|---|---|---|
| Loading | `isThreadLoading` / route fetch in flight | skeleton tree rows (skeletons not spinners, 03 §7) |
| Empty | tree empty ∧ `values.files` empty | teaching empty state: "No changes yet — files appear as the agent writes them" (+ artifact variant for non-coding) |
| Error | connector 4xx/5xx after retry | inline error row + retry; block stays mounted |
| Degraded: connector down | fetch fails, thread streaming fine | banner "Live file tree unavailable"; render `values.files` subset + **recently-touched list** derived from `write_file/edit_file/delete` tool calls in the thread (paths from args — always available from thread state); viewer/diff disabled for sandbox-only content |
| Degraded: sandbox expired | `SANDBOX_EXPIRED` (§4.2) | banner "Environment expired — showing last known state"; SWR-cached tree read-only; "Resume environment" action → F11 |
| Highlight failure | worker error/timeout | plain-text render, silent fallback |

### 3.8 Performance

- **Virtualized** file tree and diff file list (03 §7 mandates list virtualization); flattened-tree windowing so 5k-entry trees stay <16ms/frame.
- **Lazy content**: file bodies fetched on selection only (connector) with SWR cache keyed `(threadId, path, headCommit)`; `values.files` content is already in client state — no refetch, but render lazily.
- **Highlight worker**: Shiki in a Web Worker; tree-shaken grammar set (~20 languages) + lazy per-grammar load; results cached per `(path, contentHash)`; cancel superseded jobs on selection change.
- **Diff**: per-file lazy mount; files >1,500 changed lines collapsed by default with "Load diff"; takeover opens on already-fetched tree metadata (no content waterfall).
- **Terminal**: rAF-batched appends (deltas can storm), ring buffer, no re-render of prior blocks.

## 4. Contracts

### 4.1 `NormalizedFile` (consumed; produced by F04)

```ts
type NormalizedFile = {
  path: string;                       // absolute virtual-FS path
  kind: 'text' | 'binary';
  text?: string;                      // kind=text
  bytesBase64?: string;               // kind=binary
  mimeType?: string;                  // from FileDataV2 or sniffed by F04
  createdAt?: string; modifiedAt?: string;
}
```
Normalization rules (F04's job; recorded here as the consumption contract, research 21): Python `{content, encoding:'utf-8'|'base64'}` → text|binary by encoding; JS **v1** `{content: string[]}` → text via line-join; JS **v2** `{content: string|Uint8Array, mimeType}` → by content type. `Record<path, FileData>` with null-delete updates → F13 receives adds/updates/removals as map diffs. Components in this spec reject raw `FileData` at the type level.

### 4.2 Sandbox connector routes (proposed contract; routes named in 02 §4, schema owned here, implemented with F11)

Identity: enforced by the connector protocol (`secure by default`; fail-closed 403 outside the caller's identity namespace — research 20). Client calls carry the same auth as the data plane: `validated_token` direct, or `trusted_backend` via the `apps/server` proxy (P-005, [F28](./28-backend-glue-service.md); 02 §5). Classic tiers mount identical handlers via `langgraph.json` `http.app` (02 §4, D-004 fallback tiers).

`GET /connectors/deepwork/sandbox/:threadId/tree`
```jsonc
200 {
  "base": {"branch": "main", "commit": "<sha>"} | null,   // null = non-git workspace
  "head": {"branch": "deepwork/<task>", "commit": "<sha>"} | null,
  "files": [{ "path": "src/a.py", "status": "added|modified|deleted|renamed",
              "old_path": null, "additions": 12, "deletions": 3,
              "size": 4096, "binary": false }],
  "truncated": false,                                     // true past 2,000 entries
  "generated_at": "<iso8601>"
}
```
`GET /connectors/deepwork/sandbox/:threadId/file?path=<urlencoded>&ref=head|base`
```jsonc
200 { "path": "...", "ref": "head", "content": "<base64>", "mime_type": "text/x-python",
      "size": 4096, "truncated": false }
```
Errors (all routes): `{"error": {"code", "message"}}` — `403` identity, `404 SANDBOX_EXPIRED`, `400 PATH_OUTSIDE_WORKSPACE`, `413 FILE_TOO_LARGE` (cap 2 MB). Base-ref fetch exists so the client can compute a single-file diff without a dedicated diff route (whether a `/diff` route is warranted → §9). Wire fields snake_case per 02 §7.

### 4.3 Review-batch steering message (produced; the exact payload the agent receives)

One plain-text human message, deterministic and machine-parseable:

```
Review of current changes — {N} comments. Address each, then summarize what you changed.

[{i}] {path}:{line|start-end}{" (removed line)" if old-side}
> {diff line(s), verbatim incl. leading +/-/space marker}
{comment text, free markdown}
```

Grammar rules: header line fixed except `{N}`; blocks separated by one blank line; anchors use **new-file** line numbers, old-side anchors prefixed `-` (e.g. `README.md:-12`); quoted context is 1–3 verbatim diff lines each prefixed `> `; ranges `start-end` for multi-line comments. The composer sends it via F09 as a single `submit` honoring queue-vs-interrupt (enqueue default, 02 §7). The same grammar is the parser spec for re-rendering sent batches as review cards. No structured side-channel in v1 (§9).

### 4.4 Component contracts (`packages/ui`)

| Component | Props (essence) | Notes |
|---|---|---|
| `FileTree` | `entries: TreeEntry[]`, `selected`, `onSelect`, `variant: 'rail'|'takeover'` | virtualized; status dots; counts |
| `FileViewer` | `file: NormalizedFile`, `caps?`, `onDownload` | worker highlight; multimodal; truncation UX |
| `DiffViewer` | `files: DiffFile[]`, `comments`, `onCommentAdd/Edit/Delete`, `view: 'unified'|'split'` | `@pierre/diffs`; per-line gutter |
| `ReviewBar` | `commentCount`, `onSend`, `onApproveAndPr`, `prState` | takeover sticky header |
| `ArtifactList` / `ArtifactViewer` | `artifacts: NormalizedFile[]` | rail + takeover |
| `TerminalPane` | `blocks: ExecBlock[]` (derived from `AssembledToolCall`s) | read-only; ANSI SGR only |

## 5. Edge cases & failure modes

- **Sandbox expires mid-review** (idle_ttl 600s default, 02 §4): drafts persist (sessionStorage); banner per §3.7; `Send comments` still works (steering resumes the thread; F11 recreates the sandbox); `Approve & open PR` disabled until environment resumes.
- **Renames**: `status: renamed` + `old_path`; comments anchor to the new path.
- **File changes under an open comment draft** (agent still running): tree revalidation marks the file stale; on send, quoted lines are whatever the draft captured — the verbatim quote is what protects intent when line numbers drift.
- **Comment on a deleted file**: allowed; old-side anchors only.
- **`values.files` null-delete race**: map-diff consumption (§4.1) makes deletion idempotent; viewer open on a deleted file shows "File was deleted by the agent" with last content retained until closed.
- **Binary flagged in tree but requested as text** (or vice versa): trust per-response `mime_type`/decode result over tree flags.
- **Huge trees** (>2,000 entries): `truncated: true` → banner "Showing first 2,000 changes"; counts header still totals from git numstat server-side.
- **Non-UTF-8 text**: decode failure → binary fallback card, never garbled render.
- **Terminal output interleave**: multiple concurrent `execute` calls (subagents) render as separate blocks keyed by `tool_call_id`, ordered by `tool-started` arrival; namespace label on subagent-issued blocks.
- **Review sent while a run is active**: enqueue default means comments apply after the current step — the composer's existing affordance communicates this (F09); no special casing here.
- **Artifact heuristic false positives** (e.g. agent writes `notes.md` scratch at root): mitigated by `/artifacts/` convention adoption; heuristic list is labeled "Files" not "Artifacts" until the convention is detected.

## 6. Security & privacy

- **Identity-enforced routes, fail-closed** (research 20): connector routes are secure-by-default; no `ctx.router.public.*` opt-out for any F13 route. Thread ownership scoping via `metadata.owner` comes from the platform; F13 never adds its own auth.
- **Zero secrets client-side**: sandbox/git credentials never reach the browser (02 §4 zero-secrets pattern); the `trusted_backend` header path exists only inside `apps/server` (P-005).
- **Path traversal**: server resolves the requested path against the workspace root (realpath) and rejects escapes → `PATH_OUTSIDE_WORKSPACE`; never pass raw paths to shell.
- **Rendering agent-produced content as inert**: markdown artifacts render with raw HTML disabled/sanitized, `rel="noopener noreferrer"` links; PDFs in a sandboxed iframe (blob URL, no `allow-same-origin`); images/media via blob URLs only, no remote fetches from viewer content; diffs/code render as text — file content is untrusted input, consistent with 02 §10's untrusted-boundary posture.
- **ANSI hygiene**: SGR color codes only; OSC (incl. OSC 8 hyperlinks), cursor, and title sequences stripped before render.
- **No content exfiltration**: file/diff contents and review comments never enter telemetry or logs; only counts/sizes/durations may be instrumented.
- **DoS caps double as safety**: route/viewer caps (§3.2) bound memory; worker highlighting bounds main-thread impact.
- **Downloads**: client-side blob download with sanitized filename (basename only).

## 7. Acceptance criteria

1. Sandbox-backed thread: rail shows tree + per-file `+/−` counts from the `tree` route within 2s of a mutating `tool-finished`; state-backed thread: identical block from `values.files` with file-level counts. Golden fixtures cover all three `FileData` variants end-to-end (via F04).
2. `FileViewer` renders text (highlighted ≤ caps, plain above), markdown (rich + raw toggle), image, PDF, audio, video, and binary-fallback fixtures; oversize file shows truncation banner + working download.
3. Takeover opens full-width from the rail, unified diff default, per-file collapse; 100-file / 10k-line diff fixture scrolls at 60fps target with no per-file content fetched until expanded.
4. Adding 3 comments across 2 files and pressing Send produces **exactly one** human message matching the §4.3 grammar byte-for-byte against a golden transcript; the thread re-renders it as a review card; queue-vs-interrupt affordance honored.
5. `Approve & open PR` emits the F12 intent; disabled while unsent comments exist; reflects in-flight and done states.
6. Artifacts: a research-template thread writing `/artifacts/report.md` shows it in the rail list; viewer renders sanitized rich markdown; copy + download work.
7. Terminal pane replays a recorded `execute` stream (started → deltas → finished) with ANSI colors, stick-to-bottom, pause-on-scroll, copy; stdin absent.
8. Kill the connector: rail degrades to `values.files` + recently-touched list with banner, no crash; expire the sandbox: cached tree renders read-only with resume affordance.
9. All states in §3.7 have Storybook stories; empty states teach the next action (03 §7).
10. Security checks pass: path-traversal request → 400; unauthorized thread → 403; markdown with `<script>`/raw HTML renders inert; OSC 8 sequence stripped in terminal.

## 8. Task breakdown

| # | Task | Depends on | Definition of done |
|---|---|---|---|
| 1 | `NormalizedFile` consumption types + fixtures for py/js-v1/js-v2 variants in `packages/sdk` | F04 types landed | variant round-trip tests green; components compile against `NormalizedFile` only |
| 2 | Connector `tree`/`file` handlers in `packages/agent/connectors/deepwork.py` (F14) per §4.2 | F11 sandbox backend; seam review w/ F11/F14 | contract tests vs `langgraph dev` + live sandbox; 403/404/400/413 paths covered |
| 3 | `FileTree` + rail Files-changed block (virtualized, counts, status dots, source selection) | 1, 2 | AC-1, AC-8 partial; stories for both sources |
| 4 | `FileViewer` text path: Shiki worker, caps, truncation UX, markdown mode | 1 | AC-2 text/markdown; worker fallback test |
| 5 | `FileViewer` multimodal + binary fallback | 4 | AC-2 media fixtures; sanitized embeds verified |
| 6 | Diff takeover: `@pierre/diffs` unified view, file list, per-file lazy mount/collapse | 2, 3 | AC-3; split-view toggle behind preference |
| 7 | Line-comment model + drafts + §4.3 serializer/parser | 6 | AC-4 golden-transcript test; sessionStorage persistence test |
| 8 | Composer send wiring via F09 (single message, queue/interrupt honored) | 7; F09 composer | AC-4 e2e against `langgraph dev` |
| 9 | `Approve & open PR` wiring | 6; F12 intent defined | AC-5 |
| 10 | Artifacts: template convention PR (`/artifacts/`), rail list, viewer | 1, 4; F15 ack | AC-6; heuristic fallback labeled correctly |
| 11 | `TerminalPane` from `execute` streams (P-003) | F04 tool-call projections | AC-7; ANSI strip tests |
| 12 | States/degraded matrix incl. recently-touched derivation; perf + a11y pass | 3–11 | AC-8, AC-9; keyboard nav in takeover; reduced-motion clean |

## 9. Open questions

1. **`@pierre/diffs` viability** — observed only inside the ui-patterns compiled bundle (research 22); npm availability, license, theming to catppuccin (it ships github-light/dark), virtualization behavior on huge diffs, and whether it can consume Shiki tokens are all unverified. Fallback: custom Shiki-based unified renderer (risk R1).
2. **`execute` tool input/output schema** — exact arg key for the command string and whether output carries an exit code / distinct stderr is unverified; terminal block header depends on it (F04 to pin during Task 1).
3. **`FileDataV1` sunset** — the deepagents version where JS v2 (`mimeType`) replaced v1 (lines) is unknown (research 21 open question); determines when v1 handling can be dropped.
4. **Dedicated `/diff` route vs client-side base/head compare** — §4.2 avoids new routes (only `tree|file` are sanctioned in 02 §4); if per-file patch computation client-side proves heavy, propose a `diff` extension with F11/F14.
5. **Connector access to the per-thread sandbox** — how `http(ctx)` handlers resolve the MDA-generated sandbox name (research 20 notes no public runtime API for discovery); shapes Task 2's implementation and the expired-sandbox error mapping (404 vs 410).
6. **`/artifacts/` convention adoption** — needs [F15](./15-task-templates.md) sign-off; also whether Context Hub-backed memory paths can ever collide with it.
7. **Structured review side-channel** — should the batch also land as run/message metadata for lossless re-render, vs v1's parse-the-text approach?
8. **Server-side `multitask_strategy: 'interrupt'`** — SDK types accept it but only rollback + client-side enqueue confirmed (research 21); affects the "interrupt" option when sending a review mid-run (F09-shared).
9. **P-003 confirmation** — terminal pane remains provisional; if cut, Task 11 drops without touching other tasks.
10. **Shiki decision ratification** — §3.2's Prism-vs-Shiki recommendation needs a D- entry in [../decisions.md](../decisions.md) at batch review.

## 10. Risks

| # | Risk | L×I | Mitigation |
|---|---|---|---|
| R1 | `@pierre/diffs` unmaintained/unpublishable | Med×High | Spike in Task 6 week 1; fallback custom Shiki unified renderer (unified-only, no split view) |
| R2 | Connector protocol shifts during MDA beta (0.4.0-dev churn, 02 §12) | High×Med | Contract tests vs canary deployment; classic-tier `http.app` mount is the stable fallback |
| R3 | Two highlight pipelines (Shiki viewer vs pierre diffs) drift visually | Med×Low | Shared token CSS variables; theme-parity story in visual regression |
| R4 | `values.files` bloats client memory on file-heavy threads (full content in state) | Med×Med | Lazy render; F04 to expose metadata-first projection; escalate upstream (OSS-first policy, 02 §8) if state size hurts |
| R5 | Sandbox expiry makes review flows dead-end | Med×Med | Degraded matrix (§3.7) + resume seam to F11; drafts survive |
| R6 | Review-message grammar drifts between serializer and agent prompt expectations | Low×Med | Golden transcripts (AC-4); grammar lives in one shared module used by serializer + parser |
| R7 | Terminal delta storms degrade thread rendering | Med×Low | rAF batching, ring buffer, pane unmount stops subscription |

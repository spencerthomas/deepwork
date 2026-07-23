---
feature_id: DW-CODE-003
title: Files, artifacts, diff, terminal, browser flag, and phone review
release: v1
status: canonical-spec
decision_status: blocked-on-spikes
owners: [coding-experience, coding-runtime, sdk, security]
surfaces: [web, pwa, desktop, api, sandbox]
runtime_scopes: [classic, mda, local]
source_refs: [SRC-FE, SRC-LC, SRC-DW, SRC-DP]
dependencies: [DW-TASK-003, DW-TASK-004, DW-TASK-005, DW-CODE-001, DW-CODE-002]
contract_gates: [SPIKE-FILES-001, SPIKE-TERMINAL-001, SPIKE-BROWSER-001]
last_reviewed: 2026-07-22
---

# Files, artifacts, diff, terminal, browser flag, and phone review

## User outcome

A user can inspect the coding workspace, distinguish working files from final artifacts, review an exact base-to-head diff, send line-specific feedback, observe or use a sandbox terminal when safely supported, and complete the approval/PR/CI/merge loop from a phone. Browser/computer-use appears only behind a verified runtime capability and never as simulated evidence.

## Evidence and confidence

| Evidence | Classification | Planning consequence |
|---|---|---|
| The prototype task view has fixture Files, Diff, Terminal, Browser, run context, PR, and mobile-shaped review interactions. | Prototype evidence at `26c698b`; interactive but simulated | Use layout and interaction as evidence; require real file/diff/session contracts and explicit missing states. |
| Pinned LangSmith sandbox docs expose SDK file transfer/commands, snapshots, command reconnect, and service URLs. | Documented at `7b9215d` | Prefer provider SDK/application adapters over undocumented MDA connector routes. |
| Deep Agents backends expose agent file operations, but their model-facing file data is not automatically a safe human file API. | Documented/inferred | Human file browsing uses an authorized sandbox/source adapter with its own limits and MIME handling. |
| Browser/computer-use and interactive PTY behavior are not a uniform public source capability. | Unknown/gated | Browser and Terminal are independently gated by named spikes and source manifests. |

## Scope, ownership, and non-goals

### Definitions

- **Attachment** is user-provided task input.
- **Working file** is mutable content in the task filesystem/repository.
- **Artifact** is a named, versioned reviewable output with provenance under `DW-TASK-005`.
- **Diff** is an immutable comparison identified by repository/base SHA/head SHA or an equivalent content pair.
- **Terminal** is a user-controlled sandbox session/command surface, never execution on an application or device host.
- **Browser evidence** is a captured, attributable session/snapshot/event from a verified runtime; a normal external link is not computer-use evidence.

### In scope

- Lazy file tree, text/code/image/PDF-safe preview where supported, download, metadata, changed-file badges, and stale detection.
- Artifact list integrated from the canonical artifact catalog.
- Unified/split diff modes, changed-file navigation, additions/deletions, binary/large-file handling, base/head identity, and line comments.
- Batch line comments into one normal steering/follow-up message with stable file/line/hunk anchors; this is not a GitHub review submission in v1.
- Read-only command transcripts for agent/setup/test commands.
- User terminal/command session only when the verified provider adapter supports authorization, reconnect, resize/close, output limits, and audit.
- Browser tab/flag only for verified browser evidence or authorized sandbox service URL capability.
- Phone flow for summary, files changed, focused diff, comments, approval, PR/CI, and explicit merge.

### Out of scope

- Arbitrary local filesystem access, editing files directly in v1 UI, full cloud IDE, or syncing a local editor.
- Rendering active HTML/SVG/scripts, executing downloaded files, or auto-opening sandbox service URLs.
- Mobile interactive terminal or mobile computer control.
- Fabricating screenshots, action timelines, progress, terminal output, or file changes from model narration.
- Sending line comments directly as GitHub review comments; v1 sends agent steering unless a later plan adds a GitHub review contract.

### Ownership

- FastAPI owns authorized file/diff/session mediation, path policy, content limits, safe previews/downloads, review-comment batching, and capability enforcement.
- Postgres owns UI state, review batches/anchors, diff identity/checksum, terminal session metadata/audit, browser-evidence metadata, and artifact references. Provider/source owns bytes and runtime sessions.
- FastAPI source adapters normalize provider file, diff, terminal, and browser facts; `packages/sdk` maps the application contract and `packages/domain` owns client-safe projections.
- Next.js/Tauri own virtualized viewers, terminal/browser tabs, responsive review, keyboard navigation, and safe rendering.
- The sandbox/GitHub adapters provide authoritative files, commands, Git refs/diffs, service URLs, and evidence when available.

## Primary journeys

### Files and artifacts

1. Files opens a lazy root listing for the current sandbox/repository identity and freshness marker.
2. Expanding a directory fetches a bounded page; selecting a file retrieves metadata before content.
3. Safe text/code renders with line numbers; supported media uses sandboxed preview; large/binary/unknown files show metadata and explicit download/open-at-source options.
4. Working files never appear in Artifacts unless the agent/user declares a versioned artifact.
5. If the sandbox expires, the tree becomes stale/unavailable and confirmed GitHub/artifact sources remain separately accessible.

### Diff and review comments

1. Diff identifies exact base/head SHAs and loads a normalized changed-file summary.
2. The user filters files and opens virtualized hunks in unified or split view.
3. A comment stores file path, side, old/new line, hunk fingerprint, diff base/head, and text.
4. Before submission, FastAPI rechecks the head. If unchanged, comments are formatted into one steering message with anchors. If changed, comments are marked outdated and require remapping/review.
5. The resulting message appears in task history and follows verified queue/steering behavior.

### Terminal and browser

1. Agent/setup command transcripts are always read-only evidence with command source, exit, start/end, and truncation state when supplied.
2. If interactive terminal capability is verified, the user deliberately opens a sandbox-only session, reviews environment/egress/permission context, and sends input over an authenticated bounded channel.
3. Closing or expiry terminates/reconciles the provider session. Mobile shows transcript only.
4. Browser is visible only when `browserEvidence` or `sandboxServiceUrl` capability is true. Each view names origin, capture time/live state, actor (agent/user), and egress/access boundary.

### Phone review

1. Task summary shows agent outcome, verification, files changed, PR state, CI blockers, and pending approvals.
2. The user opens a file-sized diff view, navigates changes, adds comments, and sends one revision request.
3. After refresh/re-review, the user approves the relevant HITL/plan action, opens the draft PR, checks authoritative CI, and merges only through `DW-CODE-002`'s fresh-head gate.

## State matrix

| State | Required behavior | Recovery / transition |
|---|---|---|
| File tree loading | Skeleton matching tree rows; path/breadcrumb stable. | Results, empty, expired, forbidden, or error. |
| Empty workspace | Explain no files versus inaccessible source. | Refresh/run task. |
| Directory paged | Show loaded count and Load more; stable sort. | Continue. |
| File loading | Fetch metadata, enforce limits, then content. | Preview/download/error. |
| Text/code file | Safe text renderer, encoding, truncation, checksum/freshness. | Download or diff. |
| Image/PDF supported | Sandboxed preview with accessible alternative/download. | Open or download. |
| Binary/unknown/too large | No inline parse; show metadata and safe action. | Download if policy allows. |
| Symlink/out-of-root/path invalid | Block resolution and log safe policy event. | Return to tree. |
| File changed during view | Mark stale and offer reload; do not mix versions. | Reload current or retain reviewed checksum. |
| Sandbox expired | File tree unavailable; GitHub/artifact views may remain. | Recreate/recover through environment plan. |
| No artifacts | Explain promotion/declaration, not no files. | Continue task. |
| Diff loading | Show base/head identity and changed-file skeleton. | Render, empty, stale, or error. |
| Empty diff | State no changes for exact base/head. | Refresh or review commits. |
| Large diff | Load summary first, virtualize hunks, enforce bounds. | Open selected files/download patch. |
| Binary/renamed/deleted file | Render accurate metadata/status without fake lines. | Open appropriate old/new metadata. |
| Comment draft | Persist anchor and local/application draft. | Edit/delete/submit. |
| Head changed | Mark comments outdated and block blind submission. | Remap/review against new diff. |
| Comment batch submitting | One idempotent steering command. | Accepted, queued, reconcile, or failed. |
| Transcript live | Show command source, bounded output, exit pending. | Complete/reconnect/truncate. |
| Transcript truncated | Explicit bytes/lines omitted and safe download if available. | Download/open provider trace. |
| Interactive terminal unsupported | Tab hidden or read-only transcript labelled. | Use supported source/desktop. |
| Terminal opening | Authenticate task/sandbox and display connection state. | Ready, denied, expired, or error. |
| Terminal active | Sandbox-only banner, egress/environment context, Stop/close. | Reconnect/close/expire. |
| Terminal disconnected | Do not imply command stopped; reconnect by verified session ID or reconcile. | Resume/read transcript/close. |
| Browser unsupported | Tab absent; no placeholder screenshot. | None. |
| Browser evidence available | Show origin, capture time, mode, actor, and stale/live state. | Inspect timeline/open approved URL. |
| Service URL pending/expired | Do not auto-refresh or expose token. | Request new authorized URL. |
| Offline | Cached file/diff/artifact metadata/read-only content visibly stale; mutations/terminal/merge disabled. | Reconnect and re-fetch. |
| Mobile | No horizontal page overflow; diff scroll is contained, summary/next-change controls persistent. | Review/comment/approve/open PR/merge. |
| Permission revoked | Remove content/session controls and invalidate signed URLs. | Reauthenticate/switch. |

## Proposed interfaces and runtime fallback

```ts
interface FileNode {
  pathRef: string;
  name: string;
  kind: "file" | "directory" | "symlink" | "unknown";
  size?: number;
  mediaType?: string;
  modifiedAt?: string;
  checksum?: string;
  change?: "added" | "modified" | "deleted" | "renamed";
}

interface DiffDocument {
  repositoryBindingId: string;
  baseSha: string;
  headSha: string;
  files: Array<{
    path: string;
    previousPath?: string;
    status: string;
    additions?: number;
    deletions?: number;
    binary: boolean;
    hunksRef?: string;
  }>;
  checksum: string;
}

interface ReviewComment {
  commentId: string;
  baseSha: string;
  headSha: string;
  path: string;
  side: "old" | "new";
  line: number;
  hunkFingerprint: string;
  text: string;
}

interface RuntimePanelCapabilities {
  files: "sandbox" | "source" | "github" | "none";
  diff: "git" | "github" | "none";
  terminal: "interactive" | "transcript" | "none";
  browser: "evidence" | "service_url" | "none";
}
```

Proposed operations include bounded `/api/v1/tasks/{id}/files`, content/download, exact-SHA diff/hunks, review-comment batch, terminal session/stream commands, and browser-evidence/service-url requests. Paths are opaque refs or normalized validated relative paths; provider IDs/tokens never become arbitrary browser-controlled proxy targets.

`SPIKE-FILES-001` must pin the Python LangSmith sandbox/GitHub clients and prove list/read/download, directory scale, encoding, binary/media, symlink/path traversal, large file/diff, changed-during-read, sandbox expiry, exact Git base/head, rename, and error behavior. The baseline must not require undocumented MDA connector routes.

`SPIKE-TERMINAL-001` must prove command session versus PTY availability, authenticated stream, input/resize/reconnect/close, output ordering/truncation, TTL, concurrent viewers, permission, and cleanup. If only command run/reconnect is documented, v1 ships transcript plus discrete user command execution after review; it does not pretend to be a PTY.

`SPIKE-BROWSER-001` must prove the actual evidence/session/service-URL contract, authentication, origin restrictions, expiry, input/control authority, capture metadata, and mobile behavior. Until accepted, `browser: none` in production. An external URL link is labelled as such and does not enable the Browser tab.

Fallback order for files/diff is authorized sandbox API, then exact GitHub commit/PR API, then metadata-only artifact/open-at-source. Missing terminal/browser capabilities hide those tabs without affecting message/diff/approval review. MDA stays gated per adapter.

## Persistence and security

- Never persist arbitrary filesystem paths as authorization. Bind opaque path/session refs to tenant, task, sandbox, provider, and expiry.
- Normalize paths, reject traversal/NUL/absolute escapes, evaluate symlinks server-side, and enforce workspace root.
- Validate MIME by content where feasible; enforce preview/download size, decompression, image/PDF, line, hunk, ANSI, and output limits.
- Render all file content, markdown, code, ANSI output, filenames, diffs, URLs, screenshots, and browser timelines as untrusted. No active HTML/script execution.
- Terminal input is explicit user action, audited with redacted safe metadata; sensitive command text/output follows retention policy and never enters analytics.
- Interactive sessions can reach only the mapped sandbox and its published egress policy. FastAPI/Tauri/Next.js hosts never execute the command.
- Service/signed URLs are short-lived, audience-bound, not logged, and invalidated on permission loss/sandbox expiry.
- Review-comment batch revalidates exact head SHA and escapes file paths/content when forming the agent message.

## Responsive and accessible behavior

- File tree is a semantic tree only if full tree keyboard behavior is implemented; otherwise use nested lists with clear buttons and breadcrumbs.
- Code/diff line numbers are selectable separately from content where possible and have a screen-reader mode summarizing hunk headers and changed lines.
- Additions/deletions use prefixes/text and color; focusable Next/previous change and Next comment controls reduce scrolling.
- Mobile diff uses one column by default, with sticky file/change navigation and contained horizontal code scroll. Page controls remain visible at 200% zoom.
- Terminal has a labelled transcript fallback, visible focus, screen-reader status, and no flashing cursor under reduced motion. Mobile never requires terminal interaction.
- Browser evidence includes alt text/description fields where available and a textual action timeline; screenshots alone are insufficient.
- Panel/tab state is URL-addressable where safe and restores focus on close/back.

## Metrics and guardrails

- File tree/content/diff latency, large-content fallback, preview failure, stale checksum, and sandbox-expiry rate.
- Diff review completion, comment creation/outdated/remap/submission, and revision turnaround.
- Terminal capability use, reconnect, truncation, permission denial, orphan-session cleanup, and error rate.
- Browser capability/evidence availability and expired-session rate, without captured page content analytics.
- Phone funnel: task opened, diff reviewed, comment sent, approval completed, PR opened, CI checked, merge attempted/completed.
- Guardrails: zero path escape; zero application/device-host command execution; zero stale-head comment/merge submission; zero Browser tab for `browser: none`; zero active content execution.

## Dependencies and rollout

- Depends on task detail/lifecycle/artifacts, sandbox, GitHub/CI/merge, and security foundation.
- Phase 0: accept file/diff, terminal, and browser spikes plus malicious-content corpus.
- Phase 1: file tree, safe text/code preview, exact Git diff, and desktop/web review on classic sandbox.
- Phase 2: line-comment batches, artifacts, large/binary/media behavior, and phone diff review.
- Phase 3: transcript/discrete command terminal; interactive mode only if PTY conformance passes.
- Phase 4: browser evidence/service URL behind an independent feature flag after security review.
- A failing adapter disables only its panel capability; task messages, artifacts, GitHub PR link, and other review paths remain usable.

## Executable acceptance scenarios

```gherkin
Scenario: Path traversal never leaves the task workspace
  Given a malicious file request uses traversal, an absolute path, and a symlink escape fixture
  When FastAPI resolves each request
  Then each is rejected before provider content is returned
  And no host or adjacent sandbox file is read

Scenario: Diff comments bind to the reviewed head
  Given two comments target head SHA A
  And the task branch advances to SHA B before submission
  When the user sends the review batch
  Then submission is blocked as outdated
  And the comments are not silently applied to SHA B
  And the user can review/remap against the new diff

Scenario: Terminal fallback is honest
  Given a provider supports command run/reconnect but no PTY
  When the user opens Terminal
  Then Deep Work shows transcripts and an explicitly discrete command action if enabled
  And no interactive PTY controls are shown
  And commands execute only in the mapped sandbox

Scenario: Phone completes the safe coding review loop
  Given a draft PR at reviewed head SHA A with required CI green
  When the user reviews the mobile diff, resolves approvals, opens merge confirmation, and confirms
  Then FastAPI re-fetches the PR gate for SHA A
  And GitHub confirms one merge
  And the phone shows merge SHA and time

Scenario: Unsupported browser never becomes simulated evidence
  Given a source manifest has browser none
  When task detail renders
  Then no Browser tab, screenshot, or action timeline appears
  And a normal external URL remains labelled Open external link
```

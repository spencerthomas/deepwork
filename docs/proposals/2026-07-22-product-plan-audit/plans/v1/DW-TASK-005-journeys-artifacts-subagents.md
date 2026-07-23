---
feature_id: DW-TASK-005
title: Research, writing, and coding journeys with artifacts and subagents
release: v1
status: proposed
decision_status: blocked-on-spikes
owners: [product, task-experience, agent-runtime, sdk]
surfaces: [web, pwa, desktop, api, agent]
runtime_scopes: [classic, mda, fleet, local]
source_refs: [SRC-FE, SRC-LC, SRC-DW, SRC-DP]
dependencies: [DW-TASK-002, DW-TASK-003, DW-HITL-002]
contract_gates: [SPIKE-ARTIFACT-001, SPIKE-SUBAGENT-001]
last_reviewed: 2026-07-22
---

# Research, writing, and coding journeys with artifacts and subagents

## User outcome

Research, writing, and coding feel like deliberate product journeys over one task model rather than one chat interface with cosmetic labels. Each journey produces reviewable, provenance-rich outputs; subagent work is understandable without inventing internal progress; and users can distinguish working files, attachments, and final artifacts.

## Evidence and confidence

| Evidence | Classification | Planning consequence |
|---|---|---|
| Prototype fixtures depict a SWE task, research task, browser evidence, changed files, PR, artifacts, and concurrent subagents. | Prototype evidence at `8866d39`; simulated | Preserve review affordances but do not promote fixture progress, browser, or subagent assumptions into contracts. |
| Canonical vision makes coding, research/report, and content first-class v1 flows over one harness. | Internal intent at `06f0515` | Ship three template journeys with shared task/run identity and journey-specific completion criteria. |
| Deep Agents documents filesystem backends, sandboxes, todos, subagents, and multimodal file handling. | Documented building blocks at `7b9215d` | Starter Python agent may emit a versioned artifact/subagent state contract; external sources require capability mapping. |
| Async subagents are preview/later-scope in existing planning. | Gated/preview | v1 supports synchronous/namespaced subagent visibility only where verified; async workstreams remain v1.x. |

## Scope and ownership

### In scope

- Research template: source collection, citation/provenance review, structured report artifact, and optional supporting dataset/files.
- Writing template: brief/draft/revision flow, source/attachment attribution, and exportable document/text artifact.
- Coding template: repository/environment preflight, plan, edits/tests, diff, draft PR, CI, and merge handoff.
- A canonical artifact record independent of storage/runtime.
- Synchronous subagent discovery, task input summary, status, returned output summary, and failure where supplied by the source.
- Journey-specific empty, blocked, partial, failed, and complete states.
- Clear terminology: attachment is user-provided input; file is mutable working content; artifact is a named reviewable output.

### Out of scope

- Background/async subagent supervisor and multi-day workstreams.
- Automatic factual correctness claims for research or writing.
- Hosting a general collaborative document editor.
- Treating every sandbox file as a final artifact.
- Browser/computer-use control without the separate verified capability.

### Ownership

- The Python Deep Agents package owns the versioned task templates, agent instructions, todo/rubric defaults, artifact declaration tool/state, and supported subagent definitions.
- FastAPI owns task-kind validation, artifact catalog/provenance, authorized access mediation, export orchestration, and cross-source normalization.
- Postgres owns artifact metadata and provenance references, not necessarily bytes; source/sandbox/object storage remains the byte owner.
- FastAPI normalizes provider artifact/subagent facts, `packages/sdk` maps application DTOs/events, and `packages/domain` owns the client-safe artifact/subagent projections.
- Next.js/Tauri own journey-specific composer presets, detail summaries, review surfaces, and mobile landing actions.

## Journey contracts

### Research

1. User defines question, audience, desired format, time/source constraints, attachments, and rubric.
2. Agent publishes a plan when required, tracks a visible todo list, and gathers evidence with source URLs/titles/access times when tools provide them.
3. Intermediate notes remain working files; cited claims are linked to evidence records rather than treated as verified merely because a URL exists.
4. Completion produces a primary report artifact plus a provenance list and unresolved/uncertain items.
5. Review actions are Download, open source, request revision, branch, and mark rubric review complete.

### Writing

1. User selects output type, audience, tone, constraints, source material, and rubric.
2. Agent may create brief, outline, and draft working files; the final chosen output is explicitly promoted to artifact.
3. Source-derived statements retain attribution metadata where available; unsupported citations are flagged, not fabricated.
4. User reviews a clean rendered preview and can request revision while retaining prior artifact versions.

### Coding

1. User selects authorized repository/base branch and environment, then reviews plan and permissions.
2. Agent works in a task/thread-scoped sandbox and a task-specific branch, reports todos/subagent activity, and runs tests.
3. Changed files and diff are reviewed before a draft PR is opened or updated.
4. CI state and PR link become artifacts/operations metadata. Merge is a separate explicit user action governed by `DW-CODE-002`.
5. Completion distinguishes **agent finished**, **draft PR ready**, **CI green**, and **merged** rather than collapsing them into Done.

## State matrix

| State | Research | Writing | Coding |
|---|---|---|---|
| Ready | Question and source policy valid. | Brief and audience valid. | Source, GitHub, repo, branch, environment valid. |
| Missing prerequisite | Missing source/web/attachment capability. | Unsupported attachment/export. | Missing GitHub or sandbox capability. |
| Plan awaiting review | Show evidence-gathering steps. | Show brief/outline steps. | Show investigate/edit/test/PR steps. |
| Running, no artifacts yet | Explain evidence is being gathered. | Show working draft/todos only. | Show sandbox/branch/todos only. |
| Subagent running | Show supplied specialization/task/status, no fabricated percent. | Same. | Same, plus namespace/tool relation when supplied. |
| Subagent blocked/failed | Main task continues only if runtime says so; expose safe reason. | Same. | Same. |
| Partial output | Label draft/incomplete and list missing rubric/evidence. | Label draft/version. | Show uncommitted diff/test state. |
| Artifact available | Report plus provenance. | Rendered final/draft version. | Diff/patch, test result, PR link as applicable. |
| Artifact transfer pending | Show metadata and retryable transfer state. | Same. | Same. |
| Artifact unavailable/stale | Retain provenance and explain storage/source failure. | Same. | Fall back to authorized Git/PR view when possible. |
| Verification failed | Show rubric gaps/uncertainties. | Show rubric gaps. | Show failed tests/review/CI separately. |
| Agent run failed | Preserve collected evidence/artifacts. | Preserve latest draft. | Preserve sandbox, branch, diff, and logs per retention. |
| Complete | Primary report declared and reviewed state visible. | Chosen output declared and versioned. | Agent outcome plus PR/CI/merge substates. |
| Offline | Cached artifacts read-only if authorized. | Same. | Cached diff/PR metadata; no terminal/browser mutation. |
| Mobile | Source list and report review. | Rendered preview and revision prompt. | Diff summary, approvals, PR/CI, merge eligibility. |

## Proposed interfaces and runtime fallback

```ts
type ArtifactKind = "report" | "document" | "dataset" | "image" | "file" | "diff" | "patch" | "test_result" | "pull_request";

interface ArtifactDescriptor {
  artifactId: string;
  taskId: string;
  producingAttemptId: string;
  sourceId: string;
  kind: ArtifactKind;
  title: string;
  mediaType: string;
  size?: number;
  checksum?: string;
  storage: { owner: "source" | "sandbox" | "application" | "github"; locatorRef: string };
  provenance: Array<{ type: string; ref: string; observedAt?: string }>;
  version: number;
  state: "pending" | "available" | "stale" | "unavailable";
}

interface SubagentProjection {
  subagentId: string;
  namespace?: string;
  name: string;
  taskSummary?: string;
  status: "queued" | "running" | "blocked" | "done" | "failed" | "unknown";
  outputSummary?: string;
  parentId?: string;
}
```

The starter agent emits artifact declarations through a versioned state field/tool whose schema is covered by fixture tests. FastAPI validates declarations and creates catalog records; it never trusts an agent-provided URL as authorization. `GET /api/v1/tasks/{id}/artifacts` returns descriptors, and a separate authorized content route or provider redirect resolves bytes.

`SPIKE-ARTIFACT-001` must establish file/state/sandbox download behavior, media metadata, range/size limits, expiring access, and retention for the classic source. If a source cannot expose content safely, the artifact remains metadata-only with an **Open at source** action; Deep Work does not scrape undocumented connector routes.

`SPIKE-SUBAGENT-001` must capture namespace, discovery, message/tool association, completion, failure, and reconnect transcripts from the pinned starter agent. Sources without that contract show no Subagents panel. Async subagent APIs are not called in v1.

## Persistence and security

- Artifact metadata is tenant/source/task scoped and immutable per version. Checksums and provenance support tamper/staleness detection.
- Content access rechecks current authorization and uses short-lived provider/object URLs or streamed application responses with strict size/content headers.
- Render all artifact content, citations, filenames, source pages, model output, and subagent output as untrusted.
- Block active HTML/script, unsafe SVG, macro execution, path traversal, and MIME/extension mismatch. Downloads use safe disposition.
- Do not log artifact bodies, research prompts, private repository content, or hidden subagent context.
- Subagent status never broadens the user's permissions; nested source/tool access remains under the parent task's policy.
- Retention/deletion follows the byte owner's policy and an application tombstone; v1 never claims external bytes were deleted unless confirmed.

## Responsive and accessible behavior

- Every journey has the same stable Task/Run/Artifact landmarks, with journey-specific labels rather than entirely different navigation.
- Artifact list exposes title, kind, version, state, provenance summary, and size in text. Preview has a Download/Open fallback.
- Citations are keyboard reachable, have meaningful link text, and identify external navigation.
- Subagents render as a nested semantic list with textual parent/status. A compact mobile summary expands to details.
- Diff and code review requirements are defined in `DW-CODE-003`; research/writing previews reflow at 200% zoom.
- Live changes use throttled announcements; reduced motion removes subagent pulses.

## Metrics and guardrails

- Completion, failure, and time-to-first-artifact by task kind.
- Artifact transfer/preview/download success and stale-content rate.
- Percentage of research report claims/evidence records with available provenance metadata, treated as coverage rather than truth.
- Revision rate and rubric-verification outcome by journey.
- Subagent discovery/unknown/failure rates; no invented utilization metric.
- Coding funnel: task started, diff ready, draft PR ready, CI green, merged.
- Guardrails: zero cross-task artifact access; zero unsupported source shown as subagent-capable; zero Done based only on a declared artifact before runtime terminal reconciliation.

## Dependencies and rollout

- Depends on task composer/detail and HITL/verification. Coding-runtime plans consume this journey and artifact contract; the coding path remains disabled until their gates pass.
- Phase 0: accept artifact/subagent fixtures and terminology in the glossary.
- Phase 1: research and writing with text/markdown artifacts on the starter classic agent.
- Phase 2: media/document artifacts and synchronous subagent cards.
- Phase 3: coding journey after sandbox/GitHub/diff acceptance is green.
- Capability flags can disable artifact preview or subagent projection independently; metadata/history remains accessible where authorized.

## Executable acceptance scenarios

```gherkin
Scenario: Research completion includes provenance without claiming truth
  Given the research fixture produces a report and three evidence records
  When the task completes
  Then the report artifact lists all three provenance references
  And unresolved claims are visible
  And the UI does not label cited claims as verified solely because citations exist

Scenario: Working file is not automatically a final artifact
  Given a writing task has four files in its workspace
  And the agent declares only final.md as an artifact
  When the artifact list renders
  Then final.md appears as the named artifact
  And the other files remain working files

Scenario: Unsupported subagent source stays honest
  Given a source manifest has subagents false
  When its task detail renders
  Then no Subagents panel or fake progress is shown
  And the rest of the task remains usable

Scenario: Coding outcome has distinct terminal substates
  Given the agent run completed and a draft PR exists but CI is failing
  When the coding task summary renders
  Then agent status is complete
  And PR status is draft
  And CI status is failed
  And Merge remains unavailable with the failing check reason
```

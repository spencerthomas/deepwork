---
feature_id: DW-FUT-205
title: GitLab, multi-repository worktrees, and editor protocols
release: v2
status: canonical-deferred-brief
decision_status: discovery-gated
owners: [coding, integrations, desktop]
surfaces: [task-composer, task-detail, settings, editors]
runtime_scopes: [classic]
source_refs: [SRC-DW, SRC-FE]
dependencies: [DW-CODE-001, DW-CODE-002, DW-CODE-003]
last_reviewed: 2026-07-23
---

# GitLab, multi-repository worktrees, and editor protocols

> This v2 brief is discovery-gated. GitLab, multi-repository transactions, worktree behavior, ACP, A2A, and MCP are separate capability tracks. No provider route, credential flow, protocol version, or atomicity guarantee is asserted here.

## User outcome

Coding users can work through approved GitLab and multi-repository changes and hand off to supported editors/peers while retaining repository-specific isolation, credentials, provenance, diff, review, CI, and landing status.

## Evidence and confidence

- `SRC-DW` identifies GitLab, worktrees, multiple repositories, and agent/editor protocols as future expansion. Confidence: medium for demand, low for combined release scope.
- `SRC-FE` provides interaction ideas but no provider/runtime proof. Confidence: low for implementation authority.
- The v1 sandbox/GitHub/files/diff foundation supplies semantics that can be generalized only after provider and multi-repo conformance. Confidence: medium.

## Scope, ownership, and non-goals

Coding owns environment/repository manifest, worktree lifecycle, diffs, cross-repo review, CI, and partial-failure semantics. Integrations owns GitLab auth/API/webhooks and verified protocol adapters. Desktop owns secure editor handoff, local deep links, consent, and session lifecycle.

In scope:

- GitLab installation/OAuth hypothesis, repository selection, branches, merge requests, pipelines, scoped credential broker, and landing status.
- Approved multi-repository manifest, isolated checkout/worktree per repository, cross-repo task provenance, per-repo diffs/CI/landing, and explicit partial success.
- Versioned, authenticated, consented editor/peer handoff where a stable protocol is verified.

Non-goals:

- Pretending cross-repository changes are an atomic commit/merge, unrestricted repository discovery, exposing provider tokens to sandboxes, or supporting arbitrary VCS/providers.
- Generic peer-to-peer agent networking, silent local-editor control, or advertising ACP/A2A/MCP support from naming alone.
- Changing the v1 one-GitHub-repository-per-task baseline.

## Primary journeys

1. **GitLab task:** connect an installation, choose an allowed repository/ref, create an isolated branch/environment, review diff, open MR, follow pipeline, and confirm landing.
2. **Multi-repo plan:** select approved repositories and intended dependency/order; preflight access, storage, refs, setup, and policy before execution.
3. **Review partial work:** inspect per-repo files/diffs/tests/CI, understand cross-repo dependencies, and land, retry, revert, or abandon each with an explicit overall result.
4. **Editor handoff:** user chooses an approved editor, reviews shared repository/task scope and expiry, then opens a consented session with revocation.
5. **Recover:** checkout, provider, editor, CI, or merge failure preserves unaffected repositories and exact provenance.

## Complete state matrix

| State/condition | Expected experience |
| --- | --- |
| Loading | Probe provider installation, repository access, refs, environment capacity, and protocol capability independently. |
| Empty | Explain supported provider/repository limit and offer connection/selection; no repository list is shown without authorization. |
| Preflight | Display every repository/ref, access level, storage/setup estimate, branch policy, dependency, and credential mode before launch. |
| Checking out | Show per-repository progress and safe cancellation; parent status remains initializing until required repositories are ready. |
| Active | Files/diffs/terminal/CI are partitioned by repository with persistent provenance context. |
| Partial failure | Identify failed repository and downstream impact; unaffected state is preserved, and completion cannot be claimed as atomic. |
| Error | Separate provider auth/API, checkout, setup, storage, protocol, diff, CI, and landing failures with idempotent recovery. |
| Offline | Cached diffs/status may be read with timestamp; repository/provider/editor mutations require connectivity. |
| Permission denied | Hide inaccessible repositories/branches/content and revoke active handoffs when derived permission changes. |
| Reconnecting | Reconcile refs, environment/worktrees, diffs, provider objects, CI, and editor session before controls re-enable. |
| Stale/diverged | Show base/head changes per repository, block unsafe landing, and require refresh/rebase/replan under policy. |
| Editor disconnected/expired | Preserve server task state, revoke session capability, and offer a newly consented handoff. |
| Mobile | Provide per-repo summary, approvals, CI/landing status, and secure desktop handoff; terminal/full cross-repo diff are not forced onto phone. |

## Proposed interfaces (non-binding)

Illustrative application concepts are `RepositoryProvider`, `RepositoryBinding`, `EnvironmentRepository`, `MultiRepoManifest`, `RepoWorkState`, `LandingPlan`, and `EditorHandoff`. Each repository has provider identity, immutable selected ref, working ref, environment path namespace, authorization reference, diff/CI/landing state, and dependency labels.

GitLab request/payloads and protocol transports are not specified. A protocol adapter may advertise version and granular capabilities only after conformance. No `all_or_nothing` landing mode is offered unless a real transaction mechanism is proven; the default aggregate reports per-repository outcomes.

## Runtime capability and fallback

- Source manifest distinguishes GitHub/GitLab provider actions, multi-repo environment support, storage limits, worktree support, terminal/files/diff, and editor/protocol adapters.
- Unsupported provider/protocol controls remain hidden or diagnostic; no generic route guessing.
- Multi-repo fallback is a parent task with separate one-repository child tasks and explicit dependency/landing coordination.
- Editor fallback is a copyable command/path/diff bundle or secure desktop deep link; v1 web/desktop workspace remains authoritative.

## Persistence and security

Persist provider/repository/ref identities, installation/credential references, environment/worktree mapping, setup results, per-repo diffs/CI/landing references, handoff consent/scope/expiry, idempotency, and audit. Provider credentials remain in the broker and are never written to git remotes, sandboxes, patches, logs, or editor payloads.

Validate repository URLs, refs, submodules, LFS, nested repositories, symlinks, worktree paths, archive content, hooks, setup scripts, and cross-repo filesystem isolation. Protocol peers authenticate, receive least scope/time, cannot infer other repos/tenants, and are revocable. Egress and secret policies apply per environment and repository.

## Responsive and accessible behavior

Desktop provides repository switcher plus aggregate summary; selection is persistent and announced. Diffs/CI have semantic repository labels, keyboard navigation, text status, accessible added/removed content, and no color-only dependency. Narrow screens use repository cards and one-next-action summaries with a secure desktop handoff for dense tools.

## Metrics and guardrails

- GitLab task success and parity by v1 coding stage; provider auth/CI/landing failure.
- Multi-repo preflight success, partial-failure recovery, cross-repo completion, wrong-repo edit, and false-atomic-completion rates.
- Editor handoff success, expiry/revocation time, protocol errors, and unauthorized disclosure; security targets zero.
- Guardrails: zero provider token in sandbox, zero hidden repository mutation, explicit per-repo landing, and no protocol support claim without pinned conformance.

## Dependencies

- `DW-CODE-001` for sandbox/environment/snapshot/setup/egress lifecycle.
- `DW-CODE-002` for credential broker, repository/branch/PR/CI/landing semantics.
- `DW-CODE-003` for files, diff, terminal, browser flag, comments, and phone landing flow.
- `DW-FUT-101` may later coordinate multi-repo child-task fallback but is not required for discovery.

## Rollout and rollback

1. Separate GitLab, multi-repo, and protocol discovery/evaluation tracks.
2. GitLab read-only repository/CI prototype, then one-repository internal task parity.
3. Multi-repo read-only preflight and diff aggregation using fixtures; then isolated test repositories.
4. Editor handoff local prototype with synthetic task and explicit consent.
5. Pilot each capability behind independent flags after its security/conformance gates pass.

Rollback disables provider dispatch, additional repositories, and editor sessions independently; revokes active credentials/sessions; preserves read-only provenance/diffs; and keeps each repository’s branches/MRs for explicit cleanup. It never deletes or force-resets repository work automatically.

## Executable acceptance scenarios

1. Given a GitLab installation, when a task completes, then branch, diff, MR, pipeline, landing status, and audit are shown with no provider token in the sandbox.
2. Given two repositories and one checkout failure, when preflight/execution runs, then the healthy repository remains intact and the parent cannot claim atomic completion.
3. Given one repository diverges before landing, when the user reviews the plan, then only affected landing is blocked and dependency impact is explicit.
4. Given a malicious nested repository/symlink/setup script, when environment initialization runs, then cross-repository/environment boundary escape is blocked and audited.
5. Given an expired editor session, when the peer reconnects, then no task/repository metadata is disclosed before new authentication and user consent.
6. Given no verified multi-repo runtime capability, when the user requests two repositories, then linked single-repo child tasks are proposed with explicit non-atomic semantics.
7. Given a phone user opens a multi-repo approval, then each repository impact and safe next action is accessible, with full diff handoff available.

## Explicit discovery gates

- **GitLab contract:** verify current app/OAuth, repository/ref/MR/pipeline/webhook, token brokerage, rate-limit, and enterprise controls against official/live contracts.
- **Multi-repo model:** decide repository manifest, environment/worktree isolation, dependency, failure, retry, snapshot, and landing semantics.
- **Security:** threat-model provider credentials, malicious repos/submodules/hooks/symlinks, path isolation, editor peers, protocol confused-deputy, and data leakage.
- **Protocol per adapter:** pin ACP/A2A/MCP versions, authentication, discovery, capabilities, cancellation, error, and compatibility tests independently.
- **Operations:** prove storage/capacity, cleanup, reconciliation, provider outage, branch/MR orphan handling, and support tooling.
- **Product/accessibility:** validate aggregate versus per-repo comprehension and safe editor/mobile handoff.

Each track remains non-ready until its own gates pass; success in one must not promote the others.

---
feature_id: DW-QUAL-001
title: Accessibility, performance, security, testing, and release
release: v1
status: canonical-spec
decision_status: blocked-on-spikes
implementation_readiness: not-ready
owners: [quality, security, platform, product]
surfaces: [all]
runtime_scopes: [any]
source_refs: [SRC-DW, SRC-LC, SRC-FE, SRC-DA, SRC-LCPY, SRC-LCJS, SRC-LG, SRC-HE, SRC-EXEC, SRC-SYM, SRC-FASTAPI, SRC-SQLA, SRC-NEXT, SRC-QUERY, SRC-PWA, SRC-TAURI, SRC-RUST]
evidence_pins:
  frontend: 26c698b
  langchain_docs: 7b9215d
  canonical_plan: 06f0515
  deepagents: 7794b61
  langchain_python: 592055e
  langchainjs: ee76ea0
  langgraph: 31f90df
dependencies: [DW-FND-001]
cross_cutting_release_inputs: all-enabled-v1-plans-via-generated-traceability
contract_gates: [SPIKE-AUTH-002, SPIKE-SOURCE-001, SPIKE-STREAM-001, SPIKE-HARNESS-DOCS-001, SPIKE-HARNESS-ARCH-001, SPIKE-WORKTREE-001]
optional_contract_gates: [SPIKE-AUTH-001, SPIKE-MDA-001, SPIKE-FLEET-001, SPIKE-DESKTOP-001, SPIKE-PWA-001, SPIKE-SYMPHONY-001, SPIKE-DEV-OBS-001, SPIKE-DOC-GARDEN-001]
last_reviewed: 2026-07-23
---

# Accessibility, performance, security, testing, and release

## User outcome

V1 is released only when a real user can complete the promised journeys safely, accessibly, responsively, and recoverably on the supported stack. Every enabled external capability has pinned evidence; every required state is executable; fixture and live behavior share normalized contracts; and rollback preserves user state and authoritative external work.

This is a proposed release-governance plan, not an implementation-ready sign-off. It remains blocked until every owning v1 plan is accepted, all five named spikes produce approved evidence for enabled capability cells, supported platform matrices are fixed, and release criteria map to passing executable scenarios.

## Evidence and confidence

| Evidence | Classification | Confidence | Planning consequence |
|---|---|---:|---|
| The prototype at `26c698b` is rich interaction evidence but includes simulated/inert controls and incomplete responsive/failure states. | Direct repository audit | High | Screenshots and happy-path component tests cannot qualify release. |
| Existing plans contain contradictory or unsupported assumptions about auth, protocol v2, HITL, MDA, Fleet, global search, and deployment ownership. | Planning and contract audit | High | Contract tests and accepted live spikes are release-blocking for every enabled cell. |
| V1 promises a 15-minute first-task journey, complete phone loop, approvals, coding/PR flow, source health, traces where supported, agent portability, and safe sandbox/content behavior. | Product requirement | High | Each criterion needs a named owner, clean-account fixture/live scenario, telemetry, and failure recovery. |
| The chosen stack spans Python 3.12 FastAPI/Postgres, a separate Python agent package, Next.js 16/React 19 web/PWA, TypeScript SDK/UI, and Tauri v2. | Proposed architecture | Medium until review | Qualification must test contract/version/migration compatibility across independently deployable layers. |
| Accessibility, browser/PWA, and desktop-native behavior cannot be proven by automated tooling alone. | Standards/platform reality | High | Require manual keyboard, assistive-technology, zoom/reflow, real-device, and platform sign-off. |
| Classic LangSmith Deployment is the public baseline; MDA/Fleet are gated. | Audited docs posture | High | Classic must complete v1; gated adapters cannot be required to declare v1 successful. |
| The pinned LangChain repositories use package-local commands, deliberate exports, downstream/clean-consumer checks, network-disabled unit suites, standard adapter tests, and generated-artifact checks. | Direct reference-code audit | High | Those practices become release evidence; matching file names without their enforcement method is insufficient. |

## Scope, ownership, and non-goals

### In scope

- One release evidence model covering requirements, owning plan/scenario, commit/build, environment, fixture/live tier, contract/package versions, result, defect waiver if permitted, and reviewer.
- WCAG 2.2 AA, keyboard-only completion, screen-reader qualification, reduced motion, forced colors/high contrast, 200%/400% zoom/reflow, touch, voice-input fallback, and cognitive/error clarity.
- Performance budgets for Next.js shell/routes, `/api/v1`, 1,000-task aggregation, long threads, streaming reducer/memory, subagent lazy loading, artifacts/diffs, PWA foreground recovery, and Tauri startup/update.
- Threat modeling and abuse tests for auth/session, CSRF/CORS, tenant isolation, SSRF/proxying, credentials/encryption, webhooks/replay, ZIP import, untrusted content, sandbox/path/egress, GitHub auth proxy, push/cache, and Tauri webview/deep-link/updater.
- Unit, property, component, visual, contract, integration, migration, end-to-end, live external, chaos/failure-injection, accessibility, performance, and platform qualification suites.
- Fixture/live parity, network-denied demo tests, captured transcript governance, test-data safety, and deterministic clocks/IDs.
- Documentation/quickstart, support/runbook, migration/restore/rollback rehearsal, release flags, staged cohorts, acceptance decision, and post-release monitoring.
- Independent compatibility and rollback of FastAPI/Postgres migrations, Python agent package, TypeScript SDK/UI, Next.js client/service worker, and Tauri channel.
- Clean package build/install and public-import tests for both Python distributions; generated OpenAPI/TypeScript drift, export/type, downstream-package, and clean-consumer tests for browser-safe packages.
- Provider adapter conformance tests using sanitized golden transcripts plus explicit live-contract jobs; ordinary unit and fixture suites run with external networking denied.
- Architecture graph/structural tests, documentation index/living-plan/freshness/generated checks, deterministic generated traceability, and deliberate negative boundary fixtures.
- Evidence-backed `docs/QUALITY_SCORE.md`, owned/aged architecture exceptions and debt, recurring documentation gardening, and clean contributor/agent worktree qualification.
- Symphony pilot evidence for only the orchestration cells enabled in development: issue eligibility/blockers, isolated workspaces, host-only credentials, reconciliation/retry/restart, proof handoff, and Human Review. Symphony is not a product release dependency when manual dispatch is the accepted fallback.

### Ownership

- Each feature owner writes and maintains its acceptance scenarios, complete state fixtures, metrics, runbook, and rollback trigger.
- Quality owns the evidence ledger, test taxonomy, platform matrix, flake policy, release dashboard, and acceptance facilitation.
- Security owns threat model, high-risk abuse cases, finding severity/exception policy, secret/tenant tests, and release security sign-off.
- Accessibility owner and representative assistive-technology users/reviewers own manual journey sign-off; automated axe is supporting evidence only.
- Platform owns CI, environments, provenance, migrations, staged flags, release artifacts, monitoring, and rollback execution.
- Developer experience owns truthful package-local `Makefile`/`package.json` commands, the root fan-out, clean-clone quickstart, generated-artifact policy, and supported downstream compatibility jobs.
- Architecture owns the machine-readable graph, boundary diagnostics, exception lifecycle, and generated package/architecture views. Documentation owners own canonical indexes, governed-path freshness, living-plan conformance, generated-doc provenance, quality score, and gardening.
- Product owns the promised journey set, supported/fallback scope, go/no-go decision, and explicit residual-risk acceptance.
- External contract evidence is co-owned by the adapter/feature owner; no team can waive an unknown contract into “supported.”

### Non-goals

- Defining business behavior already owned by feature plans, inventing runtime APIs to make tests pass, or making QA the owner of feature quality.
- Releasing based on prototype parity, unit-test count, code coverage alone, screenshots, mocked private-beta endpoints, or a single desktop/browser path.
- Claiming all browsers/platforms/runtime tiers are supported; unqualified cells must be unavailable with a documented fallback.
- Zero defects as a slogan. V1 requires zero unresolved critical/high security findings and explicit severity/waiver rules for all other defects.
- Requiring MDA, Fleet, native desktop, install/PWA, or push to pass the classic responsive-web baseline if their gates fail; their user-facing claims must instead be removed/disabled.

## Release criteria and owning evidence

| Release criterion | Owning plans/scenarios | Required tier |
|---|---|---|
| Clean sign-in through first completed draft PR in under 15 minutes | DW-ONB-001/002, DW-TASK-002/003/004, DW-CODE-001/002/003 | Classic live plus fixture diagnostics |
| Complete phone dispatch/watch/steer/approve/review/land loop | DW-SURF-001, DW-TASK-002/003/004, DW-HITL-001, DW-CODE-003 | Qualified responsive browser/PWA; classic live |
| Ordered approval batch including edit and stale handling | DW-HITL-001, DW-FND-004/005 | Captured contract plus classic live |
| Disconnect/background/reconnect without duplicate or accidental cancel | DW-FND-004/005, DW-TASK-003/004, DW-SURF-001 | Every enabled stream adapter |
| Sandbox/repository/diff/PR/CI journey with safe credentials and egress | DW-CODE-001/002/003 | Supported coding source/live test repo |
| Fleet read/invoke or MDA behavior where advertised | DW-AGENT-001/002, DW-HITL-001 | Only accepted `SPIKE-FLEET-001`/`SPIKE-MDA-001` cells |
| Trace link on trace-enabled run; slim activity without reimplementing LangSmith | DW-OPS-001/002 | Classic trace-enabled source |
| Portable agent project round trip and explicit draft/save/deploy semantics | DW-AGENT-003/004/005 | Fixture plus supported live deploy adapter |
| Zero secrets crossing sandbox/browser/log/cache/notification/desktop boundaries | DW-FND-003, DW-CODE-001/002, DW-SURF-001/002 | Security suite and reviewed live probes |
| UI harness renders isolated states and API-backed product demo reaches the representative full-stack experience without external/provider traffic | DW-FND-001/002/003/004 | Clean CI, local product-demo stack, and preview |
| Repository map, architecture, product specs, ExecPlans, generated views, and issue traceability remain executable | DW-FND-001, DW-QUAL-001 | Architecture/docs checks plus clean-agent navigation exercise |
| Symphony pilot dispatches only reviewed unblocked work and hands off safely, or manual fallback is formally selected | DW-FND-001, DW-QUAL-001 | `SPIKE-SYMPHONY-001`; not a product runtime gate |
| Web/PWA accessible primary journey | All relevant v1 surface/feature plans | Supported browser/AT matrix |
| Desktop native value, if shipped | DW-SURF-002 | Every enabled Tauri platform/channel after `SPIKE-DESKTOP-001` |

## Primary journeys

### Feature owner: build verifiable evidence

1. Link each user outcome and state row to deterministic fixture, service contract, integration, and/or live scenario as applicable.
2. Record exact source commit, API/schema, package/server, browser/OS/device, runtime tier, and capability manifest.
3. Run happy path, required failure/recovery, accessibility, security, performance, and rollback checks.
4. Attach sanitized machine-readable results to the release evidence ledger; failures create owned defects.
5. A feature can become implementation-ready only after all implementation choices are accepted and external contract gates pass. This proposal itself remains review-stage evidence.

### Release candidate qualification

1. Build immutable artifacts from a pinned clean commit and generate provenance/checksums/version compatibility.
2. Apply expand-phase database migrations to a production-like environment and verify old/new application compatibility.
3. Run fixture, integration, captured contract, classic live, browser/PWA, security, accessibility, performance, and platform suites.
4. Complete manual clean-account journeys and documentation walkthrough with no undocumented access.
5. Review failures, waivers, gated capability claims, monitoring, support, flags, and rollback readiness.
6. Product, quality, security, accessibility, and platform owners sign one evidence-backed go/no-go record.

### Incident or failed cohort rollback

1. Monitoring or user report crosses a predefined guardrail/rollback trigger.
2. Disable the narrowest affected capability/source/surface flag while preserving healthy journeys.
3. Restore compatible application/agent/client/desktop artifacts and stop incompatible migrations from contracting.
4. Reconcile in-flight authoritative LangSmith runs without cancelling them because a client rolled back.
5. Verify user data, sessions, source state, audit history, notifications, and idempotency remain consistent.
6. Document cause/evidence and require renewed acceptance before re-enabling.

## Complete state matrix

Every asynchronous user-facing surface must exercise the following states. “Not applicable” requires a written justification in the owning plan and evidence ledger; absence of a fixture is not a justification.

| State | Required evidence | Release expectation |
|---|---|---|
| Initial loading | Skeleton/progress, dimension stability, timeout, assistive announcement. | No indefinite spinner or unauthorized flash. |
| Empty | Authorized healthy empty state distinguished from capability/permission failure. | Clear next safe action. |
| Success | Outcome, provenance/freshness, idempotency, cross-surface consistency. | Matches user promise and normalized contract. |
| Validation error | Field/summary focus, safe retained input, no upstream side effect. | Keyboard/screen-reader recoverable. |
| Authentication expiry | Protected data cleared/held safely, return path, no attempted unsafe mutation. | Reauth scenario passes on web/PWA/Tauri. |
| Permission denial/revocation | No existence/content leak, source/workspace scope, access recovery. | Tenant isolation and stale-cache purge pass. |
| Capability unsupported/unknown | Explanatory unavailable state and verified fallback. | No guessed endpoint or empty success. |
| Partial source failure | Healthy data preserved, failed source identified, stable pagination/retry. | No whole-page collapse when separable. |
| Upstream rate limit | Retry-after/backoff, no retry storm, other sources remain usable. | Bounded recovery. |
| Transport/network error | Safe error, correlation, abort/timeout, no false terminal state. | Retry/reconcile path passes. |
| Offline cold start | Safe shell/explanation only. | No credential validity or mutation claim. |
| Offline warm state | Approved bounded cache, timestamp/read-only, purge policy. | No sensitive cache/mutation replay. |
| Reconnecting/background return | Reauthorization, verified cursor/full hydration, dedupe/focus retention. | Every durable event once; no disconnect-as-cancel. |
| Stale/concurrent state | Version conflict/current entity, no silent overwrite or stale approval. | Explicit refetch/review. |
| Cancel requested | Cancelling substate and authoritative confirmation. | No client-only cancellation result. |
| Retry | New attempt, idempotency, prior history retained. | No duplicate run or rewritten history. |
| Degraded dependency | Capability/source-scoped banner and fallback. | Healthy product paths remain. |
| Malformed/untrusted content | Bounded rendering, safe links/download, no script/privilege. | Abuse suite passes. |
| Large/long content | Virtualization/lazy detail, stable order/focus, memory budget. | Supported reference-device budget passes. |
| Mobile/narrow/keyboard | Reflow, safe areas, touch targets, equivalent action, draft retention. | Complete phone journey passes. |
| Reduced motion/high contrast/zoom | Equivalent information/action without clipped content. | Manual and automated acceptance. |
| New app/service-worker/desktop version | Compatibility, controlled refresh/restart, draft/data preservation. | Upgrade and rollback pass. |
| Database migration/restore | Old/new compatibility, backup restore, idempotent replay. | No release without rehearsal. |

## Proposed interfaces

```ts
type EvidenceTier = "fixture" | "captured-contract" | "classic-live" | "gated-live" | "platform-manual";

interface ReleaseEvidence {
  criterionId: string;
  featureIds: string[];
  scenarioId: string;
  tier: EvidenceTier;
  sourceCommit: string;
  buildId: string;
  environmentId: string;
  versions: Record<string, string>;
  capabilitySnapshot?: Record<string, string>;
  result: "passed" | "failed" | "blocked" | "not-applicable";
  artifactRefs: string[];
  sanitizedAt: string;
  reviewerIds: string[];
  exceptionId?: string;
}
```

Proposed verification seams:

- FastAPI `/api/v1/health/live`, `/api/v1/health/ready`, migration compatibility, typed error/correlation IDs, and synthetic test identities are observable without exposing secrets.
- OpenAPI and TypeScript SDK compatibility are checked as artifacts; web components cannot bypass SDK contracts with raw provider calls.
- FastAPI OpenAPI generation is deterministic: CI fails on an uncommitted generated client diff, then installs the built `packages/sdk` in a clean consumer that imports only documented exports.
- The separate Python agent package publishes pinned runtime/dependency metadata and contract fixtures independently from the application service.
- `apps/api` and `packages/agent` each build and install from their own lock/manifests into clean environments, then run public-import and minimal supported-use tests without relying on a root Python environment.
- Each Python provider/source adapter passes the standard capability, identity, pagination, error, HITL, stream/recovery, redaction, and partial-failure suite under `apps/api` against sanitized transcripts. The TypeScript `internal/adapter-tests` project independently proves generated transport, DTO, reducer, and client behavior against the same corpus. Only protected live jobs may promote a source contract cell to available.
- Pull-request unit suites deny unexpected sockets. Tests requiring Postgres, browsers, providers, signing, or other services are explicit integration/qualification lanes rather than hidden unit-test dependencies.
- Next.js/PWA exposes build/schema version and safe service-worker status for compatibility checks; Tauri exposes signed app/channel/platform version and capability manifest.
- Contract evidence stores sanitized transcripts and assertions, never raw customer prompts, tools, repositories, traces, or credentials.
- Release flags are server-authoritative and source/capability scoped; client hiding alone cannot enable/disable security behavior.

## Runtime capability and fallback

- Classic LangSmith Deployment must complete the supported v1 live journey. A failure here blocks v1 unless the product claim is explicitly reduced and re-reviewed.
- `SPIKE-AUTH-002` gates the classic API-key/header baseline. `SPIKE-AUTH-001` gates optional OAuth token audiences; unsupported OAuth falls back to the verified API-key path.
- `SPIKE-STREAM-001` gates base protocol-v2/legacy/run-join transport, replay/reconnect, and hydration cells. Submit/multitask, HITL, queue/cancel, checkpoint, artifact, and subagent cells remain gated by their separate named spikes and fallbacks.
- `SPIKE-MDA-001` and `SPIKE-FLEET-001` gate private-beta/capability-specific claims. Failure disables those cells; it does not block classic baseline.
- `SPIKE-DESKTOP-001` gates each Tauri platform/native feature. Failure holds desktop/native feature while responsive web/PWA remains the fallback.
- PWA push/install/voice/offline enhancements require the platform qualification named in `DW-SURF-001`; in-app notifications and ordinary responsive web are required fallbacks.
- Unknown is never counted as passed, unsupported is never represented as empty success, and a fixture cannot promote an external capability to supported.

## Persistence and security

- Release evidence, scenario results, defect links, approvals, exceptions, versions, and rollback actions persist in a tamper-evident audit location with least-privilege access and retention policy.
- Test accounts/credentials use least privilege, synthetic workspaces/repositories/data, short-lived tokens, isolated databases/sandboxes, and automated revocation/cleanup.
- Captured contracts/fixtures are synthetic or scrubbed through an approved process; secret scanning and human review precede repository inclusion.
- CI privileged jobs never execute untrusted pull-request code with production secrets. Signing, migration, publishing, live-contract, and desktop notarization environments are protected separately.
- Security tests cover OWASP-relevant web/API boundaries plus domain-specific prompt/tool/untrusted-content and agent/sandbox risks. Results contain sanitized proof, not exploit secrets in public artifacts.
- Performance/accessibility telemetry excludes prompts, repository content, tool arguments/results, artifact content, credentials, and raw trace payloads.
- Backup/restore, encryption/key rotation, account deletion, audit retention, cache purge, and provider-owned external resource boundaries have executable evidence.

## Responsive and accessible behavior

- WCAG 2.2 AA is the minimum target for both themes and every primary/error/recovery journey; any exception requires issue, user impact, workaround, owner, deadline, and product/accessibility approval.
- Keyboard-only users complete sign-in/onboarding, task dispatch/watch/steer, ordered approvals, file/diff/PR review, settings, notification, and recovery without focus traps or pointer-only actions.
- Manual screen-reader matrix includes accepted VoiceOver/Safari, NVDA/Firefox or Chrome, Narrator/Edge, mobile VoiceOver/TalkBack, and desktop native combinations where shipped.
- Test at 320 CSS pixels and 400% zoom/reflow, 200% text zoom, landscape/portrait, virtual keyboard, safe areas, forced colors, reduced motion, and increased contrast.
- Streaming/token/tool updates are announcement-throttled; focus and reading order remain stable through hydration, virtualization, reconnect, and responsive rearrangement.
- Performance testing uses reference low/medium hardware and constrained network profiles, not only developer machines.
- Every desktop tray/notification/update action has an equivalent accessible main-window flow; every PWA enhancement has an ordinary web/in-app fallback.

## Metrics and guardrails

### Proposed release targets

- Unresolved critical/high security findings: zero.
- Serious automated accessibility violations on accepted pages/states: zero; primary journeys also require manual assistive-technology sign-off.
- Contract suite against every enabled pinned client/server/adapter pair: 100% passing.
- Clean build/install/public-import and documented-export tests for every publishable package: 100% passing; generated OpenAPI/SDK diff after regeneration: zero.
- Unexpected outbound network attempts in unit/fixture/demo suites: zero.
- Duplicate durable event, external mutation, approval, webhook, notification, or retry effect in recovery suites: zero.
- Cross-tenant/source identity or authorization escape: zero.
- p75 local UI interaction latency: under 200 ms on the agreed reference device/profile.
- 1,000-task inbox and long-thread fixtures meet accepted frame, memory, interaction, and screen-reader/keyboard budgets; 60 fps is a target where animation/scrolling is active, not a substitute for task latency.
- Clean-account median first completed draft PR: under 15 minutes, with p75 and failure categories reported.
- Complete phone journey pass: 100% on each supported browser/OS cell.
- Sensitive data found in logs/traces/cache/push/deep links/test artifacts: zero.
- Broken/orphaned canonical docs, duplicate stable IDs, generated drift, missing active-ExecPlan living sections, unrecorded architecture edges, and expired exceptions: zero.
- Blocked/unlabelled Symphony issue dispatches, cross-worktree resource collisions, child-process tracker credential exposures, and duplicate PR/external effects after retry/restart: zero in the accepted pilot.

### Guardrails

- No release from unpinned/dirty sources, missing provenance, skipped required checks, incompatible schema, failed restore, or untested rollback.
- No external capability marked supported from prose, generated types, prototype control, or fixture alone.
- No waiver for unknown authorization/credential/tenant boundary or unresolved critical/high security finding.
- No flake retry that converts a deterministic product failure into green without an owned defect and root-cause classification.
- No performance optimization that removes accessibility, content provenance, security validation, or failure-state clarity.
- No Tauri/PWA/private-beta claim may block the classic responsive web baseline; disable the gated claim instead.

## Dependencies, external contract gates, rollout, and rollback

### Dependencies and gates

- `DW-FND-001` establishes the quality harness. The generated release traceability view then consumes every enabled v1 plan/scenario as release input without an invalid `all-v1-capability-plans` tracker blocker.
- `SPIKE-AUTH-002`, `SPIKE-SOURCE-001`, and `SPIKE-STREAM-001` are required for the classic baseline cells. `SPIKE-AUTH-001`, `SPIKE-MDA-001`, `SPIKE-FLEET-001`, `SPIKE-PWA-001`, and `SPIKE-DESKTOP-001` are required only for the optional claim they enable; failed cells are visibly removed or gated.
- `SPIKE-HARNESS-DOCS-001`, `SPIKE-HARNESS-ARCH-001`, and `SPIKE-WORKTREE-001` are required before broad agent dispatch or feature migration. Failed Symphony remains compatible with manual dispatch.
- Platform support, browser/assistive-technology matrix, performance reference profiles, severity policy, retention, and release-authority matrix require explicit review decisions.
- Every v1 release criterion maps to at least one clean executable end-to-end scenario and every current route/tab/settings section maps to one owner or explicit removal disposition.

### Proposed rollout

1. Build the evidence ledger, scenario taxonomy, platform matrices, fixture corpus, and quality budgets before feature implementation begins.
2. Run package-local formatter/linter/type/test/build commands, clean Python installs, generated OpenAPI/SDK drift, TypeScript export/clean-consumer, downstream-package, fixture/unit/property/contract/accessibility/security-static checks on pull requests; preserve a no-credential network-denied path.
3. Start internal classic-deployment dogfood with synthetic repos/accounts as soon as one vertical journey exists.
4. Add live contract, chaos, browser/PWA, manual AT, performance, and Tauri qualification as capabilities become reviewable.
5. Enter a small invited cohort behind server-side flags only after security/accessibility/restore/rollback gates pass.
6. Freeze a release candidate, run clean-account/documentation walkthroughs and independent sign-off, then stage rollout with guardrail monitoring.
7. Expand cohort only when failure, latency, security, accessibility, duplicate-effect, and support metrics stay within thresholds.

### Rollback

- Each source adapter, external mutation, PWA enhancement, notification channel, and desktop native feature has a server/client flag and documented fallback.
- FastAPI, Python agent, TypeScript SDK/web, service worker, and Tauri artifacts roll back independently only within an accepted compatibility matrix.
- Database uses expand/migrate/contract; do not contract until rollback window closes and restore rehearsal passes.
- Rollback preserves Postgres application state, audit/idempotency, fixture evidence, and authoritative LangSmith runs. Disconnecting or replacing a client does not cancel work.
- Security incidents can revoke sessions/source credentials/device bindings, disable adapters/channels, and pause updates while retaining forensics under policy.

## Executable acceptance scenarios

```gherkin
Scenario: A clean account completes the classic first-PR promise
  Given a supported browser, clean Deep Work account, approved classic deployment, and synthetic GitHub repository
  When a participant follows the published quickstart without undocumented help
  Then they authenticate, select a workspace, connect a source, start a coding task, handle any ordered approval, review the diff, and create a draft PR
  And elapsed time and failure categories are recorded without user content
  And the median qualified result is under 15 minutes

Scenario: Every required async state has owned evidence
  Given the v1 feature catalog and coverage matrix
  When release evidence is validated
  Then each async surface has passing loading, empty, success, validation, auth, permission, capability, partial failure, rate limit, offline, reconnect, stale, cancel, retry, mobile, and upgrade scenarios or a reviewed not-applicable reason
  And every scenario identifies an owning feature and rollback

Scenario: Unverified runtime contracts cannot enter release scope
  Given an MDA, Fleet, protocol-v2, OAuth, or desktop capability cell lacks an accepted named spike
  When the release manifest is generated
  Then that cell is disabled or omitted with an explanatory fallback
  And fixture or prototype evidence cannot mark it supported
  And the classic responsive web baseline remains testable

Scenario: Security boundaries withstand cross-layer abuse
  Given authenticated hostile-input fixtures for tenant IDs, source URLs, headers, webhooks, ZIPs, untrusted tool content, sandbox paths/egress, push/deep links, and Tauri navigation/update packages
  When the release security suite runs
  Then unauthorized cross-tenant/source access and external side effects are zero
  And credentials/private content do not enter logs, traces, caches, notifications, deep links, or public evidence
  And tampered updates and replayed mutations are rejected

Scenario: Primary journeys are accessible on supported surfaces
  Given the supported browser, mobile, PWA, and shipped Tauri accessibility matrix
  When trained reviewers complete primary and recovery journeys using keyboard, screen reader, 400-percent reflow, forced colors, and reduced motion as applicable
  Then no critical task requires pointer precision, hover, color, animation, or desktop-only layout
  And findings are recorded and release-blocked according to policy

Scenario: A release can roll back without losing authoritative work
  Given a staged release with a compatible prior API, agent, web, database, service-worker, and desktop artifact set
  And an upstream run remains active
  When a rollback trigger is injected
  Then the affected capability is disabled and compatible artifacts are restored
  And Postgres application data, audit/idempotency, and the upstream run remain intact
  And reconnect hydrates current source state without duplicate events or accidental cancellation

Scenario: A clean contributor checkout proves package boundaries
  Given only the documented system prerequisites and a clean repository checkout
  When a contributor follows the quickstart and root fan-out commands
  Then apps/api and packages/agent sync, build, install, import, type-check, and test through their package-local locks
  And the TypeScript workspace formats, lints, type-checks, tests, and builds through pinned package-manager commands
  And the UI harness and local product demo complete with external/provider networking denied
  And no undocumented root Python environment or maintainer-only setup is required

Scenario: Wire and public-package drift cannot merge silently
  Given a reviewed FastAPI contract or TypeScript public-export change
  When CI regenerates the OpenAPI client and builds clean package consumers
  Then an uncommitted generated diff fails
  And documented exports import without repository-private paths
  And affected downstream packages and adapter conformance suites pass
  And no browser-safe schema contains a credential reference or provider secret

Scenario: Repository knowledge and architecture cannot drift silently
  Given an indexed canonical product spec, active ExecPlan, generated package graph, and allowed architecture manifest
  When a governed path changes, a generated file is hand-edited, and a browser package imports a provider SDK
  Then the docs check flags the stale owner and generated drift
  And the architecture check names the illegal edge, legal adapter boundary, architecture anchor, and local repair command
  And Human Review remains blocked

Scenario: Symphony development orchestration fails closed
  Given the reviewed low-risk pilot and a blocked agent-ready issue
  When Symphony reconciles the tracker and later restarts
  Then it never dispatches the blocked issue or creates a duplicate pull request or external effect
  And reusable tracker credentials are absent from the child environment and proof artifacts
  And the project can select manual one-agent-per-worktree dispatch without changing product behavior
```

---
feature_id: DW-OPS-002
title: Observability, trace links, notifications, and Insights
release: v1
status: proposed
decision_status: blocked-on-spikes
owners: [api, web, platform]
surfaces: [activity, agent-detail, task-detail, pwa, desktop]
runtime_scopes: [any]
source_refs: [SRC-LC, SRC-DW, SRC-FE]
dependencies: [DW-FND-003, DW-ONB-001, DW-OPS-001]
contract_gates: [SPIKE-TRACE-001, SPIKE-PWA-001, SPIKE-DESKTOP-001]
last_reviewed: 2026-07-23
---

# Observability, trace links, notifications, and Insights

## User outcome

A user can answer whether work is running, waiting, complete, or failed; open the authoritative trace when authorized; and receive one actionable, privacy-safe notification when attention is needed. Deep Work provides a slim operational layer and never implies that its summaries replace LangSmith observability.

## Evidence and confidence

| Claim | Evidence | Classification | Planning consequence |
|---|---|---|---|
| The prototype shows Observability charts, status, traces, notifications, and run panels with simulated data. | `SRC-FE`, including `FE-O03` and run-panel inventory | Direct interaction/code evidence, not data-contract proof | Fold summaries into Activity/task/agent detail; remove copied dashboard fiction. |
| The vision requires slim observability, trace links, notifications, and Insights-aware organizational learning. | `SRC-DW` | Product intent | Build application-owned events and links first, then capability-gated enhancements. |
| LangSmith traces and deep links can be authoritative where tracing is configured. | `SRC-LC` | Documented; link construction, auth, metadata, and availability need pinned fixtures | Show a link only from verified source evidence and allowlisted origin. |
| Insights and event/webhook access are uniform across account tiers and runtimes. | Internal assumption | Gated/unknown | Detect capability/tier; use application events and qualified fallback. |
| Every runtime can deliver a signed webhook to Deep Work. | Internal assumption | Unknown | Use verified event ingress where available and bounded per-source reconciliation/polling otherwise. |

The notification delivery provider, exact upstream event mechanism, trace-link format, Insights contract, and source reconciliation budget remain outputs of `SPIKE-TRACE-001`, `SPIKE-PWA-001`, and `SPIKE-DESKTOP-001`. This proposed plan cannot be marked ready until their fixtures and privacy review are accepted.

## Scope, ownership, and non-goals

This plan owns backend observability and notification contracts. The FastAPI/PostgreSQL application service owns normalized operational events, trace-link metadata, summary projection, notification intents, preference evaluation, deduplication, fan-out state, device/channel registrations, and audit. The TypeScript SDK exposes `/api/v1` query/mutation contracts. Next.js/PWA and Tauri consume those contracts; surface-specific permission prompts, service workers, native bridges, badges, and presentation belong to `DW-SURF-001`/`DW-SURF-002`, which consume this plan and are not dependencies of it.

In scope:

- task/agent/schedule trace deep links where the verified source reports trace identity and the actor is authorized;
- Activity summaries for application-observed run counts/outcomes, latency bands, approval wait, queue time, and recent failures with coverage/freshness labels;
- a versioned tracing metadata convention using pseudonymous application task, agent/source, actor/tenant, task type, surface, and release identifiers;
- capability-gated Insights configuration/deep links or explicitly qualified digest fallback;
- in-app notification inbox as the durable baseline, plus backend intents for needs-review, completion, failure, source credential failure, and schedule failure;
- channel/device preferences, event-level preferences, quiet hours, urgency exceptions, deduplication, revocation, delivery receipts, and deep-link resolution.

Non-goals are a trace waterfall, raw prompt/tool/log search, copied LangSmith charts, dataset/evaluation or billing dashboards, a guaranteed Insights API, storing trace bodies, embedding sensitive task content in notification payloads, or making push permission a prerequisite for task use.

## Primary journeys

### Diagnose work and open a trace

1. The user opens Activity, task detail, or agent detail and sees application summaries with coverage and freshness.
2. They select a failed/waiting run and see the application status, source/run identity, last event, and whether a trace was recorded.
3. If a verified authorized link exists, Deep Work opens the allowlisted source trace in a safe external context.
4. If tracing is disabled, local, permission-denied, gated, or stale, the UI states that condition and offers only verified recovery/deep-link alternatives.

### Configure and receive notifications

1. After the user experiences a meaningful event, Settings explains in-app and available device channels without blocking progress.
2. The user selects event types, channels, quiet hours/timezone, and urgent-review exceptions.
3. A normalized operational event creates at most one notification intent per recipient/event policy.
4. The service writes the durable inbox item, evaluates channels, sends minimal payloads through the configured provider, and records delivery outcome.
5. Opening the notification resolves the opaque application target under the current session and refreshes durable state before showing an action.

### Resolve a stale approval notification

1. A needs-review notification is delivered to two devices.
2. One device resolves the approval.
3. The other device opens the notification; the server authorizes and refreshes the task/interrupt.
4. The user sees the completed/stale decision and task continuation, never an enabled duplicate approval control.

## Operational event and notification taxonomy

Events are versioned and application-scoped: `task.needs_review`, `task.completed`, `task.failed`, `source.credential_failed`, `schedule.failed`, plus delivery/reconciliation events. Adding a new event requires an owner, sensitivity classification, dedupe identity, actor/audience rule, destination resolver, retention rule, and user preference default.

Notification payloads carry only an opaque notification ID, coarse event type, non-sensitive generic copy key, timestamp, urgency, and application deep-link token/route identifier. The client fetches authorized detail after session validation. No prompt, tool argument, decision payload, artifact name/content, source credential, trace URL, or organization-memory excerpt belongs in provider-visible payloads.

## Complete state matrix

| State | Required behavior |
|---|---|
| Summary loading | Keep Activity/task layout stable and show coverage sources separately. |
| No operational events | Explain what will appear; do not show zero charts as source truth. |
| Complete/current coverage | Show observation window, included sources, event count, and trace availability. |
| Partial source coverage | Qualify every aggregate, name unavailable/stale sources, and avoid organization-wide claims. |
| Source reconciliation error | Retain application events and prior source evidence as stale; retry independently. |
| Trace available/authorized | Show one allowlisted link with source and provenance. |
| Trace absent | State “No trace recorded” or “Not reported,” not a broken link. |
| Trace permission denied | Explain source authorization and keep application detail visible where allowed. |
| Trace stale/deleted upstream | Remove actionable link after revalidation and retain provenance/tombstone. |
| Insights available | Show only accepted configuration/deep-link/digest behavior and coverage. |
| Insights gated/unknown | Explain tier/capability and use qualified application-event digest; no inferred API call. |
| Notification inbox loading | Show count skeleton and keep task use unblocked. |
| Inbox empty | Explain event preferences and that external push is optional. |
| Preference save pending/error | Optimistic display must reconcile; retain prior durable preference on failure. |
| Push permission undecided | Offer contextual non-blocking education after demonstrated value. |
| Push permission denied | Keep in-app inbox, show OS/browser guidance, and stop repeated prompts. |
| Channel unsupported | Hide or explain based on device capability; in-app remains available. |
| Device registration stale/expired | Stop fan-out after provider response/reconciliation and request opt-in renewal. |
| Device revoked/logged out | Revoke subscription immediately and exclude from new intents. |
| Event duplicate/replayed | Resolve to one event, inbox item, and fan-out inside the idempotency policy. |
| Delivery queued/rate-limited | Keep durable inbox, retry with bounded backoff, and respect event expiry. |
| Delivery failed | Record provider-neutral reason; avoid repeated user-visible duplicates. |
| Quiet hours | Defer non-urgent channel delivery to calculated local end; inbox remains current. |
| Approval resolved before tap | Authorize/refetch and show stale/completed state, never an active decision. |
| Offline client | Read cached inbox without sensitive details; queue preference edits only under explicit conflict policy. |
| Reconnecting | Fetch since the last application notification cursor and dedupe by ID. |
| Permission/tenant changed | Withhold target detail and revoke invalid device/workspace subscription binding. |
| Mobile/desktop | Backend returns identical intent/state; consuming surface adapts presentation without changing policy. |

## Interfaces and state ownership

The proposed `/api/v1` contract covers operational summary queries, trace-link resolution, notification inbox pagination/read state, preferences, channel/device registration and revocation, and deep-link target resolution. Exact paths/providers remain API-review decisions. Query/mutation clients are separate from the React stream hook.

Required entities include versioned `OperationalEvent`, `TraceReference` with source/provenance/access state, `CoverageWindow`, `NotificationIntent`, per-recipient `InboxItem`, `DeliveryAttempt`, `ChannelRegistration`, and versioned `NotificationPreference`. Event ingestion uses an application idempotency key derived from source/event identity where verified, not provider payload text.

PostgreSQL owns events, summaries or their reproducible projection inputs, trace-reference metadata, inbox, preferences, device/channel metadata, dedupe keys, delivery attempts, and audit. A delivery provider owns transport only. Source runtime/LangSmith remains authoritative for traces and source run detail. Deep Work does not ingest trace bodies merely to draw a link or chart.

## Runtime capability and fallback rules

- Classic source events and trace references use only accepted pinned event/reconciliation and link fixtures.
- If verified signed event delivery exists, ingress validates it; otherwise the application reconciles source state through documented, bounded per-source queries. It never assumes a webhook or global run search.
- MDA inherits only capability-detected trace/event evidence and remains CLI/source-owned for deployment.
- Fleet trace/event behavior remains absent until `SPIKE-FLEET-001` proves read/invoke and associated provenance.
- Insights is capability/tier gated. Without it, summaries use application-owned events and explicitly supported source statistics; a digest states missing coverage.
- In-app inbox is always the notification fallback. External push/native delivery is optional and independently disableable.

## Persistence, security, and privacy

Ingress endpoints, where approved, enforce source-specific signatures or broker authentication, timestamp/replay windows, tenant/source binding, bounded payloads, idempotency, and rate limits. Poll/reconciliation credentials stay server-side. All upstream text is untrusted and redacted. Trace links are constructed/resolved server-side from allowlisted source metadata, contain no credentials, and are authorized at click time.

Notification fan-out applies tenant, workspace, actor, role, event sensitivity, channel, quiet-hours, and device-binding checks. Provider payloads are content-minimal. Device tokens are encrypted, revocable, never logged, and deleted on logout/revocation/expiry policy. Analytics records event class and delivery lifecycle with pseudonymous IDs, not prompt/task content. Retention separates operational events, inbox state, delivery attempts, and device tokens.

## Responsive and accessible behavior

Backend semantics are surface-independent. The web/PWA/Tauri consumers provide semantic counts, polite new-item announcements, keyboard-operable inbox/preferences, non-color status, timezone-aware quiet-hours copy, and accessible external-link warnings. Live updates never steal focus. Notifications remain available as an ordered inbox at 320 CSS px/200% zoom. Reduced motion suppresses animated badges/toasts. OS/browser permission prompts are triggered only by explicit user action in the owning surface plan.

## Metrics and guardrails

- 100% of trace-enabled, source-reported, authorized supported runs expose a verified link; all other runs show an explicit absence classification.
- Duplicate inbox item and external fan-out rate is zero for one recipient/event/deduplication window.
- 100% of provider-visible payload fixtures exclude prompts, tool/decision content, artifacts, credentials, and trace URLs.
- Delivery, open, and action rates are measured by event type/channel using pseudonymous identifiers.
- Median needs-review notification-to-decision time is tracked alongside stale-tap rate and false-notification rate.
- Guardrail: no aggregate is labelled workspace-wide when coverage is partial or stale.

## Dependencies and readiness gates

Depends only on backend/session foundations `DW-FND-003`, onboarding/session/tenant selection `DW-ONB-001`, and the event/activity taxonomy in `DW-OPS-001`. Surface plans consume this contract. Readiness requires the operational event schema, notification sensitivity matrix, channel-provider decision, device-token threat model, deep-link resolver contract, classic event/trace fixtures, polling budgets, and Insights capability proof.

## Rollout and rollback

1. Ship application operational events, trace-reference fixtures, and in-app inbox internally.
2. Enable classic trace links and per-source reconciliation for selected non-production sources.
3. Enable completion/failure notifications, then needs-review after stale-decision tests.
4. Add one external channel at a time through consuming surface flags; add Insights only after capability proof.
5. Expand source coverage independently, never coupling MDA/Fleet gates to classic availability.

Rollback disables affected ingress, reconciliation, event type, or delivery channel while preserving the in-app audit/inbox record and task functionality. Invalid trace links can be disabled centrally without deleting task provenance. Channel rollback revokes/ignores provider tokens according to policy and does not remove user preferences.

## Executable acceptance scenarios

1. **Trace provenance:** Given a trace-enabled classic fixture, when a run completes, then authorized task/activity views resolve one allowlisted trace link; an unauthorized actor receives no source URL.
2. **No trace:** Given local or tracing-disabled work, when detail loads, then it shows the correct absence classification and no release criterion falsely requires a link.
3. **Event fan-out:** Given completion, failure, needs-review, credential failure, and schedule failure events with preferences, when processed, then exactly the selected inbox/channel intents are created with content-minimal payloads.
4. **Replay:** Given the same authenticated source event arrives twice, when ingested, then one operational event, inbox item, and recipient/channel fan-out exists.
5. **Stale approval tap:** Given an approval resolved on another device, when the old notification opens, then current authorized state shows the completed decision and no submit control.
6. **Quiet hours:** Given a non-urgent event inside quiet hours and an urgent needs-review exception, when evaluated, then the first channel delivery defers, the second follows the explicit exception, and both inbox items exist.
7. **Revocation:** Given a registered device whose session/workspace access is revoked, when a new event occurs, then no provider delivery targets it and target detail remains inaccessible.
8. **Partial coverage:** Given one source timeout and no Insights entitlement, when summaries render, then application events remain, the unavailable source/time window is named, and no global-completeness claim appears.
9. **Offline/reconnect:** Given cached inbox state and missed events, when the client reconnects from its application cursor, then items converge without duplicates and current read state is preserved under version rules.
10. **Sensitive payload:** Given prompts, tool arguments, artifact names, tokens, and trace URLs in an upstream event fixture, when notification intents are created, then none appear in provider payloads, logs, or analytics.

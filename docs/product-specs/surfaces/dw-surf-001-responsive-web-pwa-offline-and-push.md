---
feature_id: DW-SURF-001
title: Responsive web, PWA, offline behavior, and push
release: v1
status: canonical-spec
decision_status: blocked-on-spikes
implementation_readiness: not-ready
owners: [web, api, product]
surfaces: [web, pwa, mobile]
runtime_scopes: [any]
source_refs: [SRC-FE, SRC-DW, SRC-LC, SRC-LCJS]
evidence_pins:
  frontend: 26c698b
  langchain_docs: 7b9215d
  canonical_plan: 06f0515
  langchainjs: ee76ea0
dependencies: [DW-FND-002, DW-FND-003, DW-FND-004, DW-FND-005]
contract_gates: [SPIKE-AUTH-001, SPIKE-STREAM-001, SPIKE-PWA-001]
last_reviewed: 2026-07-23
---

# Responsive web, PWA, offline behavior, and push

## User outcome

A user can dispatch, watch, steer, approve, inspect artifacts/diffs, and follow the defined landing flow from a phone or desktop browser. Installing the PWA adds convenient launch and push—not a different product contract. Offline and background states remain honest: work can continue server-side, cached content is clearly stale and read-only, and no sensitive mutation is queued or replayed without current authorization.

This plan is proposed and blocked on authentication and streaming spikes plus `SPIKE-PWA-001`. It is not implementation-ready until supported browser/OS versions, service-worker caching rules, Web Push behavior, background/foreground recovery, and notification payload policy pass against real devices.

## Evidence and confidence

| Evidence | Classification | Confidence | Planning consequence |
|---|---|---:|---|
| The prototype at `26c698b` contains desktop-oriented shell, composer, run panels, approvals, files, browser, diff, and settings concepts, but limited proven responsive behavior. | Prototype interaction evidence | High | Inventory and adapt every action; do not treat desktop rendering as mobile coverage. |
| The vision requires a complete phone loop and PWA/push experience. | Product requirement at `06f0515` | High | Mobile completion is a v1 release criterion, not a future responsive polish task. |
| LangSmith runs are server-side; closing a stream is not equivalent to cancelling a run. | Documented/audited contract | High | Backgrounding disconnects client resources only and rejoins via `SPIKE-STREAM-001`. |
| Protocol v2, legacy streams, and run join use different resume contracts. | Documented, with beta/live verification needed | High | PWA foreground recovery uses the application stream while the FastAPI source adapter selects the verified upstream mechanism; the service worker invents no stream protocol. |
| Browser install, service worker, push, notification permission, background delivery, and iOS home-screen behavior vary by platform/version. | External platform behavior | High that variance exists; current matrix unverified | Require the browser/device matrix in `SPIKE-PWA-001` and progressive fallback to in-app notifications. |
| Application-owned push subscriptions and notification preferences require durable state. | Product/security requirement | High | FastAPI/Postgres own subscriptions; push payloads contain minimal opaque references. |

## Scope, ownership, and non-goals

### In scope

- Responsive Next.js 16/React 19 App Router application from 320 CSS pixels through large desktop, using the shared design system, pure `packages/domain` contracts, and browser-safe `packages/sdk` application client.
- Installable PWA manifest, icons, display mode, launch/deep-link routing, controlled service worker, install education, and version/update UX.
- Phone bottom navigation, contextual rail/filter sheets, touch-safe composer, one-tap approval path, progressive task/run detail, file/diff/artifact views, and phone landing flow.
- Cached application shell plus a deliberately bounded, non-sensitive last-known task-summary/read state.
- Explicit offline cold/warm behavior, freshness timestamps, read-only gating, reconnect, auth refresh, and source revalidation.
- Background stream release and foreground rejoin through `DW-FND-004`; active upstream runs continue unless explicitly cancelled.
- Web Push subscription lifecycle through FastAPI `/api/v1`, application notification preferences from `DW-OPS-002`, minimal payloads, deep-link authorization, and in-app fallback.
- Browser voice input only where capability and explicit permission exist, with editable transcription before submission.
- Service-worker update, incompatible client/API version, and unsent local draft protection.

### Ownership

- Web owns responsive Next.js routes, install UX, service worker, browser permission UX, local draft boundary, foreground/background lifecycle, and device qualification. Server components handle safe shell/bootstrap work; task streams and browser capabilities remain focused client islands.
- FastAPI owns `/api/v1/push-subscriptions`, authenticated notification preference reads/mutations, opaque deep-link resolution, session/source revalidation, and application notification events.
- Postgres owns actor/device subscription, delivery preference, failure/expiry metadata, and bounded notification state.
- `DW-OPS-002` owns notification event definitions, in-app inbox, delivery preference semantics, and activity linkage. This surface consumes that contract; operations must not depend back on this plan.
- `DW-FND-004` owns the client application-stream contract and hydration semantics; FastAPI source adapters own upstream cursor/recovery semantics. The service worker cannot reinterpret either protocol.
- `DW-CODE-003` and task/HITL plans own domain actions shown in the phone journey.

### Non-goals

- Native iOS/Android (planned for v2), background agent execution in the browser, or running LangChain/deepagents in the service worker.
- Offline dispatch, approval, edit, steering, cancel, retry, deployment, PR merge, or any queued sensitive mutation in v1.
- Caching credentials, raw provider responses, tool output, repository files, artifacts, diffs, approval arguments, traces, or private/no-store API responses.
- Guaranteeing push before install/platform requirements are met, treating notification delivery as authoritative task state, or hiding in-app fallback.
- A separate mobile API or domain model; mobile uses the same FastAPI `/api/v1` and TypeScript SDK.
- A v1 `apps/mobile` package. The responsive PWA is the supported phone client until the evidence gate in `DW-FUT-202` justifies native work.

## Primary journeys

### Install after value

1. A user completes a useful action or returns, and the app detects install eligibility without interrupting first paint.
2. It offers a contextual install explanation appropriate to browser/platform; unsupported paths show no false install button.
3. The installed PWA launches to an authorized route through the same session and shell contract.
4. A service-worker update preserves unsent composer text and asks for controlled refresh when necessary.

### Phone dispatch, watch, steer, approve, and land

1. The user opens Tasks through bottom navigation and composes with touch/keyboard/optional reviewed voice input.
2. They dispatch through the same idempotent mutation service as desktop.
3. Progressive run detail shows status, messages, approvals, files/diffs, and expandable tool/subagent detail without a wide eight-tab layout.
4. The user steers or queues only when the active source advertises that capability.
5. A current approval opens in a mobile one-action path, preserves the full ordered batch, and requires review/edit where configured.
6. The user reviews a diff/artifact and follows the GitHub PR/CI/merge phone flow defined by coding plans.

### Background and foreground recovery

1. The PWA moves to background while a source run remains active.
2. The client releases/pauses network and rendering resources without sending cancel.
3. A minimal notification may arrive for an actionable application event.
4. On foreground or deep-link open, the app revalidates session, workspace, source, task, and permission.
5. It rejoins through the application stream; the server adapter resumes the verified upstream contract or performs authoritative hydration, and the client renders each durable event once.

### Offline read and recovery

1. A warm PWA loses connectivity and shows only allowed cached shell/summary state with observed timestamp.
2. Every external mutation becomes disabled with an offline explanation; local unsent composer text remains an editable draft, not an intent queue.
3. On reconnect, the app refreshes session/source/capability and current entity versions before enabling mutations.
4. Draft submission is always a new explicit user action after reconnection.

## Complete state matrix

| State | Required behavior | Recovery or transition |
|---|---|---|
| First web load / loading | Server-render or skeleton stable shell without unauthorized content; establish client/API compatibility. | Resolve session/onboarding/demo/error. |
| Empty/no source | Shell remains usable with source-onboarding action; no guessed demo data. | Connect source or explicitly enter demo. |
| Install not supported | No broken install action; ordinary responsive web remains complete. | Continue in browser. |
| Install eligible | Contextual, dismissible prompt only after user value; explain effect. | Install or defer without losing work. |
| iOS not home-screen installed | Explain current push/install limitation and exact supported path after qualification. | Install or use in-app notifications. |
| PWA first launch | Authorize launch route, hydrate shell, and display installed-mode affordance only where useful. | Sign in/onboard or open target. |
| Notification permission prompt eligible | Ask only after user opts into a clear notification purpose. | Allow, deny, or defer. |
| Push denied/revoked | Record preference safely; do not reprompt abusively. | In-app notifications remain complete; settings can retry. |
| Push subscription loading | Disable duplicate subscribe and show bounded progress. | Success or typed browser/service error. |
| Push service/provider failure | Preserve in-app event and retry policy; do not imply notification was delivered. | Retry/backoff or disable invalid subscription. |
| Stale notification | Treat payload as a hint only. | Authorize and load current durable task state. |
| Offline cold start | Show cached shell only if safe plus explicit connectivity/sign-in limitation. | Retry online; no credential validity claim. |
| Offline warm start | Show bounded last-known content with observed timestamp and read-only banner. | Reconnect; never auto-send mutation. |
| Offline with unsent composer text | Preserve local draft in allowed storage/memory and label unsent. | User reviews and explicitly submits online. |
| Mutation attempted offline | Prevent before network and explain why. | Retry explicitly after online revalidation. |
| Reconnecting | Preserve reading position/focus; show bounded progress. | Resume verified cursor or full hydrate. |
| Resume cursor expired/gap | Send only the opaque application cursor; the service adapter selects verified upstream recovery or full hydration and the domain reducer suppresses duplicates. | Render recovered current state/freshness. |
| Session expired on foreground | Clear protected in-memory state and block task reveal/mutation. | Reauthenticate then authorize target. |
| Permission revoked on foreground | Do not reveal cached protected detail. | Show access error, source/workspace switch. |
| Source partial failure | Healthy-source/task content remains; source-scoped warning. | Retry source independently. |
| Capability unavailable | Hide/disable action with explanation; never simulate in live mode. | Connect capable source or use supported path. |
| App backgrounded during active run | Disconnect/pause client only; run remains server-side. | Foreground rejoin. |
| Service-worker update waiting | Show release/version and controlled-refresh prompt; keep draft/current task. | Refresh at safe point. |
| Client/API incompatible | Block unsafe mutation and request refresh/update. | Activate compatible service worker/client. |
| Storage quota/eviction | Continue online without offline cache; explain reduced offline availability only when relevant. | Clear safe cache/rebuild. |
| Mobile keyboard open | Composer/decision controls stay visible above safe area; content can scroll. | Close keyboard without losing draft/focus. |
| Orientation/viewport changes | Preserve route, scroll anchor, focused logical control, and draft. | Reflow between rail/sheet/tab forms. |

## Proposed interfaces

```ts
interface OfflineSnapshot<T> {
  schemaVersion: string;
  actorScopeHash: string;
  observedAt: string;
  expiresAt: string;
  data: T; // explicitly cache-approved projection only
}

interface PushSubscriptionRegistration {
  endpoint: string;
  keys: { p256dh: string; auth: string };
  deviceLabel?: string;
  client: { surface: "pwa"; userAgentFamily: string; appVersion: string };
}

interface NotificationHint {
  notificationId: string;
  targetType: "task" | "approval" | "agent" | "schedule";
  opaqueTargetId: string;
  category: string;
  occurredAt: string;
}
```

Proposed service boundaries:

- The Next.js client consumes normal query/mutation/stream services from `packages/sdk`; responsive routes do not call raw LangSmith APIs.
- TanStack Query owns ordinary server cache/invalidation; the pure `packages/domain` task reducer owns ordered stream projection; URL state owns shareable navigation; bounded local UI state owns drafts and ephemeral presentation. No global store duplicates all four.
- Next.js route handlers are limited to web-specific auth/download/transport concerns and forward to `/api/v1`; they do not create a second provider adapter, credential store, or persistence model.
- `POST /api/v1/push-subscriptions`, `DELETE /api/v1/push-subscriptions/{id}`, and preference operations bind subscriptions to the current actor/device after CSRF/session checks.
- Push payloads contain a minimal `NotificationHint`; `GET /api/v1/notifications/{id}/resolve` authorizes and resolves a current application route.
- Service-worker cache policy is an explicit allowlist keyed by schema/app version. API responses are not cacheable merely because a `GET` succeeded.
- Local composer draft persistence is a UI contract distinct from offline mutation; it contains user-entered draft only under accepted retention/encryption policy and never a credential or provider response.

## Runtime capability and fallback

- Classic LangSmith Deployment is the public source baseline. Phone actions are present only for capabilities verified on the selected source.
- `SPIKE-STREAM-001` determines protocol-v2 `since`, legacy `Last-Event-ID`, run-join, or full-hydration recovery inside the FastAPI source adapter. The PWA stores only a short-lived opaque application cursor and never constructs or persists a generic upstream cursor.
- MDA/Fleet remain capability-gated by their owning plans; this surface shows explanatory unavailable states and does not call private-beta/custom routes.
- If push is unsupported, denied, revoked, throttled, or unavailable, the in-app notification inbox from `DW-OPS-002` is the complete fallback.
- If PWA install is unsupported, responsive web remains feature-complete. If voice input is unsupported/denied, normal text input remains complete.
- If offline cache is unavailable or evicted, online behavior remains complete and cold-offline shows a safe explanation.
- Native mobile is v2; no v1 feature may rely on native-only background execution or notification APIs.

## Persistence and security

- FastAPI/Postgres store push subscription identity, actor/device binding, delivery preference, failure/expiry, and notification application state. Endpoint/key fields receive secret-level handling and redaction.
- The service worker caches only immutable public assets, shell assets, and explicitly approved bounded projections. It excludes credentials, session endpoints, private/no-store responses, artifacts/files/diffs, tool outputs, approvals, and raw event streams.
- Offline snapshots are partitioned by actor scope, schema version, and expiry; sign-out, workspace change, permission loss, or account deletion purges protected caches and drafts.
- Push text is minimal and lock-screen safe by default; sensitive content requires an explicit preference after privacy review. Opaque IDs reveal no source/thread/repository identity.
- Every notification/deep link reauthorizes on open and loads current state; payload actions do not approve, cancel, merge, or mutate directly.
- Voice capture stays within the browser capability; transcription is visible/editable before dispatch and follows prompt-retention policy.
- Service worker, manifest, and dependency code follow CSP/integrity/update controls; no dynamic untrusted script is cached or executed.

## Responsive and accessible behavior

- The complete release loop is tested at 320, 375, 768, and desktop reference widths with text zoom, safe areas, portrait/landscape, and virtual keyboard.
- Bottom navigation has semantic labels and current state; sheets trap/restore focus; every desktop rail/tab action has a mobile equivalent.
- Touch targets, spacing, drag alternatives, file/diff navigation, and approval controls meet the accepted WCAG 2.2 AA target and do not rely on precision gestures.
- Offline, stale, reconnect, push denied, install, and update states use headings, concise status text, timestamp, and keyboard-reachable recovery.
- Streaming updates are batched for assistive technology; new tokens do not steal focus or constantly announce. “Jump to latest” is explicit.
- Reduced motion disables install/update/reconnect animation; browser zoom is never disabled.
- Virtualized lists retain reading order, row labels, focus restoration, and access to offscreen content.

## Metrics and guardrails

- Complete phone release journey success rate on every supported browser/OS cell.
- PWA install eligibility and successful launch measured after value, not prompt impressions alone.
- Push opt-in, delivery provider result, open, stale-target, and invalid-subscription rates without task content.
- Foreground resume with duplicate rendered events: zero in qualification tests.
- Sensitive API response or artifact found in Cache Storage/push payload: zero.
- Offline mutation network attempts and automatic replayed sensitive mutations: zero.
- p75 local interaction latency and long-list/thread memory/scroll budgets inherited from `DW-QUAL-001`.
- Guardrails: no first-paint install prompt, no permission prompt without user intent, no notification as authority, no client-unsubscribe-as-cancel, and no platform-specific dead end without in-app fallback.

## Dependencies, external contract gates, rollout, and rollback

### Dependencies and gates

- `DW-FND-002` for shell, responsive navigation, demo disclosure, and accessible state patterns.
- `DW-FND-003` for session, `/api/v1`, Postgres push persistence, notification/deep-link authorization, and cache purge events.
- `DW-FND-004` and `DW-FND-005` for source capability, reconnect/hydration, stable identity, freshness, and status.
- `DW-OPS-002` is the upstream owner of notification categories, in-app inbox, preference semantics, and event eligibility. Dependency is one-way from this surface to Operations.
- `SPIKE-AUTH-001` must verify browser/PWA session renewal and deep-link return behavior.
- `SPIKE-STREAM-001` must verify background disconnect, foreground resume, cursor expiry, and full hydration.
- `SPIKE-PWA-001` must record exact iOS Safari/home-screen, Android Chrome, desktop Chrome/Edge/Safari/Firefox support cells for install, push, permission, service-worker update, storage eviction, background/foreground, and deep links. Unsupported cells retain fallbacks.

### Proposed rollout

1. Accept device/browser matrix, cache data classification, notification privacy, and mobile information architecture.
2. Ship responsive web routes and phone journeys in fixture mode with service worker disabled.
3. Add install manifest/shell cache behind a flag; prove update/draft/cache-purge behavior.
4. Integrate offline snapshots and foreground recovery against classic test sources after stream/auth spikes.
5. Add in-app notifications first, then opt-in Web Push per qualified platform.
6. Qualify the complete phone journey on real supported devices before v1 acceptance.

### Rollback

- Disable install prompt, push registration, offline snapshot, or service worker independently with server/client flags.
- A bad service worker activates a kill-switch/version path that stops interception, purges only safe versioned caches, and reloads the last compatible client without deleting unsent drafts until exported/confirmed.
- Push rollback preserves in-app notifications and preferences; it invalidates unsafe subscriptions without losing task state.
- Responsive web remains the supported fallback for every PWA capability.

## Executable acceptance scenarios

```gherkin
Scenario: The complete phone loop uses the shared product contract
  Given a clean authorized account on a supported 375-pixel browser
  And a classic source advertises the required capabilities
  When the user dispatches, watches, steers, answers an ordered approval batch, reviews a diff, and follows the PR landing flow
  Then each action uses the same FastAPI /api/v1 and TypeScript SDK service as desktop
  And every control remains touch, keyboard, and screen-reader accessible
  And no desktop-only tab or hover action blocks completion

Scenario: Backgrounding does not cancel a run
  Given an active source run and connected task stream
  When the PWA is backgrounded long enough to release its connection
  Then no cancel mutation is sent
  And the run continues at the source
  When the PWA returns to foreground
  Then it reauthorizes through /api/v1 and resumes or hydrates through the server-owned source adapter
  And every durable event renders once

Scenario: Offline mode cannot replay sensitive intent
  Given a warm PWA has an allowed task summary and unsent composer draft
  When connectivity is lost and the user attempts dispatch, approval, cancel, and merge
  Then each external mutation is prevented before a network call
  And the summary is labelled with its observed time
  And the draft remains editable but is not queued
  When connectivity returns
  Then the user must explicitly review and submit after current authorization/state loads

Scenario: A stale push reveals no protected state
  Given a minimal opaque approval notification was delivered before access was revoked
  When the user taps it from the lock screen
  Then the app reauthenticates and reauthorizes the target
  And protected approval content is not displayed
  And the user sees the current safe access state

Scenario: A service-worker update preserves work
  Given a new compatible client is waiting and the composer contains unsent text
  When the update prompt appears
  Then the user can defer refresh
  And accepting refresh preserves or deliberately exports/restores the draft under policy
  And no stale client sends an incompatible mutation

Scenario: Push unsupported has a complete fallback
  Given SPIKE-PWA-001 marks push unsupported for a browser cell
  When an approval needs attention
  Then no unsupported permission prompt appears
  And the in-app notification inbox receives the event
  And the user can complete the approval without push
```

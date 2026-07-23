---
feature_id: DW-FUT-202
title: Native mobile applications
release: v2
status: canonical-deferred-brief
decision_status: discovery-gated
owners: [mobile, sdk, api]
surfaces: [ios, android]
runtime_scopes: [any]
source_refs: [SRC-DW, SRC-LCJS, SRC-EXPO]
evidence_pins:
  canonical_plan: 06f0515
  langchainjs: ee76ea0
dependencies: [DW-SURF-001, DW-FND-004, DW-FND-005]
last_reviewed: 2026-07-23
---

# Native mobile applications

> This v2 brief is discovery-gated. Expo/React Native is the current hypothesis, not a locked implementation choice. Native work begins only if measured PWA gaps justify a separate client and the transport, security, release, and accessibility gates close.

## User outcome

iOS and Android users can monitor tasks, make time-sensitive decisions, steer work, and share inputs safely when PWA notification, backgrounding, sharing, or device-integration limits materially impair the experience.

## Evidence and confidence

- `SRC-DW` identifies phone approval/landing flows and native mobile as future direction. Confidence: medium for need, low for a separate app before PWA evidence exists.
- Shared FastAPI contracts, generated TypeScript SDK, identities, and design tokens make a native client plausible. Confidence: medium; stream/background and artifact behavior require prototypes.
- Expo/React Native may optimize team reuse, but App Store policies, native modules, secure storage, push, and accessibility must be evaluated against alternatives. Confidence: low until spike.

## Scope, ownership, and non-goals

Mobile owns native navigation, lifecycle, push, deep links, share sheet, secure local storage, device accessibility, and releases. `packages/domain` owns transport-neutral identities and task-state reduction. A future client-core extraction may own generated application schemas, DTO mapping, and transport-neutral service contracts only after native proof; the v1 browser SDK is not assumed reusable as a whole. FastAPI owns device/session registration, upstream source recovery, push intent, revocation, and idempotency.

In scope for the first native release:

- Session/workspace/source selection, inbox, task detail, stream/status, steering, approvals, artifacts, secure deep links, push, share-sheet task draft, and biometric app unlock.
- Offline read cache with explicit freshness; consequential mutations require confirmed connectivity initially.
- Native UI built from shared tokens and domain semantics, not reused DOM components.

Non-goals:

- Full agent configuration, desktop coding workspace, terminal, complex diff review, or background autonomous execution on the device.
- App-only backend contracts or feature parity where mobile cannot present an action safely.
- Funding native solely for branding when the PWA meets measured outcomes.

## Primary journeys

1. **Push to decision:** a locked-screen notification identifies source/task safely; tap opens biometric/session gate, refreshes the exact interrupt, and presents ordered decisions.
2. **Monitor and steer:** a user follows status/stream summaries, backgrounds the app, returns, reconciles state, and sends one idempotent steering message.
3. **Share into task:** text, URL, image, or supported file enters a local draft; the user reviews workspace/source, attachments, and privacy before dispatch.
4. **Inspect artifact:** the app checks authorization and viewer support, previews safely or offers a secure handoff/download.
5. **Revoke device:** sign-out/admin revocation removes tokens, cached sensitive content, and future push delivery while preserving server audit.

## Complete state matrix

| State/condition | Expected experience |
| --- | --- |
| Loading | Native skeletons preserve selected workspace/task identity; push-open shows verification progress before any decision controls. |
| Empty | Inbox and approvals explain filters/workspace/source and offer refresh or create/share action. |
| Active | Stream/status updates are resumable or state-refetched; backgrounding never implies the task stopped. |
| Error | Distinguish session, source, stream, push, upload, and viewer errors; retain last confirmed state and correlation ID. |
| Offline | Show cached read-only data with timestamp; allow local composer draft, but no approval, cancellation, steering, or dispatch queue initially. |
| Permission denied | Remove inaccessible cached content, avoid existence leaks, and explain account/workspace remediation. |
| Reconnecting/foreground | Refresh session, task, interrupt/version, and stream position before enabling consequential actions. |
| Stale push/deep link | Navigate to current task state and explain that the approval/action changed; never replay the old payload. |
| Uploading | Show per-item progress, cancel/retry, background constraints, and server-confirmed completion. |
| Revoked session/device | Clear secure tokens and protected cache, unregister push where verifiable, and return to sign-in. |
| Compact/mobile | This is the primary surface: one next action, bottom-safe controls, dynamic type, orientation support, and no desktop-only hover dependency. |
| Tablet/foldable | Use adaptive split view only when focus order, resizing, and multiwindow state remain correct. |

## Proposed interfaces (non-binding)

Reuse the versioned FastAPI boundary, pure `packages/domain`, and browser/native-safe portions of `packages/sdk`. Illustrative mobile-owned concepts are `DeviceRegistration`, `PushIntent`, `SecureDeepLink`, `LocalDraft`, and `CacheEnvelope`. A push contains opaque intent/identity references and minimal safe preview—not task content, credentials, or an approval decision payload. Expo receives a native UI/navigation and platform-adapter layer; it does not reuse DOM components, wrap the web app, or fork the backend.

Transport choice for live streams, background recovery, push provider, secure storage, and native framework remain subject to spikes. Mutations carry idempotency and expected interrupt/task version. Deep links resolve server-side authorization and current state before navigation.

## Runtime capability and fallback

- Source capability manifests control approval, steering, artifact, cancellation, and resume actions exactly as web does.
- Where background streaming is unreliable, suspend transport and refetch/resume on foreground; push indicates a change, not authoritative task state.
- Unsupported artifacts open a secure web/desktop handoff or download under policy.
- If native value is not proven, continue the responsive PWA and evaluate a narrow notification wrapper rather than a full client.

## Persistence and security

Store short-lived session material only in platform secure storage; bind push/device records to actor, tenant, installation, and revocation state. Local cache is encrypted/protected as platform capabilities permit, minimal, TTL-bound, workspace-scoped, and wiped on revocation. Share inputs remain local drafts until explicit dispatch.

Use universal/app links with verified domains, one-time or short-lived intent resolution, screenshot/notification privacy controls, certificate/platform network defaults, jailbreak/root risk policy, and no secrets in push/logs/analytics. Biometric unlock protects local access but does not replace server authorization.

## Responsive and accessible behavior

Meet platform VoiceOver/TalkBack, dynamic type/font scaling, contrast, reduce motion, switch/keyboard access, focus restoration, touch target, orientation, and safe-area requirements. Ordered HITL decisions remain complete and labelled. Charts/diffs/artifacts require accessible alternatives or explicit handoff. Navigation preserves task and scroll context across background/rotation.

## Metrics and guardrails

- PWA-to-native baseline: push delivery/open-to-current-state, approval completion, background recovery, share completion, crash-free sessions, and task-monitor success.
- Duplicate mutation, stale-approval attempt, lost local draft, token/cache retention after revocation, and unauthorized deep-link rate; security targets zero.
- Accessibility completion rates with screen reader and dynamic type.
- Guardrails: no decision directly from notification payload, no offline consequential mutation in first release, and no native-only product capability.

## Dependencies

- `DW-SURF-001` supplies responsive/PWA baseline, offline policy, push semantics, and evidence used to justify native.
- `DW-FND-004` supplies generated SDK, stream model, and fixture/live parity.
- `DW-FND-005` supplies source-qualified identity and the pure domain reducer shared without DOM dependencies.
- `DW-HITL-001`, `DW-TASK-003`, and `DW-TASK-004` transitively supply ordered approval, stream, steering, and lifecycle semantics.

## Rollout and rollback

1. Measure PWA gaps and interview mobile-heavy users; no client build before a funding threshold.
2. Prototype push/deep-link, stream recovery, secure storage, share sheet, and accessibility on real iOS/Android devices.
3. Internal distribution against fixture and test sources.
4. Small opt-in beta with read/approval/monitor scope and remote feature flags.
5. Store release after security/privacy/accessibility and operational acceptance.

Rollback disables risky intents/actions server-side, stops new registrations, and directs users to the PWA while preserving local draft export where safe. Store rollback and minimum-supported-version policy must be defined before launch.

## Executable acceptance scenarios

1. Given a locked device receives an approval push, when tapped, then biometric/session and current-interrupt checks occur before the ordered decision UI appears.
2. Given the app backgrounds during a stream, when foregrounded, then state resumes/refetches without duplicate events or false “stopped” status.
3. Given the device is offline, when a user shares a file, then a local draft persists with clear offline state and cannot dispatch until reviewed online.
4. Given an old approval link, when current task state has changed, then no stale decision is submitted and the user sees the current outcome.
5. Given an administrator revokes a device, when it next opens or receives push, then server access fails, protected cache clears, and no sensitive preview appears.
6. Given VoiceOver/TalkBack and large text, when a user completes a mobile approval, then all requests, decision choices, edits, warnings, and submit result are understandable and operable.

## Explicit discovery gates

- **Value:** define and meet a measured PWA-gap/frequency threshold that justifies native cost.
- **Framework:** compare current Expo/React Native capabilities with alternatives for stream, push, secure storage, share, artifact viewers, updates, and accessibility.
- **Lifecycle:** prove foreground/background/reconnect semantics and idempotent mutation on representative devices/networks.
- **Security/privacy:** approve device registration, token/cache, deep-link, biometric, notification preview, analytics, and revocation threat model.
- **Distribution:** establish signing, CI, beta, store review, privacy disclosures, crash monitoring, phased release, and forced-update policy.
- **Accessibility/product:** test complete approval/monitor/share journeys with assistive technology and mobile users.

Native remains a non-ready option until the value gate and every technical/release gate close; PWA is the default mobile surface meanwhile.

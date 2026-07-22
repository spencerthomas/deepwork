# F19 · Notifications & push

*Deep Work feature spec · 2026-07-22 · Status: draft · Milestone: M4 (webhook route earlier if M2 needs it) · Depth: implementation-ready*

Sources: [02 · Architecture](../02-architecture.md) (§7 notifications, §5 identity, §10 untrusted boundaries) · [03 · UI spec](../03-ui-spec.md) (§3.6 settings, §6 platform adaptations, §3.3 approvals) · [04 · Roadmap](../04-roadmap.md) (M4, v1 criteria 2/5) · [research 05 · Cross-platform arch](../../research/05-crossplatform-arch.md) · [research 20 · MDA API surface](../../research/20-gapfill-mda-api.md) · platform webhook contract verified 2026-07-22 against [Use webhooks](https://docs.langchain.com/langsmith/use-webhooks) and the [Agent Server API](https://docs.langchain.com/langsmith/agent-server-api).

Stack facts: frontend is Next.js (D-022); the push fan-out service is the Python FastAPI `apps/server` (P-005, provisional — where [02](../02-architecture.md) §1/§11 say "Next.js server routes", P-005 supersedes). D-003 says Deep Work runs **no database of its own** — §3 and §9-Q1 confront what that means for push subscriptions.

## 1. Scope

### In scope

- The **one notification pipeline** ([02 §7](../02-architecture.md)): run-create carries a `webhook` param → `apps/server` ingress + fan-out route → Web Push/VAPID (PWA/web), an SSE event feed consumed by the Tauri desktop for native notifications, Expo Push post-v1.
- Event taxonomy derived from what the platform webhook actually delivers (one POST at run completion; §3), incl. needs-review/interrupt and schedule-fired classification.
- Webhook ingress security (per-source shared-secret tokens — the platform's documented mechanism), idempotency/dedupe, ordering posture.
- Device registration + per-device / per-event-type preferences API and the Settings UI section ([03 §3.6](../03-ui-spec.md): "notifications (Web Push opt-in per device)").
- Notification content rules (no sensitive payload in push bodies), deep-link targets, iOS PWA constraint surfaced in onboarding.
- Delivery semantics v1 (broadcast-to-owner's-devices), expired-subscription cleanup (404/410), storm control for hourly schedules × N agents.
- The seam to in-app unread state (F08) — what a push does and does not imply.

### Out of scope

- PWA mechanics: manifest, service-worker install/lifecycle, offline shell, `notificationclick` handler code — [F20 · PWA & mobile](./20-pwa-and-mobile.md). F19 defines the push message contract F20's service worker consumes.
- Tauri mechanics: tray badge, notification plugin usage, `deepwork://` deep-link registration, focus/route handling — [F21 · Desktop (Tauri)](./21-desktop-tauri.md). F19 defines the SSE feed + event shape F21 consumes.
- `apps/server` skeleton, hosting, auth middleware, shared route plumbing — [F28 · Backend glue service](./28-backend-glue-service.md). F19 owns the notification routes' behavior; F28 owns the service they live in.
- Approvals inbox UX and the one-tap approve screen itself ([03 §3.3](../03-ui-spec.md); catalog neighbors) — F19 only delivers the user to them.
- Inbox unread semantics (F08, see [catalog](./README.md)); Slack/Linear channels as notification destinations (post-v1, [04](../04-roadmap.md) backlog); LangSmith Engine/Context-Hub/prompt webhooks (different platform systems, not run webhooks).

## 2. Dependencies & seams

| Direction | Spec | What crosses the seam |
|---|---|---|
| needs ← | [F28 · backend glue](./28-backend-glue-service.md) | FastAPI app, deploy target with a **public HTTPS URL** (F01 §9-Q4 flags that none is chosen), session auth for device routes, secret management (VAPID keypair, per-source webhook tokens) |
| needs ← | packages/sdk spec ([catalog](./README.md)) | Run creation goes through `packages/sdk`; it must attach `webhook` + Deep Work run `metadata` (title/origin/actor per [02 §10](../02-architecture.md)) on every run and cron it creates |
| provides → | [F20 · PWA](./20-pwa-and-mobile.md) | Push message JSON contract (§4), VAPID public-key route, device registration API, iOS ≥16.4 onboarding requirement |
| provides → | [F21 · Tauri](./21-desktop-tauri.md) | `GET /notify/stream` SSE feed + event shape (§4); deep-link URL map (web URL ↔ `deepwork://`) |
| provides → | approvals surface ([03 §3.3](../03-ui-spec.md), catalog) | needs-review push deep-links into the one-tap approve screen — the flagship mobile flow, v1 release criterion 2 ([04](../04-roadmap.md)) |
| provides → | F08 · task inbox ([catalog](./README.md)) | Normalized notification events a client may use to set unread markers; F19 does **not** own unread state |
| depends on | P-005 (provisional) | If glue reverts to Next.js routes, §3/§4 port 1:1 (routes are framework-agnostic); the SQLite store (§3) moves with them |
| depends on | D-003 + §9-Q1 | Push requires *some* server-side persistence; this spec proposes the narrowest exception |

## 3. Design

### 3.1 The pipeline (one path for every surface)

```
run-create (packages/sdk adds webhook=…)          Deep Work apps/server (P-005)
  Agent Server ──POST at run completion──▶  /webhooks/runs/{source_id}?t=SECRET
                                                 │ verify token (constant-time)
                                                 │ parse minimal fields, DROP values/kwargs
                                                 │ classify → event · dedupe · rate-gate
                                                 ├─▶ Web Push (VAPID) ─▶ PWA / desktop browsers
                                                 ├─▶ SSE /notify/stream ─▶ Tauri native notifications
                                                 └─▶ Expo Push (post-v1)
```

- **Attachment point.** Every run-creating endpoint accepts `webhook` — verified list: `POST /threads/{id}/runs`, `/runs/stream`, `/runs/wait`, `/threads/{id}/runs/crons`, `POST /runs/crons`, stateless `/runs/stream|wait` ([Use webhooks](https://docs.langchain.com/langsmith/use-webhooks); confirmed available on MDA deployments, [research 20](../../research/20-gapfill-mda-api.md)). `packages/sdk` sets it on every run **and every cron it creates**, so schedule-fired runs flow through the same pipeline. Whether `useStream`'s protocol-v2 command envelope passes `webhook` through is unverified (§9-Q3); fallback: create the run via the SDK client (`runs.create` with `webhook`) and join its stream — resumable joins make this equivalent ([02 §7](../02-architecture.md)).
- **Why the URL carries `{source_id}`.** The webhook payload contains `run_id/thread_id/assistant_id` but **no deployment URL**; with a multi-deployment agent-source registry ([03 §3.6](../03-ui-spec.md)) the receiving route must know which source fired. The per-source path segment + per-source secret solves identification and auth in one move.
- **One POST per run, at completion.** The platform sends a single POST when a run finishes; there is no "run started/progress" webhook. Notification for "schedule fired" therefore means "a scheduled run *finished* (or needs review)" — stated honestly in the taxonomy below.

### 3.2 Event taxonomy (derived from delivered statuses)

Run terminal statuses: `success · error · timeout · interrupted` (enum verified against Agent Server API; `pending/running` never produce webhooks).

| Event | Derivation | Notify by default |
|---|---|---|
| `task.completed` | webhook `status == "success"` | yes |
| `task.failed` | `status == "error"` (payload `error: {error, message}`) or `status == "timeout"` (reason=timeout) | yes |
| `task.needs_review` | `status == "interrupted"` **and** interrupt marker present in payload (checked, then discarded — §6). Webhook delivery for interrupted runs is plausible ("at the completion of a run") but **undocumented** — verified by spike task 1; fallback in §5 | yes, `Urgency: high` |
| `schedule.run_finished` | any of the above where run `metadata` carries the Deep Work cron stamp (`deepwork.origin="schedule"`, `deepwork.schedule_id`) — set by us at cron creation; MDA-side `metadata.owner` stamping corroborates ([research 20](../../research/20-gapfill-mda-api.md)) | success: collapsed digest; failed/needs-review: yes |

Not events: run started (no webhook exists), steering/queue activity (in-band via streams), user-initiated cancel (lands as `interrupted` without a HITL marker → suppressed).

### 3.3 Subscription & device storage — the D-003 problem, stated honestly

Web Push is server-initiated: at send time no client is running, so the subscription (`endpoint`, `p256dh`, `auth`), the device's event-type prefs (filtering happens at fan-out), and a short dedupe log **must persist server-side**. D-003 ("no Deep Work database") cannot be satisfied literally. Options:

| Option | Verdict |
|---|---|
| **A. Embedded single-file store (SQLite) owned by `apps/server`** | **Recommended.** No external DB service, zero ops for self-hosters beyond one volume; scope of the D-003 exception is three tables (§4), all rebuildable (worst case: users re-enable notifications) |
| B. External KV/Postgres | Rejected for v1 — first real infrastructure dependency, contradicts the "thin glue" stance ([02 §1](../02-architecture.md)) |
| C. Stash subscriptions in the deployment's Store API | Keeps D-003 literally true (state lives in the user's org), but breaks on multi-source registries (which deployment is canonical?), MDA store access fails closed outside the identity namespace ([research 20](../../research/20-gapfill-mda-api.md)), and couples notification infra to agent runtime health. Rejected |
| D. Client-side only | Impossible for push by definition |

This is a real decision, not a detail — flagged as **§9-Q1** with recommendation A. Everything else in this spec works under any of A–C.

### 3.4 Delivery semantics (v1)

- **Broadcast, filtered.** Every event fans out to **all devices registered by the owning actor** (matched via run `metadata` actor/owner stamps, [02 §5/§10](../02-architecture.md)), filtered by each device's per-event-type prefs. No routing rules ("only the device that started the task") in v1 — cross-device handoff is a product principle ([02 §7](../02-architecture.md) resumability) and routing adds state for marginal benefit. Revisit post-v1.
- **Per-surface transport.** Web/PWA: Web Push with VAPID (RFC 8292), payload encrypted (RFC 8291), ≤ ~4 KB. Desktop: the Tauri webview has no push service; the running app subscribes to `GET /notify/stream` (SSE, `Last-Event-ID` replay window) and raises native notifications (F21). A closed desktop app receives nothing — acceptable v1, documented. Mobile native: Expo Push post-v1 ([research 05](../../research/05-crossplatform-arch.md)); the fan-out gains one more sender, contracts unchanged.
- **Collapse & ordering.** Web Push `tag` = `thread_id` with `renotify` — newer events on a thread replace older ones on the lock screen, which makes cross-run ordering largely moot for UX. The SSE feed orders by `webhook_sent_at`. The pipeline treats webhooks as **at-least-once, unordered** (no delivery/retry guarantees are documented — §9-Q4): dedupe key `(run_id, status)` within a 24 h window; late/duplicate arrivals are dropped silently.
- **Cleanup.** Push-service responses `404`/`410 Gone` delete the subscription immediately (Web Push standard); repeated `5xx`/timeouts mark the device stale after N=5 consecutive failures and prune after 30 days. Client-side `pushsubscriptionchange` re-registers (F20).
- **Storm control.** Hourly schedules × N agents is the design load. Two gates: (1) `schedule.run_finished` successes within a 5-minute window per actor collapse into one digest push ("3 scheduled runs finished"); (2) a per-actor token bucket (default 20 pushes/5 min) — overflow converts to a single summary push, never silent drop of `task.needs_review` (needs-review bypasses the digest, not the bucket). `TTL: 3600`, `Urgency: high` only for needs-review. Defaults configurable via server env.

### 3.5 Content, deep links, preferences UI

- **Content rule: nothing sensitive in a push body.** Bodies use only the Deep Work-stamped `metadata` task title + event phrase ("needs your review", "completed", "failed") — never message content, tool args, file paths, or `values`. A per-device **"generic notifications"** toggle drops even the title ("A task needs your review") for lock-screen-shy users. Push payloads are E2E-encrypted in transit, but Apple/Google/Mozilla push services are treated as untrusted infrastructure anyway.
- **Deep links.** `task.completed/failed` → task detail; `task.needs_review` → approvals one-tap screen ([03 §3.3](../03-ui-spec.md): "push notification → one-tap approve screen. This is the flagship mobile flow"); `schedule.run_finished` digest → schedules/activity list. Push carries the canonical web URL; F20's service worker opens/focuses it; F21 maps it to `deepwork://` ([03 §6](../03-ui-spec.md)). No action buttons performing the approval *from* the notification in v1 — approve must happen in an authenticated client, not a service-worker context (§6).
- **Settings** ([03 §3.6](../03-ui-spec.md)): notifications section shows *this device* opt-in (permission prompt only on explicit toggle — never on load), the registered-device list with per-device event-type toggles (completed / failed / needs review / schedules) + generic-mode + remove, and a "send test notification" button. **iOS PWA constraint surfaced in onboarding**: Web Push on iOS requires ≥16.4 **and** home-screen install ([research 05](../../research/05-crossplatform-arch.md), [03 §6](../03-ui-spec.md)) — the onboarding + settings screens detect iOS Safari-tab context and nudge "Add to Home Screen" before offering the toggle (UX owned by F20).
- **In-app unread seam.** A push does **not** authoritatively set unread state: with no Deep Work DB there is no server-side read model, and thread truth comes from `threads.search` on open. Notification events (push or SSE) may *optimistically* mark a thread unread on the receiving device; F08 owns unread semantics and reconciliation. The inbox, not the notification log, is the source of truth — missed notifications must never mean missed work (§5).

## 4. Contracts

**Ingress route** (owned here; hosted per F28):

```
POST /webhooks/runs/{source_id}?t=<per-source secret>   → 204 (always fast; processing async)
  401 unknown source_id or bad token · 204 on duplicates (idempotent)
```

Consumed payload fields (verified platform shape): `run_id`, `thread_id`, `assistant_id`, `status`, `run_started_at`, `run_ended_at`, `webhook_sent_at`, `metadata`, `error {error, message} | null`. `values` is inspected **only** for an interrupt/HITL marker on `status=interrupted`, then discarded with `kwargs` — never persisted or logged (§6).

**Normalized event** (SSE feed + internal fan-out; snake_case wire per [02 §7](../02-architecture.md)):

```json
{"event_id": "…", "type": "task.completed|task.failed|task.needs_review|schedule.run_finished",
 "source_id": "…", "thread_id": "…", "run_id": "…", "assistant_id": "…",
 "title": "<metadata title or null>", "reason": "error|timeout|null",
 "schedule_id": "…|null", "ts": "<webhook_sent_at>"}
```

**Push message JSON** (encrypted body; F20's service worker renders): `{type, url, title, body, tag: thread_id, ts}` — `url` is the deep-link target; ≤4 KB total.

**Device API** (session-authenticated via F28; actor identity from the signed-in session):

| Route | Behavior |
|---|---|
| `GET /notify/vapid` | `{public_key}` — VAPID keypair generated at server setup, private key env/secret-mounted, `sub` claim = operator `mailto:` config |
| `POST /notify/devices` | `{platform: "webpush"|"tauri"|"expo", subscription?: {endpoint, keys:{p256dh, auth}}, name?, prefs: {completed, failed, needs_review, schedule}, generic: bool}` → `{device_id}`; re-POST of same endpoint upserts |
| `PATCH /notify/devices/{id}` | update prefs / rotate subscription |
| `DELETE /notify/devices/{id}` | unregister (also the "remove device" Settings action) |
| `GET /notify/devices` | list for Settings |
| `GET /notify/stream` | SSE, per-actor event feed, `Last-Event-ID` replay of a bounded window (default 24 h) — desktop consumer |
| `POST /notify/test` | sends a test push to the calling device |

**Storage (Option A, §9-Q1)** — SQLite file, three tables: `devices` (id, actor, tenant?, platform, subscription-or-null, prefs, generic, created/last_ok/fail_count), `event_dedupe` (run_id, status, seen_at; 24 h TTL), `event_log` (normalized events for SSE replay; 24 h TTL). All contents rebuildable; no run content, no messages, no secrets beyond subscription keys.

**Webhook URL + secrets.** Per agent source: `https://<server>/webhooks/runs/{source_id}?t=<32-byte random>`, minted when a source is added to the registry, rotatable from Settings. Where the deployment's `langgraph.json` is author-controlled (classic tier), additionally set `webhooks.headers` `Authorization: Bearer ${{ env.LG_WEBHOOK_TOKEN }}` and `webhooks.url {allowed_domains: [<server host>], require_https: true}` (supported since `langgraph-api ≥0.5.36`, verified) — defense in depth; MDA pass-through unknown (§9-Q5).

## 5. Edge cases & failure modes

- **Webhook never arrives on `interrupted`** (if §9-Q2 resolves negative): needs-review pushes degrade to (a) open clients detecting interrupts in-stream (already spec'd, [03 §3.3](../03-ui-spec.md)) and (b) interrupt-count surfacing on next app open via `threads.search` — mobile one-tap loses its trigger, so escalate to LangChain (beta relationship, [04](../04-roadmap.md) risk register) rather than building a poller into the "no-DB" server.
- **Server down / unreachable when the webhook fires**: no documented platform retry (§9-Q4) → the notification is lost. Accepted: notifications are best-effort; the inbox reconciles truth on open (§3.5). Never build critical workflow on push delivery.
- **Self-hosted server without public HTTPS**: Agent Server cannot reach the route. Settings shows per-source webhook health (last received timestamp); docs cover tunnels for `langgraph dev` (a cloud deployment can never POST to `localhost`; local dev against local server works fine, mind `disable_loopback`).
- **User cancels a run**: cancel lands as `interrupted` (cancel action is literally called `interrupt`) — the missing HITL marker suppresses a bogus "needs review" push (§3.2). If marker detection proves unreliable, suppression falls back to "recently-cancelled run_ids" remembered from the cancel API call issued by our own client.
- **Enqueue double-texting**: N queued runs on one thread → N completion webhooks → collapsed by `tag: thread_id`; the dedupe key is per-run so none are wrongly dropped.
- **410/404 from push service**: immediate subscription delete; if the device row was the actor's last, Settings shows notifications as off for that device on next visit (no phantom "enabled" state).
- **iOS**: PWA uninstalled from home screen silently kills the subscription → cleanup path above handles it. EU iOS ≥17.4 web-push availability is disputed in sources ([research 05](../../research/05-crossplatform-arch.md) open question) — do not market EU iOS push until verified (§9-Q7).
- **Duplicate device registrations** (same browser re-registering): upsert on `endpoint` uniqueness, not a new row.
- **Clock skew / late webhooks**: events older than the dedupe window are dropped; `webhook_sent_at` (platform-stamped) is used for ordering, never local receive time.
- **Storm beyond the token bucket** (e.g., misconfigured 5-min schedule across 20 agents): summary push + a Settings banner suggesting muting the schedule event type; per-schedule mute is post-v1.

## 6. Security & privacy

- **Ingress auth**: per-source random ≥32-byte token compared constant-time (mirrors MDA's own ingress-secret discipline, [research 20](../../research/20-gapfill-mda-api.md)); the query-param token is the platform's documented mechanism, upgraded with `webhooks.headers` bearer where the tier allows (§4). Unknown `source_id` and bad tokens are indistinguishable 401s. Rate-limit the public route; body size cap; reject non-JSON fast.
- **Payload minimization**: `values`/`kwargs` contain full conversation state and inputs — parsed transiently for the interrupt marker only, never persisted, never logged (structured logs carry ids + status only). This satisfies the spirit of "Deep Work stores essentially nothing" even inside the D-003 exception.
- **Untrusted content boundary**: everything from the webhook — including `metadata` titles, which travel through the untrusted run pipeline — is rendered as plain text in notifications and in any UI (no markdown/HTML), consistent with v1 release criterion 5 and [02 §10](../02-architecture.md).
- **No approve-from-notification in v1**: approval decisions require the authenticated app context; a notification action button executing `respond()` from a service worker would need long-lived credentials in SW scope — rejected. One-tap = one tap *after* deep-linking into the signed-in PWA.
- **Tenant/actor isolation fail-closed**: events whose metadata matches no registered actor are dropped, never broadcast; device routes derive actor from the server-verified session (F28), so one tenant's devices can never subscribe to another's events — mirroring MDA's fail-closed store scoping ([02 §5](../02-architecture.md)).
- **Secrets**: VAPID private key and per-source tokens live in `apps/server` secret config, never in client bundles or the repo (F01 §6 posture); subscription keys at rest are as sensitive as session tokens — the SQLite file gets `0600`/volume-level protection and is excluded from backups by default.
- **Push-service exposure**: bodies already minimized (§3.5); `generic` mode exists precisely for regulated environments.

## 7. Acceptance criteria

1. A run created from the web app with an attached webhook produces exactly one push on a registered device when the run succeeds, with title = stamped task title, body free of message content, and a deep link that opens that task's detail.
2. Replaying the identical webhook POST (same `run_id` + `status`) produces no second notification; the route answers 204 both times.
3. A POST with a wrong or missing token, or an unknown `source_id`, gets 401 and no processing; timing is constant with respect to token validity.
4. Interrupt spike (task 1) has a written verdict: webhook observed (or not) for `status=interrupted` and for cron-created runs on `langgraph dev` **and** one hosted deployment; taxonomy table updated accordingly.
5. `status=error` and `status=timeout` runs both notify as `task.failed`, with reason distinguishable in the SSE event.
6. A cron created through Deep Work carries the schedule stamp; three schedule successes within 5 minutes yield one digest push, while a schedule failure pushes individually.
7. A device with `needs_review: off` receives no interrupt pushes but still receives completions; the `generic` toggle strips titles end-to-end.
8. A `410 Gone` from the push service removes the subscription; Settings reflects it and re-enabling works without a duplicate row.
9. Tauri (F21 integration test): with the app running and zero Web Push subscriptions, an event arrives over `/notify/stream` within seconds and replays correctly after a disconnect via `Last-Event-ID`.
10. On iOS Safari (non-installed), Settings/onboarding shows the home-screen-install nudge instead of a broken permission prompt; after install on ≥16.4, opt-in succeeds.
11. Kill `apps/server`, complete a run, restart: no push (documented best-effort), but the task shows correctly in the inbox on next open — no stuck state.
12. grep of server logs after a full test pass finds no `values`, `kwargs`, message content, or subscription keys.

## 8. Task breakdown

| # | Task | Depends on | Definition of done |
|---|---|---|---|
| 1 | **Spike: webhook behavior** — against `langgraph dev` + one hosted deployment: does the POST fire for `interrupted`? for cron-created runs? does `useStream`/protocol-v2 pass `webhook` through? capture golden payloads incl. an interrupt marker sample | F28 skeleton | AC-4; §9-Q2/Q3 answered; payloads committed as test fixtures |
| 2 | Ratify §9-Q1 (storage exception) with a decision-log entry | — | D-/P- ID recorded; option A/B/C chosen |
| 3 | Ingress route `/webhooks/runs/{source_id}`: token verify, minimal parse + discard, classifier, dedupe table | 1, 2 | AC-2, AC-3, AC-5, AC-12 |
| 4 | Device registry + prefs API + VAPID key mgmt (`/notify/*` routes, SQLite per §4) | 2, F28 auth | Routes pass integration tests; upsert-on-endpoint verified |
| 5 | Web Push sender: encryption, `tag`/`renotify`, TTL/Urgency, 404/410 cleanup, failure counters | 3, 4 | AC-1, AC-8 |
| 6 | Storm control: schedule digest window + per-actor token bucket | 5 | AC-6; needs-review bypass verified |
| 7 | `packages/sdk`: attach `webhook` + metadata stamps (title, origin, schedule_id, actor) on every run/cron create; per-source secret minting in the source registry | 1 | Every SDK-created run observed carrying webhook + stamps |
| 8 | SSE feed `/notify/stream` with `Last-Event-ID` replay + `event_log` TTL | 3 | AC-9 (jointly with F21) |
| 9 | Settings UI: device list, per-event toggles, generic mode, test push, webhook-health per source | 4, 5 | AC-7; test button round-trips |
| 10 | Onboarding/iOS gating: installed-PWA detection, ≥16.4 nudge (UX with F20) | 9 | AC-10 |
| 11 | Deep-link contract doc + `notificationclick` target map handed to F20/F21 | 5, 8 | AC-1 deep link; F21 `deepwork://` mapping reviewed |
| 12 | Hardening pass: rate limits, body caps, constant-time compare test, log audit, restart drill | 3–9 | AC-3, AC-11, AC-12 |

Sequencing note: tasks 1–3 are milestone-independent and small — pull them into M2 if approvals dogfooding wants needs-review pushes early (per this spec's milestone header); 4–12 land in M4 with F20/F21.

## 9. Open questions

1. **[DECISION NEEDED — flagged] Where do push subscriptions live?** D-003 says no Deep Work database, but Web Push subscriptions, per-device prefs, and the dedupe window must persist server-side (§3.3). **Recommendation: adopt Option A — an embedded SQLite file owned by `apps/server`, scoped to exactly the three tables in §4, all rebuildable — and record it as an explicit, narrow amendment to D-003.** Needs a decision-log entry before task 3.
2. Does the run webhook fire when a run ends `interrupted` (HITL) — and does the payload expose a reliable interrupt marker (e.g. in `values`)? Docs say only "at the completion of a run" with `success`/`error` examples. The flagship mobile approval flow depends on this (task 1 spike; escalate via the beta contact if negative).
3. Can `useStream` / the protocol-v2 command envelope (`run.start`) carry the `webhook` param, or must `packages/sdk` fall back to classic run-create + resumable join? ([02 §7](../02-architecture.md) asserts the param exists on run-create; the v2 envelope is unverified.)
4. What are the platform's webhook **retry/timeout semantics** on non-2xx or unreachable destinations? Nothing is documented; the design assumes none (best-effort). If retries exist, dedupe already absorbs them.
5. Does MDA's generated `langgraph.json` pass through a `webhooks` config block (`headers`, `url` restrictions), and do `define_schedule`-reconciled crons accept a `webhook`/`metadata` attachment that survives `mda deploy`'s delete-and-recreate reconciliation ([research 20](../../research/20-gapfill-mda-api.md))? If not, in-project schedules bypass the pipeline unless recreated through Deep Work's schedules UI — a real coverage gap to document or fix upstream.
6. Which actor/owner key in webhook `metadata` is authoritative for device matching across tiers (MDA `metadata.owner` vs Deep Work's own stamps on classic/`langgraph dev` where no identity preset runs)? Affects multi-tenant correctness; solo mode is unaffected.
7. EU iOS ≥17.4 web-push availability (conflicting sources, [research 05](../../research/05-crossplatform-arch.md)) — verify before claiming EU mobile push support.
8. Should `schedule.run_finished` *successes* default to on-with-digest (this spec) or off entirely? Hourly org-analyst schedules ([04](../04-roadmap.md) M3) could still be noisy for large orgs.

## 10. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| No webhook on `interrupted` (§9-Q2) | High — mobile one-tap approve loses its trigger (v1 criterion 2) | Task-1 spike runs early (M2-adjacent); degraded path spec'd (§5); beta-channel escalation |
| D-003 exception rejected / relitigated late | Med — pipeline blocked at task 3 | §9-Q1 is a named blocking decision with a concrete minimal proposal |
| `apps/server` has no public HTTPS home (F01 §9-Q4 unresolved) | High — webhooks physically undeliverable | Surface as a shared blocker with [F28](./28-backend-glue-service.md); webhook-health indicator makes misconfiguration visible, not silent |
| Best-effort delivery misread by users as reliability | Med — "the app didn't tell me" | Inbox-is-truth principle (§3.5), docs framing, AC-11 restart drill |
| Schedule storms erode trust in notifications | Med | Digest + token bucket (§3.4) with env-tunable defaults; §9-Q8 revisits the default |
| Push-service payload exposure in regulated orgs | Low-Med | Minimal bodies + `generic` mode (§3.5); nothing sensitive ever leaves the server (§6) |
| P-005 reversal to Next.js routes | Low — routes port; SQLite file moves | Contracts kept framework-agnostic (§4); no FastAPI-specific behavior in the spec |
| Platform webhook contract drift (beta-era `langgraph-api`) | Med | Golden payload fixtures from task 1 become contract tests in the F01 CI contract slot |

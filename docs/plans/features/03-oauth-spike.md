# U3 · M0 Spike 1 — OAuth probe

*Feature deep-dive · 2026-07-23 · Milestone M0 · Status: planning*
*Parent: [../2026-07-22-001-feat-deepwork-v1-delivery-plan.md](../2026-07-22-001-feat-deepwork-v1-delivery-plan.md) · Spec: [../../plan/02-architecture.md](../../plan/02-architecture.md) §5 (identity & auth), [../../plan/04-roadmap.md](../../plan/04-roadmap.md) M0 Spike 1*

---

## Objective

Resolve the single riskiest auth unknown: **does "Sign in with LangSmith" (OAuth 2.1) actually cover the surfaces Deep Work needs**, or must v1 rely on API-key paste? Output is a written decision memo that gates U8 (server routes + sign-in).

This spike touches only the **operator ↔ LangSmith plane** (arch §5, plane 1). The other two planes (end-user↔deployment, agent↔third-party) are settled by MDA identity presets and LangSmith Agent Auth respectively and are not part of this probe.

## Why this is risky

- Deep Work would be the **first OSS "Sign in with LangSmith"** — no precedent to copy. The `langsmith` CLI and MCP clients use the same OAuth surface, but their token scopes may not extend to what a full client needs.
- The danger is a **partial** result: an OAuth token that works against the control plane (`api.smith.langchain.com`) but is rejected by the data plane (`*.langgraph.app` deployment URLs), or vice versa. That would leave a half-built OAuth flow that can't actually drive the product.
- Getting this wrong late means rebuilding sign-in after M1 — expensive.

## Decision taken

### D1 — Planned posture: OAuth-first (target UX), key-proxy first (build order)

- **Build order:** the API-key **key-proxy** path is built first and ships **unconditionally** (`langgraph-nextjs-api-passthrough` pattern). It always works (PAT for personal; `lsv2_sk_` service key + `X-Tenant-Id` for teams) and unblocks the M1 dogfood regardless of OAuth outcome.
- **Presented default at v1:** if this spike is green, "Continue with LangSmith" OAuth is the primary, headline sign-in (it's what makes the "<15 min to first PR" release criterion feel effortless); key paste is the fallback shown for self-hosters and CI.
- **If the spike is red or partial:** key-first ships as the v1 default; OAuth is layered in post-launch (or for the control-plane-only surfaces it does cover).

This threads both concerns: de-risk by building the guaranteed path first, deliver the best UX by presenting OAuth-first when it's proven.

## Probe methodology

1. **Discovery (RFC 8414).** `GET https://smith.langchain.com/.well-known/oauth-authorization-server`. Record: `authorization_endpoint`, `token_endpoint`, `registration_endpoint`, `scopes_supported`, `grant_types_supported`, `code_challenge_methods_supported` (expect PKCE `S256`), device-flow support (`device_authorization_endpoint`, RFC 8628).
2. **Dynamic Client Registration.** POST to `registration_endpoint` to register a **public** client (no secret; PKCE). Confirm DCR is open (no manual client provisioning needed) — critical for an OSS app users self-deploy.
3. **PKCE authorization-code flow (web).** Drive the full code→token exchange against a test LangSmith account. Capture the resulting access token + refresh token + granted scopes.
4. **Device flow (RFC 8628, desktop).** Verify the device-authorization grant works (needed for Tauri sign-in, U18). Record polling cadence + expiry.
5. **Bearer acceptance matrix — the crux.** Take the OAuth access token and test acceptance on each surface:
   - **Control plane:** `GET api.smith.langchain.com/v2/deployments` (deployments/agents/crons CRUD).
   - **Data plane:** `POST` a stream/command against a `*.langgraph.app` deployment URL (the actual run surface).
   - **Deployment (MDA):** the standard Agent Server API at a deployment URL with an identity preset.
6. **Refresh + expiry.** Confirm refresh-token rotation works and token TTL is workable for long-lived sessions (with silent refresh).

## Decision matrix

| Outcome | Meaning | Consequence for U8 |
|---|---|---|
| **Green** — token accepted on all three surfaces | Full OAuth viable | OAuth-first default; key = fallback. Build full PKCE + device flow in U8. |
| **Partial** — control plane only (data plane rejects) | OAuth signs you in and manages the fleet, but runs go through the key-proxy | Hybrid: OAuth for control-plane/session identity, key-proxy for data-plane streaming. Document the seam. |
| **Red** — DCR closed, scopes absent, or broad rejection | OAuth not usable for OSS v1 | Key-first ships as v1 default; OAuth deferred post-launch. Sign-in hides the OAuth button. |

Any partial/red result also feeds the open question in the roadmap ("OAuth `scopes_supported` reality") and may become an upstream ask to the LangChain team.

## Artifacts

- `docs/spikes/2026-07-23-spike-oauth.md` — the memo: discovery dump, scope list, bearer-acceptance matrix table, refresh behavior, and a **binary recommendation** (green/partial/red → chosen U8 path).
- A throwaway probe script (curl/httpie or a tiny Node script) attached or linked — reproducible so the result can be re-checked when SDKs bump.

## Exit criteria

- The bearer-acceptance matrix is filled in for all three surfaces with real responses (not assumptions).
- The memo states one of {green, partial, red} and the exact U8 build path that follows.
- Device-flow feasibility is recorded (gates U18 desktop sign-in).

## Test scenarios

- **Validation:** a token obtained via the probed PKCE flow returns 2xx from all three surfaces (green case).
- **Validation:** if any surface returns 401/403, the memo records the surface, the status, and the response body, and proposes the fallback (partial/red).
- **Validation:** the device-flow grant completes end-to-end (or is documented as unsupported).
- **Edge case:** an expired access token silently refreshes; a revoked refresh token forces re-auth cleanly.

## Downstream units gated

- **U8** (server routes + sign-in) — the whole shape of that unit depends on this outcome.
- **U18** (Tauri desktop) — device-flow sign-in depends on RFC 8628 support found here.
- Informs **U7** (`packages/sdk`) — whether the control-plane client authenticates via bearer, key-proxy, or both.

## Dependencies

- **Upstream:** U1 (workspace to hold the probe script + spike doc). Requires a LangSmith test account (user has beta access).
- **Downstream:** U8, U18, U7.

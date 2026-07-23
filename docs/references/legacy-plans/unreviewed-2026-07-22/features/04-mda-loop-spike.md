# U4 · M0 Spike 2 — MDA loop

*Feature deep-dive · 2026-07-23 · Milestone M0 · Status: planning*
*Parent: [../2026-07-22-001-feat-deepwork-v1-delivery-plan.md](../2026-07-22-001-feat-deepwork-v1-delivery-plan.md) · Spec: [../../plan/02-architecture.md](../../plan/02-architecture.md) §2, §6, [../../plan/04-roadmap.md](../../plan/04-roadmap.md) M0 Spike 2*

---

## Objective

Prove the **Managed Deep Agents (MDA) loop works end-to-end from our own code**, not just via the `mda` CLI — because `packages/sdk` must reimplement the deploy flow as control-plane API calls, and `apps/web` must drive runs via `useStream` against a deployment URL. Output is a memo that gates U6 (`packages/agent`) and U7 (`packages/sdk` agent-source + deploy path).

## Why this is risky

- MDA is in **private beta** (US LangSmith Cloud). The user has beta access, but two things are unverified:
  1. Whether the **thread/run invocation API** behaves as documented from an external `useStream` client (vs the CLI's blessed path).
  2. Whether `deployment_type: managed_deep_agent` is **accepted for non-beta orgs** — this affects *users* of Deep Work, not just us. If it's gated, the deploy wizard must fall back to classic `langgraph.json` deployment of the same agent.
- The deploy flow (`mda deploy` → signed-URL tarball upload → revision polling) must be reproduced as raw API calls (`POST /v2/deployments`, 200 MB tarball cap). If that API path isn't usable outside the CLI, the fleet-manager "create/update agent" feature (U15) loses its primary mechanism.

## Probe methodology

1. **CLI baseline.** `mda init` a minimal deepagents project (one tool, no sandbox); `mda dev` locally; `mda deploy` to the beta org. Confirm the happy path works and capture what the CLI does over the wire (proxy/log the control-plane calls).
2. **External `useStream` against the deployment.** From a tiny TS client (not the CLI), open `useStream` against the deployment URL and dispatch a run. Verify: run reaches the agent, content blocks stream back, thread state persists. Test with **identity presets** — `trusted_backend` (forward `X-MDA-Ingress-Secret` + `X-MDA-Actor-Id`/`X-MDA-Tenant-Id`) and, if feasible, `validated_token`.
3. **Deploy-from-our-code.** Reproduce the deploy without the CLI: `POST /v2/deployments` → obtain signed upload URL → upload the project tarball (respect 200 MB cap) → poll revision status to healthy. This is the exact flow U15's "create/update the Deep Work agent" needs.
4. **Non-beta acceptance probe.** Determine (via docs, the LangChain relationship, or a test org if available) whether `deployment_type: managed_deep_agent` is accepted for a standard org. If unverifiable, treat as "assume gated" and validate the classic fallback (step 5).
5. **Classic fallback validation.** Deploy the *same runtime-agnostic agent* via `langgraph.json` (github/tarball source) to a classic LangSmith Deployment. Confirm feature-equivalence for v1 scope (streaming, threads, crons, HITL) — this is the degrade path in the risk register.

## Decision matrix

| Outcome | Consequence for U6/U7/U15 |
|---|---|
| **MDA fully usable from our code** (invoke + deploy API) | Primary path = MDA. `AgentSource` defaults to MDA deployment; U15 deploy wizard uses `/v2/deployments` directly. |
| **MDA invoke works, deploy API CLI-only** | Runs go through MDA; deploy in U15 shells to `mda`/uses github-source CD instead of raw tarball upload. Documented seam. |
| **MDA gated for non-beta orgs** | Deploy wizard **detects and falls back** to classic `langgraph.json` deployment for users' own orgs; we still develop against MDA with our beta access. MDA-specific bits (identity presets, managed sandboxes) degrade to documented classic patterns. |
| **MDA unusable even for us** (unlikely — we have beta) | Ship v1 entirely on classic Deployment + `langgraph dev`; MDA is a post-v1 upgrade. |

The `AgentSource` abstraction (U7) is the seam that makes all of these survivable without touching UI code.

## Artifacts

- `docs/spikes/2026-07-23-spike-mda-loop.md` — memo with: the captured deploy-flow API sequence, the `useStream`-against-deployment result, identity-preset findings, the non-beta acceptance verdict, and the classic-fallback confirmation.
- `packages/agent/spike/` — the throwaway minimal agent used (kept until U6 supersedes it; not shipped).
- A recorded control-plane call trace (from step 1) — reference material for U7's control-plane client.

## Exit criteria

- A run dispatched from external `useStream` (not the CLI) against an MDA deployment streams content blocks back.
- A tarball deploy via `POST /v2/deployments` from hand-written code reaches a healthy revision — **or** the memo documents that this is CLI-only and picks the U15 fallback.
- The non-beta gating question has a recorded verdict (even if "assume gated, fallback validated").
- Classic `langgraph.json` deploy of the same agent is confirmed feature-equivalent for v1 scope.

## Test scenarios

- **Validation:** minimal agent deployed via MDA responds to an external `useStream` run with streamed content blocks.
- **Validation:** tarball upload to the signed URL succeeds and revision polling reaches healthy.
- **Validation:** `trusted_backend` identity headers correctly scope thread/memory to the actor/tenant (`metadata.owner`, namespaced store).
- **Edge case:** a tarball over the 200 MB cap is rejected with a clear error (informs U15 packaging).
- **Edge case:** the same agent deploys and runs on classic `langgraph dev` with no code changes (proves runtime-agnostic design rule).

## Downstream units gated

- **U6** (`packages/agent`) — confirms the deployment target (MDA vs classic) and identity preset the agent is authored against.
- **U7** (`packages/sdk`) — the `AgentSource` registry types and control-plane deploy client are shaped by what this proves.
- **U15** (Fleet manager) — the "create/update agent" deploy flow depends on whether the tarball API is usable from our code.

## Dependencies

- **Upstream:** U1 (workspace); LangSmith beta account with MDA access (user has it).
- **Downstream:** U6, U7, U15. Coupled with U5 (stream contract) — both probe the same deployment; run them together to reuse the minimal agent.

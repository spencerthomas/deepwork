# Research digest

Condensed findings that ground the [v1 plan](../plan/). All research was performed on **2026-07-21** against live sources (official docs, package registries, repo source files) with confirmed/inferred labeling. Each file keeps key facts, open questions, and sources; full long-form reports exist outside the repo and can be shared on request.

## Ecosystem & runtime

| File | Topic |
|---|---|
| [01](01-managed-deep-agents.md) | Managed Deep Agents beta, LangSmith Deployment, Agent Server API |
| [02](02-deepagents-harness.md) | The deepagents harness (py 0.6.12 / js 1.11.1): middleware, backends, subagents, HITL, streaming |
| [06](06-execution-sandboxes.md) | Execution: LangSmith Sandboxes, auth proxy, GitHub App pattern, MCP |
| [20](20-gapfill-mda-api.md) | MDA control-plane surface (`/v1/deepagents/*`, `/v2/deployments`), identity internals, connector routes |
| [23](23-gapfill-runtime-tiers.md) | Licensing map (MIT vs Elastic-2.0), self-host reality, pure-OSS fallback path |
| [12](12-lifecycle-auth-followup.md) | LangSmith OAuth 2.1 server, API-key scoping, programmatic agent lifecycle |

## Product & prior art

| File | Topic |
|---|---|
| [03](03-competitor-teardown.md) | Codex, Claude Code/Cowork, Jules, Copilot, Cursor — table stakes & UX patterns |
| [10](10-openswe-fleet.md) | open-swe v2 (deepagents rewrite) and LangSmith Fleet |
| [09](09-openwiki-opengpts.md) | openwiki (live deepagents reference) and opengpts (archived; domain-model lessons) |
| [14](14-dcode.md) | Deep Agents Code (`dcode`): goals/rubrics, sandbox reattach, plugins, hooks — the local companion CLI |
| [15](15-org-intelligence.md) | Org-intelligence layer: LangSmith Insights/automations, memory synthesis, OKF/openwiki, graph & DB tooling |

## Frontend & design

| File | Topic |
|---|---|
| [04](04-langchain-uis.md) | agent-chat-ui, deep-agents-ui (archived), open-agent-platform, ui-patterns |
| [21](21-gapfill-ui-contract.md) | `@langchain/react` v1 wire contract: content blocks, tools channel, HITL `decisions`, subagent namespaces |
| [22](22-gapfill-ui-tokens.md) | Component-level tokens & layout from the first-party UIs |
| [11](11-docs-design-language.md) | docs.langchain.com design language extraction (the carbon-copy source) |
| [13](13-agent-inbox.md) | agent-inbox teardown + the HITL contract migration finding |
| [05](05-crossplatform-arch.md) | Monorepo, Next.js 16, Tauri v2 vs Electron, Expo/PWA, auth consensus |
| [07](07-oss-v1-setup.md) | Licensing landscape, repo conventions, community-file staging |

## The five load-bearing conclusions

1. **A deployed Managed Deep Agents project is a standard hosted Agent Server** — same threads/runs/streaming API as every other tier, which is what makes "one client, every runtime" real.
2. **Programmatic agent lifecycle is possible today** via the public control plane (`/v2/deployments` + tarball upload, `/v1/deepagents/*`, crons, Context Hub); Fleet CRUD is the one closed surface (invoke/read is public).
3. **"Sign in with LangSmith" is real**: a spec-complete OAuth 2.1 server with public dynamic client registration, PKCE, and device flow — unused by any OSS app so far. API-key + server proxy remains the fallback.
4. **The HITL contract migrated**: build approvals on `HITLRequest`/`decisions` with `respond()/respondAll()` (camelCase-canonical with documented exceptions) — not the legacy agent-inbox schema.
5. **The visual system is fully specified**: Mintlify "aspen" tokens (blue palette `#006DDD`/`#7FC8FF`/`#030710`, confirmed hexes/measurements) + first-party component conventions; only the commercial fonts need substitution.

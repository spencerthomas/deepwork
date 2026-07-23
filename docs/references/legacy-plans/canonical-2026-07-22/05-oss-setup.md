# 05 · Open-source project setup

*Deep Work planning docs · 2026-07-21.*

## License: MIT

Every upstream package Deep Work builds on is MIT (`deepagents` py+js, `langgraph`, `langgraph-sdk`, `@langchain/react`, `langsmith` SDK, `managed-deepagents`). Comparable apps split MIT (LibreChat, open-agent-platform) vs Apache-2.0 (Continue, Cline, Codex CLI); Apache-2.0 + NOTICE is the standard venture-shaped recommendation — but Deep Work is a **contribution intended for possible LangChain adoption**, and matching the langchain-ai org norm (MIT everywhere) minimizes adoption friction. MIT it is, with a NOTICE-style attribution block in the README. (Avoid Open WebUI's path: it relicensed MIT → branding-preservation BSD after forks stripped branding — if that ever matters here, it's LangChain's call post-adoption, not ours.)

Elastic-2.0 boundary: `langgraph-api` (Agent Server runtime) is source-available, not OSI. Deep Work never vendors or redistributes it — clients talk to it over HTTP. Document this plainly in the README licensing section.

## Naming & trademark hygiene

- Product name **Deep Work**; repo `spencerthomas/deepwork`; no `lang*` in the name, domain, or npm scope (LANGCHAIN and LANGSMITH are USPTO-registered; precedent exists for forced renames).
- Nominative fair use only: "built on LangChain deepagents", "works with LangSmith" — plus the explicit non-affiliation disclaimer (already in README).
- No LangChain wordmark/logo assets in the repo; no TWK Lausanne / Aeonik Mono font files (commercial licenses) — the token layer makes the swap trivial if LangChain adopts the project.

## Repo structure

```
deepwork/
  apps/
    web/                  # Next.js 16 App Router (Turbopack); server routes: oauth, key-proxy,
    │                     #   gh-token proxy-callback, push fan-out
    desktop/              # Tauri v2 shell wrapping the web app
    mobile/               # PWA assets/config v1; Expo app post-v1
  packages/
    agent/                # deepagents project — MUST remain a valid `mda` project root:
    │                     #   agent.py, instructions.md, tools/, middleware/, connectors/,
    │                     #   schedules/, skills/, sandbox/, identity.py
    sdk/                  # TS: agent-source registry, control-plane client, stream adapters,
    │                     #   normalized types (HITL casing lives HERE, nowhere else)
    ui/                   # tokens.css, tailwind preset, shadcn-based components
  docs/
    plan/  design/  research/
  .github/workflows/
```

Python (`packages/agent`) rides in the pnpm monorepo as a non-JS workspace (uv-managed; Turborepo task wrappers) — mirroring how open-swe v2 pairs a Python agent with a TS dashboard.

## Toolchain

| Concern | Choice | Precedent |
|---|---|---|
| Package manager / tasks | pnpm 10 + Turborepo ^2.10 (pnpm catalogs for shared deps) | 2026 consensus; deepagentsjs uses pnpm workspaces |
| Versioning / releases | changesets (+ `changelog-github`), npm provenance | deepagentsjs release.yml pattern |
| Lint / format | biome (or oxlint/oxfmt to mirror deepagentsjs) — pick one, enforce in CI | deepagentsjs |
| Python | uv + ruff + pytest (agent package) | open-swe v2 |
| PR discipline | semantic PR titles (amannn/action-semantic-pull-request) with per-package scopes; Actions pinned to SHAs | deepagentsjs |
| CI matrix | Node 22/24; jobs: format → lint → typecheck → test → build; agent package: ruff + pytest + `langgraph dev` contract tests | deepagentsjs + our M0 spike 3 |
| Previews | Vercel Git integration (not Actions) | open-agent-platform |
| Renovate/dependabot | weekly, with `@langchain/*` grouped — v1-line SDKs release weekly, keep pinned-but-fresh | research: SDK churn risk |

Version pins at scaffold time (verified 2026-07-21): `deepagents` py 0.6.12 (watch 0.7.0), js ^1.11.1 (peers: `@langchain/core ^1.2.0`, `@langchain/langgraph ^1.4.4`, `@langchain/langgraph-sdk ^1.9.23`, `langchain ^1.5.0`, `langsmith ^0.7.1`); `@langchain/react` ^1.0.28; `managed-deepagents` **dev channel** (0.4.0-dev) for per-user memory + channels; Python ≥3.11.

## Community files: staged, not ceremonial

**At v1** (deepagentsjs ships less at 1.4k stars — this is the sensible max): LICENSE, README, CONTRIBUTING (dev setup + PR conventions + DCO), SECURITY (private reporting), CODE_OF_CONDUCT (Contributor Covenant), two issue forms (bug / feature), PR template, CODEOWNERS.

**Deferred until traction**: FUNDING, stale-bots, labeler automation, translations, CLA (DCO suffices; a CLA only if LangChain adoption requires one), GOVERNANCE.

**Staging strategy** (user directive: build to v1 first): the repo stays public from day one, but "not accepting feature PRs yet — see roadmap" posture until v1 (Codex-CLI launch pattern), then open contribution lanes with good-first-issues from the post-v1 backlog.

## Docs

v1: README + `docs/` in-repo (this plan evolves into architecture docs; add quickstart + deploy + agent-authoring guides at M4). A Mintlify site (`docs.json`, matching the ecosystem) only post-v1 if traction warrants — Continue/Cline precedent is in-repo Mintlify config, cheap to add later.

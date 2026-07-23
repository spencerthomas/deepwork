# Frontend sandbox agent instructions

## Repository role

This repository is the Deep Work visual design sandbox. It exists to explore layouts, interactions, responsive behavior, and component treatments quickly. It is not the canonical application, package source, runtime contract, security architecture, or delivery plan.

The sibling `deepwork` monorepo is canonical. Changes flow one way only:

1. Explore and review a visual or interaction change here.
2. Record the affected routes, components, states, and evidence.
3. Port selected code manually into `deepwork/apps/web` and shared primitives into `deepwork/packages/ui` under canonical instructions.
4. Reconnect the port to normalized SDK contracts, security boundaries, accessibility requirements, and tests in the monorepo.

Never automatically merge this repository into the monorepo. Never backport monorepo business logic, credentials, generated clients, server routes, lockfiles, or runtime adapters merely to keep the sandbox synchronized.

## Prototype boundaries

- Mock data and interactions are simulated design evidence. Label simulations clearly and do not describe them as functional integrations.
- Do not call live LangSmith, Agent Server, Managed Deep Agents, Fleet, GitHub, sandbox, or customer endpoints from this repository.
- Do not add API keys, OAuth tokens, ingress secrets, installation tokens, production environment files, signed URLs, or real customer data.
- Do not define external API shapes from convenience. Where a design needs data, use the canonical glossary and normalized domain examples from the reviewed monorepo plans.
- Do not make deployment, source, approval, task, or settings decisions here. Raise them for the canonical decision register.

## Design exploration requirements

- Cover desktop and phone layouts for each changed journey. Include loading, empty, error, offline, permission, stale, reconnecting, interrupted, disabled, partial, and success states as applicable.
- Preserve all action semantics in the mock. If a control has no simulated result, label it as a prototype or remove it from the reviewed flow.
- Use semantic HTML, visible focus, complete keyboard operation, accessible names, AA contrast, adequate touch targets, and reduced-motion behavior even during exploration.
- Treat mock markdown, terminal text, diffs, files, tool output, and artifacts as untrusted examples and render them through safe patterns.
- Prefer existing component and token vocabulary. Note deliberate proposed token changes; do not treat sandbox token drift as permission to overwrite canonical `packages/ui` tokens.

## Porting handoff

For every proposed port, provide:

- sandbox commit and affected paths;
- route, viewport, theme, and state inventory;
- screenshots or interaction notes for the reviewed result;
- mapping from sandbox components to `apps/web` or `packages/ui` ownership;
- list of mocked actions and the canonical feature IDs that must make them live;
- accessibility behavior and known gaps;
- dependencies that must not be copied;
- explicit statement that no live contract was established by the prototype.

The canonical implementation must be reviewed and tested independently after porting. A successful sandbox build or visual review is not release evidence.

## Local quality

- Keep strict TypeScript and lint checks enabled. Do not use `ignoreBuildErrors` as an accepted state.
- Use only synthetic deterministic data. Avoid unstable random or time-dependent output unless the test controls it.
- Preserve unrelated v0-generated work and review generated dependency changes before accepting them.
- Do not claim parity with the canonical product unless a current, reviewed port map demonstrates it.

# Cross-platform app architecture

*Condensed findings (agent-researched 2026-07-21, verified against live sources). Key facts and sources only; full reports available on request.*

## KEY FACTS
- 2026 monorepo consensus: pnpm workspaces + Turborepo (turbo@2.10.5, pnpm 10.x, pnpm catalogs) is the default; Nx only for 10+ packages/generators/enforced boundaries.
- Next.js 16.2.6 is current stable (May 7, 2026): Turbopack default dev bundler, React 19.2, Cache Components, async params, middleware renamed proxy.ts; App Router only path for new features.
- LangChain's maintained reference client is langchain-ai/agent-chat-ui (Next 15.5.18, React 19.2.5, Tailwind v4, @langchain/langgraph-sdk ^1.8.10, langgraph-nextjs-api-passthrough ^0.1.4); langchain-ai/deep-agents-ui is archived.
- @langchain/langgraph-sdk@1.9.27 exports ./client,./react,./auth,./ui,./stream with all framework peers optional; the new v1 frontend hook is useStream from @langchain/react@1.0.28 (siblings @langchain/vue,-svelte,-angular).
- useStream<typeof agent> infers typed stream state from the shared deepagents agent definition, and accepts transport 'sse'|'websocket', custom fetch override, webSocketFactory, threadId/onThreadId, and returns subagents Map, toolCalls, interrupts, submit/stop/disconnect.
- deepagents JS is at 1.11.1 (peers @langchain/langgraph ^1.4.4, langchain ^1.5.0) with ./browser and ./node exports; v0.6+ added typed event-streaming projections (subagents, messages, tool calls, values).
- Agent Server streams are resumable: create run with stream_resumable=true then GET /threads/{tid}/runs/{rid}/stream with Last-Event-ID; threads.joinStream(threadID,{lastEventId}) streams all runs on a thread and is designed for mobile backgrounding and multi-device handoff.
- New Agent Server Protocol v2: POST /threads/{tid}/commands (ProtocolCommand envelope: run.start, input.respond, agent.getTree) + POST /threads/{tid}/stream/events, with WebSocket clients using the same envelope in-band plus subscription.subscribe/unsubscribe.
- Every run-creating endpoint accepts a webhook parameter POSTed at run completion — the hook for push-notification fan-out (server -> Expo Push API for native, Web Push/VAPID for PWA, local notifications on desktop).
- Managed Deep Agents (private beta, US-only, CLI-first via mda from managed-deepagents) deploys to a hosted LangGraph deployment; identity.ts presets (private-assistant, multi-tenant-saas, internal-tool...) scope threads/memory per actor/tenant via trusted_backend headers (X-MDA-Ingress-Secret/X-MDA-Actor-Id) or validated_token with built-in providers.supabase and providers.guest.
- Claude Desktop and Claude Cowork desktop are Electron (Cowork lead Felix Rieseberg sits on Electron's admin working group); ChatGPT macOS is native Swift; Cowork expanded desktop -> web + mobile in July 2026.
- Tauri v2 (@tauri-apps/api 2.11.1) has first-party updater, notification, deep-link (tauri-plugin-deep-link 2.4.5), tray plugins and ~5MB installers vs Electron 43.1.1 at ~80-120MB, but requires Next.js output:'export' (or a Node sidecar).
- Expo SDK 56 (May 21, 2026): RN 0.85, React 19.2, Hermes V1, Expo UI (SwiftUI/Compose) stable, expo-router@57 now independent of React Navigation; SDK 55+ makes the New Architecture mandatory.
- useStream/langgraph-sdk work in React Native/Expo today (assistant-ui documents npx expo install @assistant-ui/react-native @assistant-ui/react-langchain @langchain/react @langchain/langgraph-sdk; RN 0.74+ fetch streams, expo/fetch is WinterCG-compliant).
- 2026 OSS auth consensus: Better Auth is the default for new self-hosted TS apps (Auth.js v5 maintainers point new projects to it); comparable OSS apps use self-owned JWT (LibreChat), Supabase Auth (open-canvas), or BYO LangSmith key behind a server proxy (agent-chat-ui); none use Clerk.
- iOS web push works only for home-screen-installed PWAs on iOS 16.4+ — the main argument for an eventual native Expo app; v1 should ship web + Tauri desktop first with mobile as PWA.

## OPEN QUESTIONS
- Whether the Agent Server websocket transport (Protocol v2 in-band commands) is generally available on LangSmith Cloud deployments today or still rolling out — the useStream reference lists transport:'websocket' but no GA announcement was found.
- Exact Managed Deep Agents client-connection surface during private beta: docs say API-driven invocation examples were removed and programmatic use requires contacting LangChain, so whether a standard LangGraph SDK client against the hosted deployment URL is officially supported for beta users needs confirmation from the beta contact.
- The claim that iOS web push is unavailable in EU countries on iOS 17.4+ comes from one secondary source and conflicts with Apple's reversal of the EU home-screen-web-app removal; verify before making PWA push an EU-facing feature.
- Whether @langchain/react useStream needs any polyfill beyond a streaming fetch (e.g., TextDecoderStream) on Hermes/Expo SDK 56 — assistant-ui ships RN bindings implying it works, but no explicit polyfill list was found.
- Why deep-agents-ui was archived and whether LangChain plans a dedicated open-source Deep Agents client to replace it (agent-chat-ui appears to be the maintained successor, but no explicit deprecation pointer was captured).
- Precise Tauri v2 differential-update behavior (one source claims differential updates; official plugin docs describe full-artifact updates from static JSON or dynamic server).

## SOURCES
- Managed Deep Agents overview (Docs by LangChain) — https://docs.langchain.com/langsmith/managed-deep-agents-overview
- Add identity to Managed Deep Agents — https://docs.langchain.com/langsmith/managed-deep-agents-identity
- How Managed Deep Agents work — https://docs.langchain.com/langsmith/managed-deep-agents-how-it-works
- Streaming (LangSmith Deployment API, joinStream + Last-Event-ID) — https://docs.langchain.com/langsmith/streaming
- Use webhooks (Agent Server webhook parameter) — https://docs.langchain.com/langsmith/use-webhooks
- Deep Agents frontend overview (useStream, subagents, todos, sandbox) — https://docs.langchain.com/oss/javascript/deepagents/frontend/overview
- Join & rejoin pattern (@langchain/react useStream) — https://docs.langchain.com/oss/javascript/langchain/frontend/join-rejoin
- Custom authentication (Agent Server) — https://docs.langchain.com/langsmith/custom-auth
- Agent Server API: Join Run Stream (stream_resumable) — https://docs.langchain.com/langsmith/agent-server-api
- useStream reference (@langchain/react) — https://reference.langchain.com/javascript/langchain-react/index/useStream
- agent-chat-ui package.json (langchain-ai) — https://github.com/langchain-ai/agent-chat-ui/blob/main/package.json
- agent-chat-ui README (API passthrough, custom auth) — https://github.com/langchain-ai/agent-chat-ui/blob/main/README.md
- deep-agents-ui (archived) — https://github.com/langchain-ai/deep-agents-ui
- @langchain/react package.json (langgraphjs libs/sdk-react) — https://github.com/langchain-ai/langgraphjs/blob/main/libs/sdk-react/package.json
- @langchain/langgraph-sdk on npm — https://www.npmjs.com/package/@langchain/langgraph-sdk
- deepagents on npm — https://www.npmjs.com/package/deepagents
- assistant-ui LangChain React runtime (useStreamRuntime) — https://www.assistant-ui.com/docs/runtimes/langchain
- Monorepo Strategy 2026: Turborepo vs Nx Decision Guide — https://www.digitalapplied.com/blog/monorepo-strategy-2026-turborepo-nx-decision-matrix
- Turborepo vs Nx 2026 (PkgPulse) — https://www.pkgpulse.com/guides/turborepo-vs-nx-monorepo-2026
- Next.js 16: what's new (Makerkit) — https://makerkit.dev/blog/tutorials/nextjs-16
- Next.js 16 in 2026: What's New and What You Should Actually Use — https://nirajiitr.com/blog/nextjs-16-2026-whats-new-what-to-use
- Tauri v2 vs Electron 2026: The Honest Comparison — https://www.buildmvpfast.com/blog/tauri-v2-vs-electron-desktop-apps-2026
- Tauri: Next.js frontend guide (static export requirement) — https://v2.tauri.app/start/frontend/nextjs/
- Tauri updater plugin — https://v2.tauri.app/plugin/updater/
- Next.js standalone inside a Tauri v2 sidecar (vercel/next.js discussion #90982) — https://github.com/vercel/next.js/discussions/90982
- Daring Fireball: Claude's Electron Mac App Is an Inside Job (Cowork/Electron/Rieseberg) — https://daringfireball.net/2026/07/claudes_criminally_bad_mac_app_is_an_inside_job
- Why is Claude an Electron App? (dbreunig) — https://www.dbreunig.com/2026/02/21/why-is-claude-an-electron-app.html
- Claude Cowork expands to mobile and web (TechCrunch, July 2026) — https://techcrunch.com/2026/07/07/the-coding-agent-wars-are-spilling-into-the-rest-of-the-office-claude-cowork/
- Expo SDK 56 changelog — https://expo.dev/changelog/sdk-56
- Expo SDK 55 changelog — https://expo.dev/changelog/sdk-55
- Expo New Architecture guide (mandatory in SDK 55+) — https://docs.expo.dev/guides/new-architecture/
- Goodbye background-fetch, hello expo-background-task — https://expo.dev/blog/goodbye-background-fetch-hello-expo-background-task
- Expo push notifications overview — https://docs.expo.dev/push-notifications/overview/
- How to Stream LLM Responses in React Native (SSE/fetch ReadableStream) — https://getwireai.com/blog/react-native-llm-streaming
- react-native-sse (EventSource for RN) — https://github.com/binaryminds/react-native-sse
- OpenWebUI vs LibreChat 2026 (auth architecture) — https://www.requesty.ai/blog/openwebui-vs-librechat-which-self-hosted-chatgpt-ui-is-right-for-you
- open-canvas README (Supabase auth) — https://github.com/langchain-ai/open-canvas/blob/main/README.md
- Better Auth vs NextAuth v5 vs Clerk 2026 (PkgPulse) — https://www.pkgpulse.com/guides/better-auth-vs-nextauth-v5-vs-clerk-2026
- I tested every major auth library for Next.js in 2026 (LogRocket) — https://blog.logrocket.com/best-auth-library-nextjs-2026/
- PWA iOS Limitations and Safari Support 2026 (MagicBell) — https://www.magicbell.com/blog/pwa-ios-limitations-safari-support-complete-guide
- turbo on npm — https://www.npmjs.com/package/turbo
- @tauri-apps/api on npm — https://www.npmjs.com/package/@tauri-apps/api
- electron on npm — https://www.npmjs.com/package/electron
- expo-router on npm — https://www.npmjs.com/package/expo-router

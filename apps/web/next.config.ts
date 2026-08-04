import type { NextConfig } from "next";
import { fileURLToPath } from "node:url";

const repositoryRoot = fileURLToPath(new URL("../..", import.meta.url));

// The browser talks only to this app's origin; /api/* is proxied to the Deep Work
// API server-side. This keeps the API same-origin so the HttpOnly session cookie
// authenticates both REST calls and the SSE event stream (EventSource cannot send
// bearer headers). Set DEEPWORK_API_ORIGIN in the hosting environment.
const apiOrigin =
  process.env.DEEPWORK_API_ORIGIN ?? "https://deepwork-api-production.up.railway.app";
const ephemeralAcceptance = process.env.DEEPWORK_EPHEMERAL_ACCEPTANCE === "1";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  typescript: {
    tsconfigPath: ephemeralAcceptance ? "tsconfig.acceptance.json" : "tsconfig.json",
  },
  turbopack: {
    root: repositoryRoot,
  },
  webpack(config) {
    // Browser acceptance runs in disposable worktrees and CI machines where a
    // persistent webpack pack only consumes disk and is never reused. Keeping
    // this opt-in preserves normal developer caching while allowing the gates
    // to run fail-closed on constrained execution hosts.
    if (ephemeralAcceptance) {
      config.cache = false;
    }
    return config;
  },
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${apiOrigin}/api/:path*` }];
  },
};

export default nextConfig;

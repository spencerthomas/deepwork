import type { NextConfig } from "next";
import { fileURLToPath } from "node:url";

const repositoryRoot = fileURLToPath(new URL("../..", import.meta.url));

// The browser talks only to this app's origin; /api/* is proxied to the Deep Work
// API server-side. This keeps the API same-origin so the HttpOnly session cookie
// authenticates both REST calls and the SSE event stream (EventSource cannot send
// bearer headers). Set DEEPWORK_API_ORIGIN in the hosting environment.
const apiOrigin =
  process.env.DEEPWORK_API_ORIGIN ?? "https://deepwork-api-production.up.railway.app";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  turbopack: {
    root: repositoryRoot,
  },
  async rewrites() {
    return [
      { source: "/api/:path*", destination: `${apiOrigin}/api/:path*` },
    ];
  },
};

export default nextConfig;

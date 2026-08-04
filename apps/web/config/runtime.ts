export function resolveApiBaseUrl(
  configuredBaseUrl: string | undefined,
  environment: string | undefined,
): string | undefined {
  if (configuredBaseUrl !== undefined) {
    return configuredBaseUrl;
  }
  return environment === "production" ? "" : undefined;
}

export function resolveBuildSha(
  configuredBuildSha: string | undefined,
  vercelCommitSha: string | undefined,
): string {
  return configuredBuildSha?.trim() || vercelCommitSha?.trim() || "unknown";
}

export const webRuntimeConfig = Object.freeze({
  apiBaseUrl: resolveApiBaseUrl(process.env.NEXT_PUBLIC_API_BASE_URL, process.env.NODE_ENV),
  buildSha: resolveBuildSha(
    process.env.NEXT_PUBLIC_DEEPWORK_BUILD_SHA,
    process.env.VERCEL_GIT_COMMIT_SHA,
  ),
  demoMode: process.env.NEXT_PUBLIC_DEMO_MODE,
});

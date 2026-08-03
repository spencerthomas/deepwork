export function resolveApiBaseUrl(
  configuredBaseUrl: string | undefined,
  environment: string | undefined,
): string | undefined {
  if (configuredBaseUrl !== undefined) {
    return configuredBaseUrl;
  }
  return environment === "production" ? "" : undefined;
}

export const webRuntimeConfig = Object.freeze({
  apiBaseUrl: resolveApiBaseUrl(process.env.NEXT_PUBLIC_API_BASE_URL, process.env.NODE_ENV),
  demoMode: process.env.NEXT_PUBLIC_DEMO_MODE,
});

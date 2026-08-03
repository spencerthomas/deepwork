const node = JSON.stringify(process.env.DEEPWORK_NODE || process.execPath);

/** Keep visual and performance acceptance on the same production web runtime. */
export function localProductionWebServer(readyPath: string) {
  return {
    command:
      `NEXT_PUBLIC_API_BASE_URL= DEEPWORK_API_ORIGIN=http://127.0.0.1:8000 ${node} apps/web/node_modules/next/dist/bin/next build apps/web --webpack && ` +
      `DEEPWORK_NODE=${node} DEEPWORK_ACCESS_KEY=deepwork-local-browser-acceptance DEEPWORK_WEB_PRODUCTION=1 ./dev`,
    url: new URL(readyPath, "http://127.0.0.1:3000").toString(),
    reuseExistingServer: false,
    timeout: 60_000,
  };
}

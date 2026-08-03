import { defineConfig } from "@playwright/test";

import localConfig from "./playwright.config";

export default defineConfig({
  ...localConfig,
  testDir: "./tests/recovery",
  outputDir: "output/playwright/recovery-results",
  globalSetup: undefined,
  retries: 0,
  reporter: "line",
  timeout: 90_000,
  expect: { timeout: 10_000 },
  use: {
    ...localConfig.use,
    storageState: undefined,
    // This gate enters a generated access key. Never serialize request bodies,
    // cookies, or form values into a retained Playwright trace or video.
    trace: "off",
    video: "off",
  },
  webServer: {
    // Keep the web process alive while the test owns and restarts the real API.
    // The browser still uses only the reviewed same-origin /api proxy.
    command:
      "NEXT_PUBLIC_API_BASE_URL= DEEPWORK_API_ORIGIN=http://127.0.0.1:8000 pnpm --filter @deepwork/web dev --webpack --hostname 127.0.0.1 --port 3000",
    url: "http://127.0.0.1:3000/login",
    reuseExistingServer: false,
    timeout: 60_000,
  },
});

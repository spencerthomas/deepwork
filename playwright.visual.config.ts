import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/visual",
  testMatch: /.*\.spec\.ts/,
  outputDir: "output/playwright/visual-results",
  snapshotPathTemplate: "{testDir}/expected/{testFilePath}/{arg}{ext}",
  globalSetup: "./tests/e2e/global-setup.ts",
  fullyParallel: false,
  workers: 1,
  forbidOnly: Boolean(process.env.CI),
  retries: 0,
  reporter: process.env.CI ? "line" : "line",
  use: {
    baseURL: "http://127.0.0.1:3000",
    channel: "chrome",
    storageState: "output/playwright/auth.json",
    serviceWorkers: "block",
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  webServer: {
    command:
      "NEXT_PUBLIC_API_BASE_URL= DEEPWORK_API_ORIGIN=http://127.0.0.1:8000 pnpm --filter @deepwork/web build && " +
      "DEEPWORK_ACCESS_KEY=deepwork-local-browser-acceptance DEEPWORK_WEB_PRODUCTION=1 ./dev",
    url: "http://127.0.0.1:3000/tasks/new",
    reuseExistingServer: false,
    timeout: 60_000,
  },
});

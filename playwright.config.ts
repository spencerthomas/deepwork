import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  globalSetup: "./tests/e2e/global-setup.ts",
  outputDir: "output/playwright/test-results",
  fullyParallel: false,
  // The governed full-stack harness owns one API database and one dev server.
  // Serial browser execution prevents route compilation and shared task state
  // from racing across acceptance scenarios.
  workers: 1,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI
    ? [["line"], ["html", { open: "never", outputFolder: "output/playwright/report" }]]
    : "line",
  use: {
    baseURL: "http://127.0.0.1:3000",
    channel: "chrome",
    storageState: "output/playwright/auth.json",
    screenshot: "only-on-failure",
    serviceWorkers: "block",
    // This journey enters an access key. Retain masked screenshots only; a
    // Playwright trace can serialize form values and request bodies.
    trace: "off",
    launchOptions: {
      args: ["--disk-cache-size=1048576", "--media-cache-size=1048576"],
    },
  },
  webServer: {
    command:
      "DEEPWORK_EPHEMERAL_ACCEPTANCE=1 DEEPWORK_ACCESS_KEY=deepwork-local-browser-acceptance ./dev",
    url: "http://127.0.0.1:3000/tasks/new",
    reuseExistingServer: false,
    timeout: 60_000,
  },
});

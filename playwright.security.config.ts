import { defineConfig } from "@playwright/test";

const canary = process.env.DEEPWORK_SECURITY_CANARY;
if (!canary) {
  throw new Error("DEEPWORK_SECURITY_CANARY is required for the credential-boundary test.");
}

export default defineConfig({
  testDir: "./tests/security",
  outputDir: "output/playwright/security-results",
  fullyParallel: false,
  workers: 1,
  forbidOnly: Boolean(process.env.CI),
  retries: 0,
  reporter: process.env.CI
    ? [["line"], ["html", { open: "never", outputFolder: "output/playwright/security-report" }]]
    : "line",
  use: {
    baseURL: "http://127.0.0.1:3000",
    screenshot: "only-on-failure",
    serviceWorkers: "allow",
    trace: "off",
  },
  webServer: {
    command: `DEEPWORK_ACCESS_KEY=${canary} ./dev`,
    url: "http://127.0.0.1:3000/login",
    reuseExistingServer: false,
    timeout: 60_000,
  },
});

import { defineConfig } from "@playwright/test";

const hostedUrl = process.env.DEEPWORK_HOSTED_URL?.trim();
const hostedAccessKey = process.env.DEEPWORK_E2E_ACCESS_KEY?.trim();
const expectedBuildSha = process.env.DEEPWORK_EXPECTED_BUILD_SHA?.trim();

if (!hostedUrl || !hostedAccessKey || !expectedBuildSha) {
  throw new Error(
    "Hosted acceptance is blocking: DEEPWORK_HOSTED_URL, DEEPWORK_E2E_ACCESS_KEY, and DEEPWORK_EXPECTED_BUILD_SHA are required.",
  );
}

export default defineConfig({
  testDir: "./tests/hosted",
  outputDir: "output/playwright/hosted-results",
  fullyParallel: false,
  workers: 1,
  forbidOnly: true,
  retries: 1,
  timeout: 120_000,
  expect: { timeout: 30_000 },
  reporter: process.env.CI
    ? [["line"], ["html", { open: "never", outputFolder: "output/playwright/hosted-report" }]]
    : "line",
  use: {
    baseURL: hostedUrl,
    serviceWorkers: "block",
    screenshot: "only-on-failure",
    // The journey types a protected access key. Never retain traces because
    // Playwright trace inputs can include the field value.
    trace: "off",
  },
});

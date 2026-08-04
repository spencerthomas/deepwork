import { defineConfig } from "@playwright/test";

import localConfig from "./playwright.config";
import { localProductionWebServer } from "./tests/playwright/local-production-web-server";

export default defineConfig({
  ...localConfig,
  testDir: "./tests/visual",
  testMatch: /.*\.spec\.ts/,
  outputDir: "output/playwright/visual-results",
  snapshotPathTemplate: "{testDir}/expected/{testFilePath}/{arg}{ext}",
  globalSetup: undefined,
  retries: 0,
  reporter: "line",
  use: {
    ...localConfig.use,
    // Playwright 1.61's downloaded Chromium build is the visual contract. CI
    // installs this exact revision on the matching macOS image.
    channel: undefined,
    storageState: undefined,
  },
  webServer:
    process.env.DEEPWORK_VISUAL_CONTRACT_ONLY === "1"
      ? undefined
      : localProductionWebServer("/tasks/new"),
});

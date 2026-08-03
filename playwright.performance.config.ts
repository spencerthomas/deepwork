import { defineConfig } from "@playwright/test";

import localConfig from "./playwright.config";
import profile from "./tests/performance/inbox-1000.profile.json";
import { localProductionWebServer } from "./tests/playwright/local-production-web-server";

export default defineConfig({
  ...localConfig,
  testDir: "./tests/performance",
  testMatch: /.*\.spec\.ts/,
  outputDir: "output/playwright/performance-results",
  retries: 0,
  reporter: "line",
  use: {
    ...localConfig.use,
    channel: undefined,
  },
  projects: Object.entries(profile.viewports).map(([name, viewport]) => ({
    name,
    use: { viewport },
  })),
  webServer: localProductionWebServer("/tasks"),
});

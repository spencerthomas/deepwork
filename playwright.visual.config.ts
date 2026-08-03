import { defineConfig } from "@playwright/test";

import localConfig from "./playwright.config";

const node = JSON.stringify(process.env.DEEPWORK_NODE || process.execPath);

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
    storageState: undefined,
  },
  webServer: {
    command:
      `NEXT_PUBLIC_API_BASE_URL= DEEPWORK_API_ORIGIN=http://127.0.0.1:8000 ${node} apps/web/node_modules/next/dist/bin/next build apps/web --webpack && ` +
      `DEEPWORK_NODE=${node} DEEPWORK_ACCESS_KEY=deepwork-local-browser-acceptance DEEPWORK_WEB_PRODUCTION=1 ./dev`,
    url: "http://127.0.0.1:3000/tasks/new",
    reuseExistingServer: false,
    timeout: 60_000,
  },
});

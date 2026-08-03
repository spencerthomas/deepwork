import { mkdir } from "node:fs/promises";
import { dirname } from "node:path";

import { request } from "@playwright/test";

const storageStatePath = "output/playwright/auth.json";

/** Authenticate every browser context against the same local server under test. */
export default async function globalSetup() {
  await mkdir(dirname(storageStatePath), { recursive: true });
  const api = await request.newContext({ baseURL: "http://127.0.0.1:8000" });
  try {
    const response = await api.post("/api/v1/auth/login", {
      data: { accessKey: "deepwork-local-browser-acceptance" },
    });
    if (!response.ok()) {
      throw new Error(`Local browser acceptance login returned HTTP ${response.status()}.`);
    }
    await api.storageState({ path: storageStatePath });
  } finally {
    await api.dispose();
  }
}

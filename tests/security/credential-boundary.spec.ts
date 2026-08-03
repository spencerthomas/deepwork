import { expect, test } from "@playwright/test";

const canary = process.env.DEEPWORK_SECURITY_CANARY;
if (!canary) {
  throw new Error("DEEPWORK_SECURITY_CANARY is required.");
}

test("reusable access key is absent from browser and public application state", async ({
  context,
  page,
}) => {
  await context.clearCookies();
  await page.goto("/login");
  await page.getByLabel("Workspace access key").fill(canary);
  let loginBody: string | undefined;
  await page.route("**/api/v1/auth/login", async (route) => {
    const response = await route.fetch();
    loginBody = await response.text();
    await route.fulfill({ response, body: loginBody });
  });
  await page.getByRole("button", { name: "Connect workspace" }).click();
  await expect.poll(() => loginBody).toBeDefined();
  if (loginBody === undefined) {
    throw new Error("The login response body was not captured.");
  }
  const parsedLoginBody = JSON.parse(loginBody) as Record<string, unknown>;
  expect(parsedLoginBody).not.toHaveProperty("token");
  await expect(page).toHaveURL(/\/tasks$/);

  const browserState = await page.evaluate(async () => {
    const local: Record<string, string | null> = {};
    const session: Record<string, string | null> = {};
    for (let index = 0; index < localStorage.length; index += 1) {
      const key = localStorage.key(index);
      if (key) local[key] = localStorage.getItem(key);
    }
    for (let index = 0; index < sessionStorage.length; index += 1) {
      const key = sessionStorage.key(index);
      if (key) session[key] = sessionStorage.getItem(key);
    }

    const cacheEntries: Array<{ cache: string; url: string; body: string }> = [];
    if ("caches" in window) {
      for (const cacheName of await caches.keys()) {
        const cache = await caches.open(cacheName);
        for (const request of await cache.keys()) {
          const response = await cache.match(request);
          cacheEntries.push({
            cache: cacheName,
            url: request.url,
            body: response ? await response.clone().text() : "",
          });
        }
      }
    }

    const indexedDatabases =
      "databases" in indexedDB
        ? await indexedDB
            .databases()
            .then((items) =>
              items.map((item) => ({ name: item.name ?? null, version: item.version ?? null })),
            )
        : [];
    const registrations =
      "serviceWorker" in navigator
        ? await navigator.serviceWorker
            .getRegistrations()
            .then((items) =>
              items.map((item) => ({ scope: item.scope, script: item.active?.scriptURL })),
            )
        : [];

    return {
      html: document.documentElement.outerHTML,
      cookie: document.cookie,
      local,
      session,
      cacheEntries,
      indexedDatabases,
      registrations,
      resources: performance.getEntriesByType("resource").map((entry) => entry.name),
    };
  });

  const apiBodies: string[] = [];
  for (const path of [
    "/api/v1/auth/session",
    "/api/v1/tasks",
    "/api/v1/agents",
    "/api/v1/schedules",
  ]) {
    const response = await page.request.get(path);
    expect(response.ok(), `${path} should be readable after login`).toBe(true);
    apiBodies.push(await response.text());
  }
  const schema = await page.request.get("http://127.0.0.1:8000/openapi.json");
  expect(schema.ok()).toBe(true);
  const schemaBody = await schema.text();

  const retained = JSON.stringify({
    browserState,
    cookies: await context.cookies(),
    loginBody,
    apiBodies,
    schemaBody,
  });
  expect(retained).not.toContain(canary);
  for (const cookie of await context.cookies()) {
    if (cookie.name === "deepwork_session") {
      expect(loginBody).not.toContain(cookie.value);
    }
  }
  for (const forbidden of ["authRef", "credentialRef", "providerToken", "refreshToken"]) {
    expect(schemaBody).not.toContain(forbidden);
  }
});

import { createServer } from "node:http";

import { expect, test as base } from "@playwright/test";

const redirectGuardProbeHost = "browser-redirect-guard.invalid";

const test = base.extend<{ redirectProbeUrl: string }>({
  redirectProbeUrl: async ({ browserName: _browserName }, use) => {
    const server = createServer((_request, response) => {
      response.writeHead(302, {
        "access-control-allow-origin": "*",
        location: `https://${redirectGuardProbeHost}/redirect-probe`,
      });
      response.end();
    });
    await new Promise<void>((resolve, reject) => {
      server.once("error", reject);
      server.listen(0, "127.0.0.1", () => {
        server.off("error", reject);
        resolve();
      });
    });
    const address = server.address();
    if (address === null || typeof address === "string") {
      throw new Error("The redirect probe server did not expose a loopback TCP address.");
    }
    try {
      await use(`http://127.0.0.1:${address.port}/redirect-probe`);
    } finally {
      await new Promise<void>((resolve, reject) => {
        server.close((error) => (error ? reject(error) : resolve()));
      });
    }
  },
});

test("creates, approves, and completes one API-backed task", async ({
  context,
  page,
  redirectProbeUrl,
}) => {
  const guardProbeHost = "browser-guard.invalid";
  const blockedGuardProbes = new Set<string>();
  const blockedRedirectGuardProbes = new Set<string>();
  const unexpectedEgress = new Set<string>();
  const pageErrors: string[] = [];
  let redirectProbeWasRequested = false;

  const cdp = await context.newCDPSession(page);
  await cdp.send("Fetch.enable", {
    patterns: [{ urlPattern: "http://*" }, { urlPattern: "https://*" }],
  });
  cdp.on("Fetch.requestPaused", (event) => {
    void (async () => {
      const url = new URL(event.request.url);
      if (url.href === redirectProbeUrl) {
        redirectProbeWasRequested = true;
      }
      if (url.hostname !== "127.0.0.1") {
        if (url.hostname === guardProbeHost) {
          blockedGuardProbes.add(url.protocol);
        } else if (url.hostname === redirectGuardProbeHost && redirectProbeWasRequested) {
          blockedRedirectGuardProbes.add(url.href);
        } else {
          unexpectedEgress.add(url.origin);
        }
        await cdp.send("Fetch.failRequest", {
          requestId: event.requestId,
          errorReason: "BlockedByClient",
        });
        return;
      }
      await cdp.send("Fetch.continueRequest", { requestId: event.requestId });
    })();
  });
  await page.routeWebSocket(/^wss?:\/\//, async (webSocket) => {
    const url = new URL(webSocket.url());
    if ((url.protocol === "ws:" || url.protocol === "wss:") && url.hostname !== "127.0.0.1") {
      if (url.hostname === guardProbeHost) {
        blockedGuardProbes.add(url.protocol);
      } else {
        unexpectedEgress.add(url.origin);
      }
      await webSocket.close({ code: 1008, reason: "Non-loopback browser traffic is blocked" });
      return;
    }
    webSocket.connectToServer();
  });
  page.on("pageerror", (error) => pageErrors.push(error.message));

  await page.goto("/tasks/new");
  await expect(page.getByRole("heading", { name: "New task" })).toBeVisible();

  await page.evaluate(async (host) => {
    const webSocketProbe = new Promise<void>((resolve) => {
      const socket = new WebSocket(`wss://${host}/websocket-probe`);
      socket.addEventListener("close", () => resolve(), { once: true });
      socket.addEventListener("error", () => resolve(), { once: true });
    });
    await Promise.all([fetch(`https://${host}/http-probe`).catch(() => undefined), webSocketProbe]);
  }, guardProbeHost);
  await expect.poll(() => [...blockedGuardProbes].sort()).toEqual(["https:", "wss:"]);

  await page.evaluate((url) => fetch(url).catch(() => undefined), redirectProbeUrl);
  await expect
    .poll(() => [...blockedRedirectGuardProbes])
    .toEqual([`https://${redirectGuardProbeHost}/redirect-probe`]);

  const prompt = "Prepare a credential-free browser acceptance result";
  await page.getByLabel("Task", { exact: true }).fill(prompt);

  const createResponse = page.waitForResponse(
    (response) =>
      response.request().method() === "POST" &&
      response.url() === "http://127.0.0.1:8000/api/v1/tasks",
  );
  await page.getByRole("button", { name: "Dispatch" }).click();
  expect((await createResponse).status()).toBe(202);

  await expect(page).toHaveURL(/\/tasks\/task_[0-9]{8}$/);
  const taskHeader = page.getByRole("heading", { level: 1 }).locator("..");
  await expect(taskHeader.getByText("Needs review", { exact: true })).toBeVisible();

  const decisionResponse = page.waitForResponse(
    (response) =>
      response.request().method() === "POST" &&
      /\/api\/v1\/tasks\/task_[0-9]{8}\/decisions$/.test(response.url()),
  );
  await page.getByRole("button", { name: "Approve", exact: true }).click();
  expect((await decisionResponse).status()).toBe(202);

  await expect(taskHeader.getByText("Done", { exact: true })).toBeVisible();
  await expect(page.getByText("Run completed", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: prompt, exact: true })).toBeVisible();

  expect([...unexpectedEgress]).toEqual([]);
  expect(pageErrors).toEqual([]);
});

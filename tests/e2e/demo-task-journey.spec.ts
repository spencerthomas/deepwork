import { expect, test } from "@playwright/test";

test("creates, approves, and completes one API-backed task", async ({ page }) => {
  const guardProbeHost = "browser-guard.invalid";
  const blockedGuardProbes = new Set<string>();
  const unexpectedEgress = new Set<string>();
  const pageErrors: string[] = [];

  await page.route("**/*", async (route) => {
    const url = new URL(route.request().url());
    if ((url.protocol === "http:" || url.protocol === "https:") && url.hostname !== "127.0.0.1") {
      if (url.hostname === guardProbeHost) {
        blockedGuardProbes.add(url.protocol);
      } else {
        unexpectedEgress.add(url.origin);
      }
      await route.abort();
      return;
    }
    await route.continue();
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

import type { Page } from "@playwright/test";

const LOOPBACK_HOST = "127.0.0.1";

/**
 * Keep a browser page loopback-only across both HTTP(S) and WebSocket
 * transports so acceptance tests cannot depend on third-party content.
 */
export async function blockNonLoopbackEgress(page: Page): Promise<void> {
  await page.route("**/*", async (route) => {
    const url = new URL(route.request().url());
    const external =
      (url.protocol === "http:" || url.protocol === "https:") && url.hostname !== LOOPBACK_HOST;
    if (external) {
      await route.abort();
      return;
    }
    await route.continue();
  });
  await page.routeWebSocket(/^wss?:\/\//, (webSocket) => {
    const url = new URL(webSocket.url());
    const external =
      (url.protocol === "ws:" || url.protocol === "wss:") && url.hostname !== LOOPBACK_HOST;
    if (external) {
      webSocket.close({ code: 1008, reason: "Non-loopback browser traffic is blocked" });
      return;
    }
    webSocket.connectToServer();
  });
}

import { afterEach, describe, expect, it, vi } from "vitest";

import { loginWithAccessKey } from "./auth-client";

describe("loginWithAccessKey", () => {
  afterEach(() => vi.unstubAllGlobals());

  it.each([
    [200, { ok: true }],
    [401, { ok: false, reason: "rejected" }],
    [503, { ok: false, reason: "failed" }],
  ] as const)("maps HTTP %s without exposing the access key", async (status, expected) => {
    const request = vi.fn().mockResolvedValue(new Response(null, { status }));
    vi.stubGlobal("fetch", request);

    await expect(loginWithAccessKey("workspace-secret")).resolves.toEqual(expected);
    expect(request).toHaveBeenCalledWith(
      "/api/v1/auth/login",
      expect.objectContaining({
        credentials: "include",
        body: JSON.stringify({ accessKey: "workspace-secret" }),
      }),
    );
  });
});

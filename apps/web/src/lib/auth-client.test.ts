import { afterEach, describe, expect, it, vi } from "vitest";

import { getSession, loginWithAccessKey, logout } from "./auth-client";

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
        signal: expect.any(AbortSignal),
      }),
    );
  });
});

describe("authenticated session client", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("loads and validates the current session", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ actorId: "operator", expiresAt: 1_800_000_000 }), {
        status: 200,
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(getSession()).resolves.toEqual({
      actorId: "operator",
      expiresAt: 1_800_000_000,
    });
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/auth/session",
      expect.objectContaining({ credentials: "include" }),
    );
  });

  it("rejects an unavailable or malformed session", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(null, { status: 401 })));
    await expect(getSession()).rejects.toThrow("HTTP 401");

    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({}))));
    await expect(getSession()).rejects.toThrow("malformed session");
  });

  it("posts logout with the browser session cookie", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(logout()).resolves.toBeUndefined();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/auth/logout",
      expect.objectContaining({ method: "POST", credentials: "include" }),
    );
  });
});

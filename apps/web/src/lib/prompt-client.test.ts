import { afterEach, describe, expect, it, vi } from "vitest";

import { createHttpPromptClient } from "./prompt-client";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("prompt client", () => {
  it("loads and normalizes the current prompt", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        new Response(JSON.stringify({ systemPrompt: null, isDefault: true }), { status: 200 }),
      );
    vi.stubGlobal("fetch", fetchMock);

    await expect(createHttpPromptClient("http://api.test/").getPrompt()).resolves.toEqual({
      value: "",
      isDefault: true,
    });
    expect(fetchMock).toHaveBeenCalledWith(
      "http://api.test/api/v1/settings/prompt",
      expect.objectContaining({ method: "GET", credentials: "include" }),
    );
  });

  it("sends the exact prompt update and returns normalized state", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ systemPrompt: "Be concise.", isDefault: false }), {
        status: 200,
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      createHttpPromptClient("http://api.test").updatePrompt("Be concise."),
    ).resolves.toEqual({ value: "Be concise.", isDefault: false });
    expect(fetchMock).toHaveBeenCalledWith(
      "http://api.test/api/v1/settings/prompt",
      expect.objectContaining({
        method: "PUT",
        credentials: "include",
        body: JSON.stringify({ systemPrompt: "Be concise." }),
      }),
    );
  });

  it("rejects non-success, network, and malformed responses", async () => {
    const client = createHttpPromptClient("http://api.test");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(null, { status: 503 })));
    await expect(client.getPrompt()).rejects.toThrow("HTTP 503");

    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("refused")));
    await expect(client.getPrompt()).rejects.toThrow("could not reach the API");

    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({}))));
    await expect(client.getPrompt()).rejects.toThrow("malformed system prompt");
  });
});

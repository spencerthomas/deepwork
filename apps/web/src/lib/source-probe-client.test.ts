import { afterEach, describe, expect, it, vi } from "vitest";

import { probeClassicSource } from "./source-probe-client";

afterEach(() => {
  vi.unstubAllGlobals();
});

const result = {
  kind: "langsmith_deployment",
  state: "available",
  assistantId: "assistant-1",
  graphId: "deep-work",
  reason: "assistant-qualified-read-only",
  saveAllowed: false,
  capabilities: [
    { name: "assistants-read", state: "available", reason: "assistant-qualified" },
    { name: "runs-create", state: "gated", reason: "invocation-not-authorized" },
  ],
};

describe("source probe client", () => {
  it("posts only the candidate fields with the current application session", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(result)));
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      probeClassicSource("https://api.test/", {
        endpoint: "https://agent.example.test",
        assistantId: "assistant-1",
      }),
    ).resolves.toEqual(result);
    expect(fetchMock).toHaveBeenCalledWith(
      "https://api.test/api/v1/sources/probes",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
        body: JSON.stringify({
          kind: "langsmith_deployment",
          deploymentUrl: "https://agent.example.test",
          assistantId: "assistant-1",
        }),
      }),
    );
    expect(fetchMock.mock.calls[0]?.[1]?.body).not.toContain("credential");
  });

  it("uses the bounded API problem and rejects malformed success", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ message: "No server credential is configured." }), {
          status: 503,
        }),
      ),
    );
    await expect(
      probeClassicSource("https://api.test", {
        endpoint: "https://agent.example.test",
        assistantId: "assistant-1",
      }),
    ).rejects.toThrow("No server credential is configured.");

    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({}))));
    await expect(
      probeClassicSource("https://api.test", {
        endpoint: "https://agent.example.test",
        assistantId: "assistant-1",
      }),
    ).rejects.toThrow("malformed source check");
  });

  it("reports network failure without provider details", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("secret upstream detail")));
    await expect(
      probeClassicSource("https://api.test", {
        endpoint: "https://agent.example.test",
        assistantId: "assistant-1",
      }),
    ).rejects.toThrow("could not reach the API");
  });
});

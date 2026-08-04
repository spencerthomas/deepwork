import { afterEach, describe, expect, it, vi } from "vitest";

import { probeClassicSource } from "./source-probe-client";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

const result = {
  kind: "langsmith_deployment",
  state: "available",
  assistantId: "assistant-1",
  graphId: "deep-work",
  reason: "assistant-qualified-read-only",
  saveAllowed: false,
  capabilities: [
    {
      name: "assistants-read",
      state: "available",
      observedAt: "2026-08-04T00:00:00.000Z",
      adapterVersion: "classic-source-probe-v1",
      contractVersion: "langgraph-assistants-get-v1",
      evidenceClass: "live-contract",
    },
    {
      name: "runs-create",
      state: "gated",
      safeReason: "adapter-disabled",
      observedAt: "2026-08-04T00:00:00.000Z",
      adapterVersion: "classic-source-probe-v1",
      contractVersion: "langgraph-assistants-get-v1",
      evidenceClass: "documented",
    },
  ],
};

describe("source probe client", () => {
  it("posts only the candidate fields with the current application session", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(result)));
    vi.stubGlobal("fetch", fetchMock);
    const signal = new AbortController().signal;

    await expect(
      probeClassicSource(
        "https://api.test/",
        {
          assistantId: "assistant-1",
        },
        signal,
      ),
    ).resolves.toEqual(result);
    expect(fetchMock).toHaveBeenCalledWith(
      "https://api.test/api/v1/sources/probes",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
        body: JSON.stringify({
          kind: "langsmith_deployment",
          sourceTargetId: "classic-default",
          assistantId: "assistant-1",
        }),
        signal: expect.any(AbortSignal),
      }),
    );
    expect(fetchMock.mock.calls[0]?.[1]?.body).not.toContain("credential");
  });

  it("uses the bounded API problem and rejects malformed success", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            code: "source_probe_unavailable",
            message: "untrusted upstream detail",
          }),
          {
            status: 503,
          },
        ),
      ),
    );
    await expect(
      probeClassicSource("https://api.test", {
        assistantId: "assistant-1",
      }),
    ).rejects.toThrow("No server-held source credential is configured");

    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({}))));
    await expect(
      probeClassicSource("https://api.test", {
        assistantId: "assistant-1",
      }),
    ).rejects.toThrow("malformed source check");
  });

  it("reports network failure without provider details", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("secret upstream detail")));
    await expect(
      probeClassicSource("https://api.test", {
        assistantId: "assistant-1",
      }),
    ).rejects.toThrow("could not reach the API");
  });

  it("maps an expired session to an authentication message", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({ code: "unauthorized", message: "Authentication required." }),
          {
            status: 401,
          },
        ),
      ),
    );
    await expect(
      probeClassicSource("https://api.test", { assistantId: "assistant-1" }),
    ).rejects.toThrow("Authentication is required");
  });

  it("aborts a stalled request at the bounded deadline", async () => {
    vi.useFakeTimers();
    const fetchMock = vi.fn((_url: string, init?: RequestInit) => {
      return new Promise<Response>((_resolve, reject) => {
        init?.signal?.addEventListener("abort", () =>
          reject(new DOMException("Aborted", "AbortError")),
        );
      });
    });
    vi.stubGlobal("fetch", fetchMock);
    const pending = probeClassicSource("https://api.test", { assistantId: "assistant-1" });
    const rejection = expect(pending).rejects.toThrow("timed out");

    await vi.advanceTimersByTimeAsync(15_000);

    await rejection;
    expect(fetchMock.mock.calls[0]?.[1]?.signal?.aborted).toBe(true);
  });
});

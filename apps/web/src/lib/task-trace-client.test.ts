import { afterEach, describe, expect, it, vi } from "vitest";

import { createHttpTaskTraceClient } from "./task-trace-client";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("task trace client", () => {
  it("returns a correlated available trace and safely encodes the task ID", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        new Response(
          JSON.stringify({ state: "available", traceUrl: "https://smith.example/r/run-1" }),
          { status: 200 },
        ),
      );
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      createHttpTaskTraceClient("http://api.test/").getTrace("task/one"),
    ).resolves.toEqual({ state: "available", url: "https://smith.example/r/run-1" });
    expect(fetchMock).toHaveBeenCalledWith(
      "http://api.test/api/v1/tasks/task%2Fone/trace",
      expect.objectContaining({ credentials: "include" }),
    );
  });

  it.each([
    ["non-success response", () => Promise.resolve(new Response(null, { status: 404 }))],
    ["network failure", () => Promise.reject(new Error("refused"))],
    [
      "malformed response",
      () => Promise.resolve(new Response(JSON.stringify({ state: "available" }))),
    ],
  ])("fails closed when the API has a %s", async (_name, request) => {
    vi.stubGlobal("fetch", vi.fn(request));
    await expect(createHttpTaskTraceClient("http://api.test").getTrace("task-1")).resolves.toEqual({
      state: "unavailable",
    });
  });
});

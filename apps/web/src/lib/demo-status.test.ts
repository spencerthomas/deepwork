import { afterEach, describe, expect, it, vi } from "vitest";

import {
  capabilityState,
  fetchDemoStatus,
  FIXTURE_SAFE_REASON,
  fixtureDemoStatus,
  normalizeDemoStatus,
} from "./demo-status";

const apiPayload = {
  mode: "fixture",
  evidence_class: "fixture",
  capabilities: [
    { name: "local_task_loop", state: "available" },
    { name: "task_stream", state: "available" },
    { name: "durable_jobs", state: "unavailable" },
  ],
  safe_reason: "Local fixtures only; external providers are unavailable.",
};

describe("normalizeDemoStatus", () => {
  it("normalizes the API's snake_case wire shape", () => {
    expect(normalizeDemoStatus(apiPayload)).toEqual({
      mode: "fixture",
      evidenceClass: "fixture",
      capabilities: [
        { name: "local_task_loop", state: "available" },
        { name: "task_stream", state: "available" },
        { name: "durable_jobs", state: "unavailable" },
      ],
      safeReason: "Local fixtures only; external providers are unavailable.",
      source: "api",
    });
  });

  it("accepts camelCase field aliases", () => {
    const status = normalizeDemoStatus({
      mode: "fixture",
      evidenceClass: "fixture",
      capabilities: [],
      safeReason: "reason",
    });
    expect(status?.evidenceClass).toBe("fixture");
    expect(status?.safeReason).toBe("reason");
  });

  it("fails closed on malformed payloads", () => {
    expect(normalizeDemoStatus(undefined)).toBeUndefined();
    expect(normalizeDemoStatus("fixture")).toBeUndefined();
    expect(normalizeDemoStatus([])).toBeUndefined();
    expect(normalizeDemoStatus({ ...apiPayload, safe_reason: undefined })).toBeUndefined();
    expect(normalizeDemoStatus({ ...apiPayload, mode: "" })).toBeUndefined();
    expect(normalizeDemoStatus({ ...apiPayload, capabilities: "all" })).toBeUndefined();
    expect(
      normalizeDemoStatus({ ...apiPayload, capabilities: [{ state: "available" }] }),
    ).toBeUndefined();
    expect(
      normalizeDemoStatus({ ...apiPayload, capabilities: [{ name: "sources", state: 1 }] }),
    ).toBeUndefined();
  });

  it("never promotes an unrecognized capability state to available", () => {
    const status = normalizeDemoStatus({
      ...apiPayload,
      capabilities: [{ name: "sources", state: "degraded" }],
    });
    expect(status?.capabilities).toEqual([{ name: "sources", state: "unknown" }]);
  });
});

describe("capabilityState", () => {
  it("fails closed to unknown when the status or capability is missing", () => {
    expect(capabilityState(undefined, "local_task_loop")).toBe("unknown");
    expect(capabilityState(normalizeDemoStatus(apiPayload), "sources")).toBe("unknown");
  });

  it("returns the reported state for known capabilities", () => {
    const status = normalizeDemoStatus(apiPayload);
    expect(capabilityState(status, "local_task_loop")).toBe("available");
    expect(capabilityState(status, "durable_jobs")).toBe("unavailable");
  });
});

describe("fixtureDemoStatus", () => {
  it("mirrors the API fixture capability set and is labeled fixture", () => {
    const status = fixtureDemoStatus();
    expect(status.source).toBe("fixture");
    expect(status.mode).toBe("fixture");
    expect(status.evidenceClass).toBe("fixture");
    expect(status.safeReason).toBe(FIXTURE_SAFE_REASON);
    const states = Object.fromEntries(
      status.capabilities.map((capability) => [capability.name, capability.state]),
    );
    expect(states).toEqual({
      local_task_loop: "available",
      task_stream: "available",
      authentication: "unavailable",
      durable_jobs: "unavailable",
      sources: "unavailable",
      external_providers: "unavailable",
    });
  });
});

describe("fetchDemoStatus", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("fetches and normalizes the demo status", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(apiPayload), {
        headers: { "content-type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const status = await fetchDemoStatus("http://127.0.0.1:8000/");
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/v1/demo/status",
      expect.objectContaining({ headers: { accept: "application/json" } }),
    );
    expect(status?.capabilities).toHaveLength(3);
  });

  it("resolves undefined on network errors instead of rejecting", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("refused")));
    await expect(fetchDemoStatus("http://127.0.0.1:8000")).resolves.toBeUndefined();
  });

  it("resolves undefined on non-2xx responses", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("nope", { status: 503 })));
    await expect(fetchDemoStatus("http://127.0.0.1:8000")).resolves.toBeUndefined();
  });

  it("resolves undefined on malformed bodies", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("not json", { status: 200 })));
    await expect(fetchDemoStatus("http://127.0.0.1:8000")).resolves.toBeUndefined();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ mode: "fixture" }), { status: 200 })),
    );
    await expect(fetchDemoStatus("http://127.0.0.1:8000")).resolves.toBeUndefined();
  });
});

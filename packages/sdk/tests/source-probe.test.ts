import {
  createSourceProbeService,
  mapSourceProbeResult,
  sourceProbeTransportProblem,
  type SourceProbeTransport,
} from "@deepwork/sdk";
import { describe, expect, it, vi } from "vitest";

const response = {
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

describe("source probe service", () => {
  it("builds the accepted request and maps an immutable domain result", async () => {
    const check = vi.fn().mockResolvedValue(response);
    const service = createSourceProbeService({ check });

    const result = await service.check(
      { endpoint: "https://agent.example.test", assistantId: "assistant-1" },
      { signal: new AbortController().signal },
    );

    expect(result).toEqual({ ok: true, value: response });
    expect(check).toHaveBeenCalledWith(
      {
        kind: "langsmith_deployment",
        deploymentUrl: "https://agent.example.test",
        assistantId: "assistant-1",
      },
      expect.objectContaining({ signal: expect.any(AbortSignal) }),
    );
    if (!result.ok) throw new Error("Expected a mapped source result.");
    expect(Object.isFrozen(result.value)).toBe(true);
    expect(Object.isFrozen(result.value.capabilities)).toBe(true);
    expect(Object.isFrozen(result.value.capabilities[0])).toBe(true);
  });

  it("fails closed on missing, extra, and malformed wire fields", () => {
    expect(mapSourceProbeResult({})).toMatchObject({
      ok: false,
      error: { category: "contract" },
    });
    expect(mapSourceProbeResult({ ...response, providerPayload: "blocked" })).toMatchObject({
      ok: false,
      error: { category: "contract" },
    });
    expect(
      mapSourceProbeResult({
        ...response,
        capabilities: [{ ...response.capabilities[0], providerPayload: "blocked" }],
      }),
    ).toMatchObject({ ok: false, error: { category: "contract" } });
  });

  it("maps only accepted source problems to bounded messages", async () => {
    const cases: readonly [number, string, string][] = [
      [422, "source_endpoint_invalid", "not an allowed hosted HTTPS endpoint"],
      [503, "source_probe_unavailable", "No server-held source credential"],
    ];
    for (const [status, code, message] of cases) {
      const transport: SourceProbeTransport = {
        async check() {
          throw sourceProbeTransportProblem(status, code);
        },
      };
      await expect(
        createSourceProbeService(transport).check({
          endpoint: "https://agent.example.test",
          assistantId: "assistant-1",
        }),
      ).resolves.toMatchObject({
        ok: false,
        error: { safeMessage: expect.stringContaining(message) },
      });
    }
    expect(() => sourceProbeTransportProblem(500, "upstream_secret")).toThrow(
      "status/code pair is not accepted",
    );
  });

  it("sanitizes unknown transport failures", async () => {
    const transport: SourceProbeTransport = {
      async check() {
        throw new Error("secret upstream detail");
      },
    };
    await expect(
      createSourceProbeService(transport).check({
        endpoint: "https://agent.example.test",
        assistantId: "assistant-1",
      }),
    ).resolves.toEqual({
      ok: false,
      error: {
        category: "unknown",
        safeMessage: "Deep Work could not reach the API to check this source.",
        retryable: true,
      },
    });
  });
});

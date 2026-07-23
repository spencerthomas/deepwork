import {
  capabilitySummary,
  unavailableCapability,
} from "@deepwork/domain";
import {
  unavailableMutationPort,
  unavailableQueryPort,
  unavailableStreamPort,
} from "@deepwork/sdk";
import { afterEach, describe, expect, it, vi } from "vitest";

const capability = capabilitySummary(
  unavailableCapability(
    "unknown",
    "contract-not-verified",
    {
      observedAt: "2026-07-23T00:00:00.000Z",
      adapterVersion: "adapter-disabled",
      contractVersion: "contract-unverified",
      evidenceClass: "documented",
    },
  ),
);

const originalFetch = globalThis.fetch;

afterEach(() => {
  globalThis.fetch = originalFetch;
  vi.restoreAllMocks();
});

describe("explicitly unavailable ports", () => {
  it("returns CapabilityUnavailable without making a guessed request", async () => {
    const fetchSpy: typeof fetch = vi.fn(async () => {
      throw new Error("Network access denied by test.");
    });
    globalThis.fetch = fetchSpy;

    const port = unavailableMutationPort<{ action: string }, never>(
      capability,
    );
    const result = await port.mutate({ action: "gated-operation" });

    expect(result).toMatchObject({
      ok: false,
      error: {
        category: "capability-unavailable",
        retryable: true,
      },
    });
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("keeps query, mutation, and stream contracts separate", async () => {
    const query = unavailableQueryPort<undefined, never>(capability);
    const mutation = unavailableMutationPort<undefined, never>(capability);
    const stream = unavailableStreamPort<undefined, never>(capability);

    await expect(query.query(undefined)).resolves.toMatchObject({ ok: false });
    await expect(mutation.mutate(undefined)).resolves.toMatchObject({
      ok: false,
    });
    await expect(stream.open(undefined)).resolves.toMatchObject({ ok: false });
    expect("mutate" in query).toBe(false);
    expect("open" in mutation).toBe(false);
  });
});

import {
  capabilitySummary,
  type UnavailableCapabilitySummary,
  unavailableCapability,
} from "@deepwork/domain";
import {
  unavailableMutationPort,
  unavailableQueryPort,
  unavailableStreamPort,
  SDK_ERROR_CATEGORIES,
} from "@deepwork/sdk";
import { describe, expect, it } from "vitest";

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

describe("explicitly unavailable ports", () => {
  it("freezes the public error vocabulary", () => {
    expect(Object.isFrozen(SDK_ERROR_CATEGORIES)).toBe(true);
  });

  it("returns CapabilityUnavailable without making a guessed request", async () => {
    const port = unavailableMutationPort<{ action: string }, never>(
      capability,
    );
    const result = await port.mutate({ action: "gated-operation" });

    expect(result).toMatchObject({
      ok: false,
      error: {
        category: "capability-unavailable",
        retryable: false,
      },
    });
  });

  it("retries only recoverable source unavailability", async () => {
    const sourceUnavailable = capabilitySummary(
      unavailableCapability(
        "unavailable",
        "source-unavailable",
        {
          observedAt: "2026-07-23T00:00:00.000Z",
          adapterVersion: "adapter-disabled",
          contractVersion: "contract-unverified",
          evidenceClass: "documented",
        },
      ),
    );
    const port = unavailableQueryPort<undefined, never>(sourceUnavailable);

    await expect(port.query(undefined)).resolves.toMatchObject({
      ok: false,
      error: {
        category: "capability-unavailable",
        retryable: true,
      },
    });
  });

  it("does not retry contradictory state and reason summaries", async () => {
    for (const state of ["permission-denied", "unknown"] as const) {
      const contradictory = Object.freeze({
        ...capability,
        state,
        safeReason: "source-unavailable",
      }) as UnavailableCapabilitySummary;
      const port = unavailableQueryPort<undefined, never>(contradictory);

      await expect(port.query(undefined)).resolves.toMatchObject({
        ok: false,
        error: {
          retryable: false,
        },
      });
    }
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

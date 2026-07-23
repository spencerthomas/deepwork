import {
  availableCapability,
  capabilitySummary,
  isCapabilityAvailable,
  unavailableCapability,
} from "@deepwork/domain";
import { describe, expect, it } from "vitest";

const metadata = {
  observedAt: "2026-07-23T00:00:00.000Z",
  adapterVersion: "adapter-contract-1",
  contractVersion: "normalized-contract-1",
  evidenceClass: "documented" as const,
};

describe("capability evidence", () => {
  it("keeps unknown support explicitly unavailable", () => {
    const evidence = unavailableCapability(
      "unknown",
      "contract-not-verified",
      metadata,
    );

    expect(isCapabilityAvailable(evidence)).toBe(false);
    expect(evidence.safeReason).toBe("contract-not-verified");
  });

  it("omits capability values from safe summaries", () => {
    const evidence = availableCapability(
      { privatePayload: "must-not-be-summarized" },
      metadata,
    );

    expect(capabilitySummary(evidence)).toEqual({
      state: "available",
      ...metadata,
    });
    expect(JSON.stringify(capabilitySummary(evidence))).not.toContain(
      "privatePayload",
    );
  });
});

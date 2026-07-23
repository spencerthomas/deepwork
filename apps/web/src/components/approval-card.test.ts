import { describe, expect, it } from "vitest";

import { decisionActionLabel } from "./approval-card";

describe("decisionActionLabel", () => {
  it("announces the exact in-flight action without relabelling other disabled controls", () => {
    expect(decisionActionLabel("approve", "approve", true)).toBe("Sending approval…");
    expect(decisionActionLabel("reject", "reject", true)).toBe("Sending rejection…");
    expect(decisionActionLabel("respond", "respond", true)).toBe("Sending response…");
    expect(decisionActionLabel("approve", "respond", true)).toBe("Approve and continue");
    expect(decisionActionLabel("reject", "respond", true)).toBe("Reject");
  });
});

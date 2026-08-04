import { describe, expect, it } from "vitest";

import { nextComposerDispatchPhase } from "./composer-dispatch-state";

describe("composer dispatch reconciliation", () => {
  it("moves the first unknown result into a single automatic reconciliation", () => {
    expect(nextComposerDispatchPhase("submitting", "unknown")).toBe("reconciling");
  });

  it("locks on a second unknown result instead of enabling another dispatch", () => {
    expect(nextComposerDispatchPhase("reconciling", "unknown")).toBe("outcome-unknown");
    expect(nextComposerDispatchPhase("outcome-unknown", "unknown")).toBe("outcome-unknown");
  });

  it("unlocks only an authoritative rejection and locks conflicts", () => {
    expect(nextComposerDispatchPhase("submitting", "rejected")).toBe("rejected");
    expect(nextComposerDispatchPhase("reconciling", "rejected")).toBe("rejected");
    expect(nextComposerDispatchPhase("submitting", "conflict")).toBe("conflict");
  });
});

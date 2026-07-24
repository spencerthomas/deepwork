import { describe, expect, it } from "vitest";

import { readRunPanelOpen } from "./run-panel-preference";

describe("readRunPanelOpen", () => {
  it("defaults to open when unset or unexpected", () => {
    expect(readRunPanelOpen(null)).toBe(true);
    expect(readRunPanelOpen("")).toBe(true);
    expect(readRunPanelOpen("1")).toBe(true);
    expect(readRunPanelOpen("yes")).toBe(true);
  });

  it("is closed only for the explicit closed marker", () => {
    expect(readRunPanelOpen("0")).toBe(false);
  });
});

import { describe, expect, it } from "vitest";

import { nextPanelTab, PANEL_TABS } from "./run-panel-tabs";

describe("nextPanelTab", () => {
  it("steps right and left within the tablist", () => {
    expect(nextPanelTab("status", "ArrowRight")).toBe("stream");
    expect(nextPanelTab("stream", "ArrowLeft")).toBe("status");
  });

  it("wraps horizontally at both ends", () => {
    expect(nextPanelTab("trace", "ArrowRight")).toBe("status");
    expect(nextPanelTab("status", "ArrowLeft")).toBe("trace");
  });

  it("jumps to the ends with Home and End", () => {
    expect(nextPanelTab("evidence", "Home")).toBe("status");
    expect(nextPanelTab("evidence", "End")).toBe("trace");
  });

  it("ignores keys that are not tablist navigation", () => {
    expect(nextPanelTab("status", "Enter")).toBeNull();
    expect(nextPanelTab("status", "a")).toBeNull();
    expect(nextPanelTab("status", "ArrowDown")).toBeNull();
  });

  it("exposes every tab exactly once", () => {
    const keys = PANEL_TABS.map((tab) => tab.key);
    expect(new Set(keys).size).toBe(keys.length);
    expect(keys).toContain("trace");
  });
});

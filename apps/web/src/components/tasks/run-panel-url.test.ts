import { describe, expect, it } from "vitest";

import { PANEL_TABS } from "./run-panel-tabs";
import { panelTabToQuery, readPanelTab } from "./run-panel-url";

describe("readPanelTab", () => {
  it("defaults to 'status' when the query is empty", () => {
    expect(readPanelTab(new URLSearchParams(""))).toBe("status");
  });

  it("reads each known tab", () => {
    for (const { key } of PANEL_TABS) {
      expect(readPanelTab(new URLSearchParams(`panel=${key}`))).toBe(key);
    }
  });

  it("fails closed to 'status' for an unknown tab", () => {
    expect(readPanelTab(new URLSearchParams("panel=bogus"))).toBe("status");
  });
});

describe("panelTabToQuery", () => {
  it("emits nothing for the default tab", () => {
    expect(panelTabToQuery("status")).toBe("");
  });

  it("emits the panel param for a named tab", () => {
    expect(panelTabToQuery("evidence")).toBe("panel=evidence");
    expect(panelTabToQuery("trace")).toBe("panel=trace");
  });

  it("preserves unrelated params and drops the default", () => {
    const existing = new URLSearchParams("ref=abc");
    expect(panelTabToQuery("stream", existing)).toBe("ref=abc&panel=stream");
    expect(panelTabToQuery("status", new URLSearchParams("ref=abc&panel=git"))).toBe("ref=abc");
  });

  it("round-trips every known tab", () => {
    for (const { key } of PANEL_TABS) {
      expect(readPanelTab(new URLSearchParams(panelTabToQuery(key)))).toBe(key);
    }
  });
});

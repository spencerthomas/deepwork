import { describe, expect, it } from "vitest";

import { INSPECT_TABS, inspectTabToQuery, readInspectTab } from "./agent-detail-url";

describe("readInspectTab", () => {
  it("defaults to 'capabilities' when the query is empty", () => {
    expect(readInspectTab(new URLSearchParams(""))).toBe("capabilities");
  });

  it("reads each known tab", () => {
    for (const tab of INSPECT_TABS) {
      expect(readInspectTab(new URLSearchParams(`inspect=${tab}`))).toBe(tab);
    }
  });

  it("fails closed to 'capabilities' for an unknown tab", () => {
    expect(readInspectTab(new URLSearchParams("inspect=bogus"))).toBe("capabilities");
  });
});

describe("inspectTabToQuery", () => {
  it("emits nothing for the default tab", () => {
    expect(inspectTabToQuery("capabilities")).toBe("");
  });

  it("emits the inspect param for a named tab", () => {
    expect(inspectTabToQuery("recent-tasks")).toBe("inspect=recent-tasks");
  });

  it("round-trips every known tab", () => {
    for (const tab of INSPECT_TABS) {
      expect(readInspectTab(new URLSearchParams(inspectTabToQuery(tab)))).toBe(tab);
    }
  });
});

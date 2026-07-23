import { describe, expect, it } from "vitest";

import { AGENT_SOURCES, countAvailableSources } from "./agents-index";

describe("AGENT_SOURCES", () => {
  it("marks exactly the local fixture source as available", () => {
    const available = AGENT_SOURCES.filter((source) => source.state === "available");

    expect(available.map((source) => source.id)).toEqual(["local-fixture"]);
  });

  it("keeps every external source explicitly unavailable", () => {
    const external = AGENT_SOURCES.filter((source) => source.id !== "local-fixture");

    expect(external.length).toBeGreaterThan(0);
    expect(external.every((source) => source.state === "unavailable")).toBe(true);
  });

  it("gives every source an honest, non-empty reason", () => {
    expect(AGENT_SOURCES.every((source) => source.detail.trim().length > 0)).toBe(true);
  });
});

describe("countAvailableSources", () => {
  it("counts only sources that can run work", () => {
    expect(countAvailableSources(AGENT_SOURCES)).toBe(1);
  });

  it("returns zero when nothing is available", () => {
    const gated = AGENT_SOURCES.map((source) => ({ ...source, state: "unavailable" as const }));

    expect(countAvailableSources(gated)).toBe(0);
  });
});

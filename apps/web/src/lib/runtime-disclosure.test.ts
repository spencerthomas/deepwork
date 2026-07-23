import { describe, expect, it } from "vitest";

import { runtimeDisclosure, shellRuntimePresentation } from "./runtime-disclosure";

describe("runtimeDisclosure", () => {
  it("discloses the deterministic in-browser adapter in fixture mode", () => {
    expect(runtimeDisclosure("fixture")).toBe(
      "Demo fixture mode — deterministic in-browser data, no external providers.",
    );
  });

  it("does not infer the backend runner or provider state in API mode", () => {
    const disclosure = runtimeDisclosure("api");

    expect(disclosure).toBe(
      "API mode — backend runner and external-provider availability are unknown to this client.",
    );
    expect(disclosure).not.toContain("embedded deterministic runner");
    expect(disclosure).not.toContain("providers are unavailable");
  });

  it("labels the persistent shell from the selected client mode", () => {
    expect(shellRuntimePresentation("fixture")).toEqual({
      workspaceLabel: "fixture",
      workspaceSubtitle: "in-browser workspace",
    });
    expect(shellRuntimePresentation("api")).toEqual({
      workspaceLabel: "configured API",
      workspaceSubtitle: "control surface",
    });
    expect(Object.values(shellRuntimePresentation("api")).join(" ")).not.toMatch(
      /local|runner|provider/i,
    );
  });
});

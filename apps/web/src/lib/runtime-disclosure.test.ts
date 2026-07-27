import { describe, expect, it } from "vitest";

import { runtimeDisclosure, shellRuntimePresentation } from "./runtime-disclosure";

describe("runtimeDisclosure", () => {
  it("uses plain demo language in demo mode", () => {
    expect(runtimeDisclosure("fixture")).toBe("Demo — runs in your browser with sample data.");
  });

  it("uses plain connected language in api mode", () => {
    const disclosure = runtimeDisclosure("api");

    expect(disclosure).toBe("Connected to your Deep Work workspace.");
    expect(disclosure).not.toMatch(/adapter|transport|runner|provider|api mode/i);
  });

  it("labels the shell in plain, user-facing words", () => {
    expect(shellRuntimePresentation("fixture")).toEqual({
      workspaceLabel: "Demo",
      workspaceSubtitle: "sample data",
    });
    expect(shellRuntimePresentation("api")).toEqual({
      workspaceLabel: "Workspace",
      workspaceSubtitle: "connected",
    });
    expect(Object.values(shellRuntimePresentation("api")).join(" ")).not.toMatch(
      /adapter|transport|runner|provider/i,
    );
  });
});

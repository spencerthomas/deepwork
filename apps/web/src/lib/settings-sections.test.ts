import { describe, expect, it } from "vitest";

import {
  ALL_SETTINGS_SECTIONS,
  filterSettingsGroups,
  resolveSettingsSection,
  SETTINGS_GROUPS,
} from "./settings-sections";

describe("resolveSettingsSection", () => {
  it("defaults to appearance for the bare /settings route", () => {
    expect(resolveSettingsSection(undefined)).toBe("appearance");
    expect(resolveSettingsSection([])).toBe("appearance");
  });

  it("resolves every known section id", () => {
    expect(resolveSettingsSection(["appearance"])).toBe("appearance");
    expect(resolveSettingsSection(["prompt"])).toBe("prompt");
    expect(resolveSettingsSection(["agents"])).toBe("agents");
    expect(resolveSettingsSection(["runtime"])).toBe("runtime");
    expect(resolveSettingsSection(["about"])).toBe("about");
  });

  it("falls back to appearance for unknown sections", () => {
    expect(resolveSettingsSection(["models"])).toBe("appearance");
    expect(resolveSettingsSection(["deployment", "x"])).toBe("appearance");
  });

  it("uses only the first segment and ignores case", () => {
    expect(resolveSettingsSection(["Runtime"])).toBe("runtime");
    expect(resolveSettingsSection(["runtime", "extra"])).toBe("runtime");
  });
});

describe("settings catalog", () => {
  it("exposes the Agent and Workspace groups and their real sections", () => {
    expect(SETTINGS_GROUPS.map((group) => group.label)).toEqual(["Agent", "Workspace"]);
    expect(ALL_SETTINGS_SECTIONS.map((section) => section.id)).toEqual([
      "prompt",
      "agents",
      "appearance",
      "runtime",
      "about",
    ]);
  });

  it("filters by label, case-insensitively", () => {
    expect(
      filterSettingsGroups("RUN").flatMap((group) => group.items.map((item) => item.id)),
    ).toEqual(["runtime"]);
    expect(filterSettingsGroups("  ")).toHaveLength(2);
    expect(filterSettingsGroups("nothing-matches")).toEqual([]);
  });

  it("finds a section by a keyword, not only its label", () => {
    const idsFor = (query: string) =>
      filterSettingsGroups(query).flatMap((group) => group.items.map((item) => item.id));
    expect(idsFor("theme")).toEqual(["appearance"]);
    expect(idsFor("dark")).toEqual(["appearance"]);
    expect(idsFor("diagnostics")).toEqual(["runtime"]);
    expect(idsFor("version")).toEqual(["about"]);
    expect(idsFor("license")).toEqual(["about"]);
    expect(idsFor("persona")).toEqual(["prompt"]);
    expect(idsFor("instructions")).toEqual(["prompt"]);
    expect(idsFor("fleet")).toEqual(["agents"]);
    expect(idsFor("registry")).toEqual(["agents"]);
  });

  it("gives every section at least one keyword", () => {
    for (const section of ALL_SETTINGS_SECTIONS) {
      expect(section.keywords.length).toBeGreaterThan(0);
    }
  });
});

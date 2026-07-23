import { describe, expect, it } from "vitest";

import { readThemePreference, resolveIsDark } from "./theme-preference";

describe("readThemePreference", () => {
  it("treats a missing or unexpected stored value as system", () => {
    expect(readThemePreference(null)).toBe("system");
    expect(readThemePreference("")).toBe("system");
    expect(readThemePreference("midnight")).toBe("system");
  });

  it("keeps explicit overrides", () => {
    expect(readThemePreference("light")).toBe("light");
    expect(readThemePreference("dark")).toBe("dark");
  });
});

describe("resolveIsDark", () => {
  it("follows the system preference only for system", () => {
    expect(resolveIsDark("system", true)).toBe(true);
    expect(resolveIsDark("system", false)).toBe(false);
    expect(resolveIsDark("light", true)).toBe(false);
    expect(resolveIsDark("dark", false)).toBe(true);
  });
});

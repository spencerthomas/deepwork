import { describe, expect, it } from "vitest";

import { resolveApiBaseUrl } from "../../config/runtime";

describe("web runtime API base URL", () => {
  it("uses the same-origin proxy when a production build has no explicit API base URL", () => {
    expect(resolveApiBaseUrl(undefined, "production")).toBe("");
  });

  it("preserves the local API fallback outside production", () => {
    expect(resolveApiBaseUrl(undefined, "development")).toBeUndefined();
    expect(resolveApiBaseUrl(undefined, "test")).toBeUndefined();
  });

  it("preserves an explicit API origin or same-origin opt-in", () => {
    expect(resolveApiBaseUrl("https://api.example.test", "production")).toBe(
      "https://api.example.test",
    );
    expect(resolveApiBaseUrl("", "development")).toBe("");
  });
});

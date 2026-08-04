import { describe, expect, it } from "vitest";

import { resolveApiBaseUrl, resolveBuildSha } from "../../config/runtime";

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

describe("web runtime build identity", () => {
  it("prefers an explicit build identity", () => {
    expect(resolveBuildSha(" release-candidate ", "vercel-commit")).toBe("release-candidate");
  });

  it("uses Vercel's immutable Git commit when no override exists", () => {
    expect(resolveBuildSha(undefined, " 1ac8f4e ")).toBe("1ac8f4e");
  });

  it("reports an honest unknown identity outside a commit-bound build", () => {
    expect(resolveBuildSha(undefined, undefined)).toBe("unknown");
  });
});

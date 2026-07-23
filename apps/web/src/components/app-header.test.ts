import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { AppHeader, PRIMARY_NAVIGATION } from "./app-header";

describe("AppHeader product navigation", () => {
  it("exposes only the delivered Tasks destination as a working link", () => {
    const delivered = PRIMARY_NAVIGATION.filter((item) => item.href !== undefined);
    const unavailable = PRIMARY_NAVIGATION.filter((item) => !item.current);

    expect(delivered).toEqual([{ current: true, href: "#main-content", label: "Tasks" }]);
    expect(unavailable.every((item) => item.href === undefined)).toBe(true);
  });

  it("keeps the local runtime limitation visible and marks future areas disabled", () => {
    const markup = renderToStaticMarkup(
      createElement(AppHeader, {
        apiBaseUrl: "http://127.0.0.1:8000/api/v1",
        mode: "fixture",
      }),
    );

    expect(markup).toContain("External providers are unavailable");
    expect(markup).toContain('aria-current="page"');
    expect(markup).toContain('aria-disabled="true"');
    expect(markup.match(/>Soon</g)).toHaveLength(6);
    expect(markup).toContain('aria-label="Use dark theme"');
    expect(markup).toContain('aria-pressed="false"');
    expect(markup).not.toContain('href="/approvals"');
  });
});

import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { AppHeader, PRIMARY_NAVIGATION } from "./app-header";

describe("AppHeader product navigation", () => {
  it("exposes the delivered Tasks and Approvals destinations as working links", () => {
    const delivered = PRIMARY_NAVIGATION.filter((item) => item.href !== undefined);

    expect(delivered).toEqual([
      { href: "/", label: "Tasks" },
      { href: "/approvals", label: "Approvals" },
    ]);
  });

  it("marks the active destination and keeps undelivered areas disabled", () => {
    const markup = renderToStaticMarkup(
      createElement(AppHeader, {
        apiBaseUrl: "http://127.0.0.1:8000/api/v1",
        mode: "fixture",
      }),
    );

    expect(markup).toContain("External providers are unavailable");
    expect(markup).toContain('aria-current="page"');
    expect(markup).toContain('aria-disabled="true"');
    expect(markup).toContain('href="/approvals"');
    expect(markup.match(/>Soon</g)).toHaveLength(5);
    expect(markup).toContain('aria-label="Use dark theme"');
    expect(markup).toContain('aria-pressed="false"');
  });

  it("marks Approvals active when it is the current destination", () => {
    const markup = renderToStaticMarkup(
      createElement(AppHeader, {
        apiBaseUrl: "http://127.0.0.1:8000/api/v1",
        mode: "fixture",
        activePath: "/approvals",
      }),
    );

    expect(markup).toMatch(/href="\/approvals"[^>]*aria-current="page"/);
    expect(markup).not.toMatch(/href="\/"[^>]*aria-current="page"/);
  });
});

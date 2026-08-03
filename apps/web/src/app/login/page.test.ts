import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import LoginPage from "./page";

describe("LoginPage", () => {
  it("keeps the branded connection story on the real access-key contract", () => {
    const markup = renderToStaticMarkup(createElement(LoginPage));

    expect(markup).toContain("An operations room for work done by agents.");
    expect(markup).toContain("Connect to Deep Work");
    expect(markup).toContain("Workspace access key");
    expect(markup).toContain("Connect workspace");
    expect(markup).toContain("The trace is truth");
    expect(markup).not.toContain("Continue with LangSmith");
    expect(markup).not.toContain("workspace picker");
  });
});

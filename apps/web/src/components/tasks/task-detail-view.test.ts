import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { TaskThreadMarker } from "./task-detail-view";

describe("TaskThreadMarker", () => {
  it("stacks marker detail on phones and restores the inline desktop layout", () => {
    const markup = renderToStaticMarkup(
      createElement(TaskThreadMarker, {
        label: "Evidence recorded",
        detail: "The runner recorded a long evidence summary.",
      }),
    );

    expect(markup).toContain("flex-wrap");
    expect(markup).toContain("basis-full");
    expect(markup).toContain("sm:basis-auto");
    expect(markup).toContain("sm:truncate");
    expect(markup.indexOf("Evidence recorded")).toBeLessThan(markup.indexOf("evidence summary"));
  });
});

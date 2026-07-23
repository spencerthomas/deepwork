import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { SCHEDULES_UNAVAILABLE_REASON, SchedulesIndex } from "./schedules-index";

describe("SchedulesIndex", () => {
  const markup = renderToStaticMarkup(createElement(SchedulesIndex));

  it("states plainly that scheduling is unavailable", () => {
    expect(markup).toContain("Scheduling is unavailable");
    expect(markup).toContain(SCHEDULES_UNAVAILABLE_REASON);
    expect(markup).toContain("is-unavailable");
  });

  it("marks itself the active destination", () => {
    expect(markup).toMatch(/href="\/schedules"[^>]*aria-current="page"/);
  });

  it("fabricates no schedule entries", () => {
    expect(markup).not.toContain('class="task-list"');
    expect(markup).not.toContain('class="capability-list"');
  });
});

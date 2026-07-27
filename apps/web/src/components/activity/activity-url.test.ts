import { describe, expect, it } from "vitest";

import { ACTIVITY_FILTERS } from "./activity-model";
import { activityFilterToQuery, readActivityFilter } from "./activity-url";

describe("readActivityFilter", () => {
  it("defaults to 'all' when the query is empty", () => {
    expect(readActivityFilter(new URLSearchParams(""))).toBe("all");
  });

  it("reads each known filter", () => {
    for (const filter of ACTIVITY_FILTERS) {
      expect(readActivityFilter(new URLSearchParams(`type=${filter}`))).toBe(filter);
    }
  });

  it("fails closed to 'all' for an unknown filter", () => {
    expect(readActivityFilter(new URLSearchParams("type=bogus"))).toBe("all");
  });
});

describe("activityFilterToQuery", () => {
  it("emits nothing for the default filter", () => {
    expect(activityFilterToQuery("all")).toBe("");
  });

  it("emits the type param for a named filter", () => {
    expect(activityFilterToQuery("plans")).toBe("type=plans");
    expect(activityFilterToQuery("completions")).toBe("type=completions");
  });

  it("round-trips every known filter", () => {
    for (const filter of ACTIVITY_FILTERS) {
      const restored = readActivityFilter(new URLSearchParams(activityFilterToQuery(filter)));
      expect(restored).toBe(filter);
    }
  });
});

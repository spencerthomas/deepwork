import { describe, expect, it } from "vitest";

import { AGENT_FILTERS } from "./agents-url";
import { agentFilterToQuery, readAgentFilter } from "./agents-url";

describe("readAgentFilter", () => {
  it("defaults to 'all' when the query is empty", () => {
    expect(readAgentFilter(new URLSearchParams(""))).toBe("all");
  });

  it("reads each known filter", () => {
    for (const filter of AGENT_FILTERS) {
      expect(readAgentFilter(new URLSearchParams(`show=${filter}`))).toBe(filter);
    }
  });

  it("fails closed to 'all' for an unknown filter", () => {
    expect(readAgentFilter(new URLSearchParams("show=bogus"))).toBe("all");
  });
});

describe("agentFilterToQuery", () => {
  it("emits nothing for the default filter", () => {
    expect(agentFilterToQuery("all")).toBe("");
  });

  it("emits the show param for a named filter", () => {
    expect(agentFilterToQuery("active")).toBe("show=active");
  });

  it("round-trips every known filter", () => {
    for (const filter of AGENT_FILTERS) {
      expect(readAgentFilter(new URLSearchParams(agentFilterToQuery(filter)))).toBe(filter);
    }
  });
});

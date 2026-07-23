import { describe, expect, it } from "vitest";

import { activeAgentCount, deriveAgentCards } from "./agent-cards";
import { fixtureDemoStatus, normalizeDemoStatus } from "./demo-status";

describe("deriveAgentCards", () => {
  it("lists exactly the two real agents, in order", () => {
    const cards = deriveAgentCards(fixtureDemoStatus());
    expect(cards.map((card) => card.id)).toEqual(["local", "classic-langsmith"]);
  });

  it("marks the local runner active only when local_task_loop is available", () => {
    const [local, langsmith] = deriveAgentCards(fixtureDemoStatus());
    expect(local.state).toBe("active");
    expect(local.stateLabel).toBe("Active");
    expect(local.configureHref).toBe("/agents/local");
    expect(langsmith.state).toBe("gated");
    expect(langsmith.stateLabel).toBe("Gated");
    expect(langsmith.configureHref).toBeUndefined();
    expect(langsmith.gatedExplanation).toContain("unavailable in the local runtime");
  });

  it("shows unavailable, not active, when local_task_loop is reported unavailable", () => {
    const status = normalizeDemoStatus({
      mode: "fixture",
      evidence_class: "fixture",
      capabilities: [{ name: "local_task_loop", state: "unavailable" }],
      safe_reason: "reason",
    });
    const [local] = deriveAgentCards(status);
    expect(local.state).toBe("inactive");
    expect(local.stateLabel).toBe("Unavailable");
  });

  it("fails closed to unknown when no status is available", () => {
    const [local, langsmith] = deriveAgentCards(undefined);
    expect(local.state).toBe("unknown");
    expect(langsmith.state).toBe("unknown");
    expect(langsmith.stateLabel).toBe("Unknown");
    expect(activeAgentCount(deriveAgentCards(undefined))).toBe(0);
  });

  it("counts only truly active agents", () => {
    expect(activeAgentCount(deriveAgentCards(fixtureDemoStatus()))).toBe(1);
  });
});

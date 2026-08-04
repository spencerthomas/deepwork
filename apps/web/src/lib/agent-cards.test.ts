import { describe, expect, it } from "vitest";

import {
  activeAgentCount,
  agentRuntimeCopy,
  agentSessionTaskLabel,
  deriveAgentCards,
  deriveRegisteredAgentCards,
  mostRecentCreatedAt,
} from "./agent-cards";
import { fixtureDemoStatus, normalizeDemoStatus } from "./demo-status";
import type { TaskStatus, TaskSummary } from "./task-types";

function summary(id: string, createdAt?: string): TaskSummary {
  const status: TaskStatus = "completed";
  return { taskId: id, title: id, status, ...(createdAt ? { createdAt } : {}) };
}

describe("deriveAgentCards", () => {
  it("lists exactly the two real agents, in order", () => {
    const cards = deriveAgentCards(fixtureDemoStatus(), "fixture");
    expect(cards.map((card) => card.id)).toEqual(["local", "classic-langsmith"]);
  });

  it("marks the local runner active only when local_task_loop is available", () => {
    const [local, langsmith] = deriveAgentCards(fixtureDemoStatus(), "fixture");
    expect(local.name).toBe("In-browser fixture runner");
    expect(local.description).toContain("in-browser fixture adapter");
    expect(local.state).toBe("active");
    expect(local.stateLabel).toBe("Active");
    expect(local.configureHref).toBe("/agents/local");
    expect(langsmith.state).toBe("gated");
    expect(langsmith.stateLabel).toBe("Gated");
    expect(langsmith.configureHref).toBeUndefined();
    expect(langsmith.gatedExplanation).toContain("in-browser fixture reports sources unavailable");
  });

  it("shows unavailable, not active, when local_task_loop is reported unavailable", () => {
    const status = normalizeDemoStatus({
      mode: "fixture",
      evidence_class: "fixture",
      capabilities: [{ name: "local_task_loop", state: "unavailable" }],
      safe_reason: "reason",
    });
    const [local] = deriveAgentCards(status, "fixture");
    expect(local.state).toBe("inactive");
    expect(local.stateLabel).toBe("Unavailable");
  });

  it("fails closed to unknown when no status is available", () => {
    const [local, langsmith] = deriveAgentCards(undefined, "api");
    expect(local.state).toBe("unknown");
    expect(langsmith.state).toBe("unknown");
    expect(langsmith.stateLabel).toBe("Unknown");
    expect(activeAgentCount(deriveAgentCards(undefined, "api"))).toBe(0);
  });

  it("counts only truly active agents", () => {
    expect(activeAgentCount(deriveAgentCards(fixtureDemoStatus(), "fixture"))).toBe(1);
  });
});

describe("deriveRegisteredAgentCards", () => {
  it("projects the source registry in provider order without inventing agents", () => {
    const cards = deriveRegisteredAgentCards([
      {
        agentId: "agent-default",
        name: "Workspace generalist",
        description: "Plans and executes cross-functional work.",
        isDefault: true,
        createdAt: "2026-08-03T00:00:00Z",
        updatedAt: "2026-08-03T00:00:00Z",
      },
      {
        agentId: "agent-code",
        name: "Coding review",
        isDefault: false,
        createdAt: "2026-08-03T00:00:00Z",
        updatedAt: "2026-08-03T00:00:00Z",
      },
    ]);

    expect(cards.map((card) => card.id)).toEqual(["agent-default", "agent-code"]);
    expect(cards.map((card) => card.name)).toEqual(["Workspace generalist", "Coding review"]);
    expect(cards[0]).toMatchObject({
      agentId: "agent-default",
      state: "active",
      stateLabel: "Default",
      actionHref: "/settings/agents",
      actionLabel: "Manage",
    });
    expect(cards[1]).toMatchObject({
      agentId: "agent-code",
      state: "active",
      stateLabel: "Available",
    });
    expect(cards[1].description).toContain("registered on the connected task source");
  });

  it("returns no cards when the registry contains no agents", () => {
    expect(deriveRegisteredAgentCards([])).toEqual([]);
  });
});

describe("agentSessionTaskLabel", () => {
  it("reports loading while the task list is being fetched", () => {
    expect(agentSessionTaskLabel(true, 0)).toBe("Loading tasks…");
    // Loading takes precedence over a stale count or error.
    expect(agentSessionTaskLabel(true, 3, "boom")).toBe("Loading tasks…");
  });

  it("never fabricates a zero count when the task-list fetch failed", () => {
    expect(agentSessionTaskLabel(false, 0, "network error")).toBe("Task count unavailable");
    // Even a non-empty stale list is reported as unavailable on refresh failure.
    expect(agentSessionTaskLabel(false, 4, "network error")).toBe("Task count unavailable");
  });

  it("pluralizes the honest task count", () => {
    expect(agentSessionTaskLabel(false, 0)).toBe("0 tasks this session");
    expect(agentSessionTaskLabel(false, 1)).toBe("1 task this session");
    expect(agentSessionTaskLabel(false, 2)).toBe("2 tasks this session");
  });

  it("never infers a deterministic runner or provider state in API mode", () => {
    const status = normalizeDemoStatus({
      mode: "fixture",
      evidence_class: "fixture",
      capabilities: [
        { name: "local_task_loop", state: "available" },
        { name: "sources", state: "unavailable" },
      ],
      safe_reason: "Fixture capability response.",
    });
    const [runner, deployment] = deriveAgentCards(status, "api");
    const copy = agentRuntimeCopy("api");
    const apiText = [
      runner.name,
      runner.description,
      deployment.gatedExplanation,
      copy.fleetDescription,
      copy.contractDescription,
      copy.executionDetail,
      copy.contractFooter,
    ].join(" ");

    expect(runner.name).toBe("API task runner");
    expect(apiText).toContain("backend runner");
    expect(apiText).not.toMatch(/deterministic|embedded|no external providers/i);
  });
});

describe("mostRecentCreatedAt", () => {
  it("is undefined when no task carries a parseable timestamp", () => {
    expect(mostRecentCreatedAt([])).toBeUndefined();
    expect(mostRecentCreatedAt([summary("a"), summary("b", "not-a-date")])).toBeUndefined();
  });

  it("returns the newest createdAt, ignoring order and unparseable values", () => {
    const tasks = [
      summary("older", "2026-07-24T10:00:00.000Z"),
      summary("newest", "2026-07-24T12:00:00.000Z"),
      summary("bad", "nonsense"),
      summary("middle", "2026-07-24T11:00:00.000Z"),
    ];
    expect(mostRecentCreatedAt(tasks)).toBe("2026-07-24T12:00:00.000Z");
  });
});

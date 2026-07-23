import { describe, expect, it } from "vitest";

import { taskRuntimePresentation } from "./task-runtime-presentation";

function renderedCopy(copy: ReturnType<typeof taskRuntimePresentation>): string {
  return Object.values(copy).join("\n");
}

describe("taskRuntimePresentation", () => {
  it("labels fixture task surfaces as deterministic and in-browser", () => {
    const copy = taskRuntimePresentation("fixture");
    const text = renderedCopy(copy);

    expect(copy.runnerName).toBe("In-browser fixture runner");
    expect(text).toMatch(/deterministic/i);
    expect(text).toMatch(/in-browser fixture/i);
    expect(text).toMatch(/no external providers/i);
    expect(copy.runEventSource).not.toMatch(/api/i);
  });

  it("does not infer an API runner, provider state, or local deployment", () => {
    const copy = taskRuntimePresentation("api", "https://deepwork.example.test");
    const text = renderedCopy(copy);

    expect(copy.runnerName).toBe("Configured API task runner");
    expect(copy.settingsConnectionTarget).toBe("https://deepwork.example.test");
    expect(text).toContain("server-side runner and provider configuration remain unknown");
    expect(text).toContain("Server-side retention is not inferred");
    expect(text).not.toMatch(
      /local (?:api|agent|runner|runtime)|deterministic (?:api|runner)|embedded|no external providers|providers? (?:are|is) unavailable/i,
    );
  });

  it("keeps API task, approval, activity, run-panel, command, and settings copy fail closed", () => {
    const copy = taskRuntimePresentation("api");
    const surfaces = [
      copy.newTaskDescription,
      copy.sourceSelectionDescription,
      copy.commandNewTaskHint,
      copy.approvalsDescription,
      copy.activityDescription,
      copy.inboxDescription,
      copy.runEventSource,
      copy.runFilesDescription,
      copy.runFooter,
      copy.settingsStatusSourceDescription,
    ].join("\n");

    expect(surfaces).toContain("configured API");
    expect(surfaces).toMatch(/unknown|not inferred|not established/i);
    expect(surfaces).not.toMatch(/deterministic|embedded|local runner|local API/i);
    expect(copy.settingsModeDescription).toContain(
      "fixture selects a deterministic in-browser adapter",
    );
  });
});

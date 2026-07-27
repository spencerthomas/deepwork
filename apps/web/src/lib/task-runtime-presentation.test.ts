import { describe, expect, it } from "vitest";

import { taskRuntimePresentation } from "./task-runtime-presentation";

function renderedCopy(copy: ReturnType<typeof taskRuntimePresentation>): string {
  return Object.values(copy).join("\n");
}

// Language the interface must never surface to a user: it describes plumbing,
// not the person or their task.
const SYSTEMS_JARGON =
  /client adapter|client transport|dispatch target|interruption|provider configuration|server-side (?:execution|retention)|fixture runner|deterministic in-browser|not inferred|no external providers/i;

describe("taskRuntimePresentation", () => {
  it("speaks to the user and the task, without systems jargon (connected)", () => {
    const copy = taskRuntimePresentation("api", "https://deepwork.example.test");
    const text = renderedCopy(copy);

    expect(text).not.toMatch(SYSTEMS_JARGON);
    expect(copy.newTaskDescription).toMatch(/describe what you want/i);
    expect(copy.approvalsDescription).toMatch(/you decide|go-ahead/i);
    expect(copy.commandNewTaskHint).toBe("Start a task");
    // The workspace address is still shown verbatim in settings.
    expect(copy.settingsConnectionTarget).toBe("https://deepwork.example.test");
  });

  it("uses plain demo language in demo mode", () => {
    const copy = taskRuntimePresentation("fixture");
    const text = renderedCopy(copy);

    expect(text).not.toMatch(SYSTEMS_JARGON);
    expect(text).toMatch(/demo/i);
    expect(copy.taskOriginLabel).toBe("Demo");
  });

  it("describes the task the same plain way regardless of mode", () => {
    expect(taskRuntimePresentation("api").newTaskDescription).toBe(
      taskRuntimePresentation("fixture").newTaskDescription,
    );
    expect(taskRuntimePresentation("api").approvalsDescription).toBe(
      taskRuntimePresentation("fixture").approvalsDescription,
    );
  });
});

import { describe, expect, it } from "vitest";

import { artifactDownloadHref, buildTaskArtifacts } from "./task-artifacts";

describe("task artifacts", () => {
  it("derives result and evidence downloads from retained API records", () => {
    const artifacts = buildTaskArtifacts(
      {
        taskId: "task_00000001",
        runId: "run_00000001",
        title: "Prepare a brief",
        objective: "Prepare a brief",
        status: "completed",
        result: "# Useful result",
      },
      [
        {
          evidenceId: "evidence_00000001",
          kind: "fixture",
          source: "local-runner",
          summary: "Bounded local evidence.",
          verified: false,
        },
      ],
    );

    expect(artifacts.map((artifact) => artifact.name)).toEqual([
      "result.md",
      "evidence-evidence_00000001.json",
    ]);
    expect(artifactDownloadHref(artifacts[0])).toContain("%23%20Useful%20result");
    expect(artifacts[1].content).toContain('"taskId": "task_00000001"');
    expect(artifacts[1].content).toContain('"runId": "run_00000001"');
    expect(artifacts[1].content).toContain('"objective": "Prepare a brief"');
    expect(artifacts[1].content).toContain('"verified": false');
  });
});

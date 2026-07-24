import { describe, expect, it } from "vitest";

import { formatResultBrief } from "./result-brief";
import type { EvidenceRecord } from "./task-types";

const evidence: EvidenceRecord[] = [
  {
    evidenceId: "evidence_00000001",
    kind: "citation",
    source: "fixture://demo",
    summary: "Reviewed the bounded request.",
    verified: true,
  },
  {
    evidenceId: "evidence_00000002",
    kind: "note",
    source: "fixture://demo",
    summary: "Left an unverified follow-up.",
    verified: false,
  },
];

describe("formatResultBrief", () => {
  it("includes the title, prompt, result, and evidence with verification status", () => {
    const brief = formatResultBrief({
      title: "Draft the launch note",
      prompt: "Write a short launch note.",
      result: "The launch note is ready.",
      evidence,
    });

    expect(brief).toContain("# Draft the launch note");
    expect(brief).toContain("## Prompt\n\nWrite a short launch note.");
    expect(brief).toContain("## Result\n\nThe launch note is ready.");
    expect(brief).toContain(
      "- [verified] citation · fixture://demo — Reviewed the bounded request.",
    );
    expect(brief).toContain("- [unverified] note · fixture://demo — Left an unverified follow-up.");
    expect(brief.endsWith("\n")).toBe(true);
  });

  it("omits the evidence section when there is no evidence", () => {
    const brief = formatResultBrief({
      title: "No evidence task",
      prompt: "Just answer.",
      result: "Answered.",
      evidence: [],
    });

    expect(brief).not.toContain("## Evidence");
  });

  it("omits the prompt section when no prompt is present and trims whitespace", () => {
    const brief = formatResultBrief({
      title: "  Trimmed title  ",
      result: "  A result.  ",
      evidence: [],
    });

    expect(brief).toContain("# Trimmed title");
    expect(brief).not.toContain("## Prompt");
    expect(brief).toContain("## Result\n\nA result.");
  });

  it("falls back to safe placeholders for an empty title and missing result", () => {
    const brief = formatResultBrief({ title: "", evidence: [] });

    expect(brief).toContain("# Task result");
    expect(brief).toContain("## Result\n\n_No result was produced._");
  });
});

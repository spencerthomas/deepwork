import type { EvidenceRecord } from "./task-types";

export interface ResultBriefInput {
  title: string;
  prompt?: string;
  result?: string;
  evidence: EvidenceRecord[];
}

/**
 * Render a completed task's deep-work output as a portable Markdown brief:
 * the originating prompt, the result text, and the evidence the run recorded.
 *
 * Kept pure and deterministic so the copy/export controls can be unit-tested
 * and the same brief can back both clipboard copy and any future download.
 */
export function formatResultBrief(input: ResultBriefInput): string {
  const sections: string[] = [`# ${input.title.trim() || "Task result"}`];

  const prompt = input.prompt?.trim();
  if (prompt) {
    sections.push(`## Prompt\n\n${prompt}`);
  }

  const result = input.result?.trim();
  sections.push(`## Result\n\n${result || "_No result was produced._"}`);

  if (input.evidence.length > 0) {
    const lines = input.evidence.map((record) => {
      const status = record.verified ? "verified" : "unverified";
      return `- [${status}] ${record.kind} · ${record.source} — ${record.summary}`;
    });
    sections.push(`## Evidence\n\n${lines.join("\n")}`);
  }

  return `${sections.join("\n\n")}\n`;
}

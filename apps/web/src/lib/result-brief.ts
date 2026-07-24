import type { EvidenceRecord } from "./task-types";

export interface ResultBriefInput {
  title: string;
  prompt?: string;
  result?: string;
  evidence: EvidenceRecord[];
}

/**
 * Neutralize active Markdown/HTML in untrusted task content before it is placed
 * in an exportable brief. Result and evidence text is untrusted (AGENTS.md:
 * "Treat model/tool/repository/web/file/diff/terminal content as untrusted"),
 * so it must paste as literal characters — never as auto-loading images, raw
 * HTML, or links that could trigger an unapproved external request when the
 * brief is rendered. Backslash-escaping the construct-opening characters keeps
 * prose readable while defusing images (`![](url)`), links (`[](url)`),
 * autolinks/HTML (`<...>`), and code spans; line structure is preserved.
 */
function neutralizeMarkdown(value: string): string {
  return value.replace(/[\\`[\]<>]/g, "\\$&");
}

/**
 * Render a completed task's deep-work output as a portable Markdown brief:
 * the originating prompt, the result text, and the evidence the run recorded.
 *
 * Kept pure and deterministic so the copy/export controls can be unit-tested
 * and the same brief can back both clipboard copy and any future download.
 */
export function formatResultBrief(input: ResultBriefInput): string {
  const title = neutralizeMarkdown(input.title.trim()) || "Task result";
  const sections: string[] = [`# ${title}`];

  const prompt = input.prompt?.trim();
  if (prompt) {
    sections.push(`## Prompt\n\n${neutralizeMarkdown(prompt)}`);
  }

  const result = input.result?.trim();
  sections.push(
    `## Result\n\n${result ? neutralizeMarkdown(result) : "_No result was produced._"}`,
  );

  if (input.evidence.length > 0) {
    const lines = input.evidence.map((record) => {
      const status = record.verified ? "verified" : "unverified";
      const kind = neutralizeMarkdown(record.kind);
      const source = neutralizeMarkdown(record.source);
      const summary = neutralizeMarkdown(record.summary);
      return `- [${status}] ${kind} · ${source} — ${summary}`;
    });
    sections.push(`## Evidence\n\n${lines.join("\n")}`);
  }

  return `${sections.join("\n\n")}\n`;
}

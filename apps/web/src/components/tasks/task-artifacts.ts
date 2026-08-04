import type { EvidenceRecord, TaskDetail } from "@/lib/task-types";

export interface TaskArtifact {
  id: string;
  name: string;
  kind: "result" | "evidence";
  description: string;
  mimeType: "text/markdown" | "application/json";
  content: string;
}

function safeSegment(value: string): string {
  const segment = value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9._-]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return segment || "record";
}

/** Build downloadable artifacts only from result/evidence returned by the task API. */
export function buildTaskArtifacts(
  detail: TaskDetail | undefined,
  evidence: readonly EvidenceRecord[],
): TaskArtifact[] {
  const artifacts: TaskArtifact[] = [];
  if (detail?.result?.trim()) {
    artifacts.push({
      id: `${detail.taskId}:result`,
      name: "result.md",
      kind: "result",
      description: "The retained task result in portable Markdown.",
      mimeType: "text/markdown",
      content: detail.result,
    });
  }
  for (const record of evidence) {
    artifacts.push({
      id: record.evidenceId,
      name: `evidence-${safeSegment(record.evidenceId)}.json`,
      kind: "evidence",
      description: record.summary,
      mimeType: "application/json",
      content: JSON.stringify(
        {
          taskId: detail?.taskId ?? null,
          runId: detail?.runId ?? null,
          objective: detail?.prompt ?? null,
          evidence: record,
        },
        null,
        2,
      ),
    });
  }
  return artifacts;
}

export function artifactDownloadHref(artifact: TaskArtifact): string {
  return `data:${artifact.mimeType};charset=utf-8,${encodeURIComponent(artifact.content)}`;
}

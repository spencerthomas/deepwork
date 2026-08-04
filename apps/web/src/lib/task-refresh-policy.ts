import { isTerminalStatus } from "./task-normalizers";
import type { TaskDetail, TaskSummary } from "./task-types";

export const AUTHORITATIVE_SILENCE_THRESHOLD_MS = 4_000;

export function sameTaskSummaryProjection(current: TaskSummary, incoming: TaskSummary): boolean {
  return (
    current.status === incoming.status &&
    current.lastEventId === incoming.lastEventId &&
    current.updatedAt === incoming.updatedAt
  );
}

export function sameTaskDetailProjection(current: TaskDetail, incoming: TaskDetail): boolean {
  return (
    sameTaskSummaryProjection(current, incoming) &&
    current.result === incoming.result &&
    current.pendingInterrupt?.interruptId === incoming.pendingInterrupt?.interruptId &&
    current.pendingInterrupt?.planRevision === incoming.pendingInterrupt?.planRevision &&
    current.pendingInterrupt?.version === incoming.pendingInterrupt?.version &&
    current.proposedPlan?.revision === incoming.proposedPlan?.revision
  );
}

export function shouldRefreshAuthoritativeTask(
  current: TaskDetail | undefined,
  {
    inFlight,
    silentForMs,
  }: {
    inFlight: boolean;
    silentForMs: number;
  },
): boolean {
  if (inFlight || silentForMs < AUTHORITATIVE_SILENCE_THRESHOLD_MS) return false;
  if (!current) return true;
  return current.status !== "waiting-approval" && !isTerminalStatus(current.status);
}

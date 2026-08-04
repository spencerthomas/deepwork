import type { TaskCreateFailureKind } from "./task-create-outcome";

export type ComposerDispatchPhase =
  | "editing"
  | "submitting"
  | "reconciling"
  | "outcome-unknown"
  | "rejected"
  | "conflict";

export function nextComposerDispatchPhase(
  current: ComposerDispatchPhase,
  outcome: TaskCreateFailureKind,
): ComposerDispatchPhase {
  if (outcome === "rejected") return "rejected";
  if (outcome === "conflict") return "conflict";
  if (current === "submitting") return "reconciling";
  return "outcome-unknown";
}

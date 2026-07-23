import type { TaskStatus } from "@/lib/task-types";
import { cn } from "@/lib/utils";

interface ChipStyle {
  dot: string;
  text: string;
  bg: string;
  label: string;
  breathe?: boolean;
}

const styles: Record<TaskStatus, ChipStyle> = {
  queued: {
    dot: "bg-status-queued",
    text: "text-status-queued",
    bg: "bg-status-queued-bg",
    label: "Queued",
  },
  running: {
    dot: "bg-status-running",
    text: "text-status-running",
    bg: "bg-status-running-bg",
    label: "Running",
    breathe: true,
  },
  "waiting-approval": {
    dot: "bg-status-review",
    text: "text-status-review",
    bg: "bg-status-review-bg",
    label: "Needs review",
  },
  completed: {
    dot: "bg-status-done",
    text: "text-status-done",
    bg: "bg-status-done-bg",
    label: "Done",
  },
  rejected: {
    dot: "bg-status-failed",
    text: "text-status-failed",
    bg: "bg-status-failed-bg",
    label: "Rejected",
  },
  failed: {
    dot: "bg-status-failed",
    text: "text-status-failed",
    bg: "bg-status-failed-bg",
    label: "Failed",
  },
  cancelled: {
    dot: "bg-status-neutral",
    text: "text-status-neutral",
    bg: "bg-status-neutral-bg",
    label: "Cancelled",
  },
  unknown: {
    dot: "bg-status-neutral",
    text: "text-status-neutral",
    bg: "bg-status-neutral-bg",
    label: "Unknown",
  },
};

export function statusChipLabel(status: TaskStatus): string {
  return styles[status].label;
}

export function StatusChip({ status, className }: { status: TaskStatus; className?: string }) {
  const s = styles[status];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium",
        s.bg,
        s.text,
        className,
      )}
    >
      <span className={cn("size-1.5 rounded-full", s.dot, s.breathe && "breathe")} aria-hidden />
      {s.label}
    </span>
  );
}

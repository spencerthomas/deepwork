import type { CapabilityState } from "@/lib/demo-status";
import { cn } from "@/lib/utils";

interface ChipStyle {
  bg: string;
  dot: string;
  label: string;
  text: string;
}

const styles: Record<CapabilityState, ChipStyle> = {
  available: {
    bg: "bg-status-done-bg",
    dot: "bg-status-done",
    label: "Available",
    text: "text-status-done",
  },
  unavailable: {
    bg: "bg-status-review-bg",
    dot: "bg-status-review",
    label: "Unavailable",
    text: "text-status-review",
  },
  unknown: {
    bg: "bg-status-neutral-bg",
    dot: "bg-status-neutral",
    label: "Unknown",
    text: "text-status-neutral",
  },
};

/** Amber/green/neutral chip for a reported capability state. Never fabricates. */
export function CapabilityChip({
  state,
  label,
  className,
}: {
  state: CapabilityState;
  label?: string;
  className?: string;
}) {
  const s = styles[state];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium",
        s.bg,
        s.text,
        className,
      )}
    >
      <span className={cn("size-1.5 rounded-full", s.dot)} aria-hidden />
      {label ?? s.label}
    </span>
  );
}

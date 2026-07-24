"use client";

import { RotateCcw } from "lucide-react";
import { useRouter } from "next/navigation";

import { useTasksStore } from "@/lib/tasks-store";
import { cn } from "@/lib/utils";

/**
 * Re-dispatch a terminal task: create a fresh task from the same prompt and
 * navigate to it. Lets a user retry a failed/rejected run or run a completed
 * one again without retyping. Reuses the shared createTask flow — no backend
 * change — and mirrors the dispatch → navigate behavior of the New task form.
 */
export function RerunTaskButton({ prompt }: { prompt: string }) {
  const router = useRouter();
  const { createTask, creating } = useTasksStore();

  async function rerun() {
    const created = await createTask(prompt);
    if (created) {
      router.push(`/tasks/${created.taskId}`);
    }
  }

  return (
    <button
      type="button"
      disabled={creating}
      onClick={() => void rerun()}
      title="Start a new task from this prompt"
      className={cn(
        "flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-1.5 text-[13px] font-medium text-foreground/80 transition-colors hover:bg-accent",
        creating && "pointer-events-none opacity-60",
      )}
    >
      <RotateCcw className="size-3.5" />
      {creating ? "Starting…" : "Run again"}
    </button>
  );
}

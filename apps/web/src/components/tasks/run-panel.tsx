"use client";

import { Activity, ListChecks, ShieldCheck, X } from "lucide-react";
import { useState } from "react";

import { StatusChip } from "@/components/shell/status-chip";
import type {
  ClientMode,
  ConnectionState,
  EvidenceRecord,
  ProposedPlan,
  TaskDetail,
  TaskEvent,
  TaskSummary,
} from "@/lib/task-types";
import { taskRuntimePresentation } from "@/lib/task-runtime-presentation";
import { cn } from "@/lib/utils";

type PanelTab = "status" | "stream" | "evidence" | "files" | "git" | "trace";

const tabs: { key: PanelTab; label: string }[] = [
  { key: "status", label: "Status" },
  { key: "stream", label: "Stream" },
  { key: "evidence", label: "Evidence" },
  { key: "files", label: "Files" },
  { key: "git", label: "Git" },
  { key: "trace", label: "Trace" },
];

const eventLabels: Record<string, string> = {
  "task.created": "Task created",
  "run.started": "Run started",
  "content.delta": "Narration",
  "plan.proposed": "Plan proposed",
  "plan.updated": "Plan updated",
  "evidence.recorded": "Evidence recorded",
  "interrupt.requested": "Approval requested",
  "decision.recorded": "Decision recorded",
  "run.completed": "Run completed",
};

function connectionLabel(state: ConnectionState): string {
  switch (state) {
    case "connecting":
      return "Connecting to run";
    case "connected":
      return "Live";
    case "reconnecting":
      return "Reconnecting";
    default:
      return "Stream closed";
  }
}

function UnavailableTab({ title, body }: { title: string; body: string }) {
  return (
    <div className="px-4 py-8 text-center">
      <p className="text-sm font-medium">{title}</p>
      <p className="mx-auto mt-1 max-w-[26ch] text-[13px] leading-relaxed text-muted-foreground">
        {body}
      </p>
      <span className="mt-3 inline-flex items-center gap-1.5 rounded-full bg-status-review-bg px-2.5 py-1 text-xs font-medium text-status-review">
        Unavailable in this client
      </span>
    </div>
  );
}

export function RunPanel({
  selected,
  detail,
  events,
  evidence,
  plan,
  connectionState,
  mode,
  onClose,
}: {
  selected: TaskSummary;
  detail?: TaskDetail;
  events: readonly TaskEvent[];
  evidence: readonly EvidenceRecord[];
  plan?: ProposedPlan;
  connectionState: ConnectionState;
  mode: ClientMode;
  onClose: () => void;
}) {
  const [tab, setTab] = useState<PanelTab>("status");
  const runtimeCopy = taskRuntimePresentation(mode);

  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden rounded-2xl border border-border bg-card">
      <div className="flex items-center gap-1 overflow-x-auto border-b border-border px-2 no-scrollbar">
        {tabs.map((t) => (
          <button
            key={t.key}
            type="button"
            onClick={() => setTab(t.key)}
            className={cn(
              "relative shrink-0 px-2.5 py-2.5 text-[13px] transition-colors",
              tab === t.key
                ? "text-crisp text-foreground"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            {t.label}
            {tab === t.key && (
              <span className="absolute inset-x-2 -bottom-px h-0.5 rounded-full bg-brand" />
            )}
          </button>
        ))}
        <button
          type="button"
          onClick={onClose}
          aria-label="Close panel"
          className="ml-auto flex size-7 shrink-0 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
        >
          <X className="size-4" />
        </button>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto">
        {tab === "status" && (
          <div className="space-y-4 px-4 py-4">
            <div className="flex items-center gap-2">
              <StatusChip status={detail?.status ?? selected.status} />
              <span
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium",
                  connectionState === "connected"
                    ? "bg-status-running-bg text-status-running"
                    : "bg-muted text-muted-foreground",
                )}
              >
                <span
                  className={cn(
                    "size-1.5 rounded-full",
                    connectionState === "connected"
                      ? "breathe bg-status-running"
                      : "bg-muted-foreground",
                  )}
                  aria-hidden
                />
                {connectionLabel(connectionState)}
              </span>
            </div>
            <dl className="space-y-2 text-[13px]">
              <div className="flex justify-between gap-3">
                <dt className="text-muted-foreground">Task</dt>
                <dd className="truncate font-mono text-xs">{selected.taskId}</dd>
              </div>
              {selected.runId && (
                <div className="flex justify-between gap-3">
                  <dt className="text-muted-foreground">Run</dt>
                  <dd className="truncate font-mono text-xs">{selected.runId}</dd>
                </div>
              )}
              <div className="flex justify-between gap-3">
                <dt className="text-muted-foreground">{runtimeCopy.taskConnectionLabel}</dt>
                <dd>{runtimeCopy.taskOriginLabel}</dd>
              </div>
              <div className="flex justify-between gap-3">
                <dt className="text-muted-foreground">Events</dt>
                <dd className="tabular-nums">{events.length}</dd>
              </div>
            </dl>
            {plan && (
              <div>
                <p className="label-caps mb-2 flex items-center gap-1.5 text-muted-foreground">
                  <ListChecks className="size-3.5" /> Plan · rev {plan.revision}
                </p>
                <ol className="space-y-1.5">
                  {plan.steps.map((step, index) => (
                    <li
                      key={`${String(plan.revision)}-${String(index)}`}
                      className="flex gap-2 text-[13px] leading-relaxed"
                    >
                      <span className="mt-0.5 font-mono text-[11px] tabular-nums text-muted-foreground">
                        {index + 1}.
                      </span>
                      <span className="text-foreground/85">{step}</span>
                    </li>
                  ))}
                </ol>
              </div>
            )}
          </div>
        )}

        {tab === "stream" && (
          <div className="px-2 py-2">
            {events.length === 0 ? (
              <p className="px-2 py-8 text-center text-[13px] text-muted-foreground">
                Waiting for the first event…
              </p>
            ) : (
              <ol className="space-y-0.5">
                {events.map((event) => (
                  <li
                    key={event.id}
                    className="flex items-baseline gap-2.5 rounded-lg px-2 py-1.5 hover:bg-accent/40"
                  >
                    <span className="shrink-0 font-mono text-[11px] tabular-nums text-muted-foreground">
                      #{event.id}
                    </span>
                    <span className="shrink-0 rounded-md bg-muted px-1.5 py-0.5 font-mono text-[11px] text-foreground/70">
                      {event.name}
                    </span>
                    <span className="min-w-0 truncate text-[12px] text-muted-foreground">
                      {eventLabels[event.name] ?? event.name}
                    </span>
                  </li>
                ))}
              </ol>
            )}
            <p className="border-t border-border px-2 py-2 text-[11px] text-muted-foreground">
              {events.length} events · {runtimeCopy.runEventSource}
            </p>
          </div>
        )}

        {tab === "evidence" && (
          <div className="space-y-3 px-4 py-4">
            {evidence.length === 0 ? (
              <div className="py-6 text-center">
                <ShieldCheck className="mx-auto size-5 text-muted-foreground" />
                <p className="mt-2 text-[13px] leading-relaxed text-muted-foreground">
                  No evidence recorded yet. A result is not considered verified without explicit
                  evidence.
                </p>
              </div>
            ) : (
              evidence.map((record) => (
                <div key={record.evidenceId} className="rounded-xl border border-border p-3">
                  <div className="flex items-center gap-2">
                    <span className="rounded-md bg-muted px-1.5 py-0.5 font-mono text-[11px]">
                      {record.kind}
                    </span>
                    <span
                      className={cn(
                        "rounded-full px-2 py-0.5 text-[11px] font-medium",
                        record.verified
                          ? "bg-status-done-bg text-status-done"
                          : "bg-status-review-bg text-status-review",
                      )}
                    >
                      {record.verified ? "Verified" : "Not independently verified"}
                    </span>
                  </div>
                  <p className="mt-2 text-[13px] leading-relaxed text-foreground/90">
                    {record.summary}
                  </p>
                  <p className="mt-1.5 font-mono text-[11px] text-muted-foreground">
                    {record.source} · {record.evidenceId}
                  </p>
                </div>
              ))
            )}
          </div>
        )}

        {tab === "files" && (
          <UnavailableTab title="No file workspace" body={runtimeCopy.runFilesDescription} />
        )}
        {tab === "git" && (
          <UnavailableTab
            title="No repository attached"
            body="Branches, commits, and draft PRs appear here when a coding task runs against a connected repository."
          />
        )}
        {tab === "trace" && (
          <UnavailableTab
            title="No trace backend"
            body="Run traces link out to your observability platform when an external source executes the task."
          />
        )}
      </div>

      <div className="border-t border-border px-4 py-2">
        <p className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
          <Activity className="size-3" aria-hidden />
          {runtimeCopy.runFooter}
        </p>
      </div>
    </div>
  );
}

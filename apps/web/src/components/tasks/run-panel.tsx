"use client";

import {
  Activity,
  Download,
  ExternalLink,
  FileJson,
  FileText,
  ListChecks,
  Route,
  ShieldCheck,
  X,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { StatusChip } from "@/components/shell/status-chip";
import {
  ACTIVITY_FILTERS,
  ACTIVITY_FILTER_LABELS,
  eventDetailText,
  eventMatchesActivityFilter,
  type ActivityFilter,
} from "@/components/activity/activity-model";
import { nextPanelTab, PANEL_TABS, type PanelTab } from "@/components/tasks/run-panel-tabs";
import { panelTabToQuery, readPanelTab } from "@/components/tasks/run-panel-url";
import { artifactDownloadHref, buildTaskArtifacts } from "@/components/tasks/task-artifacts";
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

const eventLabels: Record<string, string> = {
  "task.created": "Task created",
  "run.started": "Run started",
  "content.delta": "Narration",
  "plan.proposed": "Plan proposed",
  "plan.updated": "Plan updated",
  "evidence.recorded": "Sources recorded",
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
  const [streamFilter, setStreamFilter] = useState<ActivityFilter>("all");
  const [trace, setTrace] = useState<{
    state: "loading" | "available" | "unavailable";
    url?: string;
  }>({
    state: "loading",
  });
  useEffect(() => {
    if (tab !== "trace") return;
    let cancelled = false;
    setTrace({ state: "loading" });
    fetch(`/api/v1/tasks/${encodeURIComponent(selected.taskId)}/trace`)
      .then(async (response) => {
        if (cancelled) return;
        const body = response.ok ? await response.json() : null;
        if (body?.state === "available" && typeof body.traceUrl === "string") {
          setTrace({ state: "available", url: body.traceUrl });
        } else {
          setTrace({ state: "unavailable" });
        }
      })
      .catch(() => {
        if (!cancelled) setTrace({ state: "unavailable" });
      });
    return () => {
      cancelled = true;
    };
  }, [tab, selected.taskId]);
  const tabRefs = useRef<Partial<Record<PanelTab, HTMLButtonElement | null>>>({});
  const runtimeCopy = taskRuntimePresentation(mode);

  // Narrow the Stream tab's event list to one kind (plans, evidence, …) using
  // the same filter vocabulary as the Activity feed. Session-local; the full,
  // unfiltered event history is always one click ("All") away.
  const visibleStreamEvents = useMemo(
    () => events.filter((event) => eventMatchesActivityFilter(event.name, streamFilter)),
    [events, streamFilter],
  );
  const artifacts = useMemo(
    () =>
      tab === "files"
        ? buildTaskArtifacts(detail, evidence).map((artifact) => ({
            ...artifact,
            downloadHref: artifactDownloadHref(artifact),
          }))
        : [],
    [detail?.result, detail?.taskId, evidence, tab],
  );

  // Reflect the active tab in the URL so a task's Evidence, Stream, or Trace
  // view is deep-linkable and survives a refresh or reopening the panel — the
  // same URL-restore contract the inbox and queues use. Other params on the
  // task-detail URL are preserved.
  const selectTab = useCallback((next: PanelTab) => {
    setTab((current) => {
      if (current === next) return current;
      const { pathname, search } = window.location;
      const query = panelTabToQuery(next, new URLSearchParams(search));
      window.history.pushState(window.history.state, "", query ? `${pathname}?${query}` : pathname);
      return next;
    });
  }, []);

  useEffect(() => {
    const syncFromUrl = () => setTab(readPanelTab(new URLSearchParams(window.location.search)));
    syncFromUrl();
    window.addEventListener("popstate", syncFromUrl);
    return () => window.removeEventListener("popstate", syncFromUrl);
  }, []);

  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden rounded-2xl border border-border bg-card">
      <div className="flex items-center gap-1 border-b border-border px-2">
        <div
          role="tablist"
          aria-label="Run details"
          aria-orientation="horizontal"
          className="flex items-center gap-1 overflow-x-auto no-scrollbar"
          onKeyDown={(event) => {
            const next = nextPanelTab(tab, event.key);
            if (next === null) return;
            event.preventDefault();
            selectTab(next);
            tabRefs.current[next]?.focus();
          }}
        >
          {PANEL_TABS.map((t) => {
            const isActive = tab === t.key;
            return (
              <button
                key={t.key}
                ref={(element) => {
                  tabRefs.current[t.key] = element;
                }}
                type="button"
                role="tab"
                id={`run-tab-${t.key}`}
                aria-selected={isActive}
                // Only the active tab's panel is rendered, so only it claims the
                // controls relationship; inactive tabs must not point at the
                // active tab's panel.
                aria-controls={isActive ? "run-tabpanel" : undefined}
                tabIndex={isActive ? 0 : -1}
                onClick={() => selectTab(t.key)}
                className={cn(
                  "relative shrink-0 px-2.5 py-2.5 text-[13px] transition-colors",
                  isActive
                    ? "text-crisp text-foreground"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                {t.label}
                {isActive && (
                  <span className="absolute inset-x-2 -bottom-px h-0.5 rounded-full bg-brand" />
                )}
              </button>
            );
          })}
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close panel"
          className="ml-auto flex size-7 shrink-0 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
        >
          <X className="size-4" />
        </button>
      </div>

      <div
        role="tabpanel"
        id="run-tabpanel"
        aria-labelledby={`run-tab-${tab}`}
        tabIndex={0}
        className="min-h-0 flex-1 overflow-y-auto focus:outline-none"
      >
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
              {selected.agentId && (
                <div className="flex justify-between gap-3">
                  <dt className="text-muted-foreground">Agent</dt>
                  <dd className="truncate font-mono text-xs">{selected.agentId}</dd>
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
            {events.length > 0 && (
              <div
                role="group"
                aria-label="Filter stream events"
                className="mb-2 flex flex-wrap items-center gap-1 px-1"
              >
                {ACTIVITY_FILTERS.map((option) => {
                  const active = streamFilter === option;
                  return (
                    <button
                      key={option}
                      type="button"
                      aria-pressed={active}
                      onClick={() => setStreamFilter(option)}
                      className={cn(
                        "rounded-full px-2.5 py-1 text-[12px] transition-colors",
                        active
                          ? "bg-accent text-foreground"
                          : "text-muted-foreground hover:bg-accent/50 hover:text-foreground",
                      )}
                    >
                      {ACTIVITY_FILTER_LABELS[option]}
                    </button>
                  );
                })}
              </div>
            )}
            {events.length === 0 ? (
              <p className="px-2 py-8 text-center text-[13px] text-muted-foreground">
                Waiting for the first event…
              </p>
            ) : visibleStreamEvents.length === 0 ? (
              <p className="px-2 py-8 text-center text-[13px] text-muted-foreground">
                No {ACTIVITY_FILTER_LABELS[streamFilter].toLowerCase()} in this run yet.
              </p>
            ) : (
              <ol className="space-y-0.5">
                {visibleStreamEvents.map((event) => {
                  const detail = eventDetailText(event);
                  return (
                    <li key={event.id} className="rounded-lg px-2 py-1.5 hover:bg-accent/40">
                      <div className="flex items-baseline gap-2.5">
                        <span className="shrink-0 font-mono text-[11px] tabular-nums text-muted-foreground">
                          #{event.id}
                        </span>
                        <span className="shrink-0 rounded-md bg-muted px-1.5 py-0.5 font-mono text-[11px] text-foreground/70">
                          {event.name}
                        </span>
                        <span className="min-w-0 truncate text-[12px] text-muted-foreground">
                          {eventLabels[event.name] ?? event.name}
                        </span>
                      </div>
                      {detail !== undefined && (
                        <p className="mt-1 ml-1.5 border-l border-border pl-2.5 text-[12px] leading-relaxed text-foreground/80">
                          {detail}
                        </p>
                      )}
                    </li>
                  );
                })}
              </ol>
            )}
            <p className="border-t border-border px-2 py-2 text-[11px] text-muted-foreground">
              {streamFilter === "all"
                ? `${events.length} events · ${runtimeCopy.runEventSource}`
                : `Showing ${visibleStreamEvents.length} of ${events.length} events · ${runtimeCopy.runEventSource}`}
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
          <div className="space-y-3 px-4 py-4">
            <div>
              <p className="text-sm font-medium">Retained task files</p>
              <p className="mt-1 text-[12px] leading-relaxed text-muted-foreground">
                Portable files derived from the result and evidence records returned by this task’s
                API. This is not a claim of access to the runner’s filesystem.
              </p>
            </div>
            {artifacts.length === 0 ? (
              <div className="rounded-xl border border-dashed border-border px-3 py-5 text-center">
                <p className="text-[13px] text-muted-foreground">
                  {runtimeCopy.runFilesDescription}
                </p>
              </div>
            ) : (
              <ul className="space-y-2">
                {artifacts.map((artifact) => {
                  const Icon = artifact.kind === "result" ? FileText : FileJson;
                  return (
                    <li key={artifact.id} className="rounded-xl border border-border p-3">
                      <div className="flex items-start gap-3">
                        <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-secondary text-muted-foreground">
                          <Icon className="size-4" />
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="truncate font-mono text-[12px] font-medium">
                            {artifact.name}
                          </p>
                          <p className="mt-1 line-clamp-2 text-[12px] leading-relaxed text-muted-foreground">
                            {artifact.description}
                          </p>
                        </div>
                        <a
                          href={artifact.downloadHref}
                          download={artifact.name}
                          aria-label={`Download ${artifact.name}`}
                          className="flex size-8 shrink-0 items-center justify-center rounded-lg border border-border text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
                        >
                          <Download className="size-3.5" />
                        </a>
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        )}
        {tab === "git" && (
          <UnavailableTab
            title="No repository attached"
            body="Branches, commits, and draft PRs appear here when a coding task runs against a connected repository."
          />
        )}
        {tab === "trace" && trace.state !== "loading" && (
          <div className="space-y-4 px-4 py-4">
            <div>
              <p className="flex items-center gap-2 text-sm font-medium">
                <Route className="size-4 text-brand-accent" /> Execution trace
              </p>
              <p className="mt-1 text-[12px] leading-relaxed text-muted-foreground">
                The task’s retained event trail is available here. An external provider trace is
                linked only when the API resolves one for this exact run.
              </p>
            </div>
            <dl className="space-y-2 rounded-xl border border-border p-3 text-[12px]">
              <div className="flex justify-between gap-3">
                <dt className="text-muted-foreground">Task</dt>
                <dd className="truncate font-mono">{selected.taskId}</dd>
              </div>
              <div className="flex justify-between gap-3">
                <dt className="text-muted-foreground">Run</dt>
                <dd className="truncate font-mono">{selected.runId ?? "Not reported"}</dd>
              </div>
              <div className="flex justify-between gap-3">
                <dt className="text-muted-foreground">Retained events</dt>
                <dd className="tabular-nums">{events.length}</dd>
              </div>
              <div className="flex justify-between gap-3">
                <dt className="text-muted-foreground">Provider trace</dt>
                <dd>{trace.state === "available" ? "Available" : "Not available"}</dd>
              </div>
            </dl>
            {trace.state === "available" && trace.url ? (
              <a
                href={trace.url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 rounded-xl bg-brand px-3 py-2 text-[13px] font-medium text-brand-foreground"
              >
                Open provider trace <ExternalLink className="size-3.5" />
              </a>
            ) : (
              <p className="rounded-xl bg-secondary/60 px-3 py-2 text-[12px] text-muted-foreground">
                No external trace was resolved. Activity and evidence above remain the local,
                inspectable execution record.
              </p>
            )}
          </div>
        )}
        {tab === "trace" && trace.state === "loading" && (
          <p className="p-4 text-sm text-muted-foreground">Looking up this task's trace…</p>
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

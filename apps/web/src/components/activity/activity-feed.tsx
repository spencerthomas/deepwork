"use client";

import {
  Activity,
  AlignLeft,
  ArrowUpRight,
  Check,
  CheckCircle2,
  ClipboardList,
  Paperclip,
  PencilLine,
  Play,
  Plus,
  RefreshCw,
  ShieldQuestion,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import type { ComponentType } from "react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { AppShell } from "@/components/shell/app-shell";
import { PageHeader } from "@/components/shell/page-header";
import { SidebarItem, SidebarLabel } from "@/components/shell/sidebar-nav";
import { StatusChip } from "@/components/shell/status-chip";
import { moveInboxFocus } from "@/components/tasks/task-inbox-navigation";
import { taskRuntimePresentation } from "@/lib/task-runtime-presentation";
import type { TaskEventName } from "@/lib/task-types";
import { useTasksStore } from "@/lib/tasks-store";
import { cn } from "@/lib/utils";

import type { ActivityEntry, ActivityFilter } from "./activity-model";
import {
  ACTIVITY_FILTER_LABELS,
  ACTIVITY_FILTERS,
  activityFilterCounts,
  buildActivityFeed,
  EVENT_LABELS,
  filterActivityFeed,
} from "./activity-model";
import { activityEntryHref } from "./activity-links";
import { activityFilterToQuery, readActivityFilter } from "./activity-url";

type IconComponent = ComponentType<{ className?: string }>;

const EVENT_ICONS: Record<TaskEventName, IconComponent> = {
  "task.created": Plus,
  "run.started": Play,
  "content.delta": AlignLeft,
  "plan.proposed": ClipboardList,
  "plan.updated": PencilLine,
  "evidence.recorded": Paperclip,
  "interrupt.requested": ShieldQuestion,
  "decision.recorded": Check,
  "run.completed": CheckCircle2,
};

const FILTER_ICONS: Record<ActivityFilter, IconComponent> = {
  all: Activity,
  plans: ClipboardList,
  evidence: Paperclip,
  decisions: ShieldQuestion,
  completions: CheckCircle2,
};

const INTERACTIVE_TARGET_SELECTOR =
  'a[href], button, input, textarea, select, [role="button"], [role="link"], [role="menuitem"], [role="tab"], [contenteditable="true"]';

/**
 * Yield the shortcut keys whenever focus is on a control the user is operating —
 * the Refresh button, a sidebar filter, or a row's task link. Otherwise a
 * window-level Enter would hijack the control's own activation (and typing would
 * move the highlight). Mirrors the task inbox's guard so the keyboard-navigable
 * lists behave identically. The highlighted row itself is not matched by the
 * selector, so resting focus on it keeps j/k/Enter working.
 */
function isInteractiveTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  if (target.isContentEditable) return true;
  return target.closest(INTERACTIVE_TARGET_SELECTOR) !== null;
}

function TimelineSkeleton() {
  return (
    <ol aria-hidden className="relative ml-2 animate-pulse border-l border-border">
      {[0, 1, 2, 3].map((index) => (
        <li key={index} className="relative mb-5 pl-6">
          <span className="absolute -left-[13px] top-0 size-6 rounded-full border border-border bg-accent" />
          <div className="h-3.5 w-40 rounded bg-accent" />
          <div className="mt-2 h-3.5 w-64 rounded bg-accent/70" />
        </li>
      ))}
    </ol>
  );
}

function FeedRow({ entry, focused }: { entry: ActivityEntry; focused: boolean }) {
  const Icon = entry.kind === "status" ? Activity : EVENT_ICONS[entry.eventName];
  return (
    <li
      id={`activity-row-${entry.key}`}
      tabIndex={focused ? 0 : -1}
      aria-current={focused ? "true" : undefined}
      className={cn(
        "relative mb-5 rounded-lg py-1 pl-6 pr-3 outline-none transition-colors",
        focused ? "bg-accent/50 ring-1 ring-brand/40" : "",
      )}
    >
      <span className="absolute -left-[13px] top-1 flex size-6 items-center justify-center rounded-full border border-border bg-card">
        <Icon className="size-3 text-muted-foreground" />
      </span>

      {entry.kind === "status" ? (
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
          <span className="max-w-[22rem] truncate text-[13px] font-medium text-crisp">
            {entry.taskTitle}
          </span>
          <StatusChip status={entry.status} />
        </div>
      ) : (
        <>
          <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
            <span className="text-[13px] font-medium text-crisp">
              {EVENT_LABELS[entry.eventName]}
            </span>
            <span className="max-w-[18rem] truncate text-xs text-muted-foreground">
              {entry.taskTitle}
            </span>
          </div>
          {entry.detail !== undefined && (
            <p className="mt-0.5 text-[14px] leading-relaxed text-foreground/90">{entry.detail}</p>
          )}
        </>
      )}

      <Link
        href={activityEntryHref(entry)}
        className="mt-1 inline-flex items-center gap-1 font-mono text-[11px] text-brand-accent hover:underline"
      >
        tasks/{entry.taskId} <ArrowUpRight className="size-3" />
      </Link>
    </li>
  );
}

export function ActivityFeed() {
  const { tasks, loadingTasks, listError, refreshList, eventsByTask, mode } = useTasksStore();
  const [filter, setFilter] = useState<ActivityFilter>("all");
  const [focusedKey, setFocusedKey] = useState<string | null>(null);
  const runtimeCopy = taskRuntimePresentation(mode);
  const router = useRouter();

  // Mirror the active filter in the URL so a filtered feed is shareable, and
  // restore it on first load and on browser back/forward — the same contract
  // the task inbox uses. Each discrete filter change pushes a history entry so
  // back/forward step through prior views.
  const selectFilter = useCallback((next: ActivityFilter) => {
    setFilter((current) => {
      if (current === next) return current;
      const query = activityFilterToQuery(next);
      const { pathname } = window.location;
      const url = query ? `${pathname}?${query}` : pathname;
      window.history.pushState(window.history.state, "", url);
      return next;
    });
  }, []);

  useEffect(() => {
    const syncFromUrl = () =>
      setFilter(readActivityFilter(new URLSearchParams(window.location.search)));
    syncFromUrl();
    window.addEventListener("popstate", syncFromUrl);
    return () => window.removeEventListener("popstate", syncFromUrl);
  }, []);

  const entries = useMemo(() => buildActivityFeed(tasks, eventsByTask), [tasks, eventsByTask]);
  const counts = useMemo(() => activityFilterCounts(entries), [entries]);
  const visibleEntries = useMemo(() => filterActivityFeed(entries, filter), [entries, filter]);
  const orderedKeys = useMemo(() => visibleEntries.map((entry) => entry.key), [visibleEntries]);

  // Roving keyboard navigation over the timeline (mirrors the task inbox and the
  // approvals queue): j/k or arrows move the highlight, Enter opens the focused
  // entry's task. Keys are ignored while typing so they never hijack a field.
  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.metaKey || event.ctrlKey || event.altKey) return;
      if (isInteractiveTarget(event.target)) return;
      if (orderedKeys.length === 0) return;
      if (event.key === "j" || event.key === "ArrowDown") {
        event.preventDefault();
        setFocusedKey((current) => moveInboxFocus(current, orderedKeys, 1));
        return;
      }
      if (event.key === "k" || event.key === "ArrowUp") {
        event.preventDefault();
        setFocusedKey((current) => moveInboxFocus(current, orderedKeys, -1));
        return;
      }
      if (event.key === "Enter" && focusedKey !== null) {
        const entry = visibleEntries.find((candidate) => candidate.key === focusedKey);
        if (entry === undefined) return;
        event.preventDefault();
        router.push(`/tasks/${entry.taskId}`);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [orderedKeys, focusedKey, visibleEntries, router]);

  // Release a highlight that filtering or a refreshed feed removed from view.
  useEffect(() => {
    if (focusedKey !== null && !orderedKeys.includes(focusedKey)) setFocusedKey(null);
  }, [orderedKeys, focusedKey]);

  // Move real DOM focus to the highlighted row (roving tabindex) so keyboard and
  // assistive-technology users land on the exact entry Enter will open.
  useEffect(() => {
    if (focusedKey === null) return;
    document.getElementById(`activity-row-${focusedKey}`)?.focus();
  }, [focusedKey]);

  const sidebar = (
    <nav className="flex flex-col gap-1">
      <SidebarLabel>Activity</SidebarLabel>
      {ACTIVITY_FILTERS.map((candidate) => (
        <SidebarItem
          key={candidate}
          icon={FILTER_ICONS[candidate]}
          label={ACTIVITY_FILTER_LABELS[candidate]}
          count={counts[candidate]}
          active={filter === candidate}
          onClick={() => selectFilter(candidate)}
        />
      ))}
    </nav>
  );

  return (
    <AppShell active="Activity" sidebar={sidebar}>
      <PageHeader
        eyebrow="Provenance"
        title="Activity"
        description={runtimeCopy.activityDescription}
        actions={
          <button
            type="button"
            onClick={refreshList}
            className="flex items-center gap-1.5 rounded-xl border border-border bg-card px-3 py-1.5 text-[13px] font-medium transition-colors hover:bg-accent"
          >
            <RefreshCw className="size-3.5" />
            Refresh
          </button>
        }
      />

      <p className="mb-5 text-xs text-muted-foreground">{runtimeCopy.activitySessionNote}</p>

      {listError !== undefined && (
        <div
          role="alert"
          className="mb-4 flex flex-wrap items-center gap-2 rounded-2xl border border-status-failed/35 bg-status-failed-bg px-4 py-3 text-[13px]"
        >
          <span className="min-w-0 flex-1">{listError}</span>
          <button
            type="button"
            onClick={refreshList}
            className="flex items-center gap-1.5 rounded-xl border border-border bg-card px-3 py-1.5 font-medium transition-colors hover:bg-accent"
          >
            <RefreshCw className="size-3.5" />
            Retry
          </button>
        </div>
      )}

      {loadingTasks && entries.length === 0 ? (
        <>
          <p role="status" className="sr-only">
            Loading activity…
          </p>
          <TimelineSkeleton />
        </>
      ) : entries.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-border bg-card p-10 text-center">
          <span className="mx-auto flex size-10 items-center justify-center rounded-xl bg-secondary text-secondary-foreground">
            <Activity className="size-5" />
          </span>
          <h2 className="mt-3 text-lg font-semibold tracking-tight">No activity yet</h2>
          <p className="mx-auto mt-1 max-w-sm text-[14px] leading-relaxed text-muted-foreground">
            Dispatch a task — its status and streamed events land here as they are observed.
          </p>
          <Link
            href="/tasks/new"
            className="mt-4 inline-flex items-center gap-1.5 rounded-xl bg-brand px-3 py-1.5 text-[13px] font-medium text-brand-foreground transition-colors hover:bg-brand-hover"
          >
            <Plus className="size-4" />
            New task
          </Link>
        </div>
      ) : visibleEntries.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-border bg-card p-8 text-center">
          <p className="text-[14px] text-muted-foreground">
            No “{ACTIVITY_FILTER_LABELS[filter]}” events have been observed in this session.
          </p>
          <button
            type="button"
            onClick={() => selectFilter("all")}
            className="mt-3 rounded-xl border border-border bg-card px-3 py-1.5 text-[13px] font-medium transition-colors hover:bg-accent"
          >
            Show all events
          </button>
        </div>
      ) : (
        <>
          <p className="mb-2 text-[12px] text-muted-foreground">
            Keyboard: <span className="font-medium text-foreground/80">j / k</span> move ·{" "}
            <span className="font-medium text-foreground/80">Enter</span> open task
          </p>
          <ol aria-label="Activity timeline" className="relative ml-2 border-l border-border">
            {visibleEntries.map((entry) => (
              <FeedRow key={entry.key} entry={entry} focused={entry.key === focusedKey} />
            ))}
          </ol>
        </>
      )}
    </AppShell>
  );
}

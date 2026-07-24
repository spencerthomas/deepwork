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
import type { ComponentType } from "react";
import { useMemo, useState } from "react";

import { AppShell } from "@/components/shell/app-shell";
import { PageHeader } from "@/components/shell/page-header";
import { SidebarItem, SidebarLabel } from "@/components/shell/sidebar-nav";
import { StatusChip } from "@/components/shell/status-chip";
import { taskRuntimePresentation } from "@/lib/task-runtime-presentation";
import type { TaskEventName } from "@/lib/task-types";
import { useTasksStore } from "@/lib/tasks-store";

import type { ActivityEntry, ActivityFilter } from "./activity-model";
import {
  ACTIVITY_FILTER_LABELS,
  ACTIVITY_FILTERS,
  activityFilterCounts,
  buildActivityFeed,
  EVENT_LABELS,
  filterActivityFeed,
} from "./activity-model";

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

function FeedRow({ entry }: { entry: ActivityEntry }) {
  const Icon = entry.kind === "status" ? Activity : EVENT_ICONS[entry.eventName];
  return (
    <li className="relative mb-5 pl-6">
      <span className="absolute -left-[13px] top-0 flex size-6 items-center justify-center rounded-full border border-border bg-card">
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
        href={`/tasks/${entry.taskId}`}
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
  const runtimeCopy = taskRuntimePresentation(mode);

  const entries = useMemo(() => buildActivityFeed(tasks, eventsByTask), [tasks, eventsByTask]);
  const counts = useMemo(() => activityFilterCounts(entries), [entries]);
  const visibleEntries = useMemo(() => filterActivityFeed(entries, filter), [entries, filter]);

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
          onClick={() => setFilter(candidate)}
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
            className="mt-4 inline-flex items-center gap-1.5 rounded-xl bg-brand px-3 py-1.5 text-[13px] font-medium text-brand-foreground transition-colors hover:bg-brand/90"
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
            onClick={() => setFilter("all")}
            className="mt-3 rounded-xl border border-border bg-card px-3 py-1.5 text-[13px] font-medium transition-colors hover:bg-accent"
          >
            Show all events
          </button>
        </div>
      ) : (
        <ol aria-label="Activity timeline" className="relative ml-2 border-l border-border">
          {visibleEntries.map((entry) => (
            <FeedRow key={entry.key} entry={entry} />
          ))}
        </ol>
      )}
    </AppShell>
  );
}

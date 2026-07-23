"use client";

import {
  AlertCircle,
  ArrowUpRight,
  CheckCircle2,
  Inbox,
  Layers,
  List,
  Loader,
  Search,
  XCircle,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import type { ComponentType } from "react";
import { useEffect, useMemo, useRef, useState } from "react";

import { AppShell } from "@/components/shell/app-shell";
import { PageHeader } from "@/components/shell/page-header";
import { SidebarItem, SidebarLabel } from "@/components/shell/sidebar-nav";
import { StatusChip, statusChipLabel } from "@/components/shell/status-chip";
import {
  countTasks,
  describeTaskFilter,
  EMPTY_TASK_INBOX_FILTER,
  filterTasks,
  hasActiveTaskFilter,
  normalizeTaskQuery,
  TASK_SEARCH_MAX_LENGTH,
  type TaskInboxFilter,
  type TaskStatusFilter,
} from "@/components/task-inbox-filter";
import {
  INBOX_GROUP_ORDER,
  moveInboxFocus,
  orderedInboxIds,
} from "@/components/tasks/task-inbox-navigation";
import { taskRuntimePresentation } from "@/lib/task-runtime-presentation";
import { useTasksStore } from "@/lib/tasks-store";
import type { ClientMode, TaskStatus, TaskSummary } from "@/lib/task-types";
import { cn } from "@/lib/utils";

const groupOrder: readonly TaskStatus[] = INBOX_GROUP_ORDER;

/** Ignore the shortcut keys while the caret is in a field so typing stays intact. */
function isTypingTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  const tag = target.tagName;
  return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || target.isContentEditable;
}

interface ViewDef {
  key: TaskStatusFilter;
  label: string;
  icon: ComponentType<{ className?: string }>;
  always: boolean;
}

const views: ViewDef[] = [
  { key: "all", label: "Inbox", icon: Inbox, always: true },
  { key: "running", label: "Running", icon: Loader, always: true },
  { key: "waiting-approval", label: "Needs review", icon: AlertCircle, always: true },
  { key: "completed", label: "Done", icon: CheckCircle2, always: true },
  { key: "failed", label: "Failed", icon: XCircle, always: true },
  { key: "queued", label: "Queued", icon: Loader, always: false },
  { key: "rejected", label: "Rejected", icon: XCircle, always: false },
  { key: "cancelled", label: "Cancelled", icon: XCircle, always: false },
];

function TaskRow({
  mode,
  task,
  focused,
}: {
  mode: ClientMode;
  task: TaskSummary;
  focused: boolean;
}) {
  const runtimeCopy = taskRuntimePresentation(mode);
  const ref = useRef<HTMLAnchorElement>(null);

  useEffect(() => {
    if (focused) ref.current?.scrollIntoView({ block: "nearest" });
  }, [focused]);

  return (
    <Link
      ref={ref}
      href={`/tasks/${task.taskId}`}
      data-focused={focused || undefined}
      className={cn(
        "group flex items-center gap-4 px-4 py-3.5 transition-colors hover:bg-accent/50",
        focused && "bg-accent/60 ring-2 ring-inset ring-brand/40",
      )}
    >
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="truncate text-sm font-medium text-crisp">{task.title}</span>
          <ArrowUpRight className="size-3.5 shrink-0 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
        </div>
        <div className="mt-1 flex items-center gap-2 text-[13px] text-muted-foreground">
          <span className="font-medium text-foreground/70">{runtimeCopy.taskOriginLabel}</span>
          <span className="text-border">·</span>
          <span className="truncate font-mono text-xs">
            {task.runId ? `Run ${task.runId.slice(0, 10)}` : `Task ${task.taskId.slice(0, 10)}`}
          </span>
        </div>
      </div>
      <StatusChip status={task.status} />
    </Link>
  );
}

function SkeletonRows() {
  return (
    <div className="divide-y divide-border" aria-hidden>
      {[0, 1, 2, 3].map((row) => (
        <div key={row} className="flex items-center gap-4 px-4 py-3.5">
          <div className="min-w-0 flex-1">
            <div className="h-4 w-2/3 rounded bg-muted" />
            <div className="mt-2 h-3 w-1/3 rounded bg-muted/70" />
          </div>
          <div className="h-6 w-20 rounded-full bg-muted" />
        </div>
      ))}
    </div>
  );
}

function KbdHint({ children }: { children: string }) {
  return (
    <kbd className="rounded-[5px] border border-border bg-background px-1.5 py-0.5 font-mono text-[11px] leading-none">
      {children}
    </kbd>
  );
}

export function TaskInbox() {
  const router = useRouter();
  const { tasks, loadingTasks, listError, refreshList, mode } = useTasksStore();
  const [filter, setFilter] = useState<TaskInboxFilter>(EMPTY_TASK_INBOX_FILTER);
  const [grouped, setGrouped] = useState(true);
  const [focusedId, setFocusedId] = useState<string | null>(null);
  const runtimeCopy = taskRuntimePresentation(mode);

  const counts = countTasks(tasks);
  const visible = useMemo(() => filterTasks(tasks, filter), [tasks, filter]);
  const filterActive = hasActiveTaskFilter(filter);
  const needsYou = counts.byStatus["waiting-approval"];

  const orderedIds = useMemo(
    () => orderedInboxIds(visible, grouped, filter.status),
    [visible, grouped, filter.status],
  );

  // Release a highlight that filtering, grouping, or a refresh removed from view.
  useEffect(() => {
    if (focusedId !== null && !orderedIds.includes(focusedId)) setFocusedId(null);
  }, [orderedIds, focusedId]);

  // Roving keyboard navigation: j/k or arrows move the highlight, Enter opens it.
  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.metaKey || event.ctrlKey || event.altKey) return;
      if (isTypingTarget(event.target)) return;
      if (orderedIds.length === 0) return;
      if (event.key === "j" || event.key === "ArrowDown") {
        event.preventDefault();
        setFocusedId((current) => moveInboxFocus(current, orderedIds, 1));
      } else if (event.key === "k" || event.key === "ArrowUp") {
        event.preventDefault();
        setFocusedId((current) => moveInboxFocus(current, orderedIds, -1));
      } else if (event.key === "Enter" && focusedId !== null) {
        event.preventDefault();
        router.push(`/tasks/${focusedId}`);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [orderedIds, focusedId, router]);

  const sidebar = (
    <nav className="flex flex-col gap-1">
      <SidebarLabel>Views</SidebarLabel>
      {views
        .filter(
          (view) =>
            view.always || (view.key !== "all" && counts.byStatus[view.key as TaskStatus] > 0),
        )
        .map((view) => {
          const count = view.key === "all" ? counts.total : counts.byStatus[view.key as TaskStatus];
          return (
            <SidebarItem
              key={view.key}
              icon={view.icon}
              label={view.label}
              count={count}
              active={filter.status === view.key}
              onClick={() => setFilter((current) => ({ ...current, status: view.key }))}
            />
          );
        })}

      <div className="my-3 h-px bg-border" />
      <SidebarLabel>Scope</SidebarLabel>
      <p className="px-3 text-[12px] leading-relaxed text-muted-foreground">
        {runtimeCopy.inboxScope}
      </p>
    </nav>
  );

  return (
    <AppShell active="Tasks" sidebar={sidebar}>
      <PageHeader
        eyebrow={runtimeCopy.inboxEyebrow}
        title="Tasks"
        description={runtimeCopy.inboxDescription}
        actions={
          <div className="flex items-center gap-1 rounded-xl border border-border bg-card p-0.5">
            <button
              type="button"
              onClick={() => setGrouped(true)}
              className={cn(
                "flex items-center gap-1.5 rounded-[9px] px-2.5 py-1.5 text-[13px] transition-colors",
                grouped
                  ? "bg-accent text-foreground"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              <Layers className="size-3.5" /> By status
            </button>
            <button
              type="button"
              onClick={() => setGrouped(false)}
              className={cn(
                "flex items-center gap-1.5 rounded-[9px] px-2.5 py-1.5 text-[13px] transition-colors",
                !grouped
                  ? "bg-accent text-foreground"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              <List className="size-3.5" /> Recent
            </button>
          </div>
        }
      />

      {needsYou > 0 && filter.status === "all" && !filter.attentionOnly && (
        <div className="mb-6 flex items-center gap-3 rounded-2xl border border-status-review/30 bg-status-review-bg px-4 py-3">
          <AlertCircle className="size-4 text-status-review" />
          <p className="text-sm text-foreground">
            <span className="font-medium">
              {needsYou} {needsYou === 1 ? "task needs" : "tasks need"} you.
            </span>{" "}
            <span className="text-muted-foreground">Review agent plans before they continue.</span>
          </p>
          <button
            type="button"
            onClick={() => setFilter((current) => ({ ...current, status: "waiting-approval" }))}
            className="ml-auto text-[13px] font-medium text-status-review hover:underline"
          >
            Review now
          </button>
        </div>
      )}

      <div className="mb-4 flex items-center gap-2 rounded-full border border-border bg-card px-3.5">
        <Search className="size-4 shrink-0 text-muted-foreground" />
        <input
          type="search"
          name="task-search"
          aria-label="Search loaded tasks"
          placeholder="Search title, run ID, or status…"
          autoComplete="off"
          maxLength={TASK_SEARCH_MAX_LENGTH}
          value={filter.query}
          onChange={(event) =>
            setFilter((current) => ({
              ...current,
              query: normalizeTaskQuery(event.target.value),
            }))
          }
          onKeyDown={(event) => {
            if (event.key === "Escape" && filter.query !== "") {
              event.preventDefault();
              setFilter((current) => ({ ...current, query: "" }));
            }
          }}
          className="h-10 min-w-0 flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
        />
        {filterActive && (
          <button
            type="button"
            onClick={() => setFilter(EMPTY_TASK_INBOX_FILTER)}
            className="shrink-0 text-[13px] font-medium text-brand hover:underline"
          >
            Clear
          </button>
        )}
      </div>

      {listError && (
        <div
          className="mb-4 flex items-center gap-3 rounded-2xl border border-status-failed/30 bg-status-failed-bg px-4 py-3"
          role="alert"
        >
          <XCircle className="size-4 text-status-failed" />
          <p className="min-w-0 flex-1 text-sm">
            <span className="font-medium">Tasks unavailable.</span>{" "}
            <span className="text-muted-foreground">{listError}</span>
          </p>
          <button
            type="button"
            onClick={refreshList}
            className="shrink-0 text-[13px] font-medium text-status-failed hover:underline"
          >
            Try again
          </button>
        </div>
      )}

      <div className="overflow-hidden rounded-2xl border border-border bg-card">
        {loadingTasks && tasks.length === 0 ? (
          <SkeletonRows />
        ) : tasks.length === 0 ? (
          <div className="px-4 py-16 text-center">
            <p className="text-sm font-medium">No tasks yet</p>
            <p className="mx-auto mt-1 max-w-sm text-sm text-muted-foreground">
              {runtimeCopy.inboxEmptyDescription}
            </p>
            <Link
              href="/tasks/new"
              className="mt-4 inline-flex items-center gap-1.5 rounded-xl bg-brand px-3 py-1.5 text-[13px] font-medium text-brand-foreground transition-colors hover:bg-brand/90"
            >
              New task
            </Link>
          </div>
        ) : visible.length === 0 ? (
          <div className="px-4 py-12 text-center">
            <p className="text-sm font-medium">No matching tasks</p>
            <p className="mt-1 text-sm text-muted-foreground">{describeTaskFilter(filter)}</p>
            <button
              type="button"
              onClick={() => setFilter(EMPTY_TASK_INBOX_FILTER)}
              className="mt-3 text-[13px] font-medium text-brand hover:underline"
            >
              Clear filters
            </button>
          </div>
        ) : grouped && filter.status === "all" ? (
          groupOrder.map((status) => {
            const group = visible.filter((task) => task.status === status);
            if (group.length === 0) return null;
            return (
              <div key={status} className="border-b border-border last:border-b-0">
                <div className="flex items-center gap-2 bg-muted/40 px-4 py-2">
                  <span className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                    {statusChipLabel(status)}
                  </span>
                  <span className="text-[11px] tabular-nums text-muted-foreground">
                    {group.length}
                  </span>
                </div>
                <div className="divide-y divide-border">
                  {group.map((task) => (
                    <TaskRow
                      key={task.taskId}
                      mode={mode}
                      task={task}
                      focused={task.taskId === focusedId}
                    />
                  ))}
                </div>
              </div>
            );
          })
        ) : (
          <div className="divide-y divide-border">
            {visible.map((task) => (
              <TaskRow
                key={task.taskId}
                mode={mode}
                task={task}
                focused={task.taskId === focusedId}
              />
            ))}
          </div>
        )}
      </div>

      {tasks.length > 0 && (
        <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1">
          <p className="text-[12px] tabular-nums text-muted-foreground" role="status">
            {filterActive
              ? `Showing ${visible.length} of ${counts.total} loaded tasks · ${counts.attention} need attention`
              : `${counts.total} loaded ${counts.total === 1 ? "task" : "tasks"} · ${counts.attention} ${counts.attention === 1 ? "needs" : "need"} attention`}
          </p>
          {orderedIds.length > 1 && (
            <p className="hidden items-center gap-1.5 text-[12px] text-muted-foreground sm:flex">
              <KbdHint>J</KbdHint>
              <KbdHint>K</KbdHint>
              <span>to move</span>
              <KbdHint>↵</KbdHint>
              <span>to open</span>
            </p>
          )}
        </div>
      )}
    </AppShell>
  );
}

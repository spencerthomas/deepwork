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
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

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
  TASK_DATE_WINDOW_LABELS,
  TASK_DATE_WINDOW_OPTIONS,
  TASK_SEARCH_MAX_LENGTH,
  type TaskDateWindow,
  type TaskInboxFilter,
  type TaskStatusFilter,
} from "@/components/task-inbox-filter";
import {
  INBOX_GROUP_ORDER,
  moveInboxFocus,
  orderedInboxIds,
  sortTasksByRecency,
} from "@/components/tasks/task-inbox-navigation";
import { inboxViewToQuery, type InboxView, readInboxView } from "@/components/tasks/task-inbox-url";
import { taskRuntimePresentation } from "@/lib/task-runtime-presentation";
import { formatTaskAge } from "@/lib/task-time";
import { useTasksStore } from "@/lib/tasks-store";
import type { ClientMode, TaskStatus, TaskSummary } from "@/lib/task-types";
import { cn } from "@/lib/utils";

const groupOrder: readonly TaskStatus[] = INBOX_GROUP_ORDER;

const INTERACTIVE_TARGET_SELECTOR =
  'a[href], button, input, textarea, select, [role="button"], [role="link"], [role="menuitem"], [role="tab"], [contenteditable="true"]';

/**
 * Yield the shortcut keys whenever focus is on a control the user is operating —
 * a search field, a sidebar filter, the grouping toggle, "Review now," or a row
 * link. Otherwise a window-level Enter would hijack the control's own
 * activation and typing would move the highlight. The highlight itself never
 * takes DOM focus, so the ordinary j/k flow (focus resting on the body) is
 * unaffected.
 */
function isInteractiveTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  if (target.isContentEditable) return true;
  return target.closest(INTERACTIVE_TARGET_SELECTOR) !== null;
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
  const age = formatTaskAge(task.createdAt);

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
          {age !== undefined && (
            <>
              <span className="text-border">·</span>
              <span className="shrink-0 whitespace-nowrap" title={task.createdAt}>
                {age}
              </span>
            </>
          )}
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
  const [view, setView] = useState<InboxView>(() => ({
    filter: EMPTY_TASK_INBOX_FILTER,
    grouped: true,
  }));
  const filter = view.filter;
  const grouped = view.grouped;
  const viewRef = useRef(view);
  viewRef.current = view;
  const [focusedId, setFocusedId] = useState<string | null>(null);
  const searchRef = useRef<HTMLInputElement>(null);
  const runtimeCopy = taskRuntimePresentation(mode);

  // Mirror the view in the URL so a filtered/grouped inbox is shareable, and
  // restore it on first load and on browser back/forward. Discrete status and
  // grouping changes push a history entry so back/forward step through prior
  // views; a search keystroke only replaces the current entry so typing doesn't
  // spam history.
  const commitView = useCallback((next: InboxView) => {
    const prev = viewRef.current;
    const statusSame = prev.filter.status === next.filter.status;
    const groupedSame = prev.grouped === next.grouped;
    const attentionSame = prev.filter.attentionOnly === next.filter.attentionOnly;
    const querySame = prev.filter.query === next.filter.query;
    const createdSame = prev.filter.createdWithin === next.filter.createdWithin;
    if (statusSame && groupedSame && attentionSame && querySame && createdSame) return;
    setView(next);
    const query = inboxViewToQuery(next);
    const { pathname } = window.location;
    const url = query ? `${pathname}?${query}` : pathname;
    const onlyQueryChanged = statusSame && groupedSame && attentionSame && createdSame;
    if (onlyQueryChanged) {
      window.history.replaceState(window.history.state, "", url);
    } else {
      window.history.pushState(window.history.state, "", url);
    }
  }, []);

  useEffect(() => {
    const syncFromUrl = () => setView(readInboxView(new URLSearchParams(window.location.search)));
    syncFromUrl();
    window.addEventListener("popstate", syncFromUrl);
    return () => window.removeEventListener("popstate", syncFromUrl);
  }, []);

  const setFilter = useCallback(
    (update: TaskInboxFilter | ((current: TaskInboxFilter) => TaskInboxFilter)) => {
      const nextFilter = typeof update === "function" ? update(viewRef.current.filter) : update;
      commitView({ filter: nextFilter, grouped: viewRef.current.grouped });
    },
    [commitView],
  );

  const setGrouped = useCallback(
    (next: boolean) => commitView({ filter: viewRef.current.filter, grouped: next }),
    [commitView],
  );

  const setCreatedWithin = useCallback(
    (window: TaskDateWindow | undefined) =>
      setFilter((current) => {
        if (window === undefined) {
          const next = { ...current };
          delete next.createdWithin;
          return next;
        }
        return { ...current, createdWithin: window };
      }),
    [setFilter],
  );

  // Re-render on a slow cadence so an open inbox's relative creation ages
  // ("just now" → "1m ago") keep advancing without a task update or manual
  // refresh. The interval is client-only, so no rows exist to hydrate against.
  const [, advanceAgeClock] = useState(0);
  useEffect(() => {
    const timer = window.setInterval(() => advanceAgeClock((tick) => tick + 1), 60_000);
    return () => window.clearInterval(timer);
  }, []);

  const counts = countTasks(tasks);
  const visible = useMemo(() => filterTasks(tasks, filter), [tasks, filter]);
  const filterActive = hasActiveTaskFilter(filter);
  const needsYou = counts.byStatus["waiting-approval"];

  // The ungrouped "Recent" view sorts newest-created first so its label is
  // honest; the grouped view keeps the server order within each status section.
  // Render and keyboard navigation both read this one ordered list, so they can
  // never drift.
  const ordered = useMemo(
    () => (grouped ? visible : sortTasksByRecency(visible)),
    [visible, grouped],
  );

  const orderedIds = useMemo(
    () => orderedInboxIds(ordered, grouped, filter.status),
    [ordered, grouped, filter.status],
  );

  // Release a highlight that filtering, grouping, or a refresh removed from view.
  useEffect(() => {
    if (focusedId !== null && !orderedIds.includes(focusedId)) setFocusedId(null);
  }, [orderedIds, focusedId]);

  // Roving keyboard navigation: j/k or arrows move the highlight, Enter opens it.
  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.metaKey || event.ctrlKey || event.altKey) return;
      if (isInteractiveTarget(event.target)) return;
      if (event.key === "/") {
        // Jump to search from anywhere on the page (the guard above means this
        // never fires while the caret is already in a field).
        event.preventDefault();
        searchRef.current?.focus();
        return;
      }
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
          ref={searchRef}
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
            if (event.key === "Escape") {
              event.preventDefault();
              // First Escape clears the query; a second (empty) one leaves search.
              if (filter.query !== "") {
                setFilter((current) => ({ ...current, query: "" }));
              } else {
                event.currentTarget.blur();
              }
            }
          }}
          className="h-10 min-w-0 flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
        />
        {filterActive ? (
          <button
            type="button"
            onClick={() => setFilter(EMPTY_TASK_INBOX_FILTER)}
            className="shrink-0 text-[13px] font-medium text-brand-accent hover:underline"
          >
            Clear
          </button>
        ) : (
          <kbd
            aria-hidden
            className="hidden shrink-0 rounded-[5px] border border-border px-1.5 py-0.5 font-mono text-[11px] leading-none text-muted-foreground sm:inline-flex"
          >
            /
          </kbd>
        )}
      </div>

      <div className="mb-4 flex flex-wrap items-center gap-2">
        <span id="created-filter-label" className="text-[12px] font-medium text-muted-foreground">
          Created
        </span>
        <div
          role="group"
          aria-labelledby="created-filter-label"
          className="inline-flex items-center gap-0.5 rounded-xl border border-border bg-card p-0.5"
        >
          <button
            type="button"
            aria-pressed={filter.createdWithin === undefined}
            onClick={() => setCreatedWithin(undefined)}
            className={cn(
              "rounded-[9px] px-2.5 py-1 text-[12px] font-medium transition-colors",
              filter.createdWithin === undefined
                ? "bg-accent text-foreground"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            Any time
          </button>
          {TASK_DATE_WINDOW_OPTIONS.map((window) => (
            <button
              key={window}
              type="button"
              aria-pressed={filter.createdWithin === window}
              onClick={() => setCreatedWithin(window)}
              className={cn(
                "rounded-[9px] px-2.5 py-1 text-[12px] font-medium transition-colors",
                filter.createdWithin === window
                  ? "bg-accent text-foreground"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              {TASK_DATE_WINDOW_LABELS[window]}
            </button>
          ))}
        </div>
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
              className="mt-4 inline-flex items-center gap-1.5 rounded-xl bg-brand px-3 py-1.5 text-[13px] font-medium text-brand-foreground transition-colors hover:bg-brand-hover"
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
              className="mt-3 text-[13px] font-medium text-brand-accent hover:underline"
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
            {ordered.map((task) => (
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

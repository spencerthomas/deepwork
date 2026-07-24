"use client";

import {
  ArrowUpRight,
  Check,
  CheckCheck,
  CheckCircle2,
  CheckSquare,
  Inbox,
  MessageSquare,
  Plus,
  RefreshCw,
  ShieldQuestion,
  Square,
  X,
} from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { AppShell } from "@/components/shell/app-shell";
import { PageHeader } from "@/components/shell/page-header";
import { SidebarItem, SidebarLabel } from "@/components/shell/sidebar-nav";
import { taskRuntimePresentation } from "@/lib/task-runtime-presentation";
import { useTasksStore } from "@/lib/tasks-store";
import { cn } from "@/lib/utils";

import { ApprovalDecisionPanel } from "./approval-decision-panel";
import type { ApprovalCapabilityFilter, ApprovalRow, DecisionVerb } from "./approvals-model";
import {
  approvalCapabilityCounts,
  deriveApprovalRows,
  filterRowsByCapability,
  waitingTaskIdsNeedingDetail,
} from "./approvals-model";

const VERB_FILTER_LABELS: Record<DecisionVerb, string> = {
  approve: "Approve",
  reject: "Reject",
  respond: "Respond",
};

const CONFIRMATION_TEXT: Record<DecisionVerb, string> = {
  approve: "Approval recorded",
  reject: "Rejection recorded",
  respond: "Response sent",
};

interface ResolvedConfirmation {
  decision: DecisionVerb;
  taskId: string;
  taskTitle: string;
}

function addToSet(current: ReadonlySet<string>, value: string): ReadonlySet<string> {
  const next = new Set(current);
  next.add(value);
  return next;
}

function removeFromSet(current: ReadonlySet<string>, value: string): ReadonlySet<string> {
  if (!current.has(value)) {
    return current;
  }
  const next = new Set(current);
  next.delete(value);
  return next;
}

function ApprovalListSkeleton() {
  return (
    <div aria-hidden className="space-y-3">
      {[0, 1, 2].map((index) => (
        <div key={index} className="animate-pulse rounded-2xl border border-border bg-card p-4">
          <div className="flex items-center gap-2">
            <span className="size-6 rounded-md bg-accent" />
            <span className="h-3.5 w-48 rounded bg-accent" />
            <span className="ml-auto h-3.5 w-24 rounded bg-accent" />
          </div>
          <div className="mt-3 h-28 rounded-2xl bg-accent/60" />
        </div>
      ))}
    </div>
  );
}

function DetailLoadingPanel() {
  return (
    <div className="rounded-2xl border border-status-review/20 bg-status-review-bg/40 p-3.5">
      <div className="flex items-center gap-2">
        <ShieldQuestion className="size-4 text-status-review" />
        <span className="text-[11px] font-semibold uppercase tracking-wide text-status-review">
          Needs review
        </span>
      </div>
      <div aria-hidden className="mt-3 animate-pulse space-y-2">
        <div className="h-3.5 w-2/3 rounded bg-accent" />
        <div className="h-3.5 w-1/2 rounded bg-accent" />
        <div className="h-8 w-full max-w-64 rounded-xl bg-accent/70" />
      </div>
      <p role="status" className="mt-2 text-xs text-muted-foreground">
        Loading the approval request…
      </p>
    </div>
  );
}

export function ApprovalsView() {
  const {
    tasks,
    loadingTasks,
    listError,
    refreshList,
    detailsByTask,
    loadDetail,
    decideForTask,
    mode,
  } = useTasksStore();
  const runtimeCopy = taskRuntimePresentation(mode);

  const [filter, setFilter] = useState<ApprovalCapabilityFilter>("all");
  const [resolvedInterruptIds, setResolvedInterruptIds] = useState<ReadonlySet<string>>(
    () => new Set(),
  );
  const [failedDetailIds, setFailedDetailIds] = useState<ReadonlySet<string>>(() => new Set());
  const [interruptFreeIds, setInterruptFreeIds] = useState<ReadonlySet<string>>(() => new Set());
  const [confirmation, setConfirmation] = useState<ResolvedConfirmation>();
  // Multi-select bulk approval. A supervisor can clear a backlog of proposed
  // plans in one action instead of deciding each row separately. Selection is
  // always explicit — this never auto-approves — so the human-in-the-loop
  // contract holds; each selected plan is still approved individually.
  const [selectedIds, setSelectedIds] = useState<ReadonlySet<string>>(() => new Set());
  const [bulkProgress, setBulkProgress] = useState<{ done: number; total: number }>();
  const [bulkSummary, setBulkSummary] = useState<{ approved: number; failed: number }>();
  const requestedRef = useRef<Set<string>>(new Set());

  const rows = useMemo(
    () => deriveApprovalRows(tasks, detailsByTask, resolvedInterruptIds),
    [tasks, detailsByTask, resolvedInterruptIds],
  );
  const counts = useMemo(() => approvalCapabilityCounts(rows), [rows]);
  const visibleRows = useMemo(() => filterRowsByCapability(rows, filter), [rows, filter]);

  // Rows that can actually be bulk-approved: hydrated interrupts that advertise
  // "approve". Rows still loading or offering only reject/respond are excluded.
  const approvableRows = useMemo(
    () => visibleRows.filter((row) => row.interrupt?.decisions.includes("approve") ?? false),
    [visibleRows],
  );
  const selectedApprovable = useMemo(
    () => approvableRows.filter((row) => selectedIds.has(row.task.taskId)),
    [approvableRows, selectedIds],
  );
  const bulkRunning = bulkProgress !== undefined;
  const allApprovableSelected =
    approvableRows.length > 0 && selectedApprovable.length === approvableRows.length;

  const toggleSelected = useCallback((taskId: string) => {
    setSelectedIds((current) =>
      current.has(taskId) ? removeFromSet(current, taskId) : addToSet(current, taskId),
    );
  }, []);
  const toggleSelectAll = useCallback(() => {
    setSelectedIds((current) =>
      approvableRows.length > 0 && approvableRows.every((row) => current.has(row.task.taskId))
        ? new Set()
        : new Set(approvableRows.map((row) => row.task.taskId)),
    );
  }, [approvableRows]);

  const approveSelected = useCallback(async () => {
    const targets = approvableRows.filter(
      (row) => row.interrupt !== undefined && selectedIds.has(row.task.taskId),
    );
    if (targets.length === 0) {
      return;
    }
    setBulkSummary(undefined);
    setBulkProgress({ done: 0, total: targets.length });
    let approved = 0;
    let failed = 0;
    // Sequential so each decision's receipt is validated and the queue drains
    // in order; a single failure never aborts the rest of the batch.
    for (const row of targets) {
      const interrupt = row.interrupt;
      if (interrupt === undefined) {
        continue;
      }
      const failure = await decideForTask(row.task.taskId, {
        interruptId: interrupt.interruptId,
        decision: "approve",
      });
      if (failure === undefined) {
        approved += 1;
        setResolvedInterruptIds((current) => addToSet(current, interrupt.interruptId));
        setSelectedIds((current) => removeFromSet(current, row.task.taskId));
      } else {
        failed += 1;
      }
      setBulkProgress((current) => (current ? { ...current, done: current.done + 1 } : current));
    }
    setBulkProgress(undefined);
    setBulkSummary({ approved, failed });
  }, [approvableRows, selectedIds, decideForTask]);

  const hydrate = useCallback(
    (taskId: string) => {
      requestedRef.current.add(taskId);
      void loadDetail(taskId).then((detail) => {
        if (detail === undefined) {
          setFailedDetailIds((current) => addToSet(current, taskId));
        } else if (detail.pendingInterrupt === undefined) {
          setInterruptFreeIds((current) => addToSet(current, taskId));
        }
      });
    },
    [loadDetail],
  );

  useEffect(() => {
    for (const taskId of waitingTaskIdsNeedingDetail(tasks, detailsByTask)) {
      if (!requestedRef.current.has(taskId)) {
        hydrate(taskId);
      }
    }
  }, [tasks, detailsByTask, hydrate]);

  const retryDetail = useCallback(
    (taskId: string) => {
      setFailedDetailIds((current) => removeFromSet(current, taskId));
      setInterruptFreeIds((current) => removeFromSet(current, taskId));
      hydrate(taskId);
    },
    [hydrate],
  );

  const handleResolved = useCallback((row: ApprovalRow, decision: DecisionVerb) => {
    if (row.interrupt) {
      const resolvedId = row.interrupt.interruptId;
      setResolvedInterruptIds((current) => addToSet(current, resolvedId));
    }
    setConfirmation({ decision, taskId: row.task.taskId, taskTitle: row.task.title });
  }, []);

  const sidebar = (
    <nav className="flex flex-col gap-1">
      <SidebarLabel>Queue</SidebarLabel>
      <SidebarItem
        icon={CheckCheck}
        label="All pending"
        count={rows.length}
        active={filter === "all"}
        onClick={() => setFilter("all")}
      />
      <div className="my-3 h-px bg-border" />
      <SidebarLabel>By capability</SidebarLabel>
      <SidebarItem
        icon={Check}
        label="Approve"
        count={counts.approve}
        active={filter === "approve"}
        onClick={() => setFilter("approve")}
      />
      <SidebarItem
        icon={X}
        label="Reject"
        count={counts.reject}
        active={filter === "reject"}
        onClick={() => setFilter("reject")}
      />
      <SidebarItem
        icon={MessageSquare}
        label="Respond"
        count={counts.respond}
        active={filter === "respond"}
        onClick={() => setFilter("respond")}
      />
    </nav>
  );

  const listErrorBanner = listError !== undefined && (
    <div
      role="alert"
      className="mb-3 flex flex-wrap items-center gap-2 rounded-2xl border border-status-failed/35 bg-status-failed-bg px-4 py-3 text-[13px]"
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
  );

  return (
    <AppShell active="Approvals" sidebar={sidebar}>
      <PageHeader
        eyebrow="Human in the loop"
        title="Approvals"
        description={runtimeCopy.approvalsDescription}
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

      {confirmation && (
        <div
          role="status"
          className="mb-4 flex flex-wrap items-center gap-2 rounded-2xl border border-status-done/35 bg-status-done-bg px-4 py-3 text-[13px]"
        >
          <CheckCircle2 className="size-4 shrink-0 text-status-done" />
          <span className="min-w-0">
            <span className="font-medium text-crisp">
              {CONFIRMATION_TEXT[confirmation.decision]}
            </span>{" "}
            —{" "}
            <Link
              href={`/tasks/${confirmation.taskId}`}
              className="underline decoration-border underline-offset-2 transition-colors hover:text-foreground"
            >
              {confirmation.taskId}
            </Link>{" "}
            left the queue.
          </span>
          <button
            type="button"
            aria-label="Dismiss confirmation"
            onClick={() => setConfirmation(undefined)}
            className="ml-auto rounded-md p-1 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
          >
            <X className="size-3.5" />
          </button>
        </div>
      )}

      {/* Rendered at the top level, not inside the list branch: a batch that
          approves the last pending rows empties the queue, and the outcome must
          still be reported after those rows are gone. */}
      {bulkSummary && (
        <div
          role="status"
          className={cn(
            "mb-4 flex flex-wrap items-center gap-2 rounded-2xl border px-4 py-3 text-[13px]",
            bulkSummary.failed === 0
              ? "border-status-done/35 bg-status-done-bg"
              : "border-status-review/35 bg-status-review-bg",
          )}
        >
          {bulkSummary.failed === 0 ? (
            <CheckCircle2 className="size-4 shrink-0 text-status-done" />
          ) : (
            <ShieldQuestion className="size-4 shrink-0 text-status-review" />
          )}
          <span className="min-w-0">
            <span className="font-medium text-crisp">
              {bulkSummary.approved > 0
                ? `Approved ${bulkSummary.approved} ${bulkSummary.approved === 1 ? "plan" : "plans"}`
                : "No plans approved"}
            </span>
            {bulkSummary.failed > 0 && (
              <span className="text-muted-foreground">
                {" "}
                — {bulkSummary.failed} could not be approved and{" "}
                {bulkSummary.failed === 1 ? "remains" : "remain"} in the queue.
              </span>
            )}
          </span>
          <button
            type="button"
            aria-label="Dismiss bulk approval summary"
            onClick={() => setBulkSummary(undefined)}
            className="ml-auto rounded-md p-1 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
          >
            <X className="size-3.5" />
          </button>
        </div>
      )}

      {loadingTasks && tasks.length === 0 ? (
        <>
          <p role="status" className="sr-only">
            Loading approvals…
          </p>
          <ApprovalListSkeleton />
        </>
      ) : listError !== undefined && tasks.length === 0 ? (
        <div className="rounded-2xl border border-status-failed/35 bg-status-failed-bg p-8 text-center">
          <h2 className="text-lg font-semibold tracking-tight">Approvals can’t be loaded</h2>
          <p className="mx-auto mt-1 max-w-md text-[14px] leading-relaxed text-muted-foreground">
            {listError}
          </p>
          <button
            type="button"
            onClick={refreshList}
            className="mt-4 inline-flex items-center gap-1.5 rounded-xl border border-border bg-card px-3 py-1.5 text-[13px] font-medium transition-colors hover:bg-accent"
          >
            <RefreshCw className="size-3.5" />
            Retry
          </button>
        </div>
      ) : rows.length === 0 ? (
        <>
          {listErrorBanner}
          <div className="rounded-2xl border border-dashed border-border bg-card p-10 text-center">
            <span className="mx-auto flex size-10 items-center justify-center rounded-xl bg-secondary text-secondary-foreground">
              <Inbox className="size-5" />
            </span>
            <h2 className="mt-3 text-lg font-semibold tracking-tight">No approvals waiting</h2>
            <p className="mx-auto mt-1 max-w-sm text-[14px] leading-relaxed text-muted-foreground">
              Agents pause here when they need you. Dispatch a task and it appears the moment it
              wants a decision.
            </p>
            <Link
              href="/tasks/new"
              className="mt-4 inline-flex items-center gap-1.5 rounded-xl bg-brand px-3 py-1.5 text-[13px] font-medium text-brand-foreground transition-colors hover:bg-brand-hover"
            >
              <Plus className="size-4" />
              New task
            </Link>
          </div>
        </>
      ) : visibleRows.length === 0 ? (
        <>
          {listErrorBanner}
          <div className="rounded-2xl border border-dashed border-border bg-card p-8 text-center">
            <p className="text-[14px] text-muted-foreground">
              None of the pending approvals offer the “
              {filter === "all" ? "" : VERB_FILTER_LABELS[filter]}” action.
            </p>
            <button
              type="button"
              onClick={() => setFilter("all")}
              className="mt-3 rounded-xl border border-border bg-card px-3 py-1.5 text-[13px] font-medium transition-colors hover:bg-accent"
            >
              Show all pending
            </button>
          </div>
        </>
      ) : (
        <>
          {listErrorBanner}
          {approvableRows.length > 0 && (
            <div className="mb-3 flex flex-wrap items-center gap-2 rounded-2xl border border-border bg-card px-3 py-2.5">
              <button
                type="button"
                onClick={toggleSelectAll}
                className="flex items-center gap-1.5 rounded-xl border border-border bg-card px-2.5 py-1.5 text-[13px] font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
              >
                {allApprovableSelected ? (
                  <CheckSquare className="size-3.5" />
                ) : (
                  <Square className="size-3.5" />
                )}
                {allApprovableSelected ? "Clear selection" : `Select all ${approvableRows.length}`}
              </button>
              <span className="text-[13px] text-muted-foreground">
                {selectedApprovable.length > 0
                  ? `${selectedApprovable.length} selected`
                  : "Select plans to approve together"}
              </span>
              <button
                type="button"
                onClick={() => void approveSelected()}
                disabled={selectedApprovable.length === 0 || bulkRunning}
                className="ml-auto flex items-center gap-1.5 rounded-xl bg-brand px-3 py-1.5 text-[13px] font-medium text-brand-foreground transition-colors hover:bg-brand-hover disabled:pointer-events-none disabled:opacity-50"
              >
                <CheckCheck className="size-3.5" />
                {bulkProgress
                  ? `Approving ${bulkProgress.done} of ${bulkProgress.total}…`
                  : `Approve selected${
                      selectedApprovable.length > 0 ? ` (${selectedApprovable.length})` : ""
                    }`}
              </button>
              <span role="status" aria-live="polite" className="sr-only">
                {bulkProgress
                  ? `Approving ${bulkProgress.done} of ${bulkProgress.total} selected plans.`
                  : ""}
              </span>
            </div>
          )}
          <ul aria-label="Pending approvals" className="space-y-3">
            {visibleRows.map((row) => (
              <li key={row.task.taskId} className="rounded-2xl border border-border bg-card p-4">
                <div className="mb-3 flex flex-wrap items-center gap-2">
                  {(row.interrupt?.decisions.includes("approve") ?? false) && (
                    <input
                      type="checkbox"
                      checked={selectedIds.has(row.task.taskId)}
                      onChange={() => toggleSelected(row.task.taskId)}
                      disabled={bulkRunning}
                      aria-label={`Select “${row.task.title}” for bulk approval`}
                      className="size-4 shrink-0 cursor-pointer accent-brand disabled:cursor-not-allowed"
                    />
                  )}
                  <span className="flex size-6 shrink-0 items-center justify-center rounded-md bg-secondary text-secondary-foreground">
                    <ShieldQuestion className="size-3.5" />
                  </span>
                  <span className="min-w-0 max-w-[24rem] truncate text-sm font-medium text-crisp">
                    {row.task.title}
                  </span>
                  <span className="rounded-full bg-accent px-2 py-0.5 font-mono text-[11px] text-muted-foreground">
                    {row.task.taskId}
                  </span>
                  <Link
                    href={`/tasks/${row.task.taskId}`}
                    className="ml-auto flex items-center gap-1 text-[13px] text-muted-foreground transition-colors hover:text-foreground"
                  >
                    Open task
                    <ArrowUpRight className="size-3.5" />
                  </Link>
                </div>

                {row.interrupt ? (
                  <ApprovalDecisionPanel
                    interrupt={row.interrupt}
                    plan={row.plan}
                    onDecide={(input) => decideForTask(row.task.taskId, input)}
                    onResolved={(decision) => handleResolved(row, decision)}
                  />
                ) : failedDetailIds.has(row.task.taskId) ? (
                  <div
                    role="alert"
                    className="rounded-2xl border border-status-failed/35 bg-status-failed-bg/60 p-3.5"
                  >
                    <p className="text-[13px] font-medium">
                      This approval request could not be loaded from the API.
                    </p>
                    <button
                      type="button"
                      onClick={() => retryDetail(row.task.taskId)}
                      className="mt-2 flex items-center gap-1.5 rounded-xl border border-border bg-card px-3 py-1.5 text-[13px] font-medium transition-colors hover:bg-accent"
                    >
                      <RefreshCw className="size-3.5" />
                      Retry
                    </button>
                  </div>
                ) : interruptFreeIds.has(row.task.taskId) ? (
                  <div className="rounded-2xl border border-border bg-accent/40 p-3.5">
                    <p className="text-[13px] leading-relaxed text-muted-foreground">
                      The task reports it is waiting for approval, but the API returned no pending
                      interruption. Open the task for the full picture, or reload.
                    </p>
                    <button
                      type="button"
                      onClick={() => retryDetail(row.task.taskId)}
                      className="mt-2 flex items-center gap-1.5 rounded-xl border border-border bg-card px-3 py-1.5 text-[13px] font-medium transition-colors hover:bg-accent"
                    >
                      <RefreshCw className="size-3.5" />
                      Reload
                    </button>
                  </div>
                ) : (
                  <DetailLoadingPanel />
                )}
              </li>
            ))}
          </ul>
        </>
      )}
    </AppShell>
  );
}

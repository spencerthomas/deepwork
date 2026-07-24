"use client";

import {
  AlertTriangle,
  ArrowLeft,
  Ban,
  Bot,
  CheckCircle2,
  CircleDot,
  ListChecks,
  PanelRight,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useMemo, useState } from "react";

import { AppShell } from "@/components/shell/app-shell";
import { SidebarItem, SidebarLabel } from "@/components/shell/sidebar-nav";
import { StatusChip } from "@/components/shell/status-chip";
import { ApprovalCard } from "@/components/tasks/approval-card";
import { PlanCard } from "@/components/tasks/plan-card";
import { RunPanel } from "@/components/tasks/run-panel";
import { TaskResultActions } from "@/components/tasks/task-result-actions";
import { buildThread } from "@/components/tasks/task-thread-model";
import { setEditRerunPrompt } from "@/lib/edit-rerun-handoff";
import {
  getActiveInterrupt,
  getEvidenceRecords,
  getLatestPlan,
  isTerminalStatus,
} from "@/lib/task-normalizers";
import { useActiveTask } from "@/lib/tasks-store";
import type { TaskStatus } from "@/lib/task-types";
import { cn } from "@/lib/utils";

function AgentAvatar() {
  return (
    <span className="flex size-7 shrink-0 items-center justify-center rounded-lg bg-secondary text-secondary-foreground">
      <Bot className="size-4" />
    </span>
  );
}

function statusDot(status: TaskStatus): string {
  if (status === "running" || status === "queued") return "bg-status-running";
  if (status === "waiting-approval") return "bg-status-review";
  if (status === "failed" || status === "rejected") return "bg-status-failed";
  if (status === "completed") return "bg-status-done";
  return "bg-status-neutral";
}

export function TaskThreadMarker({ label, detail }: { label: string; detail?: string }) {
  return (
    <div className="ml-10 flex flex-wrap items-center gap-x-2 gap-y-0.5 text-[13px] text-muted-foreground sm:flex-nowrap">
      <span className="size-1.5 shrink-0 rounded-full bg-border" aria-hidden />
      <span className="min-w-0 sm:shrink-0">{label}</span>
      {detail && (
        <span className="basis-full break-words pl-3.5 sm:min-w-0 sm:flex-1 sm:truncate sm:pl-0">
          · {detail}
        </span>
      )}
    </div>
  );
}

/**
 * Two-step "Stop run" control. The first click reveals an inline confirmation
 * so a task is never cancelled by a single stray click; confirming calls the
 * store, which records an honest terminal cancelled state.
 */
function StopRunControl({ onStop, cancelling }: { onStop: () => void; cancelling: boolean }) {
  const [confirming, setConfirming] = useState(false);

  if (!confirming) {
    return (
      <button
        type="button"
        onClick={() => setConfirming(true)}
        className="flex items-center gap-1.5 rounded-lg border border-border bg-card px-2.5 py-1.5 text-[13px] font-medium text-muted-foreground transition-colors hover:border-status-failed/40 hover:bg-status-failed-bg hover:text-status-failed"
      >
        <Ban className="size-3.5" /> Stop run
      </button>
    );
  }

  return (
    <div className="flex items-center gap-1.5" role="group" aria-label="Confirm stopping the run">
      <span className="hidden text-[13px] text-muted-foreground sm:inline">Stop this run?</span>
      <button
        type="button"
        disabled={cancelling}
        onClick={onStop}
        className={cn(
          "flex items-center gap-1.5 rounded-lg border border-status-failed/50 bg-status-failed-bg px-2.5 py-1.5 text-[13px] font-medium text-status-failed transition-colors hover:bg-status-failed/15",
          cancelling && "pointer-events-none opacity-60",
        )}
      >
        <Ban className="size-3.5" />
        {cancelling ? "Stopping…" : "Stop"}
      </button>
      <button
        type="button"
        disabled={cancelling}
        onClick={() => setConfirming(false)}
        className="rounded-lg border border-border px-2.5 py-1.5 text-[13px] font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-foreground disabled:pointer-events-none disabled:opacity-60"
      >
        Keep going
      </button>
    </div>
  );
}

export function TaskDetailView({ taskId }: { taskId: string }) {
  const store = useActiveTask(taskId);
  const {
    tasks,
    detailsByTask,
    eventsByTask,
    connectionState,
    detailError,
    streamError,
    actionError,
    planError,
    submittingDecision,
    submittedDecision,
    updatingPlan,
    cancelling,
    cancelError,
    mode,
    decide,
    updatePlan,
    cancelTask,
    createTask,
    creating,
    createError,
  } = store;
  const router = useRouter();
  const [panelOpen, setPanelOpen] = useState(true);
  const [rerunAttempted, setRerunAttempted] = useState(false);

  const selected = tasks.find((task) => task.taskId === taskId);
  const detail = detailsByTask[taskId];
  const events = useMemo(() => eventsByTask[taskId] ?? [], [eventsByTask, taskId]);

  const activeInterrupt = useMemo(
    () => (detail ? detail.pendingInterrupt : getActiveInterrupt(events)),
    [detail, events],
  );
  const plan = useMemo(
    () => getLatestPlan(detail?.proposedPlan, events),
    [detail?.proposedPlan, events],
  );
  const evidence = useMemo(
    () => getEvidenceRecords(detail?.evidence, events),
    [detail?.evidence, events],
  );
  const thread = useMemo(() => buildThread(detail, events), [detail, events]);

  const status = detail?.status ?? selected?.status ?? "unknown";
  const terminal = isTerminalStatus(status);
  const hasInterruptItem = thread.some((item) => item.kind === "interrupt");
  const hasPlanItem = thread.some((item) => item.kind === "plan");
  const title = detail?.title ?? selected?.title ?? taskId;
  // Re-dispatch the original request (the full prompt, not the truncated title)
  // as a brand-new task and follow it.
  const rerunPrompt = detail?.prompt ?? selected?.prompt;
  const runAgain = useCallback(async () => {
    // Mark the attempt so the store's createError only surfaces here after a
    // re-run this view actually started — never a stale error from elsewhere.
    setRerunAttempted(true);
    const created = await createTask(rerunPrompt ?? title);
    if (created) {
      router.push(`/tasks/${created.taskId}`);
    }
  }, [createTask, router, rerunPrompt, title]);
  const editRerun = useCallback(() => {
    // Hand the full prompt to the composer through transient state, not the URL.
    setEditRerunPrompt(rerunPrompt ?? title);
    router.push("/tasks/new");
  }, [rerunPrompt, router, title]);

  const sidebar = (
    <div className="flex flex-col gap-1">
      <Link
        href="/tasks"
        className="mb-2 flex items-center gap-2 rounded-xl px-3 py-1.5 text-[13px] text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
      >
        <ArrowLeft className="size-4" /> All tasks
      </Link>
      <SidebarLabel>In this run</SidebarLabel>
      <SidebarItem icon={CircleDot} label="Thread" active />
      {plan && (
        <SidebarItem
          icon={ListChecks}
          label={`Plan rev ${String(plan.revision)}`}
          count={plan.steps.length}
        />
      )}
      <SidebarItem icon={ShieldCheck} label="Evidence" count={evidence.length} />
      <div className="my-3 h-px bg-border" />
      <SidebarLabel>Other tasks</SidebarLabel>
      {tasks
        .filter((task) => task.taskId !== taskId)
        .slice(0, 4)
        .map((task) => (
          <SidebarItem
            key={task.taskId}
            href={`/tasks/${task.taskId}`}
            dot={statusDot(task.status)}
            label={task.title}
          />
        ))}
    </div>
  );

  if (!selected && !detail && detailError) {
    return (
      <AppShell active="Tasks" sidebar={sidebar}>
        <div className="mx-auto max-w-lg py-16 text-center">
          <XCircle className="mx-auto size-6 text-status-failed" />
          <h1 className="mt-3 text-xl font-semibold tracking-tight">Task unavailable</h1>
          <p className="mt-2 text-sm text-muted-foreground">{detailError}</p>
          <Link
            href="/tasks"
            className="mt-4 inline-flex items-center gap-1.5 rounded-xl bg-brand px-3 py-1.5 text-[13px] font-medium text-brand-foreground hover:bg-brand-hover"
          >
            Back to tasks
          </Link>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell active="Tasks" sidebar={sidebar}>
      <div className="flex min-h-[calc(100vh-14rem)] flex-col">
        {/* toolbar */}
        <div className="mb-4 flex items-start gap-3">
          <div className="min-w-0 flex-1">
            <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-brand-accent">
              Task · <span className="font-mono normal-case">{taskId}</span>
            </p>
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="truncate text-pretty text-xl font-semibold tracking-tight">{title}</h1>
              <StatusChip status={status} />
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-1.5">
            {!terminal && (selected ?? detail) && (
              <StopRunControl onStop={() => void cancelTask(taskId)} cancelling={cancelling} />
            )}
            <button
              type="button"
              onClick={() => setPanelOpen((open) => !open)}
              aria-pressed={panelOpen}
              title="Toggle run panel"
              className={cn(
                "flex size-8 items-center justify-center rounded-lg border transition-colors",
                panelOpen
                  ? "border-brand/30 bg-brand/10 text-brand-accent"
                  : "border-border text-muted-foreground hover:bg-accent hover:text-foreground",
              )}
            >
              <PanelRight className="size-4" />
              <span className="sr-only">Toggle run panel</span>
            </button>
          </div>
        </div>

        {(detailError ?? streamError) && (selected || detail) && (
          <div
            className="mb-4 flex items-center gap-3 rounded-2xl border border-status-review/30 bg-status-review-bg px-4 py-3"
            role="alert"
          >
            <AlertTriangle className="size-4 shrink-0 text-status-review" />
            <p className="min-w-0 text-sm text-foreground/90">{detailError ?? streamError}</p>
          </div>
        )}

        {cancelError && (
          <div
            className="mb-4 flex items-center gap-3 rounded-2xl border border-status-failed/30 bg-status-failed-bg px-4 py-3"
            role="alert"
          >
            <Ban className="size-4 shrink-0 text-status-failed" />
            <p className="min-w-0 text-sm text-foreground/90">
              <span className="font-medium">Couldn’t stop the run.</span> {cancelError}
            </p>
          </div>
        )}

        {/* workspace: thread + right panel */}
        <div className="flex min-h-0 flex-1 flex-col gap-5 lg:flex-row">
          <div className="flex min-w-0 flex-1 flex-col">
            <div className="min-h-0 flex-1 space-y-4">
              {detail?.prompt && (
                <p className="text-[15px] leading-relaxed text-muted-foreground">{detail.prompt}</p>
              )}

              {thread.length === 0 && (
                <div className="flex gap-3">
                  <AgentAvatar />
                  <p className="mt-1 text-[15px] leading-relaxed text-muted-foreground">
                    Waiting for the first event…
                  </p>
                </div>
              )}

              {thread.map((item) => {
                if (item.kind === "narration") {
                  return (
                    <div key={item.id} className="flex gap-3">
                      <AgentAvatar />
                      <div className="min-w-0 flex-1">
                        <div className="flex items-baseline gap-2">
                          <span className="text-[13px] font-medium text-crisp">{item.label}</span>
                          <span className="font-mono text-[11px] text-muted-foreground">
                            #{item.id}
                          </span>
                        </div>
                        <p className="mt-1 whitespace-pre-wrap text-[15px] leading-relaxed text-foreground/90">
                          {item.text}
                        </p>
                      </div>
                    </div>
                  );
                }
                if (item.kind === "plan" && plan) {
                  return (
                    <div key={item.id} className="pl-10">
                      <PlanCard
                        key={`${activeInterrupt?.interruptId ?? "static"}:${String(plan.revision)}`}
                        plan={plan}
                        activeInterrupt={activeInterrupt}
                        error={planError}
                        saving={updatingPlan}
                        onUpdate={updatePlan}
                      />
                    </div>
                  );
                }
                if (item.kind === "interrupt" && activeInterrupt && !terminal) {
                  return (
                    <div key={item.id} className="pl-10">
                      <ApprovalCard
                        key={activeInterrupt.interruptId}
                        interrupt={activeInterrupt}
                        submitting={submittingDecision}
                        submittedDecision={submittedDecision}
                        error={actionError}
                        onDecide={decide}
                      />
                    </div>
                  );
                }
                if (item.kind === "result") {
                  const success = item.status === "completed";
                  return (
                    <div
                      key={item.id}
                      className={cn(
                        "ml-10 rounded-2xl border p-4",
                        success
                          ? "border-status-done/30 bg-status-done-bg"
                          : "border-border bg-card",
                      )}
                    >
                      <p className="flex items-center gap-2 text-sm font-medium">
                        {success ? (
                          <CheckCircle2 className="size-4 text-status-done" />
                        ) : (
                          <XCircle className="size-4 text-status-failed" />
                        )}
                        {success
                          ? "Run completed"
                          : item.status === "rejected"
                            ? "Run stopped — plan rejected"
                            : item.status === "cancelled"
                              ? "Run stopped — you cancelled it"
                              : "Run failed"}
                      </p>
                      {success && detail?.result && (
                        <p className="mt-2 whitespace-pre-wrap text-[15px] leading-relaxed text-foreground/90">
                          {detail.result}
                        </p>
                      )}
                      <TaskResultActions
                        title={title}
                        prompt={rerunPrompt}
                        result={success ? detail?.result : undefined}
                        evidence={evidence}
                        onRunAgain={() => void runAgain()}
                        runningAgain={creating}
                        runError={rerunAttempted ? createError : undefined}
                        onEditRerun={editRerun}
                      />
                    </div>
                  );
                }
                if (item.kind === "marker") {
                  return <TaskThreadMarker key={item.id} label={item.label} detail={item.detail} />;
                }
                return null;
              })}

              {/* Detail knows about a pending interrupt the stream has not replayed yet */}
              {activeInterrupt && !terminal && !hasInterruptItem && (
                <div className="space-y-4 pl-10">
                  {plan && !hasPlanItem && (
                    <PlanCard
                      key={`${activeInterrupt.interruptId}:${String(plan.revision)}`}
                      plan={plan}
                      activeInterrupt={activeInterrupt}
                      error={planError}
                      saving={updatingPlan}
                      onUpdate={updatePlan}
                    />
                  )}
                  <ApprovalCard
                    key={activeInterrupt.interruptId}
                    interrupt={activeInterrupt}
                    submitting={submittingDecision}
                    submittedDecision={submittedDecision}
                    error={actionError}
                    onDecide={decide}
                  />
                </div>
              )}
            </div>

            {/* status bar */}
            {!terminal && (
              <div className="mt-4 shrink-0 rounded-xl border border-border bg-card/60 p-2.5">
                <div className="flex flex-wrap items-center gap-2">
                  <span
                    className={cn(
                      "flex items-center gap-1.5 text-[12px]",
                      status === "waiting-approval"
                        ? "text-status-review"
                        : "text-muted-foreground",
                    )}
                  >
                    <span className="relative flex size-1.5">
                      {(status === "running" || status === "queued") && (
                        <span className="absolute inline-flex size-full animate-ping rounded-full bg-status-running opacity-75" />
                      )}
                      <span
                        className={cn(
                          "relative inline-flex size-1.5 rounded-full",
                          status === "waiting-approval" ? "bg-status-review" : "bg-status-running",
                        )}
                      />
                    </span>
                    {status === "waiting-approval"
                      ? "Paused — the agent is waiting for your review above"
                      : "Agent is working — it pauses at the plan checkpoint for your review"}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Run panel. On lg+ it is the right rail; below lg it stacks under the
              thread (via the parent's flex-col) so its tabs stay reachable on a
              phone instead of being hidden — the header toggle controls it in
              both layouts. */}
          {panelOpen && selected && (
            <aside className="w-full shrink-0 self-stretch lg:w-96 xl:w-[28rem]">
              <RunPanel
                selected={selected}
                detail={detail}
                events={events}
                evidence={evidence}
                plan={plan}
                connectionState={connectionState}
                mode={mode}
                onClose={() => setPanelOpen(false)}
              />
            </aside>
          )}
        </div>
      </div>
    </AppShell>
  );
}

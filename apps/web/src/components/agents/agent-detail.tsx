"use client";

import { ArrowLeft, Bot, ListChecks, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { CapabilityChip } from "@/components/capability-chip";
import { AppShell } from "@/components/shell/app-shell";
import { SidebarItem, SidebarLabel } from "@/components/shell/sidebar-nav";
import { StatusChip } from "@/components/shell/status-chip";
import { agentRuntimeCopy } from "@/lib/agent-cards";
import { describeTaskCounts, summarizeTasks } from "@/lib/task-count-summary";
import { formatTaskAge } from "@/lib/task-time";
import { PLAN_STEP_MAX_COUNT, PLAN_STEP_MAX_LENGTH } from "@/lib/task-types";
import { useTasksStore } from "@/lib/tasks-store";
import { useDemoStatus } from "@/lib/use-demo-status";
import { cn } from "@/lib/utils";

const panelTabs = [
  { key: "capabilities", label: "Capabilities", icon: ShieldCheck },
  { key: "recent-tasks", label: "Recent tasks", icon: ListChecks },
] as const;

type TabKey = (typeof panelTabs)[number]["key"];

const DECISION_VERBS = ["approve", "reject", "respond"] as const;

function behaviorContract(mode: "api" | "fixture") {
  const runtimeCopy = agentRuntimeCopy(mode);
  return [
    {
      title: "Creates a plan",
      detail: `Proposes up to ${PLAN_STEP_MAX_COUNT} steps of at most ${PLAN_STEP_MAX_LENGTH.toLocaleString("en-US")} characters each. The plan stays editable until it is approved.`,
    },
    {
      title: "Waits for approval",
      detail: "Every run pauses at an interrupt. Nothing executes until a reviewer decides.",
    },
    {
      title: runtimeCopy.executionTitle,
      detail: runtimeCopy.executionDetail,
    },
    {
      title: "Records evidence",
      detail: "Each run produces an evidence-backed brief tied to the recorded events.",
    },
  ];
}

function CapabilitiesPanel() {
  const { status, loading } = useDemoStatus();

  if (loading) {
    return (
      <p className="p-4 text-[13px] text-muted-foreground" role="status">
        Checking the runtime…
      </p>
    );
  }
  if (!status) {
    return (
      <p className="m-4 rounded-xl bg-status-review-bg px-3.5 py-2.5 text-[13px] text-status-review">
        The runtime did not report its capabilities. States are unknown, not assumed.
      </p>
    );
  }
  return (
    <div className="p-3">
      <ul className="space-y-1">
        {status.capabilities.map((capability) => (
          <li
            key={capability.name}
            className="flex items-center justify-between rounded-xl px-2.5 py-2 hover:bg-accent/50"
          >
            <span className="font-mono text-[13px]">{capability.name}</span>
            <CapabilityChip state={capability.state} />
          </li>
        ))}
      </ul>
      <p className="mt-3 px-2.5 text-[12px] leading-relaxed text-muted-foreground">
        {status.safeReason}
      </p>
    </div>
  );
}

function RecentTasksPanel() {
  const { tasks, loadingTasks } = useTasksStore();

  // Advance a slow client-only clock so each row's relative creation age
  // ("just now" → "1m ago") keeps moving without a task update or refresh.
  const [, advanceAgeClock] = useState(0);
  useEffect(() => {
    const timer = window.setInterval(() => advanceAgeClock((tick) => tick + 1), 60_000);
    return () => window.clearInterval(timer);
  }, []);

  if (loadingTasks) {
    return (
      <p className="p-4 text-[13px] text-muted-foreground" role="status">
        Loading tasks…
      </p>
    );
  }
  if (tasks.length === 0) {
    return (
      <div className="p-4">
        <p className="text-[13px] font-medium text-crisp">No tasks yet this session</p>
        <p className="mt-0.5 text-[12px] text-muted-foreground">
          Runs by this agent will appear here.{" "}
          <Link href="/tasks/new" className="text-brand-accent hover:underline">
            Create a task
          </Link>{" "}
          to see one.
        </p>
      </div>
    );
  }
  const summary = describeTaskCounts(summarizeTasks(tasks));
  return (
    <div>
      {summary !== undefined && (
        <p className="border-b border-border px-4 py-2 text-[12px] text-muted-foreground">
          {summary}
        </p>
      )}
      <ul className="divide-y divide-border">
        {tasks.map((task) => {
          const age = formatTaskAge(task.createdAt);
          return (
            <li key={task.taskId}>
              <Link
                href={`/tasks/${task.taskId}`}
                className="flex items-center gap-3 px-4 py-2.5 transition-colors hover:bg-accent/50"
              >
                <span className="min-w-0 flex-1 truncate text-[13px] text-foreground">
                  {task.title}
                </span>
                {age !== undefined && (
                  <span
                    className="shrink-0 whitespace-nowrap text-[12px] text-muted-foreground"
                    title={task.createdAt}
                  >
                    {age}
                  </span>
                )}
                <StatusChip status={task.status} />
              </Link>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export function AgentDetail() {
  const [tab, setTab] = useState<TabKey>("capabilities");
  const { mode, apiBaseUrl } = useTasksStore();
  const runtimeCopy = agentRuntimeCopy(mode);

  const sidebar = (
    <div className="flex flex-col gap-1">
      <Link
        href="/agents"
        className="mb-2 flex items-center gap-2 rounded-xl px-3 py-1.5 text-[13px] text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
      >
        <ArrowLeft className="size-4" /> All agents
      </Link>
      <SidebarLabel>Inspect</SidebarLabel>
      {panelTabs.map((t) => (
        <SidebarItem
          key={t.key}
          icon={t.icon}
          label={t.label}
          active={tab === t.key}
          onClick={() => setTab(t.key)}
        />
      ))}
    </div>
  );

  return (
    <AppShell active="Agents" sidebar={sidebar}>
      <div className="mb-6 flex items-center gap-3">
        <span className="flex size-9 items-center justify-center rounded-lg bg-secondary text-secondary-foreground">
          <Bot className="size-4.5" />
        </span>
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-wide text-brand-accent">
            Agent
          </p>
          <h1 className="text-2xl font-semibold tracking-tight">{runtimeCopy.name}</h1>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Behavior contract — read-only, no chat-to-configure, no save. */}
        <div className="flex flex-col rounded-2xl border border-border bg-card lg:min-h-[32rem]">
          <div className="border-b border-border px-4 py-2.5">
            <p className="text-[13px] font-medium text-crisp">About this agent</p>
            <p className="text-[11px] text-muted-foreground">{runtimeCopy.contractDescription}</p>
          </div>
          <ol className="flex-1 space-y-4 overflow-auto p-4">
            {behaviorContract(mode).map((step, index) => (
              <li key={step.title} className="flex gap-3">
                <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-brand-soft font-mono text-[12px] font-medium text-brand-accent">
                  {index + 1}
                </span>
                <div className="min-w-0">
                  <p className="text-[13px] font-medium text-crisp">{step.title}</p>
                  <p className="mt-0.5 text-[13px] leading-relaxed text-muted-foreground">
                    {step.detail}
                  </p>
                </div>
              </li>
            ))}
            <li className="flex gap-3">
              <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-brand-soft font-mono text-[12px] font-medium text-brand-accent">
                ✓
              </span>
              <div className="min-w-0">
                <p className="text-[13px] font-medium text-crisp">Decisions a reviewer can make</p>
                <div className="mt-1.5 flex flex-wrap gap-1">
                  {DECISION_VERBS.map((verb) => (
                    <span
                      key={verb}
                      className="rounded-full bg-accent px-2 py-0.5 font-mono text-[11px] text-muted-foreground"
                    >
                      {verb}
                    </span>
                  ))}
                </div>
              </div>
            </li>
          </ol>
          <div className="border-t border-border px-4 py-2.5">
            <span className="font-mono text-[11px] text-muted-foreground">
              {runtimeCopy.contractFooter}
            </span>
          </div>
        </div>

        {/* Live runtime data — real capabilities and real tasks only. */}
        <div className="flex flex-col overflow-hidden rounded-2xl border border-border bg-card lg:min-h-[32rem]">
          <div className="flex items-center gap-1 border-b border-border px-2 py-1.5">
            {panelTabs.map((t) => (
              <button
                key={t.key}
                type="button"
                onClick={() => setTab(t.key)}
                className={cn(
                  "rounded-lg px-2.5 py-1 font-mono text-[12px] transition-colors",
                  tab === t.key
                    ? "bg-accent text-foreground"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                {t.label}
              </button>
            ))}
          </div>

          <div className="flex-1 overflow-auto">
            {tab === "capabilities" ? <CapabilitiesPanel /> : <RecentTasksPanel />}
          </div>

          <div className="border-t border-border px-4 py-2.5">
            <span className="font-mono text-[11px] text-muted-foreground">
              reported by {mode === "fixture" ? "the local fixture adapter" : apiBaseUrl}
            </span>
          </div>
        </div>
      </div>
    </AppShell>
  );
}

"use client";

import { ArrowUpRight, Bot, LayoutGrid, Plus, RefreshCw, Server } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { CapabilityChip } from "@/components/capability-chip";
import { AppShell } from "@/components/shell/app-shell";
import { PageHeader } from "@/components/shell/page-header";
import { SidebarItem, SidebarLabel } from "@/components/shell/sidebar-nav";
import {
  activeAgentCount,
  agentRuntimeCopy,
  agentSessionTaskLabel,
  type AgentCardModel,
  deriveAgentCards,
  deriveRegisteredAgentCards,
  mostRecentCreatedAt,
} from "@/lib/agent-cards";
import { formatTaskAge } from "@/lib/task-time";
import type { TaskSummary } from "@/lib/task-types";
import { useTasksStore } from "@/lib/tasks-store";
import { useAgents } from "@/lib/use-agents";
import { useDemoStatus } from "@/lib/use-demo-status";
import { cn } from "@/lib/utils";

import { type AgentFilter, agentFilterToQuery, readAgentFilter } from "./agents-url";

const cardStateDot: Record<AgentCardModel["state"], { dot: string; text: string }> = {
  active: { dot: "bg-status-running breathe", text: "text-status-running" },
  inactive: { dot: "bg-status-review", text: "text-status-review" },
  gated: { dot: "bg-status-review", text: "text-status-review" },
  unknown: { dot: "bg-muted-foreground", text: "text-muted-foreground" },
};

function CardStateIndicator({ card }: { card: AgentCardModel }) {
  if (card.state === "gated" || card.state === "unknown") {
    return (
      <CapabilityChip
        state={card.state === "gated" ? "unavailable" : "unknown"}
        label={card.stateLabel}
      />
    );
  }
  const s = cardStateDot[card.state];
  return (
    <span className={cn("flex items-center gap-1 text-[11px] font-medium", s.text)}>
      <span className={cn("size-1.5 rounded-full", s.dot)} aria-hidden />
      {card.stateLabel}
    </span>
  );
}

export function AgentFleet() {
  const { mode, tasks, loadingTasks, listError } = useTasksStore();
  const {
    status,
    loading: statusLoading,
    refetch: refetchStatus,
  } = useDemoStatus(mode === "fixture");
  const registry = useAgents(mode === "api");

  const runtimeCopy = agentRuntimeCopy(mode);
  const cards =
    mode === "fixture"
      ? deriveAgentCards(status, mode)
      : registry.available
        ? deriveRegisteredAgentCards(registry.agents)
        : [];
  const activeCount = activeAgentCount(cards);
  const availableCapabilities =
    status?.capabilities.filter((capability) => capability.state === "available") ?? [];
  const taskActivity = useMemo(() => {
    const byAgent = new Map<string, TaskSummary[]>();
    for (const task of tasks) {
      if (!task.agentId) continue;
      const current = byAgent.get(task.agentId);
      if (current) current.push(task);
      else byAgent.set(task.agentId, [task]);
    }
    return {
      all: { count: tasks.length, mostRecent: mostRecentCreatedAt(tasks) },
      byAgent: new Map(
        [...byAgent].map(([agentId, agentTasks]) => [
          agentId,
          { count: agentTasks.length, mostRecent: mostRecentCreatedAt(agentTasks) },
        ]),
      ),
    };
  }, [tasks]);

  // Advance a slow client-only clock so the "last run" age keeps moving
  // ("just now" → "1m ago") without a store or filter update (mirrors the
  // Recent tasks panel).
  const [, advanceAgeClock] = useState(0);
  useEffect(() => {
    const timer = window.setInterval(() => advanceAgeClock((tick) => tick + 1), 60_000);
    return () => window.clearInterval(timer);
  }, []);

  const [filter, setFilter] = useState<AgentFilter>("all");

  // Mirror the fleet filter in the URL so a filtered view is shareable, and
  // restore it on first load and on browser back/forward — the same contract
  // the inbox and queues use.
  const selectFilter = useCallback((next: AgentFilter) => {
    setFilter((current) => {
      if (current === next) return current;
      const query = agentFilterToQuery(next);
      const { pathname } = window.location;
      const url = query ? `${pathname}?${query}` : pathname;
      window.history.pushState(window.history.state, "", url);
      return next;
    });
  }, []);

  useEffect(() => {
    const syncFromUrl = () =>
      setFilter(readAgentFilter(new URLSearchParams(window.location.search)));
    syncFromUrl();
    window.addEventListener("popstate", syncFromUrl);
    return () => window.removeEventListener("popstate", syncFromUrl);
  }, []);

  const visibleCardIds = new Set(
    (filter === "active" ? cards.filter((card) => card.state === "active") : cards).map(
      (card) => card.id,
    ),
  );

  const sidebar = (
    <nav className="flex flex-col gap-1">
      <SidebarLabel>Fleet</SidebarLabel>
      <SidebarItem
        icon={LayoutGrid}
        label="All agents"
        count={cards.length}
        active={filter === "all"}
        onClick={() => selectFilter("all")}
      />
      <SidebarItem
        icon={Bot}
        label="Active"
        count={activeCount}
        active={filter === "active"}
        onClick={() => selectFilter("active")}
      />
      <div className="my-3 h-px bg-border" />
      <p className="px-3 text-[12px] leading-relaxed text-muted-foreground">
        Agents are owned by the connected task source. Create and manage them through workspace
        settings.
      </p>
    </nav>
  );

  return (
    <AppShell active="Agents" sidebar={sidebar}>
      <PageHeader
        eyebrow="Fleet"
        title="Agents"
        description={runtimeCopy.fleetDescription}
        actions={
          mode === "api" && registry.available ? (
            <Link
              href="/settings/agents"
              className="inline-flex items-center gap-1.5 rounded-xl bg-brand px-3.5 py-2 text-[13px] font-semibold text-brand-foreground transition-opacity hover:opacity-90"
            >
              <Plus aria-hidden className="size-4" />
              New agent
            </Link>
          ) : undefined
        }
      />

      {mode === "api" && !registry.loading && registry.error !== undefined && (
        <div className="mb-4 rounded-xl bg-status-review-bg px-3.5 py-2.5 text-[13px] text-status-review">
          <p>The workspace agent registry could not be loaded. No agents are assumed.</p>
          <button
            type="button"
            onClick={registry.refetch}
            className="mt-2 inline-flex items-center gap-1.5 rounded-lg border border-status-review/40 px-2.5 py-1 text-[12px] font-medium transition-colors hover:bg-status-review/10"
          >
            <RefreshCw className="size-3.5" />
            Check again
          </button>
        </div>
      )}
      {mode === "fixture" && !statusLoading && status === undefined && (
        <div className="mb-4 rounded-xl bg-status-review-bg px-3.5 py-2.5 text-[13px] text-status-review">
          <p>
            The runtime did not report its capabilities, so agent states are shown as unknown rather
            than assumed.
          </p>
          <button
            type="button"
            onClick={refetchStatus}
            className="mt-2 inline-flex items-center gap-1.5 rounded-lg border border-status-review/40 px-2.5 py-1 text-[12px] font-medium transition-colors hover:bg-status-review/10"
          >
            <RefreshCw className="size-3.5" />
            Check again
          </button>
        </div>
      )}
      {(mode === "api" ? registry.loading : statusLoading) && (
        <p className="mb-4 text-[13px] text-muted-foreground" role="status">
          {mode === "api" ? "Loading registered agents…" : "Checking runtime capabilities…"}
        </p>
      )}

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {cards.map((card) => {
          if (!visibleCardIds.has(card.id)) return null;
          const activity = card.agentId
            ? (taskActivity.byAgent.get(card.agentId) ?? { count: 0, mostRecent: undefined })
            : taskActivity.all;
          const lastRunAge =
            !loadingTasks && listError === undefined
              ? formatTaskAge(activity.mostRecent)
              : undefined;
          const actionHref = card.actionHref ?? card.configureHref;
          return (
            <div
              key={card.id}
              className="group flex flex-col rounded-2xl border border-border bg-card p-4 transition-colors hover:border-brand/40"
            >
              <div className="flex items-start gap-3">
                <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-secondary text-secondary-foreground">
                  {card.id === "classic-langsmith" ? (
                    <Server className="size-4.5" />
                  ) : (
                    <Bot className="size-4.5" />
                  )}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-semibold text-crisp">{card.name}</h3>
                    <CardStateIndicator card={card} />
                  </div>
                  <p className="mt-1 text-[13px] leading-relaxed text-muted-foreground">
                    {card.description}
                  </p>
                </div>
              </div>

              {!card.agentId &&
                card.id !== "classic-langsmith" &&
                availableCapabilities.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1">
                    {availableCapabilities.map((capability) => (
                      <span
                        key={capability.name}
                        className="rounded-full bg-accent px-2 py-0.5 font-mono text-[11px] text-muted-foreground"
                      >
                        {capability.name}
                      </span>
                    ))}
                  </div>
                )}

              <div className="mt-4 flex items-center gap-3 border-t border-border pt-3 text-[13px] text-muted-foreground">
                {card.state === "active" ? (
                  <>
                    <span className="tabular-nums">
                      {agentSessionTaskLabel(loadingTasks, activity.count, listError)}
                    </span>
                    {lastRunAge !== undefined && (
                      <span className="text-muted-foreground">· last run {lastRunAge}</span>
                    )}
                  </>
                ) : (
                  <p className="min-w-0 text-[12px] leading-relaxed">{card.gatedExplanation}</p>
                )}
                {actionHref ? (
                  <Link
                    href={actionHref}
                    className="ml-auto flex items-center gap-1 rounded-lg px-2 py-1 text-[13px] font-medium text-brand-accent transition-colors hover:bg-brand-soft"
                  >
                    {card.actionLabel ?? "Inspect"} <ArrowUpRight className="size-3.5" />
                  </Link>
                ) : (
                  <span
                    aria-disabled="true"
                    title={card.gatedExplanation}
                    className="ml-auto flex shrink-0 cursor-not-allowed items-center gap-1 rounded-lg px-2 py-1 text-[13px] font-medium text-muted-foreground/60"
                  >
                    Configure <ArrowUpRight className="size-3.5" />
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {!(mode === "api" ? registry.loading : statusLoading) && visibleCardIds.size === 0 && (
        <div className="rounded-2xl border border-dashed border-border bg-card p-8 text-center">
          <p className="text-[14px] font-medium text-crisp">
            {mode === "api" && !registry.available
              ? "No agent source connected"
              : filter === "active"
                ? "No active agents match this filter"
                : "No agents are registered yet"}
          </p>
          <p className="mt-1 text-[13px] text-muted-foreground">
            {mode === "api" && !registry.available
              ? "Connect the workspace API to a supported task source before choosing an agent."
              : "Registered source agents appear here and in the task composer."}
          </p>
          {filter === "active" && (
            <button
              type="button"
              onClick={() => selectFilter("all")}
              className="mt-3 rounded-xl border border-border bg-card px-3 py-1.5 text-[13px] font-medium transition-colors hover:bg-accent"
            >
              Show all agents
            </button>
          )}
        </div>
      )}
    </AppShell>
  );
}

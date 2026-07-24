"use client";

import { ArrowUpRight, Bot, LayoutGrid, Server } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

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
  mostRecentCreatedAt,
} from "@/lib/agent-cards";
import { formatTaskAge } from "@/lib/task-time";
import { useTasksStore } from "@/lib/tasks-store";
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
  const { status, loading: statusLoading } = useDemoStatus();

  const runtimeCopy = agentRuntimeCopy(mode);
  const cards = deriveAgentCards(status, mode);
  const activeCount = activeAgentCount(cards);
  const availableCapabilities =
    status?.capabilities.filter((capability) => capability.state === "available") ?? [];

  // How long ago the local runner last started a task — only when the list is
  // trustworthy (loaded, no error), so a failed fetch never implies "no runs".
  const lastRunAge =
    !loadingTasks && listError === undefined
      ? formatTaskAge(mostRecentCreatedAt(tasks))
      : undefined;

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
        Templates and an org library are coming with the packaged agent. No additional runner
        configuration is exposed to this browser.
      </p>
    </nav>
  );

  return (
    <AppShell active="Agents" sidebar={sidebar}>
      <PageHeader eyebrow="Fleet" title="Agents" description={runtimeCopy.fleetDescription} />

      {!statusLoading && status === undefined && (
        <p className="mb-4 rounded-xl bg-status-review-bg px-3.5 py-2.5 text-[13px] text-status-review">
          The runtime did not report its capabilities, so agent states are shown as unknown rather
          than assumed.
        </p>
      )}
      {statusLoading && (
        <p className="mb-4 text-[13px] text-muted-foreground" role="status">
          Checking runtime capabilities…
        </p>
      )}

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {/* The current task runner, labeled only from browser-known evidence. */}
        {visibleCardIds.has(cards[0].id) && (
          <div className="group flex flex-col rounded-2xl border border-border bg-card p-4 transition-colors hover:border-brand/40">
            <div className="flex items-start gap-3">
              <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-secondary text-secondary-foreground">
                <Bot className="size-4.5" />
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-semibold text-crisp">{cards[0].name}</h3>
                  <CardStateIndicator card={cards[0]} />
                </div>
                <p className="mt-1 text-[13px] leading-relaxed text-muted-foreground">
                  {cards[0].description}
                </p>
              </div>
            </div>

            {availableCapabilities.length > 0 && (
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
              <span className="tabular-nums">
                {agentSessionTaskLabel(loadingTasks, tasks.length, listError)}
              </span>
              {lastRunAge !== undefined && (
                <span className="text-muted-foreground">· last run {lastRunAge}</span>
              )}
              <div className="ml-auto flex items-center gap-1">
                <Link
                  href="/agents/local"
                  className="flex items-center gap-1 rounded-lg px-2 py-1 text-[13px] font-medium text-brand-accent transition-colors hover:bg-brand-soft"
                >
                  Configure <ArrowUpRight className="size-3.5" />
                </Link>
              </div>
            </div>
          </div>
        )}

        {/* Classic LangSmith deployment — gated, deliberately not configurable. */}
        {visibleCardIds.has(cards[1].id) && (
          <div className="flex flex-col rounded-2xl border border-border bg-card p-4">
            <div className="flex items-start gap-3">
              <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-secondary text-secondary-foreground">
                <Server className="size-4.5" />
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-semibold text-crisp">{cards[1].name}</h3>
                  <CardStateIndicator card={cards[1]} />
                </div>
                <p className="mt-1 text-[13px] leading-relaxed text-muted-foreground">
                  {cards[1].description}
                </p>
              </div>
            </div>

            <div className="mt-auto flex items-center gap-3 border-t border-border pt-3 text-[13px] text-muted-foreground">
              <p className="min-w-0 text-[12px] leading-relaxed">{cards[1].gatedExplanation}</p>
              <span
                aria-disabled="true"
                title={cards[1].gatedExplanation}
                className="ml-auto flex shrink-0 cursor-not-allowed items-center gap-1 rounded-lg px-2 py-1 text-[13px] font-medium text-muted-foreground/60"
              >
                Configure <ArrowUpRight className="size-3.5" />
              </span>
            </div>
          </div>
        )}
      </div>

      {visibleCardIds.size === 0 && (
        <div className="rounded-2xl border border-dashed border-border bg-card p-8 text-center">
          <p className="text-[14px] text-muted-foreground">
            No agents are reporting an active state right now.
          </p>
          <button
            type="button"
            onClick={() => selectFilter("all")}
            className="mt-3 rounded-xl border border-border bg-card px-3 py-1.5 text-[13px] font-medium transition-colors hover:bg-accent"
          >
            Show all agents
          </button>
        </div>
      )}
    </AppShell>
  );
}

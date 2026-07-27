"use client";

import { ArrowUpRight, CalendarClock, CalendarOff } from "lucide-react";

import { AppShell } from "@/components/shell/app-shell";
import { PageHeader } from "@/components/shell/page-header";
import { SidebarLabel } from "@/components/shell/sidebar-nav";
import { useAgents } from "@/lib/use-agents";
import { useSchedules } from "@/lib/use-schedules";

const PLANS_DOC_URL = "https://github.com/spencerthomas/deepwork/blob/main/docs/PLANS.md";
const CREATE_DISABLED_REASON =
  "The runs a schedule triggers don't yet appear in your task inbox, so creating one here would be misleading. Manage schedules directly on your task source until that's wired up.";

function formatTimestamp(iso: string): string {
  const parsed = new Date(iso);
  return Number.isNaN(parsed.getTime()) ? iso : parsed.toLocaleString();
}

export function SchedulesView() {
  const { available, schedules, loading, error, refetch } = useSchedules();
  const { agents } = useAgents();
  const agentNames = new Map(agents.map((agent) => [agent.agentId, agent.name]));

  const sidebar = (
    <nav className="flex flex-col gap-1">
      <SidebarLabel>Schedules</SidebarLabel>
      <p className="px-3 text-[12px] leading-relaxed text-muted-foreground">
        Recurring runs registered on your task source. Read-only for now.
      </p>
    </nav>
  );

  return (
    <AppShell active="Schedules" sidebar={sidebar}>
      <PageHeader
        eyebrow="Recurring"
        title="Schedules"
        description="Recurring runs registered on your connected task source."
      />

      {loading ? (
        <div className="rounded-2xl border border-border bg-card p-8 text-center text-[13px] text-muted-foreground">
          Checking schedule availability…
        </div>
      ) : error !== undefined ? (
        <div className="rounded-2xl border border-status-failed/30 bg-status-failed-bg p-6 text-center">
          <p className="text-sm">
            <span className="font-medium">Schedules unavailable.</span>{" "}
            <span className="text-muted-foreground">{error}</span>
          </p>
          <button
            type="button"
            onClick={refetch}
            className="mt-3 rounded-xl border border-border bg-card px-3 py-1.5 text-[13px] font-medium transition-colors hover:bg-accent"
          >
            Try again
          </button>
        </div>
      ) : !available ? (
        <div className="rounded-2xl border border-border bg-card p-8">
          <div className="mx-auto flex max-w-md flex-col items-center text-center">
            <span className="flex size-11 items-center justify-center rounded-xl bg-secondary text-secondary-foreground">
              <CalendarOff className="size-5" />
            </span>
            <h2 className="mt-3 text-lg font-semibold tracking-tight text-crisp">
              No task source is configured
            </h2>
            <p className="mt-2 text-[13px] leading-relaxed text-muted-foreground">
              Schedules read from your connected task source's own recurring-run registry. Connect a
              real task source to see and eventually manage them here.
            </p>
            <a
              href={PLANS_DOC_URL}
              target="_blank"
              rel="noreferrer"
              className="mt-4 flex items-center gap-1 rounded-lg px-2 py-1 text-[13px] font-medium text-brand-accent transition-colors hover:bg-brand-soft"
            >
              Read the delivery plan (docs/PLANS.md) <ArrowUpRight className="size-3.5" />
            </a>
          </div>
        </div>
      ) : schedules.length === 0 ? (
        <div className="rounded-2xl border border-border bg-card p-8">
          <div className="mx-auto flex max-w-md flex-col items-center text-center">
            <span className="flex size-11 items-center justify-center rounded-xl bg-secondary text-secondary-foreground">
              <CalendarClock className="size-5" />
            </span>
            <h2 className="mt-3 text-lg font-semibold tracking-tight text-crisp">
              No schedules yet
            </h2>
            <p className="mt-2 text-[13px] leading-relaxed text-muted-foreground">
              Your task source has no recurring runs registered.
            </p>
            <button
              type="button"
              disabled
              title={CREATE_DISABLED_REASON}
              className="mt-4 cursor-not-allowed rounded-xl bg-brand px-3 py-2 text-[13px] font-medium text-brand-foreground opacity-50"
            >
              Create schedule
            </button>
            <p className="mt-2 max-w-sm text-[12px] leading-relaxed text-muted-foreground">
              {CREATE_DISABLED_REASON}
            </p>
          </div>
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-border bg-card">
          <div className="flex items-center justify-between border-b border-border px-4 py-3">
            <p className="text-[13px] font-medium text-crisp">
              {schedules.length} schedule{schedules.length === 1 ? "" : "s"}
            </p>
            <button
              type="button"
              disabled
              title={CREATE_DISABLED_REASON}
              className="cursor-not-allowed rounded-xl bg-brand px-3 py-1.5 text-[13px] font-medium text-brand-foreground opacity-50"
            >
              Create schedule
            </button>
          </div>
          <div className="divide-y divide-border">
            {schedules.map((schedule) => (
              <div
                key={schedule.scheduleId}
                className="flex flex-wrap items-center justify-between gap-3 px-4 py-3"
              >
                <div className="min-w-0">
                  <p className="font-mono text-[13px] font-medium text-crisp">
                    {schedule.cronExpression}
                    {schedule.timezone && (
                      <span className="ml-2 text-[11px] font-normal text-muted-foreground">
                        {schedule.timezone}
                      </span>
                    )}
                  </p>
                  <p className="mt-0.5 text-[12px] text-muted-foreground">
                    {agentNames.get(schedule.agentId) ?? schedule.agentId}
                  </p>
                </div>
                <p className="shrink-0 text-[12px] text-muted-foreground">
                  Created {formatTimestamp(schedule.createdAt)}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </AppShell>
  );
}

"use client";

import { ArrowUpRight, Calendar, CalendarOff, Clock, Pause } from "lucide-react";

import { CapabilityChip } from "@/components/capability-chip";
import { AppShell } from "@/components/shell/app-shell";
import { PageHeader } from "@/components/shell/page-header";
import { SidebarItem, SidebarLabel } from "@/components/shell/sidebar-nav";
import { CAPABILITY_NAMES, capabilityState } from "@/lib/demo-status";
import { useDemoStatus } from "@/lib/use-demo-status";

const PLANS_DOC_URL = "https://github.com/spencerthomas/deepwork/blob/main/docs/PLANS.md";

export function SchedulesView() {
  const { status, loading } = useDemoStatus();
  const durableJobs = capabilityState(status, CAPABILITY_NAMES.durableJobs);

  const sidebar = (
    <nav className="flex flex-col gap-1">
      <SidebarLabel>Schedules</SidebarLabel>
      <SidebarItem icon={Calendar} label="All" count={0} active />
      <SidebarItem icon={Clock} label="Active" count={0} />
      <SidebarItem icon={Pause} label="Paused" count={0} />
    </nav>
  );

  return (
    <AppShell active="Schedules" sidebar={sidebar}>
      <PageHeader
        eyebrow="Recurring"
        title="Schedules"
        description="Recurring runs that dispatch themselves. Not available in the local runtime — nothing here is scheduled or running in the background."
      />

      <div className="rounded-2xl border border-border bg-card p-8">
        <div className="mx-auto flex max-w-md flex-col items-center text-center">
          <span className="flex size-11 items-center justify-center rounded-xl bg-secondary text-secondary-foreground">
            <CalendarOff className="size-5" />
          </span>
          <div className="mt-4 flex items-center gap-2">
            <span className="rounded-full bg-accent px-2 py-0.5 font-mono text-[11px] text-muted-foreground">
              {CAPABILITY_NAMES.durableJobs}
            </span>
            {loading ? (
              <span className="text-[12px] text-muted-foreground" role="status">
                checking…
              </span>
            ) : (
              <CapabilityChip state={durableJobs} />
            )}
          </div>
          <h2 className="mt-3 text-lg font-semibold tracking-tight text-crisp">
            Schedules need a durable job runner
          </h2>
          <p className="mt-2 text-[13px] leading-relaxed text-muted-foreground">
            The local runtime executes tasks only while the API process is alive. Until a durable
            job runner ships, no schedule can be created, stored, or fired.
          </p>
          {!loading && status === undefined && (
            <p className="mt-3 rounded-xl bg-status-review-bg px-3.5 py-2 text-[12px] text-status-review">
              The runtime did not report this capability, so its state is shown as unknown.
            </p>
          )}
          <a
            href={PLANS_DOC_URL}
            target="_blank"
            rel="noreferrer"
            className="mt-4 flex items-center gap-1 rounded-lg px-2 py-1 text-[13px] font-medium text-brand transition-colors hover:bg-brand-soft"
          >
            Read the delivery plan (docs/PLANS.md) <ArrowUpRight className="size-3.5" />
          </a>
        </div>
      </div>
    </AppShell>
  );
}

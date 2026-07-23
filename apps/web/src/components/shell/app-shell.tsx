"use client";

import { BookText, ChevronDown, Plus, Settings } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";
import { useState } from "react";

import { runtimeDisclosure } from "@/lib/runtime-disclosure";
import { taskClient } from "@/lib/task-client";
import { cn } from "@/lib/utils";

import { CommandBar } from "./command-bar";
import { ThemeToggle } from "./theme-toggle";

const tabs = [
  { label: "Tasks", href: "/tasks" },
  { label: "Approvals", href: "/approvals" },
  { label: "Agents", href: "/agents" },
  { label: "Schedules", href: "/schedules" },
  { label: "Activity", href: "/activity" },
];

function Logo() {
  return (
    <Link href="/tasks" className="flex items-center gap-2">
      <span className="flex size-6 items-center justify-center rounded-md bg-brand text-brand-foreground">
        <span className="size-2.5 rounded-[3px] bg-brand-foreground" />
      </span>
      <span className="text-[15px] font-semibold tracking-tight">deepwork</span>
    </Link>
  );
}

function WorkspaceSelector() {
  return (
    <button
      type="button"
      className="flex items-center gap-2 rounded-[13.6px] border border-border bg-card px-2.5 py-1.5 text-left transition-colors hover:bg-accent"
    >
      <span className="flex size-6 items-center justify-center rounded-md bg-secondary text-[11px] font-semibold text-secondary-foreground">
        DW
      </span>
      <span className="hidden leading-tight sm:block">
        <span className="block text-[13px] font-medium">local</span>
        <span className="block text-[11px] text-muted-foreground">personal workspace</span>
      </span>
      <ChevronDown className="size-3.5 text-muted-foreground" />
    </button>
  );
}

/**
 * Persistent runtime disclosure. Honesty rule from docs/DESIGN.md: fixture or
 * local-runtime mode must stay unmistakable, so this strip is not dismissible.
 */
function RuntimeBanner() {
  const fixture = taskClient.mode === "fixture";
  return (
    <div className="flex min-h-10 items-center justify-center gap-2 bg-brand px-4 text-center text-[13px] text-brand-foreground">
      <span className="font-medium">{runtimeDisclosure(taskClient.mode)}</span>
      <span
        className="hidden rounded-md bg-white/15 px-1.5 py-0.5 font-mono text-[11px] sm:inline"
        title={taskClient.apiBaseUrl}
      >
        {fixture ? "fixture" : taskClient.apiBaseUrl}
      </span>
    </div>
  );
}

export function AppShell({
  active,
  sidebar,
  rail,
  children,
}: {
  active: string;
  sidebar?: ReactNode;
  rail?: ReactNode;
  children: ReactNode;
}) {
  const [cmdOpen, setCmdOpen] = useState(false);

  return (
    <div className="min-h-screen bg-background">
      <CommandBar open={cmdOpen} onOpenChange={setCmdOpen} />

      <RuntimeBanner />

      {/* Header: navbar (56px) + tab row (40px) */}
      <header className="sticky top-0 z-30 border-b border-border bg-background/85 backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-[92rem] items-center gap-4 px-4 sm:px-6">
          <Logo />
          <span className="text-border">/</span>
          <WorkspaceSelector />

          <button
            type="button"
            onClick={() => setCmdOpen(true)}
            className="ml-auto flex h-9 min-w-0 flex-1 items-center gap-2 rounded-full border border-border bg-foreground/[0.03] px-3.5 text-[13px] text-muted-foreground transition-colors hover:bg-foreground/[0.06] sm:max-w-sm"
          >
            <span className="truncate">Search or run a command…</span>
            <kbd className="ml-auto hidden items-center gap-0.5 rounded-md border border-border bg-background px-1.5 py-0.5 font-mono text-[11px] sm:flex">
              ⌘K
            </kbd>
          </button>

          <a
            href="https://docs.langchain.com"
            target="_blank"
            rel="noreferrer"
            className="hidden items-center gap-1.5 rounded-xl px-2.5 py-1.5 text-[13px] text-muted-foreground transition-colors hover:bg-accent hover:text-foreground md:flex"
          >
            <BookText className="size-4" />
            Docs
          </a>
          <ThemeToggle />
          <Link
            href="/settings"
            aria-label="Settings"
            className={cn(
              "flex size-8 items-center justify-center rounded-xl transition-colors hover:bg-accent hover:text-foreground",
              active === "Settings" ? "text-brand" : "text-muted-foreground",
            )}
          >
            <Settings className="size-4" />
          </Link>
          <Link
            href="/tasks/new"
            className="flex items-center gap-1.5 rounded-xl bg-brand px-3 py-1.5 text-[13px] font-medium text-brand-foreground transition-colors hover:bg-brand/90"
          >
            <Plus className="size-4" />
            <span className="hidden sm:inline">New task</span>
          </Link>
        </div>

        <nav className="mx-auto flex h-10 max-w-[92rem] items-center gap-1 px-4 sm:px-6">
          {tabs.map((tab) => {
            const isActive = active === tab.label;
            return (
              <Link
                key={tab.href}
                href={tab.href}
                aria-current={isActive ? "page" : undefined}
                className={cn(
                  "relative flex h-10 items-center px-2.5 text-[13px] transition-colors",
                  isActive
                    ? "text-crisp text-foreground"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                {tab.label}
                {isActive && (
                  <span className="absolute inset-x-2 -bottom-px h-0.5 rounded-full bg-brand" />
                )}
              </Link>
            );
          })}
        </nav>
      </header>

      {/* Body: sidebar + content + rail */}
      <div className="mx-auto flex max-w-[92rem] px-4 sm:px-6">
        {sidebar && (
          <aside className="hidden w-64 shrink-0 py-8 pr-6 lg:block xl:w-72">
            <div className="sticky top-[136px]">{sidebar}</div>
          </aside>
        )}

        <main className="min-w-0 flex-1 py-8 lg:pl-2">{children}</main>

        {rail && (
          <aside className="hidden w-72 shrink-0 py-8 pl-8 xl:block">
            <div className="sticky top-[136px]">{rail}</div>
          </aside>
        )}
      </div>
    </div>
  );
}

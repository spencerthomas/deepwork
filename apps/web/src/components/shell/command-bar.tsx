"use client";

import {
  Activity,
  Bot,
  Calendar,
  CheckCheck,
  CornerDownLeft,
  Inbox,
  Plus,
  Search,
  Settings,
} from "lucide-react";
import { useRouter } from "next/navigation";
import type { ComponentType } from "react";
import { useEffect, useMemo, useState } from "react";

import { taskRuntimePresentation } from "@/lib/task-runtime-presentation";
import { useTasksStore } from "@/lib/tasks-store";
import { cn } from "@/lib/utils";

interface Command {
  label: string;
  hint: string;
  icon: ComponentType<{ className?: string }>;
  href: string;
}

function commandsForMode(mode: "api" | "fixture"): Command[] {
  const runtimeCopy = taskRuntimePresentation(mode);
  return [
    {
      label: "New task",
      hint: runtimeCopy.commandNewTaskHint,
      icon: Plus,
      href: "/tasks/new",
    },
    { label: "Tasks", hint: "Task inbox", icon: Inbox, href: "/tasks" },
    {
      label: "Approvals",
      hint: "What task runs need from you",
      icon: CheckCheck,
      href: "/approvals",
    },
    { label: "Agents", hint: "Manage your fleet", icon: Bot, href: "/agents" },
    { label: "Schedules", hint: "Recurring runs", icon: Calendar, href: "/schedules" },
    { label: "Activity", hint: "Recent runs", icon: Activity, href: "/activity" },
    { label: "Settings", hint: "Workspace settings", icon: Settings, href: "/settings" },
  ];
}

export function CommandBar({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const router = useRouter();
  const { mode } = useTasksStore();
  const [query, setQuery] = useState("");
  const [index, setIndex] = useState(0);
  const commands = useMemo(() => commandsForMode(mode), [mode]);

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        onOpenChange(!open);
      }
      if (event.key === "Escape") onOpenChange(false);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onOpenChange]);

  const filtered = useMemo(
    () =>
      commands.filter(
        (command) =>
          command.label.toLowerCase().includes(query.toLowerCase()) ||
          command.hint.toLowerCase().includes(query.toLowerCase()),
      ),
    [query],
  );

  useEffect(() => setIndex(0), [query]);

  if (!open) return null;

  function run(href: string) {
    onOpenChange(false);
    setQuery("");
    router.push(href);
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center bg-foreground/25 px-4 pt-[12vh] backdrop-blur-sm"
      onClick={() => onOpenChange(false)}
    >
      <div
        className="w-full max-w-lg overflow-hidden rounded-2xl border border-border bg-popover shadow-2xl"
        onClick={(event) => event.stopPropagation()}
        onKeyDown={(event) => {
          if (event.key === "ArrowDown") {
            event.preventDefault();
            setIndex((current) => Math.min(current + 1, filtered.length - 1));
          }
          if (event.key === "ArrowUp") {
            event.preventDefault();
            setIndex((current) => Math.max(current - 1, 0));
          }
          const selected = filtered[index];
          if (event.key === "Enter" && selected) run(selected.href);
        }}
      >
        <div className="flex items-center gap-2.5 border-b border-border px-4">
          <Search className="size-4 text-muted-foreground" />
          <input
            // eslint-disable-next-line jsx-a11y/no-autofocus
            autoFocus
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search or run a command…"
            aria-label="Search commands"
            className="h-12 flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
          />
          <kbd className="rounded-md border border-border bg-background px-1.5 py-0.5 font-mono text-[11px] text-muted-foreground">
            esc
          </kbd>
        </div>
        <ul className="max-h-80 overflow-auto p-2">
          {filtered.length === 0 && (
            <li className="px-3 py-6 text-center text-sm text-muted-foreground">
              No commands found
            </li>
          )}
          {filtered.map((command, i) => {
            const Icon = command.icon;
            return (
              <li key={command.href}>
                <button
                  type="button"
                  onMouseEnter={() => setIndex(i)}
                  onClick={() => run(command.href)}
                  className={cn(
                    "flex w-full items-center gap-3 rounded-xl px-3 py-2 text-left text-sm transition-colors",
                    i === index ? "bg-accent" : "hover:bg-accent/60",
                  )}
                >
                  <Icon className="size-4 text-muted-foreground" />
                  <span className="font-medium">{command.label}</span>
                  <span className="text-muted-foreground">{command.hint}</span>
                  {i === index && (
                    <CornerDownLeft className="ml-auto size-3.5 text-muted-foreground" />
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}

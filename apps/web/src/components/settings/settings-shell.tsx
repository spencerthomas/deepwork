"use client";

import { ArrowLeft, Cpu, Info, Palette, Search } from "lucide-react";
import Link from "next/link";
import type { ComponentType, ReactNode } from "react";
import { useMemo, useState } from "react";

import {
  ALL_SETTINGS_SECTIONS,
  filterSettingsGroups,
  type SettingsSectionId,
} from "@/lib/settings-sections";
import { cn } from "@/lib/utils";

import { AboutSection } from "./about-section";
import { AppearanceSection } from "./appearance-section";
import { RuntimeSection } from "./runtime-section";

const sectionIcons: Record<SettingsSectionId, ComponentType<{ className?: string }>> = {
  appearance: Palette,
  runtime: Cpu,
  about: Info,
};

const sectionBodies: Record<SettingsSectionId, () => ReactNode> = {
  appearance: () => <AppearanceSection />,
  runtime: () => <RuntimeSection />,
  about: () => <AboutSection />,
};

export function SettingsShell({ section }: { section: SettingsSectionId }) {
  const [query, setQuery] = useState("");

  const active =
    ALL_SETTINGS_SECTIONS.find((candidate) => candidate.id === section) ?? ALL_SETTINGS_SECTIONS[0];

  const filteredGroups = useMemo(() => filterSettingsGroups(query), [query]);

  return (
    <div className="flex min-h-screen bg-background">
      {/* Sidebar */}
      <aside className="hidden w-72 shrink-0 flex-col border-r border-border bg-secondary/30 lg:flex">
        <div className="flex flex-col gap-4 p-4">
          <Link
            href="/tasks"
            className="flex items-center gap-2 text-[13px] font-medium text-muted-foreground transition-colors hover:text-foreground"
          >
            <ArrowLeft className="size-4" /> Back to app
          </Link>
          <div className="relative">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search settings..."
              className="w-full rounded-lg border border-border bg-background py-2 pl-8 pr-2 text-[13px] outline-none placeholder:text-muted-foreground focus:border-brand/50"
            />
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto px-3 pb-6">
          {filteredGroups.map((group) => (
            <div key={group.label} className="mb-4">
              <p className="px-3 pb-1.5 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                {group.label}
              </p>
              <div className="flex flex-col gap-0.5">
                {group.items.map((item) => {
                  const isActive = item.id === active.id;
                  const Icon = sectionIcons[item.id];
                  return (
                    <Link
                      key={item.id}
                      href={`/settings/${item.id}`}
                      aria-current={isActive ? "page" : undefined}
                      className={cn(
                        "flex items-center gap-2.5 rounded-xl px-3 py-2 text-[13px] transition-colors",
                        isActive
                          ? "bg-brand-soft text-foreground"
                          : "text-muted-foreground hover:bg-accent hover:text-foreground",
                      )}
                    >
                      <Icon className={cn("size-4", isActive && "text-brand")} />
                      <span className="truncate">{item.label}</span>
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
          {filteredGroups.length === 0 && (
            <p className="px-3 text-[13px] text-muted-foreground">
              No settings match &ldquo;{query}&rdquo;.
            </p>
          )}
        </nav>
      </aside>

      {/* Mobile top bar + content */}
      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex items-center gap-3 border-b border-border p-4 lg:hidden">
          <Link
            href="/tasks"
            className="flex items-center gap-1.5 text-[13px] text-muted-foreground"
          >
            <ArrowLeft className="size-4" /> Back
          </Link>
          <div className="flex gap-1 overflow-x-auto">
            {ALL_SETTINGS_SECTIONS.map((item) => (
              <Link
                key={item.id}
                href={`/settings/${item.id}`}
                className={cn(
                  "shrink-0 rounded-lg px-2.5 py-1 text-[12px] font-medium transition-colors",
                  item.id === active.id ? "bg-accent text-foreground" : "text-muted-foreground",
                )}
              >
                {item.label}
              </Link>
            ))}
          </div>
        </div>

        <main className="mx-auto w-full max-w-3xl flex-1 px-5 py-10 sm:px-8">
          {sectionBodies[active.id]()}
        </main>
      </div>
    </div>
  );
}

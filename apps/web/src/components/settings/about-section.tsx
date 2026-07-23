"use client";

import { ArrowUpRight } from "lucide-react";

import { Card, GroupLabel, Row, SettingsHeader } from "./settings-ui";

const REPO_URL = "https://github.com/spencerthomas/deepwork";

/** Trademark note copied from the repository README. */
const TRADEMARK_NOTE =
  "Deep Work is an independent open-source project built for compatibility with " +
  "LangChain technologies. It is not affiliated with, endorsed by, or sponsored by " +
  "LangChain, Inc. “LangChain” and “LangSmith” are trademarks of their respective " +
  "owner and are used only to describe compatibility.";

function ExternalLinkControl({ href, label }: { href: string; label: string }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="flex items-center gap-1 rounded-lg px-2 py-1 text-[13px] font-medium text-brand transition-colors hover:bg-brand-soft"
    >
      {label} <ArrowUpRight className="size-3.5" />
    </a>
  );
}

export function AboutSection() {
  return (
    <section>
      <SettingsHeader
        title="About"
        description="Version, source, and licensing for this Deep Work build."
      />

      <GroupLabel>Build</GroupLabel>
      <Card className="mb-6">
        <Row
          title="Version"
          description="From apps/web package.json."
          control={
            <span className="rounded-md bg-accent px-2 py-1 font-mono text-[12px] text-foreground">
              0.0.0
            </span>
          }
        />
        <Row
          title="License"
          description="Deep Work is released under the MIT license."
          control={
            <span className="rounded-md bg-accent px-2 py-1 font-mono text-[12px] text-foreground">
              MIT
            </span>
          }
        />
      </Card>

      <GroupLabel>Source</GroupLabel>
      <Card className="mb-6">
        <Row
          title="GitHub repository"
          description="spencerthomas/deepwork"
          control={<ExternalLinkControl href={REPO_URL} label="Open" />}
        />
        <Row
          title="README"
          description="Project overview and validation steps."
          control={<ExternalLinkControl href={`${REPO_URL}/blob/main/README.md`} label="Open" />}
        />
        <Row
          title="Architecture"
          description="System boundaries and runtime shape."
          control={
            <ExternalLinkControl href={`${REPO_URL}/blob/main/ARCHITECTURE.md`} label="Open" />
          }
        />
      </Card>

      <GroupLabel>Trademarks</GroupLabel>
      <Card>
        <p className="px-4 py-3.5 text-pretty text-[12px] leading-relaxed text-muted-foreground">
          {TRADEMARK_NOTE}
        </p>
      </Card>
    </section>
  );
}

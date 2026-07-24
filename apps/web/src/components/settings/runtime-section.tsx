"use client";

import { Check, Copy, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";

import { CapabilityChip } from "@/components/capability-chip";
import { formatRuntimeDiagnostics } from "@/lib/runtime-diagnostics";
import { taskRuntimePresentation } from "@/lib/task-runtime-presentation";
import { useTasksStore } from "@/lib/tasks-store";
import { useDemoStatus } from "@/lib/use-demo-status";
import { cn } from "@/lib/utils";

import { Card, GroupLabel, Row, SettingsHeader } from "./settings-ui";

const ACTION_CLASS =
  "flex items-center gap-1.5 rounded-xl border border-border bg-card px-3 py-1.5 text-[13px] font-medium transition-colors hover:bg-accent disabled:cursor-not-allowed disabled:opacity-60";

function MonoValue({ children }: { children: string }) {
  return (
    <span className="rounded-md bg-accent px-2 py-1 font-mono text-[12px] text-foreground">
      {children}
    </span>
  );
}

/** Read-only view of what this client is actually connected to. */
export function RuntimeSection() {
  const { mode, apiBaseUrl } = useTasksStore();
  const { status, loading, refetch } = useDemoStatus();
  const runtimeCopy = taskRuntimePresentation(mode, apiBaseUrl);

  const [copied, setCopied] = useState(false);
  const [copyFailed, setCopyFailed] = useState(false);

  useEffect(() => {
    if (!copied) {
      return;
    }
    const timer = window.setTimeout(() => setCopied(false), 2000);
    return () => window.clearTimeout(timer);
  }, [copied]);

  async function copyDiagnostics() {
    // The formatter neutralizes active Markdown/HTML in the server-provided
    // status fields, so the pasted block cannot issue an unapproved request.
    const diagnostics = formatRuntimeDiagnostics({
      mode,
      connectionTarget: runtimeCopy.settingsConnectionTarget,
      status,
    });
    try {
      await navigator.clipboard.writeText(diagnostics);
      setCopyFailed(false);
      setCopied(true);
    } catch {
      // Clipboard access can be denied; surface it instead of failing silently.
      // Clear any lingering success (e.g. a denied retry within the "Copied"
      // window) so the error and success states never both show.
      setCopied(false);
      setCopyFailed(true);
    }
  }

  return (
    <section>
      <SettingsHeader
        title="Runtime"
        description="What this client is actually connected to, and what the runtime reports about itself. Everything here is read-only."
        actions={
          <>
            {mode !== "fixture" && (
              <button type="button" onClick={refetch} disabled={loading} className={ACTION_CLASS}>
                <RefreshCw aria-hidden className={cn("size-3.5", loading && "animate-spin")} />
                {loading ? "Rechecking…" : "Recheck"}
              </button>
            )}
            <button type="button" onClick={() => void copyDiagnostics()} className={ACTION_CLASS}>
              {copied ? (
                <Check aria-hidden className="size-3.5 text-status-done" />
              ) : (
                <Copy aria-hidden className="size-3.5" />
              )}
              {copied ? "Copied" : "Copy diagnostics"}
            </button>
          </>
        }
      />

      {copyFailed && (
        <div
          role="alert"
          className="mb-4 rounded-xl border border-status-failed/35 bg-status-failed-bg px-4 py-3 text-[13px]"
        >
          Couldn’t copy the diagnostics — your browser may have blocked clipboard access.
        </div>
      )}

      <GroupLabel>Connection</GroupLabel>
      <Card className="mb-6">
        <Row
          title="Client mode"
          description={runtimeCopy.settingsModeDescription}
          control={<MonoValue>{mode}</MonoValue>}
        />
        <Row
          title="Connection target"
          control={<MonoValue>{runtimeCopy.settingsConnectionTarget}</MonoValue>}
        />
      </Card>

      <GroupLabel>Reported capabilities</GroupLabel>
      <Card className="mb-6">
        {loading ? (
          <Row title="Checking the runtime…" description="Fetching /api/v1/demo/status." />
        ) : status ? (
          status.capabilities.map((capability) => (
            <div
              key={capability.name}
              className="flex items-center justify-between gap-4 px-4 py-3"
            >
              <span className="font-mono text-[13px]">{capability.name}</span>
              <CapabilityChip state={capability.state} />
            </div>
          ))
        ) : (
          <Row
            title="Runtime status unavailable"
            description="The demo status endpoint could not be reached or returned an unexpected shape. Capability states are unknown, not assumed."
            align="start"
            control={<CapabilityChip state="unknown" />}
          />
        )}
      </Card>

      <GroupLabel>Evidence</GroupLabel>
      <Card>
        <Row
          title="Evidence class"
          description="How the runtime labels the provenance of everything it produces."
          control={<MonoValue>{status?.evidenceClass ?? "unknown"}</MonoValue>}
        />
        <Row
          title="Safe reason"
          description={
            status?.safeReason ??
            (loading ? "Waiting for the runtime…" : "Not reported — treated as unknown.")
          }
          align="start"
        />
        <Row
          title="Status source"
          description={runtimeCopy.settingsStatusSourceDescription}
          control={<MonoValue>{status?.source ?? "unknown"}</MonoValue>}
        />
      </Card>

      <span role="status" aria-live="polite" className="sr-only">
        {copied ? "Runtime diagnostics copied to clipboard." : ""}
      </span>
    </section>
  );
}

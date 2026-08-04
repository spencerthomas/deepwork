"use client";

import { Check, Copy, RefreshCw, ShieldCheck } from "lucide-react";
import { type FormEvent, useEffect, useRef, useState } from "react";

import { CapabilityChip } from "@/components/capability-chip";
import { formatRuntimeDiagnostics } from "@/lib/runtime-diagnostics";
import {
  probeClassicSource,
  type SourceProbeResult,
  type SourceProbeState,
} from "@/lib/source-probe-client";
import { taskRuntimePresentation } from "@/lib/task-runtime-presentation";
import { useTasksStore } from "@/lib/tasks-store";
import { useDemoStatus } from "@/lib/use-demo-status";
import { cn } from "@/lib/utils";

import { Card, GroupLabel, Row, SettingsHeader, TextInput } from "./settings-ui";

const ACTION_CLASS =
  "flex items-center gap-1.5 rounded-xl border border-border bg-card px-3 py-1.5 text-[13px] font-medium transition-colors hover:bg-accent disabled:cursor-not-allowed disabled:opacity-60";

function MonoValue({ children }: { children: string }) {
  return (
    <span className="rounded-md bg-accent px-2 py-1 font-mono text-[12px] text-foreground">
      {children}
    </span>
  );
}

function probeChipState(state: SourceProbeState): "available" | "unavailable" | "unknown" {
  if (state === "available") return "available";
  if (state === "unknown") return "unknown";
  return "unavailable";
}

function sourceAnnouncement(checking: boolean, result: SourceProbeResult | null): string {
  if (checking) return "Checking the source.";
  if (result?.state === "available") return "Assistant found. The source was not saved.";
  if (result) return "The source was not qualified or saved.";
  return "";
}

function SourceConnectionCheck({ apiBaseUrl }: { apiBaseUrl: string }) {
  const [endpoint, setEndpoint] = useState("");
  const [assistantId, setAssistantId] = useState("");
  const [checking, setChecking] = useState(false);
  const [result, setResult] = useState<SourceProbeResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const activeRequest = useRef<AbortController | null>(null);

  useEffect(
    () => () => {
      activeRequest.current?.abort();
      activeRequest.current = null;
    },
    [],
  );

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (activeRequest.current) return;

    const controller = new AbortController();
    activeRequest.current = controller;
    setChecking(true);
    setError(null);
    setResult(null);
    try {
      const nextResult = await probeClassicSource(
        apiBaseUrl,
        {
          endpoint: endpoint.trim(),
          assistantId: assistantId.trim(),
        },
        controller.signal,
      );
      if (activeRequest.current === controller && !controller.signal.aborted) {
        setResult(nextResult);
      }
    } catch (caught) {
      if (activeRequest.current === controller && !controller.signal.aborted) {
        setError(caught instanceof Error ? caught.message : "The source check failed safely.");
      }
    } finally {
      if (activeRequest.current === controller) {
        activeRequest.current = null;
        if (!controller.signal.aborted) setChecking(false);
      }
    }
  }

  return (
    <>
      <GroupLabel>Check a source</GroupLabel>
      <Card className="mb-6">
        <form onSubmit={(event) => void submit(event)} className="space-y-4 p-4">
          <div>
            <h3 className="text-[13px] font-medium text-crisp">Classic LangSmith deployment</h3>
            <p className="mt-1 text-pretty text-[12px] leading-relaxed text-muted-foreground">
              Check an operator-approved hosted deployment URL and assistant ID with the credential
              held by this workspace server. Browser input cannot probe arbitrary hosts. This check
              reads assistant identity only; it does not create a run or save a connection.
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="min-w-0 text-[12px] font-medium text-foreground">
              Deployment URL
              <TextInput
                type="url"
                required
                value={endpoint}
                onChange={setEndpoint}
                placeholder="https://deployment.example.com"
                autoComplete="url"
                mono
                className="mt-1.5 w-full py-2 text-[12px]"
              />
            </label>
            <label className="min-w-0 text-[12px] font-medium text-foreground">
              Assistant ID
              <TextInput
                type="text"
                required
                value={assistantId}
                onChange={setAssistantId}
                placeholder="deep-work-agent"
                autoComplete="off"
                mono
                className="mt-1.5 w-full py-2 text-[12px]"
              />
            </label>
          </div>
          <button
            type="submit"
            disabled={checking || endpoint.trim() === "" || assistantId.trim() === ""}
            className="inline-flex items-center gap-2 rounded-xl bg-brand px-3.5 py-2 text-[13px] font-semibold text-brand-foreground transition-opacity disabled:cursor-not-allowed disabled:opacity-55"
          >
            <ShieldCheck aria-hidden className="size-4" />
            {checking ? "Checking…" : "Run read-only check"}
          </button>
        </form>

        {error && (
          <div role="alert" className="bg-status-failed-bg px-4 py-3 text-[13px] text-foreground">
            {error}
          </div>
        )}

        {result && (
          <div className="space-y-3 px-4 py-4" aria-label="Source check result">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-[13px] font-medium text-crisp">
                  {result.state === "available" ? "Assistant found" : "Source not qualified"}
                </p>
                <p className="mt-0.5 text-[12px] text-muted-foreground">
                  {result.state === "available"
                    ? `Assistant ${result.assistantId ?? "unknown"} · graph ${result.graphId ?? "unknown"}`
                    : "No connection was saved or enabled."}
                </p>
              </div>
              <CapabilityChip state={probeChipState(result.state)} />
            </div>
            <ul className="divide-y divide-border rounded-xl border border-border">
              {result.capabilities.map((capability) => (
                <li
                  key={capability.name}
                  className="flex flex-wrap items-center justify-between gap-2 px-3 py-2.5"
                >
                  <span>
                    <span className="block font-mono text-[12px] text-foreground">
                      {capability.name}
                    </span>
                    <span className="block text-[11px] text-muted-foreground">
                      {capability.reason}
                    </span>
                  </span>
                  <CapabilityChip
                    state={probeChipState(capability.state)}
                    label={capability.state.replace("-", " ")}
                  />
                </li>
              ))}
            </ul>
            <p className="rounded-xl bg-status-review-bg px-3 py-2.5 text-[12px] leading-relaxed text-foreground">
              Assistant read access is not execution proof. Saving and selecting this source stay
              blocked until an explicitly authorized invocation check verifies run and stream
              behavior.
            </p>
          </div>
        )}
      </Card>
      <span role="status" aria-live="polite" className="sr-only">
        {sourceAnnouncement(checking, result)}
      </span>
    </>
  );
}

/** Read-only view of what this client is actually connected to. */
export function RuntimeSection() {
  const { mode, apiBaseUrl } = useTasksStore();
  const { status, loading, refetch } = useDemoStatus();
  const runtimeCopy = taskRuntimePresentation(mode, apiBaseUrl || undefined);

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

      {mode === "api" && <SourceConnectionCheck apiBaseUrl={apiBaseUrl} />}

      <GroupLabel>Evidence</GroupLabel>
      <Card>
        <Row
          title="Source"
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

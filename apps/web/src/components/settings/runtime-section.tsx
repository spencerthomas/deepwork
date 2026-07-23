"use client";

import { CapabilityChip } from "@/components/capability-chip";
import { taskRuntimePresentation } from "@/lib/task-runtime-presentation";
import { useTasksStore } from "@/lib/tasks-store";
import { useDemoStatus } from "@/lib/use-demo-status";

import { Card, GroupLabel, Row, SettingsHeader } from "./settings-ui";

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
  const { status, loading } = useDemoStatus();
  const runtimeCopy = taskRuntimePresentation(mode, apiBaseUrl);

  return (
    <section>
      <SettingsHeader
        title="Runtime"
        description="What this client is actually connected to, and what the runtime reports about itself. Everything here is read-only."
      />

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
    </section>
  );
}

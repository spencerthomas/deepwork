"use client";

import { Plus, Trash2 } from "lucide-react";
import { useState } from "react";

import { agentClient, type AgentSummary } from "@/lib/agent-client";
import { useAgents } from "@/lib/use-agents";
import { useTasksStore } from "@/lib/tasks-store";
import { cn } from "@/lib/utils";

import { Card, GroupLabel, Row, SettingsHeader, TextInput } from "./settings-ui";

const ACTION_CLASS =
  "flex items-center gap-1.5 rounded-xl border border-border bg-card px-3 py-1.5 text-[13px] font-medium transition-colors hover:bg-accent disabled:cursor-not-allowed disabled:opacity-60";
const PRIMARY_CLASS =
  "flex items-center gap-1.5 rounded-xl bg-brand px-3 py-1.5 text-[13px] font-medium text-brand-foreground transition-colors hover:bg-brand/90 disabled:cursor-not-allowed disabled:opacity-60";

interface EditableDraft {
  name: string;
  description: string;
  systemPrompt: string;
}

function draftFrom(agent?: AgentSummary): EditableDraft {
  return {
    name: agent?.name ?? "",
    description: agent?.description ?? "",
    systemPrompt: agent?.systemPrompt ?? "",
  };
}

function AgentForm({
  draft,
  onChange,
  disabled,
}: {
  draft: EditableDraft;
  onChange: (draft: EditableDraft) => void;
  disabled: boolean;
}) {
  return (
    <div className="flex flex-col gap-2 py-2">
      <TextInput
        value={draft.name}
        onChange={(value) => onChange({ ...draft, name: value })}
        placeholder="Agent name"
        className="w-full"
      />
      <TextInput
        value={draft.description}
        onChange={(value) => onChange({ ...draft, description: value })}
        placeholder="Description (optional)"
        className="w-full"
      />
      <textarea
        value={draft.systemPrompt}
        disabled={disabled}
        onChange={(event) => onChange({ ...draft, systemPrompt: event.target.value })}
        placeholder="System prompt override (optional) — leave empty to use the graph's default persona"
        rows={4}
        className="w-full resize-y rounded-lg border border-border bg-background p-2.5 font-mono text-[12px] leading-relaxed outline-none focus:border-brand/50 disabled:opacity-60"
      />
    </div>
  );
}

function AgentRow({ agent, onChanged }: { agent: AgentSummary; onChanged: () => void }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState<EditableDraft>(() => draftFrom(agent));
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string>();

  async function save() {
    setSaving(true);
    setError(undefined);
    try {
      await agentClient.updateAgent(agent.agentId, {
        name: draft.name,
        description: draft.description,
        systemPrompt: draft.systemPrompt,
      });
      setEditing(false);
      onChanged();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not save the agent.");
    } finally {
      setSaving(false);
    }
  }

  async function remove() {
    if (!window.confirm(`Delete “${agent.name}”? This cannot be undone.`)) {
      return;
    }
    setDeleting(true);
    setError(undefined);
    try {
      await agentClient.deleteAgent(agent.agentId);
      onChanged();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not delete the agent.");
      setDeleting(false);
    }
  }

  return (
    <div>
      <Row
        title={agent.name}
        description={
          agent.description ??
          (agent.systemPrompt ? "Custom system prompt." : "Uses the graph's default persona.")
        }
        align="start"
        control={
          <div className="flex items-center gap-2">
            {agent.isDefault ? (
              <span className="rounded-md bg-accent px-2 py-0.5 text-[11px] font-medium text-muted-foreground">
                Default
              </span>
            ) : (
              <>
                <button
                  type="button"
                  onClick={() => {
                    setDraft(draftFrom(agent));
                    setEditing((value) => !value);
                  }}
                  className={ACTION_CLASS}
                >
                  {editing ? "Cancel" : "Edit"}
                </button>
                <button
                  type="button"
                  onClick={() => void remove()}
                  disabled={deleting}
                  aria-label={`Delete ${agent.name}`}
                  className={cn(ACTION_CLASS, "text-status-failed hover:bg-status-failed-bg")}
                >
                  <Trash2 aria-hidden className="size-3.5" />
                </button>
              </>
            )}
          </div>
        }
      >
        {editing && (
          <div className="mt-2">
            <AgentForm draft={draft} onChange={setDraft} disabled={saving} />
            {error && <p className="mb-2 text-[12px] text-status-failed">{error}</p>}
            <button
              type="button"
              onClick={() => void save()}
              disabled={saving || draft.name.trim() === ""}
              className={PRIMARY_CLASS}
            >
              {saving ? "Saving…" : "Save"}
            </button>
          </div>
        )}
      </Row>
      {!editing && error && <p className="px-4 pb-3 text-[12px] text-status-failed">{error}</p>}
    </div>
  );
}

function NewAgentForm({ onCreated }: { onCreated: () => void }) {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState<EditableDraft>(() => draftFrom());
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string>();

  async function create() {
    setCreating(true);
    setError(undefined);
    try {
      await agentClient.createAgent({
        name: draft.name,
        description: draft.description,
        systemPrompt: draft.systemPrompt,
      });
      setDraft(draftFrom());
      setOpen(false);
      onCreated();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not create the agent.");
    } finally {
      setCreating(false);
    }
  }

  if (!open) {
    return (
      <button type="button" onClick={() => setOpen(true)} className={cn(ACTION_CLASS, "mt-3")}>
        <Plus aria-hidden className="size-3.5" />
        New agent
      </button>
    );
  }

  return (
    <div className="mt-3 rounded-2xl border border-border bg-card p-4">
      <AgentForm draft={draft} onChange={setDraft} disabled={creating} />
      {error && <p className="mb-2 text-[12px] text-status-failed">{error}</p>}
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => void create()}
          disabled={creating || draft.name.trim() === ""}
          className={PRIMARY_CLASS}
        >
          {creating ? "Creating…" : "Create agent"}
        </button>
        <button
          type="button"
          onClick={() => {
            setOpen(false);
            setDraft(draftFrom());
            setError(undefined);
          }}
          disabled={creating}
          className={ACTION_CLASS}
        >
          Cancel
        </button>
      </div>
    </div>
  );
}

/**
 * Named agents sharing the deployed graph. Deep Work owns no agent storage —
 * this reads and writes /api/v1/agents, which itself is a thin wrapper over
 * the configured task source's own Assistants registry.
 */
export function AgentsSection() {
  const { mode } = useTasksStore();
  const connected = mode !== "fixture";
  const { available, agents, loading, error, refetch } = useAgents();

  return (
    <section>
      <SettingsHeader
        title="Agents"
        description="Named agents sharing the deployed graph, each with its own optional system prompt. Select one when starting a task instead of always using the default. Every agent still runs through the same graph — only its persona differs."
      />

      {!connected ? (
        <div className="rounded-2xl border border-border bg-card px-4 py-6 text-[13px] text-muted-foreground">
          Agents apply to real agent runs. This client is in fixture mode, so there is no registry
          to manage. Connect it to a running API to manage agents.
        </div>
      ) : loading ? (
        <div className="rounded-2xl border border-border bg-card px-4 py-6 text-[13px] text-muted-foreground">
          Loading agents…
        </div>
      ) : !available ? (
        <div className="rounded-2xl border border-border bg-card px-4 py-6 text-[13px] text-muted-foreground">
          No real task source is configured, so there is no agent registry to manage yet. Once a
          source is connected, its registered agents will appear here.
        </div>
      ) : (
        <>
          {error && (
            <div
              role="alert"
              className="mb-4 rounded-xl border border-status-failed/35 bg-status-failed-bg px-4 py-3 text-[13px]"
            >
              {error}
            </div>
          )}
          <GroupLabel>Registered agents</GroupLabel>
          <Card>
            {agents.map((agent) => (
              <AgentRow key={agent.agentId} agent={agent} onChanged={refetch} />
            ))}
          </Card>
          <NewAgentForm onCreated={refetch} />
        </>
      )}
    </section>
  );
}

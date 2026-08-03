"use client";

import { Check, RotateCcw } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { promptClient, type PromptState } from "@/lib/prompt-client";
import { useTasksStore } from "@/lib/tasks-store";
import { cn } from "@/lib/utils";

import { GroupLabel, SettingsHeader } from "./settings-ui";

const ACTION_CLASS =
  "flex items-center gap-1.5 rounded-xl border border-border bg-card px-3 py-1.5 text-[13px] font-medium transition-colors hover:bg-accent disabled:cursor-not-allowed disabled:opacity-60";
const PRIMARY_CLASS =
  "flex items-center gap-1.5 rounded-xl bg-brand px-3 py-1.5 text-[13px] font-medium text-brand-foreground transition-colors hover:bg-brand/90 disabled:cursor-not-allowed disabled:opacity-60";

/**
 * Edit the workspace system prompt that governs the agent's execution. Reads and
 * writes /api/v1/settings/prompt; a saved prompt takes effect on the next run.
 */
export function PromptSection() {
  const { mode } = useTasksStore();
  const connected = mode !== "fixture";

  const [draft, setDraft] = useState("");
  const [saved, setSaved] = useState<PromptState | null>(null);
  const [loading, setLoading] = useState(connected);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [savedFlash, setSavedFlash] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const prompt = await promptClient.getPrompt();
      setSaved(prompt);
      setDraft(prompt.value);
    } catch {
      setLoadError(
        "Couldn’t load the current system prompt. Check that the API is reachable and you’re signed in.",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (connected) {
      void load();
    }
  }, [connected, load]);

  useEffect(() => {
    if (!savedFlash) {
      return;
    }
    const timer = window.setTimeout(() => setSavedFlash(false), 2000);
    return () => window.clearTimeout(timer);
  }, [savedFlash]);

  const dirty = saved !== null && draft !== saved.value;

  async function save() {
    setSaving(true);
    setSaveError(null);
    try {
      const trimmed = draft.trim();
      const prompt = await promptClient.updatePrompt(trimmed === "" ? null : draft);
      setSaved(prompt);
      setDraft(prompt.value);
      setSavedFlash(true);
    } catch {
      setSaveError("Couldn’t save the system prompt. Your change was not applied.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section>
      <SettingsHeader
        title="System prompt"
        description="The instructions that govern how the agent works — its persona, priorities, and rules. A saved prompt takes effect on the next task; clearing it reverts to the built-in default."
        actions={
          connected ? (
            <>
              <button
                type="button"
                onClick={() => setDraft("")}
                disabled={saving || draft.trim() === ""}
                className={ACTION_CLASS}
                title="Clear the override and revert to the built-in default"
              >
                <RotateCcw aria-hidden className="size-3.5" />
                Reset to default
              </button>
              <button
                type="button"
                onClick={() => void save()}
                disabled={saving || !dirty}
                className={PRIMARY_CLASS}
              >
                {savedFlash ? <Check aria-hidden className="size-3.5" /> : null}
                {saving ? "Saving…" : savedFlash ? "Saved" : "Save"}
              </button>
            </>
          ) : undefined
        }
      />

      {!connected ? (
        <div className="rounded-2xl border border-border bg-card px-4 py-6 text-[13px] text-muted-foreground">
          The system prompt applies to real agent runs. This client is in fixture mode, so there is
          no prompt to edit. Connect it to a running API to manage the prompt.
        </div>
      ) : (
        <>
          {loadError && (
            <div
              role="alert"
              className="mb-4 rounded-xl border border-status-failed/35 bg-status-failed-bg px-4 py-3 text-[13px]"
            >
              {loadError}
            </div>
          )}
          {saveError && (
            <div
              role="alert"
              className="mb-4 rounded-xl border border-status-failed/35 bg-status-failed-bg px-4 py-3 text-[13px]"
            >
              {saveError}
            </div>
          )}

          <div className="mb-2 flex items-center justify-between">
            <GroupLabel>Prompt</GroupLabel>
            {saved !== null && (
              <span
                className={cn(
                  "rounded-md px-2 py-0.5 text-[11px] font-medium",
                  saved.isDefault
                    ? "bg-accent text-muted-foreground"
                    : "bg-brand-soft text-brand-accent",
                )}
              >
                {saved.isDefault ? "Using built-in default" : "Custom prompt active"}
              </span>
            )}
          </div>

          <textarea
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            disabled={loading}
            spellCheck={false}
            placeholder={
              loading
                ? "Loading…"
                : "Leave empty to use the built-in default, or write instructions to govern every run…"
            }
            rows={18}
            className="w-full resize-y rounded-2xl border border-border bg-card p-4 font-mono text-[13px] leading-relaxed outline-none focus:border-brand/50 disabled:opacity-60"
          />
          <p className="mt-2 text-[12px] text-muted-foreground">
            {dirty
              ? "Unsaved changes — Save to apply them to the next run."
              : "This is the prompt every new task will run with."}
          </p>
        </>
      )}
    </section>
  );
}

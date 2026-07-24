"use client";

import { ArrowLeft, Bot, CornerDownLeft, History, ShieldCheck, Sparkles, X } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useId, useState } from "react";

import { AppShell } from "@/components/shell/app-shell";
import { PageHeader } from "@/components/shell/page-header";
import { SidebarLabel } from "@/components/shell/sidebar-nav";
import {
  clearComposerDraft,
  formatDraftAge,
  loadComposerDraft,
  saveComposerDraft,
} from "@/lib/composer-draft";
import { consumeEditRerunPrompt } from "@/lib/edit-rerun-handoff";
import { unicodeLength, validatePrompt } from "@/lib/task-normalizers";
import { taskRuntimePresentation } from "@/lib/task-runtime-presentation";
import { useTasksStore } from "@/lib/tasks-store";
import { PROMPT_MAX_LENGTH } from "@/lib/task-types";
import { cn } from "@/lib/utils";

const templates = [
  "Research the competitive landscape for Deep Work",
  "Write a launch announcement for the local product",
  "Plan the deployment of the next release",
  "Review the code conventions for new contributors",
];

export function NewTask() {
  const router = useRouter();
  const { creating, createError, createTask, mode } = useTasksStore();
  const [prompt, setPrompt] = useState("");
  const [validationError, setValidationError] = useState<string>();
  const [restoredAge, setRestoredAge] = useState<string>();
  const runtimeCopy = taskRuntimePresentation(mode);

  // Seed the composer once on mount. An in-session "Edit & re-run" handoff wins
  // (an explicit action, carried through transient module state — never the URL,
  // so private prompt content is not written to history or the referrer);
  // otherwise a persisted device-local draft is restored so navigating away or
  // reloading does not lose in-progress work. The draft key is scoped to the
  // runtime mode so a fixture-mode draft cannot surface in an API-backed one.
  useEffect(() => {
    const seeded = consumeEditRerunPrompt();
    if (seeded !== null && seeded.trim() !== "") {
      setPrompt(seeded.slice(0, PROMPT_MAX_LENGTH * 2));
      return;
    }
    const draft = loadComposerDraft(mode);
    if (draft !== null) {
      setPrompt(draft.prompt.slice(0, PROMPT_MAX_LENGTH * 2));
      setRestoredAge(formatDraftAge(draft.savedAt, Date.now()));
    }
  }, [mode]);

  // Persist the in-progress prompt device-locally; emptying the field clears it.
  useEffect(() => {
    saveComposerDraft(mode, prompt);
  }, [mode, prompt]);

  const draftRestored = restoredAge !== undefined;

  function discardDraft() {
    clearComposerDraft(mode);
    setPrompt("");
    setRestoredAge(undefined);
    setValidationError(undefined);
  }

  const fieldId = useId();
  const countId = `${fieldId}-count`;
  const errorId = `${fieldId}-error`;
  // validatePrompt measures the trimmed value, so the visible/accessible invalid
  // state uses it too and matches what actually dispatches.
  const promptLength = unicodeLength(prompt.trim());
  const overLimit = promptLength > PROMPT_MAX_LENGTH;
  const shownError = validationError ?? createError;
  const promptDescribedBy = [countId, shownError !== undefined ? errorId : null]
    .filter((id): id is string => id !== null)
    .join(" ");

  async function dispatch() {
    try {
      validatePrompt(prompt);
    } catch (error) {
      setValidationError(error instanceof Error ? error.message : "The prompt is invalid.");
      return;
    }
    setValidationError(undefined);
    // The fields are disabled while `creating`, so `prompt` cannot change under
    // the in-flight request — the value dispatched is the value cleared.
    const created = await createTask(prompt);
    if (created) {
      // The work is now a real task; drop the local draft so a later visit
      // starts clean.
      clearComposerDraft(mode);
      setRestoredAge(undefined);
      router.push(`/tasks/${created.taskId}`);
    }
  }

  const sidebar = (
    <div className="flex flex-col gap-1">
      <Link
        href="/tasks"
        className="mb-2 flex items-center gap-2 rounded-xl px-3 py-1.5 text-[13px] text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
      >
        <ArrowLeft className="size-4" /> All tasks
      </Link>
      <SidebarLabel>Templates</SidebarLabel>
      {templates.map((template) => (
        <button
          key={template}
          type="button"
          disabled={creating}
          onClick={() => setPrompt(template)}
          className="rounded-xl px-3 py-1.5 text-left text-[13px] text-muted-foreground transition-colors hover:bg-accent hover:text-foreground disabled:pointer-events-none disabled:opacity-50"
        >
          {template}
        </button>
      ))}
    </div>
  );

  return (
    <AppShell active="Tasks" sidebar={sidebar}>
      <div className="mx-auto max-w-2xl">
        <PageHeader
          eyebrow="Dispatch"
          title="New task"
          description={runtimeCopy.newTaskDescription}
        />

        <label className="mb-2 block text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
          {runtimeCopy.dispatchTargetLabel}
        </label>
        <div className="mb-6 grid grid-cols-1 gap-2 sm:grid-cols-2">
          <button
            type="button"
            className="flex items-start gap-3 rounded-2xl border border-brand bg-brand-soft p-3 text-left"
          >
            <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-secondary text-secondary-foreground">
              <Bot className="size-4" />
            </span>
            <span className="min-w-0">
              <span className="block text-sm font-medium text-crisp">
                {runtimeCopy.taskOriginLabel}
              </span>
              <span className="mt-0.5 block truncate font-mono text-[11px] text-muted-foreground">
                plan · approval · evidence
              </span>
            </span>
          </button>
          <div className="flex items-start gap-3 rounded-2xl border border-dashed border-border p-3 text-left">
            <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-secondary text-muted-foreground">
              <Bot className="size-4" />
            </span>
            <span className="min-w-0">
              <span className="block text-sm font-medium text-muted-foreground">
                External agent sources
              </span>
              <span className="mt-0.5 block text-[11px] text-muted-foreground">
                {runtimeCopy.sourceSelectionDescription}
              </span>
            </span>
          </div>
        </div>

        <label
          htmlFor="new-task-prompt"
          className="mb-2 block text-[11px] font-semibold uppercase tracking-wide text-muted-foreground"
        >
          Task
        </label>
        {draftRestored && (
          <div
            role="status"
            className="mb-2 flex flex-wrap items-center gap-2 rounded-xl border border-border bg-secondary/60 px-3 py-2 text-[13px]"
          >
            <History className="size-3.5 shrink-0 text-muted-foreground" />
            <span className="min-w-0 text-muted-foreground">
              Restored an unsent draft from this device, saved {restoredAge}.
            </span>
            <button
              type="button"
              onClick={discardDraft}
              className="ml-auto rounded-lg border border-border bg-card px-2.5 py-1 font-medium text-foreground transition-colors hover:bg-accent"
            >
              Discard draft
            </button>
            <button
              type="button"
              aria-label="Keep the draft and dismiss this notice"
              onClick={() => setRestoredAge(undefined)}
              className="rounded-md p-1 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
            >
              <X className="size-3.5" />
            </button>
          </div>
        )}
        <div className="rounded-2xl border border-border bg-card p-3">
          <textarea
            id="new-task-prompt"
            value={prompt}
            rows={5}
            maxLength={PROMPT_MAX_LENGTH * 2}
            disabled={creating}
            placeholder="Describe the outcome you want. The agent plans its own steps and pauses for your review."
            aria-invalid={shownError !== undefined || overLimit}
            aria-describedby={promptDescribedBy}
            onChange={(event) => {
              setPrompt(event.target.value);
              setValidationError(undefined);
              setRestoredAge(undefined);
            }}
            onKeyDown={(event) => {
              if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
                event.preventDefault();
                void dispatch();
              }
            }}
            className="w-full resize-y bg-transparent text-sm outline-none placeholder:text-muted-foreground disabled:opacity-60"
          />
          <div className="mt-2 flex flex-wrap items-center gap-3 border-t border-border pt-3">
            <span className="inline-flex items-center gap-1.5 rounded-xl border border-border px-2.5 py-1 text-[13px] text-muted-foreground">
              <ShieldCheck className="size-3.5 text-brand-accent" />
              Plan approval always required
            </span>
            <span
              id={countId}
              className={cn(
                "ml-auto text-[11px] tabular-nums",
                overLimit ? "text-status-failed" : "text-muted-foreground",
              )}
            >
              {promptLength.toLocaleString()} / {PROMPT_MAX_LENGTH.toLocaleString()}
            </span>
            <button
              type="button"
              disabled={creating || prompt.trim() === ""}
              onClick={() => void dispatch()}
              className="flex items-center gap-1.5 rounded-xl bg-brand px-3 py-1.5 text-[13px] font-medium text-brand-foreground transition-colors hover:bg-brand-hover disabled:pointer-events-none disabled:opacity-50"
            >
              {creating ? (
                "Dispatching…"
              ) : (
                <>
                  <Sparkles className="size-3.5" /> Dispatch
                  <CornerDownLeft className="size-3.5 opacity-70" />
                </>
              )}
            </button>
          </div>
        </div>

        {shownError !== undefined && (
          <div
            id={errorId}
            className="mt-3 rounded-2xl border border-status-failed/30 bg-status-failed-bg px-4 py-3"
            role="alert"
          >
            <p className="text-sm">
              <span className="font-medium">Task was not created.</span>{" "}
              <span className="text-muted-foreground">{shownError}</span>
            </p>
          </div>
        )}

        <p className="mt-3 text-[13px] text-muted-foreground">
          The run streams into your inbox. The agent pauses at its proposed plan — you can edit the
          steps, approve, reject, or respond before it continues.
        </p>
      </div>
    </AppShell>
  );
}

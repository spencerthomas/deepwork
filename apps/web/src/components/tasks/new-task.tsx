"use client";

import {
  ArrowLeft,
  Bot,
  Code2,
  CornerDownLeft,
  GitBranch,
  History,
  ShieldCheck,
  Sparkles,
  X,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useId, useRef, useState } from "react";

import { AppShell } from "@/components/shell/app-shell";
import { PageHeader } from "@/components/shell/page-header";
import { SidebarLabel } from "@/components/shell/sidebar-nav";
import {
  clearComposerDraft,
  draftScopeForRuntime,
  formatDraftAge,
  loadComposerDraft,
  saveComposerDraft,
} from "@/lib/composer-draft";
import { getSession } from "@/lib/auth-client";
import { consumeEditRerunPrompt } from "@/lib/edit-rerun-handoff";
import { unicodeLength, validatePrompt } from "@/lib/task-normalizers";
import { taskRuntimePresentation } from "@/lib/task-runtime-presentation";
import { useTasksStore } from "@/lib/tasks-store";
import { PROMPT_MAX_LENGTH } from "@/lib/task-types";
import { useAgents } from "@/lib/use-agents";
import { useDemoStatus } from "@/lib/use-demo-status";
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
  const {
    available: agentsAvailable,
    agents,
    loading: agentsLoading,
    error: agentsError,
    refetch: refetchAgents,
  } = useAgents();
  const { status: runtimeStatus, loading: runtimeLoading } = useDemoStatus(mode === "api");
  const [prompt, setPrompt] = useState("");
  const [agentId, setAgentId] = useState<string>("");
  const [journey, setJourney] = useState<"general" | "coding">("general");
  const [validationError, setValidationError] = useState<string>();
  const [restoredAge, setRestoredAge] = useState<string>();
  const [draftScope, setDraftScope] = useState<string | null>(() =>
    mode === "fixture" ? draftScopeForRuntime({ mode: "fixture" }) : null,
  );
  const [readyDraftScope, setReadyDraftScope] = useState<string | null>(null);
  const promptTouchedRef = useRef(false);
  const editRerunCheckedRef = useRef(false);
  const editRerunWonRef = useRef(false);
  const runtimeCopy = taskRuntimePresentation(mode);
  const codingFixtureAvailable =
    mode === "fixture" || (mode === "api" && runtimeStatus?.runtimeKind === "fixture");
  const codingUnavailable =
    mode === "api" && (agentsLoading || runtimeLoading || !codingFixtureAvailable);

  // Consume the transient Edit & re-run handoff immediately. It wins over any
  // persisted draft, including while an API session is still resolving.
  useEffect(() => {
    if (editRerunCheckedRef.current) return;
    editRerunCheckedRef.current = true;
    const seeded = consumeEditRerunPrompt();
    if (seeded !== null && seeded.trim() !== "") {
      editRerunWonRef.current = true;
      setPrompt(seeded.slice(0, PROMPT_MAX_LENGTH * 2));
    }
  }, []);

  // Resolve an authenticated identity before API-mode storage is touched.
  // Failure leaves persistence disabled but never disables or clears typing.
  useEffect(() => {
    setReadyDraftScope(null);
    setRestoredAge(undefined);
    if (mode === "fixture") {
      setDraftScope(draftScopeForRuntime({ mode: "fixture" }));
      return;
    }

    setDraftScope(null);
    const controller = new AbortController();
    let active = true;
    void getSession(controller.signal)
      .then((session) => {
        if (!active) return;
        setDraftScope(
          draftScopeForRuntime({
            mode: "api",
            identity: { actorId: session.actorId, workspaceId: session.workspaceId },
          }),
        );
      })
      .catch(() => {
        // No identity means no API draft access; the composer itself stays live.
      });
    return () => {
      active = false;
      controller.abort();
    };
  }, [mode]);

  // Restore only after a valid scope exists. A delayed session/storage read
  // must never overwrite text the user already entered, and Edit & re-run keeps
  // precedence over device-local persistence.
  useEffect(() => {
    if (draftScope === null) return;
    if (promptTouchedRef.current || editRerunWonRef.current) {
      setReadyDraftScope(draftScope);
      return;
    }
    const draft = loadComposerDraft(draftScope);
    if (draft !== null) {
      setPrompt(draft.prompt.slice(0, PROMPT_MAX_LENGTH * 2));
      setRestoredAge(formatDraftAge(draft.savedAt, Date.now()));
    }
    setReadyDraftScope(draftScope);
  }, [draftScope]);

  useEffect(() => {
    if (mode === "api" && agentsAvailable && agents.length > 0 && agentId === "") {
      setAgentId((agents.find((agent) => agent.isDefault) ?? agents[0]).agentId);
    }
  }, [agentId, agents, agentsAvailable, mode]);

  useEffect(() => {
    if (codingUnavailable && journey === "coding") {
      setJourney("general");
    }
  }, [codingUnavailable, journey]);

  // Persist the in-progress prompt device-locally; emptying the field clears it.
  useEffect(() => {
    if (draftScope === null || readyDraftScope !== draftScope) return;
    saveComposerDraft(draftScope, prompt);
  }, [draftScope, prompt, readyDraftScope]);

  const draftRestored = restoredAge !== undefined;

  function discardDraft() {
    if (draftScope !== null) {
      clearComposerDraft(draftScope);
    }
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
    if (mode === "api" && (agentsLoading || runtimeLoading) && journey === "coding") {
      setValidationError("Wait for the runtime checks before starting a coding review.");
      return;
    }
    if (mode === "api" && !codingFixtureAvailable && journey === "coding") {
      setValidationError("The coding demo is available only in the credential-free fixture.");
      return;
    }
    if (mode === "api" && agentsAvailable && !agentId) {
      setValidationError("Choose a connected agent before dispatching this task.");
      return;
    }
    try {
      validatePrompt(prompt);
    } catch (error) {
      setValidationError(error instanceof Error ? error.message : "The prompt is invalid.");
      return;
    }
    setValidationError(undefined);
    // The fields are disabled while `creating`, so `prompt` cannot change under
    // the in-flight request — the value dispatched is the value cleared.
    const created = await createTask(prompt, agentId || undefined, journey);
    if (created) {
      // The work is now a real task; drop the local draft so a later visit
      // starts clean.
      if (draftScope !== null) {
        clearComposerDraft(draftScope);
      }
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
          onClick={() => {
            promptTouchedRef.current = true;
            setPrompt(template);
          }}
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
          eyebrow="New task"
          title="New task"
          description={runtimeCopy.newTaskDescription}
        />

        <fieldset className="mb-6">
          <legend className="mb-2 block text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
            Choose agent
          </legend>
          <div
            role="radiogroup"
            aria-label="Choose agent"
            className="grid grid-cols-1 gap-2 sm:grid-cols-2"
          >
            {agentsAvailable && agents.length > 0 ? (
              agents.map((agent) => {
                const value = agent.agentId;
                const selected = agentId === value;
                return (
                  <button
                    key={agent.agentId}
                    type="button"
                    role="radio"
                    aria-checked={selected}
                    disabled={creating}
                    onClick={() => setAgentId(value)}
                    className={cn(
                      "flex min-h-24 items-start gap-3 rounded-2xl border p-3 text-left transition-colors disabled:pointer-events-none disabled:opacity-60",
                      selected
                        ? "border-brand bg-brand-soft"
                        : "border-border bg-card hover:bg-accent/50",
                    )}
                  >
                    <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-secondary text-secondary-foreground">
                      <Bot className="size-4" />
                    </span>
                    <span className="min-w-0">
                      <span className="block text-sm font-medium text-crisp">
                        {agent.name}
                        {agent.isDefault ? (
                          <span className="ml-1.5 font-normal text-muted-foreground">default</span>
                        ) : null}
                      </span>
                      <span className="mt-1 block text-[12px] leading-relaxed text-muted-foreground">
                        {agent.description?.trim() ||
                          "Connected through the configured agent registry."}
                      </span>
                    </span>
                  </button>
                );
              })
            ) : (
              <button
                type="button"
                role="radio"
                aria-checked="true"
                disabled
                className="flex min-h-24 items-start gap-3 rounded-2xl border border-brand bg-brand-soft p-3 text-left disabled:opacity-100"
              >
                <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-secondary text-secondary-foreground">
                  <Bot className="size-4" />
                </span>
                <span className="min-w-0">
                  <span className="block text-sm font-medium text-crisp">
                    {runtimeCopy.taskOriginLabel}
                  </span>
                  <span className="mt-1 block text-[12px] leading-relaxed text-muted-foreground">
                    {runtimeCopy.sourceSelectionDescription}
                  </span>
                  <span className="mt-2 block font-mono text-[11px] text-muted-foreground">
                    plan · approval · evidence
                  </span>
                </span>
              </button>
            )}
          </div>
        </fieldset>

        {mode === "api" && agentsError ? (
          <div
            role="alert"
            className="mb-6 flex flex-wrap items-center gap-3 rounded-2xl border border-status-failed/30 bg-status-failed-bg px-4 py-3 text-sm"
          >
            <span className="min-w-0 flex-1">
              <span className="font-medium">Agent registry unavailable.</span>{" "}
              <span className="text-muted-foreground">{agentsError}</span>
            </span>
            <button
              type="button"
              onClick={refetchAgents}
              className="rounded-lg border border-border bg-card px-2.5 py-1 font-medium"
            >
              Retry
            </button>
          </div>
        ) : null}

        <fieldset className="mb-6">
          <legend className="mb-2 block text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
            Choose outcome
          </legend>
          <div
            role="radiogroup"
            aria-label="Choose outcome"
            className="grid grid-cols-1 gap-2 sm:grid-cols-2"
          >
            <button
              type="button"
              role="radio"
              aria-checked={journey === "general"}
              disabled={creating}
              onClick={() => setJourney("general")}
              className={cn(
                "flex min-h-24 items-start gap-3 rounded-2xl border p-3 text-left transition-colors disabled:pointer-events-none disabled:opacity-60",
                journey === "general"
                  ? "border-brand bg-brand-soft"
                  : "border-border bg-card hover:bg-accent/50",
              )}
            >
              <Sparkles className="mt-0.5 size-4 shrink-0 text-brand-accent" />
              <span>
                <span className="block text-sm font-medium">General task</span>
                <span className="mt-1 block text-[12px] leading-relaxed text-muted-foreground">
                  Produce a supervised brief, report, plan, or analysis.
                </span>
              </span>
            </button>
            <button
              type="button"
              role="radio"
              aria-checked={journey === "coding"}
              aria-disabled={codingUnavailable}
              disabled={creating || codingUnavailable}
              onClick={() => setJourney("coding")}
              className={cn(
                "flex min-h-24 items-start gap-3 rounded-2xl border p-3 text-left transition-colors disabled:cursor-not-allowed disabled:opacity-60",
                journey === "coding"
                  ? "border-brand bg-brand-soft"
                  : "border-border bg-card hover:bg-accent/50",
              )}
            >
              <Code2 className="mt-0.5 size-4 shrink-0 text-brand-accent" />
              <span>
                <span className="block text-sm font-medium">Coding review</span>
                <span className="mt-1 block text-[12px] leading-relaxed text-muted-foreground">
                  {mode === "api" && (agentsLoading || runtimeLoading)
                    ? "Checking whether this workspace exposes the local reviewed coding fixture."
                    : codingFixtureAvailable
                      ? "Run the exact-revision local proof, including diff, draft PR, and CI states."
                      : "Unavailable until the approved sandbox and GitHub proxy are connected."}
                </span>
              </span>
            </button>
          </div>
          {journey === "coding" ? (
            <div className="mt-2 flex items-start gap-3 rounded-2xl border border-border bg-card px-3 py-3">
              <GitBranch className="mt-0.5 size-4 shrink-0 text-brand-accent" />
              <div className="min-w-0">
                <p className="text-sm font-medium">deepwork-fixtures/sample-app</p>
                <p className="mt-1 text-[12px] leading-relaxed text-muted-foreground">
                  Local reviewed repository · main · no GitHub token or external request
                </p>
              </div>
            </div>
          ) : null}
        </fieldset>

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
              promptTouchedRef.current = true;
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
              disabled={
                creating ||
                prompt.trim() === "" ||
                (mode === "api" &&
                  (agentsLoading || agentsError !== undefined || (agentsAvailable && !agentId)))
              }
              onClick={() => void dispatch()}
              className="flex items-center gap-1.5 rounded-xl bg-brand px-3 py-1.5 text-[13px] font-medium text-brand-foreground transition-colors hover:bg-brand-hover disabled:pointer-events-none disabled:opacity-50"
            >
              {creating ? (
                "Starting…"
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

        <details className="mt-4 rounded-2xl border border-border bg-card p-3 lg:hidden">
          <summary className="cursor-pointer text-[13px] font-medium">
            Start from a template
          </summary>
          <div className="mt-2 grid gap-1">
            {templates.map((template) => (
              <button
                key={template}
                type="button"
                disabled={creating}
                onClick={() => {
                  promptTouchedRef.current = true;
                  setPrompt(template);
                }}
                className="rounded-xl px-3 py-2 text-left text-[13px] text-muted-foreground transition-colors hover:bg-accent hover:text-foreground disabled:pointer-events-none disabled:opacity-50"
              >
                {template}
              </button>
            ))}
          </div>
        </details>

        <p className="mt-3 text-[13px] text-muted-foreground">
          The run streams into your inbox. The agent pauses at its proposed plan — you can edit the
          steps, approve, reject, or respond before it continues.
        </p>
      </div>
    </AppShell>
  );
}

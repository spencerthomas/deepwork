"use client";

import { useId, useState, type FormEvent, type KeyboardEvent } from "react";

import { unicodeLength } from "../lib/task-normalizers";
import { PROMPT_MAX_LENGTH } from "../lib/task-types";

interface TaskComposerProps {
  busy: boolean;
  onCreate: (prompt: string) => Promise<boolean>;
}

export function TaskComposer({ busy, onCreate }: TaskComposerProps) {
  const [prompt, setPrompt] = useState("");
  const promptLength = unicodeLength(prompt);
  const promptId = useId();
  const hintId = `${promptId}-hint`;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = prompt.trim();
    if (!value || busy) {
      return;
    }
    if (await onCreate(value)) {
      setPrompt("");
    }
  }

  function submitWithShortcut(event: KeyboardEvent<HTMLTextAreaElement>) {
    if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
      event.preventDefault();
      event.currentTarget.form?.requestSubmit();
    }
  }

  return (
    <section className="composer-card" aria-labelledby="composer-heading">
      <div className="composer-heading">
        <div>
          <p className="eyebrow">Start something</p>
          <h1 id="composer-heading">What should Deep Work take on?</h1>
        </div>
        <span className="composer-badge">New task</span>
      </div>
      <form onSubmit={submit}>
        <label className="sr-only" htmlFor={promptId}>
          Task prompt
        </label>
        <textarea
          id={promptId}
          value={prompt}
          onChange={(event) => {
            if (unicodeLength(event.target.value) <= PROMPT_MAX_LENGTH) {
              setPrompt(event.target.value);
            }
          }}
          onKeyDown={submitWithShortcut}
          placeholder="Describe the outcome, constraints, and what a good result looks like…"
          rows={4}
          aria-describedby={hintId}
          disabled={busy}
        />
        <div className="composer-actions">
          <div className="composer-hints" id={hintId}>
            <p>
              <kbd>⌘</kbd>
              <span aria-hidden="true"> + </span>
              <kbd>Enter</kbd>
              <span> to create</span>
            </p>
            <span
              className="character-count"
              aria-label={`${promptLength} of ${PROMPT_MAX_LENGTH} characters`}
            >
              {promptLength.toLocaleString("en-US")} / {PROMPT_MAX_LENGTH.toLocaleString("en-US")}
            </span>
          </div>
          <button className="primary-button" type="submit" disabled={busy || prompt.trim() === ""}>
            {busy ? (
              <>
                <span className="button-spinner" aria-hidden="true" />
                Creating…
              </>
            ) : (
              <>
                Create task
                <span aria-hidden="true">→</span>
              </>
            )}
          </button>
        </div>
      </form>
    </section>
  );
}

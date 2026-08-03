"use client";

import { ArrowRight, FileCheck2, Route, ShieldCheck } from "lucide-react";
import { type FormEvent, useState } from "react";

import { BeamField } from "@/components/auth/beam-field";
import { ThemeToggle } from "@/components/shell/theme-toggle";

const trust = [
  {
    icon: ShieldCheck,
    title: "Your workspace, your control",
    text: "The access key is checked by the configured Deep Work API and exchanged for an HTTP-only session.",
  },
  {
    icon: Route,
    title: "The trace is truth",
    text: "Plans, decisions, evidence, and available execution traces remain attached to the task.",
  },
  {
    icon: FileCheck2,
    title: "Review before execution",
    text: "Every new task pauses at its proposed plan before the runner can continue.",
  },
] as const;

export default function LoginPage() {
  const [accessKey, setAccessKey] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const response = await fetch("/api/v1/auth/login", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ accessKey }),
      });
      if (response.ok) {
        window.location.assign("/tasks");
        return;
      }
      setError(response.status === 401 ? "That access key was not accepted." : "Sign in failed.");
    } catch {
      setError("Could not reach Deep Work. Please try again.");
    }
    setBusy(false);
  }

  return (
    <main className="grid min-h-dvh bg-background lg:grid-cols-[46%_54%]">
      <section className="relative flex min-h-[32rem] flex-col justify-between overflow-hidden border-b border-border bg-secondary/40 p-8 lg:min-h-dvh lg:border-r lg:border-b-0 lg:p-12 dark:bg-background">
        <BeamField />
        <div className="relative z-10 flex items-center gap-2">
          <span className="flex size-6 items-center justify-center rounded-md bg-brand text-brand-foreground">
            <span className="size-2.5 rounded-[3px] bg-brand-foreground" />
          </span>
          <span className="text-[15px] font-semibold tracking-tight">deepwork</span>
        </div>

        <div className="relative z-10 my-12 max-w-md">
          <h1 className="animate-fade-up text-balance text-3xl font-semibold tracking-tight lg:text-[2.75rem] lg:leading-[1.05] dark:text-gradient-blue">
            An operations room for work done by agents.
          </h1>
          <p
            className="mt-4 animate-fade-up text-pretty text-[15px] leading-relaxed text-muted-foreground"
            style={{ animationDelay: "0.12s" }}
          >
            Choose the right agent, review its plan, follow the work live, and inspect the evidence
            behind the result.
          </p>
        </div>

        <ul className="relative z-10 space-y-4">
          {trust.map((item, index) => {
            const Icon = item.icon;
            return (
              <li
                key={item.title}
                className="flex animate-fade-up gap-3"
                style={{ animationDelay: `${0.24 + index * 0.08}s` }}
              >
                <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-brand-soft text-brand">
                  <Icon className="size-4" />
                </span>
                <div>
                  <p className="text-sm font-medium text-crisp">{item.title}</p>
                  <p className="text-[13px] leading-relaxed text-muted-foreground">{item.text}</p>
                </div>
              </li>
            );
          })}
        </ul>
      </section>

      <section className="relative flex items-center justify-center p-6 sm:p-12">
        <div className="absolute top-6 right-6">
          <ThemeToggle />
        </div>
        <form onSubmit={handleSubmit} className="w-full max-w-sm">
          <p className="label-caps text-brand-accent">Connect</p>
          <h2 className="mt-2 text-xl font-semibold tracking-tight">Connect to Deep Work</h2>
          <p className="mt-1.5 text-[13px] leading-relaxed text-muted-foreground">
            Enter the access key for the Deep Work workspace your agents run in.
          </p>

          <label className="mt-6 block">
            <span className="mb-1.5 block text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
              Workspace access key
            </span>
            <input
              type="password"
              autoComplete="current-password"
              value={accessKey}
              onChange={(event) => setAccessKey(event.target.value)}
              required
              autoFocus
              placeholder="Enter access key"
              className="w-full rounded-xl border border-border bg-card px-3 py-2.5 font-mono text-[13px] outline-none transition-shadow focus:border-brand focus:ring-2 focus:ring-ring/30"
            />
          </label>

          {error ? (
            <p role="alert" className="mt-3 text-[13px] text-status-failed">
              {error}
            </p>
          ) : null}

          <button
            type="submit"
            disabled={busy || accessKey.trim() === ""}
            className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-brand px-4 py-2.5 text-sm font-medium text-brand-foreground transition-colors hover:bg-brand-hover disabled:pointer-events-none disabled:opacity-50"
          >
            {busy ? "Connecting…" : "Connect workspace"}
            {!busy && <ArrowRight className="size-4" />}
          </button>

          <div className="mt-6 rounded-2xl border border-border bg-secondary/40 p-4">
            <p className="text-[13px] font-medium">What happens next</p>
            <p className="mt-1 text-[12px] leading-relaxed text-muted-foreground">
              Deep Work opens your task inbox. Connection mode and target remain visible in the app
              shell; unsupported capabilities stay explicitly unavailable.
            </p>
          </div>
        </form>
      </section>
    </main>
  );
}

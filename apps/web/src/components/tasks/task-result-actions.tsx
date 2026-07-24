"use client";

import { Check, Copy, Download, FileText, PencilLine, RotateCcw } from "lucide-react";
import { useState } from "react";

import { formatResultBrief } from "@/lib/result-brief";
import type { EvidenceRecord } from "@/lib/task-types";

/** Turn a task title into a safe, bounded Markdown filename stem. */
function resultFilename(title: string): string {
  const stem = title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 60)
    .replace(/-+$/g, "");
  return `${stem || "task-result"}.md`;
}

function triggerDownload(filename: string, contents: string): void {
  const blob = new Blob([contents], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

const ACTION_CLASS =
  "inline-flex items-center gap-1.5 rounded-lg border border-border px-2.5 py-1.5 text-[13px] font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-foreground disabled:pointer-events-none disabled:opacity-50";

/**
 * Actions that make a finished run usable: copy the raw result, copy or download
 * a portable Markdown brief (prompt + result + evidence), and either re-dispatch
 * the objective immediately or open it in the composer to edit first. Purely
 * client-side, so it works identically against the loopback API and the
 * in-browser fixture runner.
 */
export function TaskResultActions({
  title,
  prompt,
  result,
  evidence = [],
  onRunAgain,
  runningAgain = false,
  runError,
  onEditRerun,
}: {
  title: string;
  prompt?: string;
  result?: string;
  evidence?: EvidenceRecord[];
  onRunAgain?: () => void;
  runningAgain?: boolean;
  runError?: string;
  onEditRerun?: () => void;
}) {
  const [copied, setCopied] = useState(false);
  const [briefCopied, setBriefCopied] = useState(false);
  const [copyFailed, setCopyFailed] = useState(false);

  async function copyResult(): Promise<void> {
    if (!result) return;
    try {
      await navigator.clipboard.writeText(result);
      setCopyFailed(false);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard access can be denied; surface it instead of failing silently.
      setCopyFailed(true);
    }
  }

  async function copyBrief(): Promise<void> {
    if (!result) return;
    try {
      // A portable Markdown brief: prompt + result + recorded evidence. The
      // formatter neutralizes active Markdown/HTML in untrusted fields so the
      // pasted brief cannot issue an unapproved external request.
      await navigator.clipboard.writeText(formatResultBrief({ title, prompt, result, evidence }));
      setCopyFailed(false);
      setBriefCopied(true);
      window.setTimeout(() => setBriefCopied(false), 2000);
    } catch {
      setCopyFailed(true);
    }
  }

  const hasResult = result !== undefined && result.trim() !== "";

  return (
    <div className="mt-3 border-t border-border/60 pt-3">
      <div className="flex flex-wrap items-center gap-2">
        {hasResult && (
          <>
            <button type="button" onClick={() => void copyResult()} className={ACTION_CLASS}>
              {copied ? (
                <Check aria-hidden className="size-3.5 text-status-done" />
              ) : (
                <Copy aria-hidden className="size-3.5" />
              )}
              {copied ? "Copied" : "Copy"}
            </button>
            <button type="button" onClick={() => void copyBrief()} className={ACTION_CLASS}>
              {briefCopied ? (
                <Check aria-hidden className="size-3.5 text-status-done" />
              ) : (
                <FileText aria-hidden className="size-3.5" />
              )}
              {briefCopied ? "Copied" : "Copy brief"}
            </button>
            <button
              type="button"
              onClick={() =>
                triggerDownload(
                  resultFilename(title),
                  formatResultBrief({ title, prompt, result, evidence }),
                )
              }
              className={ACTION_CLASS}
            >
              <Download aria-hidden className="size-3.5" />
              Download
            </button>
          </>
        )}
        {(onRunAgain || onEditRerun) && (
          <div className="ml-auto flex items-center gap-2">
            {onEditRerun && (
              <button type="button" onClick={onEditRerun} className={ACTION_CLASS}>
                <PencilLine aria-hidden className="size-3.5" />
                Edit &amp; re-run
              </button>
            )}
            {onRunAgain && (
              <button
                type="button"
                onClick={onRunAgain}
                disabled={runningAgain}
                className={ACTION_CLASS}
              >
                <RotateCcw aria-hidden className="size-3.5" />
                {runningAgain ? "Starting…" : "Run again"}
              </button>
            )}
          </div>
        )}
      </div>
      {copyFailed && (
        <p role="alert" className="mt-2 text-[13px] text-status-failed">
          Could not copy to the clipboard. Copy the result text above, or use Download to save the
          full brief.
        </p>
      )}
      {runError !== undefined && (
        <p role="alert" className="mt-2 text-[13px] text-status-failed">
          The re-run could not be started. {runError}
        </p>
      )}
      <span role="status" aria-live="polite" className="sr-only">
        {copied ? "Result copied to clipboard." : ""}
        {briefCopied ? "Result brief copied to clipboard." : ""}
      </span>
    </div>
  );
}

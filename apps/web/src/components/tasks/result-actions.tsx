"use client";

import { Check, Copy, FileText } from "lucide-react";
import { useCallback, useState } from "react";

import { formatResultBrief } from "@/lib/result-brief";
import type { EvidenceRecord } from "@/lib/task-types";
import { cn } from "@/lib/utils";

type CopyTarget = "result" | "brief";

const buttonClass =
  "flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-1.5 text-[13px] font-medium text-foreground/80 transition-colors hover:bg-accent";

/**
 * Copy/export controls for a completed task's deep-work output. Lets a user
 * take the result out of the app: the raw result text, or a full Markdown
 * brief (prompt + result + recorded evidence) for pasting into a doc or PR.
 */
export function ResultActions({
  title,
  prompt,
  result,
  evidence,
}: {
  title: string;
  prompt?: string;
  result?: string;
  evidence: EvidenceRecord[];
}) {
  const [copied, setCopied] = useState<CopyTarget | null>(null);
  const [error, setError] = useState<string | null>(null);

  const copy = useCallback(
    async (target: CopyTarget) => {
      const text =
        target === "brief"
          ? formatResultBrief({ title, prompt, result, evidence })
          : (result ?? "");
      try {
        await navigator.clipboard.writeText(text);
        setError(null);
        setCopied(target);
        setTimeout(() => {
          setCopied((current) => (current === target ? null : current));
        }, 2000);
      } catch {
        setError("Copy failed — your browser blocked clipboard access.");
      }
    },
    [title, prompt, result, evidence],
  );

  if (!result) {
    return null;
  }

  return (
    <div className="mt-3 flex flex-wrap items-center gap-2">
      <button type="button" onClick={() => void copy("result")} className={cn(buttonClass)}>
        {copied === "result" ? (
          <Check className="size-3.5 text-status-done" />
        ) : (
          <Copy className="size-3.5" />
        )}
        {copied === "result" ? "Copied" : "Copy result"}
      </button>
      <button type="button" onClick={() => void copy("brief")} className={cn(buttonClass)}>
        {copied === "brief" ? (
          <Check className="size-3.5 text-status-done" />
        ) : (
          <FileText className="size-3.5" />
        )}
        {copied === "brief" ? "Copied" : "Copy brief"}
      </button>
      {error && (
        <span role="status" className="text-[12px] text-status-failed">
          {error}
        </span>
      )}
    </div>
  );
}

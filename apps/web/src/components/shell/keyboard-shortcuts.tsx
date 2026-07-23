"use client";

import { X } from "lucide-react";
import { useEffect, useId, useRef } from "react";

interface Shortcut {
  keys: readonly string[];
  label: string;
}

interface ShortcutGroup {
  title: string;
  shortcuts: readonly Shortcut[];
}

/** Only shortcuts that are actually implemented are listed here. */
const GROUPS: readonly ShortcutGroup[] = [
  {
    title: "Global",
    shortcuts: [
      { keys: ["⌘", "K"], label: "Open the command palette" },
      { keys: ["?"], label: "Show this shortcuts help" },
      { keys: ["Esc"], label: "Close a dialog or overlay" },
    ],
  },
  {
    title: "Tasks inbox",
    shortcuts: [
      { keys: ["/"], label: "Focus the task search" },
      { keys: ["J", "↓"], label: "Move the highlight down" },
      { keys: ["K", "↑"], label: "Move the highlight up" },
      { keys: ["↵"], label: "Open the highlighted task" },
    ],
  },
  {
    title: "Run panel",
    shortcuts: [
      { keys: ["←", "→"], label: "Switch between tabs" },
      { keys: ["Home", "End"], label: "Jump to the first / last tab" },
    ],
  },
];

const FOCUSABLE =
  'a[href], button:not([disabled]), input, select, textarea, [tabindex]:not([tabindex="-1"])';

export function KeyboardShortcuts({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const restoreFocusRef = useRef<HTMLElement | null>(null);
  const titleId = useId();

  useEffect(() => {
    if (!open) return;
    // Move focus into the dialog, remembering the invoking element to restore.
    restoreFocusRef.current =
      document.activeElement instanceof HTMLElement ? document.activeElement : null;
    dialogRef.current?.focus();

    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        onOpenChange(false);
        return;
      }
      if (event.key !== "Tab") return;
      const dialog = dialogRef.current;
      if (!dialog) return;
      const focusables = Array.from(dialog.querySelectorAll<HTMLElement>(FOCUSABLE));
      if (focusables.length === 0) {
        event.preventDefault();
        return;
      }
      const first = focusables[0];
      const last = focusables[focusables.length - 1];
      const active = document.activeElement;
      const atEdge = event.shiftKey ? active === first || active === dialog : active === last;
      if (atEdge || !dialog.contains(active)) {
        event.preventDefault();
        (event.shiftKey ? last : first).focus();
      }
    }

    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("keydown", onKey);
      restoreFocusRef.current?.focus();
    };
  }, [open, onOpenChange]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center bg-foreground/25 px-4 pt-[12vh] backdrop-blur-sm"
      onClick={() => onOpenChange(false)}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        className="w-full max-w-lg overflow-hidden rounded-2xl border border-border bg-popover shadow-2xl focus:outline-none"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          <h2 id={titleId} className="text-sm font-semibold text-crisp">
            Keyboard shortcuts
          </h2>
          <button
            type="button"
            onClick={() => onOpenChange(false)}
            aria-label="Close shortcuts help"
            className="flex size-7 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
          >
            <X className="size-4" />
          </button>
        </div>
        <div className="max-h-[60vh] space-y-5 overflow-auto p-4">
          {GROUPS.map((group) => (
            <section key={group.title}>
              <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                {group.title}
              </h3>
              <ul className="space-y-1.5">
                {group.shortcuts.map((shortcut) => (
                  <li
                    key={shortcut.label}
                    className="flex items-center justify-between gap-4 text-sm"
                  >
                    <span className="text-foreground/90">{shortcut.label}</span>
                    <span className="flex shrink-0 items-center gap-1">
                      {shortcut.keys.map((key) => (
                        <kbd
                          key={key}
                          className="inline-flex min-w-[1.5rem] justify-center rounded-md border border-border bg-background px-1.5 py-0.5 font-mono text-[11px] text-muted-foreground"
                        >
                          {key}
                        </kbd>
                      ))}
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>
      </div>
    </div>
  );
}

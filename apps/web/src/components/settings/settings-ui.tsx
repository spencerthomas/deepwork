"use client";

import { Check, ChevronDown } from "lucide-react";
import type { ReactNode } from "react";
import { useEffect, useRef, useState } from "react";

import { cn } from "@/lib/utils";

/** Page heading for a settings section. */
export function SettingsHeader({
  title,
  description,
  learnMore,
  actions,
}: {
  title: string;
  description?: string;
  learnMore?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-8 flex items-start justify-between gap-4">
      <div>
        <h1 className="text-balance text-2xl font-semibold tracking-tight text-crisp">{title}</h1>
        {description && (
          <p className="mt-1.5 max-w-2xl text-pretty text-[13px] leading-relaxed text-muted-foreground">
            {description}
            {learnMore && (
              <>
                {" "}
                <a
                  href={learnMore}
                  target="_blank"
                  rel="noreferrer"
                  className="text-brand-accent hover:underline"
                >
                  Learn more
                </a>
              </>
            )}
          </p>
        )}
      </div>
      {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
    </div>
  );
}

/** Small group label above a card. */
export function GroupLabel({ children }: { children: ReactNode }) {
  return <h2 className="mb-2 text-[13px] font-semibold text-crisp">{children}</h2>;
}

/** A bordered card that holds a stack of rows. */
export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={cn(
        "divide-y divide-border overflow-hidden rounded-2xl border border-border bg-card",
        className,
      )}
    >
      {children}
    </div>
  );
}

/** A single labeled row inside a Card. Control goes on the right. */
export function Row({
  title,
  description,
  control,
  children,
  align = "center",
}: {
  title: string;
  description?: string;
  control?: ReactNode;
  children?: ReactNode;
  align?: "center" | "start";
}) {
  return (
    <div
      className={cn(
        "flex justify-between gap-4 px-4 py-3.5",
        align === "center" ? "items-center" : "items-start",
      )}
    >
      <div className="min-w-0">
        <p className="text-[13px] font-medium text-crisp">{title}</p>
        {description && (
          <p className="mt-0.5 text-pretty text-[12px] leading-relaxed text-muted-foreground">
            {description}
          </p>
        )}
        {children}
      </div>
      {control && <div className="shrink-0">{control}</div>}
    </div>
  );
}

/** iOS-style toggle. */
export function Toggle({
  checked,
  onChange,
  label,
}: {
  checked: boolean;
  onChange: (value: boolean) => void;
  label?: string;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      onClick={() => onChange(!checked)}
      className={cn(
        "relative inline-flex h-6 w-10 shrink-0 items-center rounded-full transition-colors",
        checked ? "bg-brand" : "bg-secondary",
      )}
    >
      <span
        className={cn(
          "inline-block size-5 rounded-full bg-white shadow-sm transition-transform",
          checked ? "translate-x-[18px]" : "translate-x-0.5",
        )}
      />
    </button>
  );
}

/** Text / number input styled for settings. */
export function TextInput({
  value,
  onChange,
  placeholder,
  type = "text",
  className,
  mono,
}: {
  value: string | number;
  onChange: (value: string) => void;
  placeholder?: string;
  type?: string;
  className?: string;
  mono?: boolean;
}) {
  return (
    <input
      type={type}
      value={value}
      onChange={(event) => onChange(event.target.value)}
      placeholder={placeholder}
      className={cn(
        "rounded-lg border border-border bg-background px-3 py-1.5 text-[13px] text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-brand/50",
        mono && "font-mono",
        className,
      )}
    />
  );
}

/** Dropdown select. */
export function Select<T extends string>({
  value,
  options,
  onChange,
  className,
}: {
  value: T;
  options: { value: T; label: string; hint?: string }[];
  onChange: (value: T) => void;
  className?: string;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const current = options.find((option) => option.value === value);

  useEffect(() => {
    if (!open) {
      return;
    }
    const onDown = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    window.addEventListener("mousedown", onDown);
    return () => window.removeEventListener("mousedown", onDown);
  }, [open]);

  return (
    <div ref={ref} className={cn("relative", className)}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex min-w-36 items-center justify-between gap-2 rounded-lg border border-border bg-background px-3 py-1.5 text-[13px] font-medium text-foreground transition-colors hover:bg-accent"
      >
        <span className="truncate">{current?.label ?? value}</span>
        <ChevronDown
          className={cn(
            "size-3.5 text-muted-foreground transition-transform",
            open && "rotate-180",
          )}
        />
      </button>
      {open && (
        <div className="absolute right-0 z-30 mt-1 max-h-72 w-64 overflow-auto rounded-xl border border-border bg-popover p-1 shadow-xl">
          {options.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => {
                onChange(option.value);
                setOpen(false);
              }}
              className={cn(
                "flex w-full items-start gap-2 rounded-lg px-2.5 py-2 text-left transition-colors hover:bg-accent",
                option.value === value && "bg-accent/60",
              )}
            >
              <Check
                className={cn(
                  "mt-0.5 size-3.5 shrink-0 text-brand-accent",
                  option.value === value ? "opacity-100" : "opacity-0",
                )}
              />
              <span className="min-w-0">
                <span className="block text-[13px] font-medium text-foreground">
                  {option.label}
                </span>
                {option.hint && (
                  <span className="block text-[12px] text-muted-foreground">{option.hint}</span>
                )}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

/** Segmented control (tabs). */
export function Segmented<T extends string>({
  value,
  options,
  onChange,
  size = "md",
}: {
  value: T;
  options: { value: T; label: string }[];
  onChange: (value: T) => void;
  size?: "sm" | "md";
}) {
  return (
    <div className="inline-flex items-center gap-0.5 rounded-xl border border-border bg-secondary/50 p-0.5">
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          aria-pressed={value === option.value}
          onClick={() => onChange(option.value)}
          className={cn(
            "rounded-[9px] font-medium transition-colors",
            size === "sm" ? "px-2 py-1 text-[12px]" : "px-2.5 py-1.5 text-[13px]",
            value === option.value
              ? "bg-card text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground",
          )}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

/** Empty-state card. */
export function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-2xl border border-border bg-card p-5">
      <p className="text-[13px] font-medium text-crisp">{title}</p>
      <p className="mt-0.5 text-[12px] text-muted-foreground">{description}</p>
    </div>
  );
}

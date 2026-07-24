import Link from "next/link";
import type { ComponentType, MouseEventHandler, ReactNode } from "react";

import { cn } from "@/lib/utils";

export function SidebarLabel({ children }: { children: ReactNode }) {
  return (
    <p className="px-3 pb-1.5 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
      {children}
    </p>
  );
}

interface SidebarItemProps {
  icon?: ComponentType<{ className?: string }>;
  label: string;
  count?: number;
  active?: boolean;
  dot?: string;
  href?: string;
  onClick?: MouseEventHandler<HTMLElement>;
}

export function SidebarItem({
  icon: Icon,
  label,
  count,
  active,
  dot,
  href,
  onClick,
}: SidebarItemProps) {
  const className = cn(
    "flex w-full items-center gap-2.5 rounded-xl px-3 py-1.5 text-left text-sm transition-colors",
    active
      ? "bg-brand-soft text-crisp text-foreground"
      : "text-muted-foreground hover:bg-accent hover:text-foreground",
  );
  const body = (
    <>
      {Icon && <Icon className={cn("size-4", active ? "text-brand-accent" : "")} />}
      {dot && <span className={cn("size-1.5 rounded-full", dot)} aria-hidden />}
      <span className="truncate">{label}</span>
      {count !== undefined && (
        <span
          className={cn(
            "ml-auto rounded-full px-1.5 py-0.5 text-[11px] font-medium tabular-nums",
            active ? "bg-brand/15 text-brand-accent" : "bg-accent text-muted-foreground",
          )}
        >
          {count}
        </span>
      )}
    </>
  );

  if (href !== undefined) {
    return (
      <Link
        href={href}
        className={className}
        onClick={onClick}
        aria-current={active ? "page" : undefined}
      >
        {body}
      </Link>
    );
  }
  return (
    <button type="button" className={className} onClick={onClick} aria-pressed={active}>
      {body}
    </button>
  );
}

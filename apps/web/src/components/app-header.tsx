"use client";

import { useEffect, useState } from "react";

import type { ClientMode } from "../lib/task-types";

interface AppHeaderProps {
  apiBaseUrl: string;
  mode: ClientMode;
  /** Route of the destination currently being viewed; used to mark the active nav item. */
  activePath?: string;
}

export interface PrimaryNavigationItem {
  /** Present when the destination is a delivered route; absent items are not yet available. */
  href?: string;
  label: string;
}

export const PRIMARY_NAVIGATION: readonly PrimaryNavigationItem[] = [
  { href: "/", label: "Tasks" },
  { href: "/approvals", label: "Approvals" },
  { href: "/agents", label: "Agents" },
  { href: "/schedules", label: "Schedules" },
  { href: "/activity", label: "Activity" },
  { label: "Observability" },
  { label: "Settings" },
];

export function AppHeader({ apiBaseUrl, mode, activePath = "/" }: AppHeaderProps) {
  const [darkTheme, setDarkTheme] = useState(false);
  const runtimeLabel = mode === "fixture" ? "Deterministic local fixture" : "Local API transport";

  useEffect(() => {
    const storedTheme = window.localStorage.getItem("dw-theme");
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const shouldUseDarkTheme = storedTheme ? storedTheme === "dark" : prefersDark;

    setDarkTheme(shouldUseDarkTheme);
    document.documentElement.classList.toggle("dark", shouldUseDarkTheme);
  }, []);

  function toggleTheme() {
    const shouldUseDarkTheme = !darkTheme;

    setDarkTheme(shouldUseDarkTheme);
    document.documentElement.classList.toggle("dark", shouldUseDarkTheme);
    window.localStorage.setItem("dw-theme", shouldUseDarkTheme ? "dark" : "light");
  }

  return (
    <>
      <div className={`runtime-banner runtime-${mode}`} role="note">
        <span className="runtime-banner-mark" aria-hidden="true" />
        <strong>{runtimeLabel}</strong>
        <span>
          External providers are unavailable; status and stream health describe this local product
          session only.
        </span>
      </div>
      <header className="app-header">
        <div className="header-topbar">
          <a className="brand" href="#main-content" aria-label="Deep Work home">
            <span className="brand-mark" aria-hidden="true">
              <span />
            </span>
            <span className="brand-copy">
              <strong>deepwork</strong>
            </span>
          </a>

          <span className="header-divider" aria-hidden="true">
            /
          </span>

          <div className="workspace-selector" aria-label="Current workspace">
            <span className="workspace-avatar" aria-hidden="true">
              DW
            </span>
            <span className="workspace-copy">
              <strong>local</strong>
              <span>product workspace</span>
            </span>
          </div>

          <div className="header-actions">
            <div className={`api-target target-${mode}`} title={apiBaseUrl}>
              <span className="api-target-dot" aria-hidden="true" />
              <span>{runtimeLabel}</span>
            </div>
            <button
              type="button"
              className="theme-toggle"
              aria-label={darkTheme ? "Use light theme" : "Use dark theme"}
              aria-pressed={darkTheme}
              onClick={toggleTheme}
            >
              {darkTheme ? (
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M21 12.8A8.6 8.6 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z" />
                </svg>
              ) : (
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <circle cx="12" cy="12" r="4" />
                  <path d="M12 2v2M12 20v2M4.93 4.93l1.42 1.42M17.65 17.65l1.42 1.42M2 12h2M20 12h2M4.93 19.07l1.42-1.42M17.65 6.35l1.42-1.42" />
                </svg>
              )}
            </button>
            <a className="new-task-link" href="#composer-heading">
              <span aria-hidden="true">+</span>
              New task
            </a>
          </div>
        </div>

        <nav className="product-navigation" aria-label="Primary navigation">
          {PRIMARY_NAVIGATION.map((item) => {
            if (item.href) {
              const current = item.href === activePath;
              return (
                <a
                  className={`product-navigation-item${current ? " is-active" : ""}`}
                  href={item.href}
                  aria-current={current ? "page" : undefined}
                  key={item.label}
                >
                  {item.label}
                  {current ? <span className="navigation-indicator" aria-hidden="true" /> : null}
                </a>
              );
            }
            return (
              <span
                className="product-navigation-item is-disabled"
                aria-disabled="true"
                title={`${item.label} — coming soon`}
                key={item.label}
              >
                {item.label}
                <span className="navigation-soon">Soon</span>
              </span>
            );
          })}
        </nav>
      </header>
    </>
  );
}

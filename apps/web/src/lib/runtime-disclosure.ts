import type { ClientMode } from "./task-types";

export interface ShellRuntimePresentation {
  workspaceLabel: string;
  workspaceSubtitle: string;
}

export function shellRuntimePresentation(mode: ClientMode): ShellRuntimePresentation {
  if (mode === "fixture") {
    return {
      workspaceLabel: "Demo",
      workspaceSubtitle: "sample data",
    };
  }

  return {
    workspaceLabel: "Workspace",
    workspaceSubtitle: "connected",
  };
}

/**
 * A short, plain line about where the user's tasks run — for the person, not
 * the system. Demo says it is a demo; connected speaks to their workspace.
 */
export function runtimeDisclosure(mode: ClientMode): string {
  if (mode === "fixture") {
    return "Demo — runs in your browser with sample data.";
  }

  return "Connected to your Deep Work workspace.";
}

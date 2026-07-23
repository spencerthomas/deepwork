import type { ClientMode } from "./task-types";

export interface ShellRuntimePresentation {
  workspaceLabel: string;
  workspaceSubtitle: string;
}

export function shellRuntimePresentation(mode: ClientMode): ShellRuntimePresentation {
  if (mode === "fixture") {
    return {
      workspaceLabel: "fixture",
      workspaceSubtitle: "in-browser workspace",
    };
  }

  return {
    workspaceLabel: "configured API",
    workspaceSubtitle: "control surface",
  };
}

/**
 * Describe only runtime facts the browser can prove from its selected adapter.
 * API mode identifies a transport boundary, not the server-side runner or its
 * provider configuration.
 */
export function runtimeDisclosure(mode: ClientMode): string {
  if (mode === "fixture") {
    return "Demo fixture mode — deterministic in-browser data, no external providers.";
  }

  return "API mode — backend runner and external-provider availability are unknown to this client.";
}

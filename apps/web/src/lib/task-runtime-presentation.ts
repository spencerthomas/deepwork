import type { ClientMode } from "./task-types";

/**
 * Browser-safe runtime language for task surfaces.
 *
 * Fixture mode can describe the adapter this bundle selects directly. API mode
 * only identifies the configured HTTP boundary; runner, provider, and
 * durability details stay unknown unless an explicit capability response
 * proves them elsewhere.
 */
export interface TaskRuntimePresentation {
  runnerName: string;
  newTaskDescription: string;
  sourceSelectionDescription: string;
  commandNewTaskHint: string;
  approvalsDescription: string;
  activityDescription: string;
  activitySessionNote: string;
  inboxEyebrow: string;
  inboxDescription: string;
  inboxScope: string;
  inboxEmptyDescription: string;
  runEventSource: string;
  runFilesDescription: string;
  runFooter: string;
  settingsModeDescription: string;
  settingsConnectionTarget: string;
  settingsStatusSourceDescription: string;
}

export function taskRuntimePresentation(
  mode: ClientMode,
  apiBaseUrl = "the configured API",
): TaskRuntimePresentation {
  if (mode === "fixture") {
    return {
      runnerName: "In-browser fixture runner",
      newTaskDescription:
        "Describe the outcome you want. The in-browser fixture runner proposes a plan and waits for your approval before executing.",
      sourceSelectionDescription:
        "Unavailable — fixture mode uses deterministic in-browser data with no external providers.",
      commandNewTaskHint: "Dispatch the in-browser fixture runner",
      approvalsDescription:
        "Every in-browser fixture run paused for your decision. The available verbs come from each interruption itself — nothing here acts without you.",
      activityDescription:
        "Task status plus every fixture event this browser session has observed. Reloading the page resets fixture task history; entries are ordered by task and event id — no timestamps are fabricated.",
      activitySessionNote:
        "Fixture events are captured in this browser; status rows come from the in-browser fixture task list.",
      inboxEyebrow: "Workspace · fixture",
      inboxDescription:
        "Dispatch work to the in-browser fixture runner, watch it run, steer the plan, and review the evidence behind every result.",
      inboxScope:
        "Search and filters cover deterministic fixture tasks in this browser session. This client does not provide global or provider-side search.",
      inboxEmptyDescription:
        "Dispatch your first task to the in-browser fixture runner — it plans, pauses for your approval, and reports evidence-backed results.",
      runEventSource: "replayed and appended by the in-browser fixture adapter",
      runFilesDescription:
        "File changes appear here when a coding-capable source runs the task. The in-browser fixture runner produces a text brief only.",
      runFooter: "Deterministic in-browser fixture runner · no external providers",
      settingsModeDescription:
        "fixture selects a deterministic in-browser adapter with no network; api sends requests to the configured Deep Work API.",
      settingsConnectionTarget: "in-browser fixture adapter",
      settingsStatusSourceDescription:
        "This fixture status was synthesized by the in-browser adapter, not fetched from an API.",
    };
  }

  return {
    runnerName: "Configured API task runner",
    newTaskDescription:
      "Describe the outcome you want. The configured API task runner can propose a plan and wait for your approval before executing.",
    sourceSelectionDescription:
      "Source selection is unavailable in this client. API-side runner and provider configuration are not inferred.",
    commandNewTaskHint: "Dispatch through the configured API",
    approvalsDescription:
      "Every task run loaded from the configured API that has paused for your decision. The available verbs come from each interruption itself — nothing here acts without you.",
    activityDescription:
      "Task status plus every event this browser session has observed from the configured API. Entries are ordered by task and event id — no timestamps are fabricated. Server-side retention is not inferred.",
    activitySessionNote:
      "Streamed events are captured while a task page is open in this tab; status rows come from the configured API task list.",
    inboxEyebrow: "Workspace · API",
    inboxDescription:
      "Dispatch work through the configured API, watch it run, steer the plan, and review the evidence behind every result.",
    inboxScope:
      "Search and filters cover tasks loaded from the configured API in this session. This client does not provide global or provider-side search.",
    inboxEmptyDescription:
      "Dispatch your first task through the configured API — the server-side runner and provider configuration remain unknown to this client.",
    runEventSource: "replayed and appended from the configured API",
    runFilesDescription:
      "File changes appear here when a coding-capable source runs the task. This client has not established that capability for the configured API.",
    runFooter: "Configured API task runner · server-side runner and provider configuration unknown",
    settingsModeDescription:
      "api sends requests to the configured Deep Work API; fixture selects a deterministic in-browser adapter with no network.",
    settingsConnectionTarget: apiBaseUrl,
    settingsStatusSourceDescription:
      "api means this status was fetched from the configured API. It does not identify the server-side runner, provider configuration, or durability model.",
  };
}

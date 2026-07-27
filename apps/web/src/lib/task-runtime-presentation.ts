import type { ClientMode } from "./task-types";

/**
 * User-facing copy for task surfaces, written for the person and their task.
 *
 * The voice is plain and outcome-first: say what the user can do and what will
 * happen, not how the system is wired. Demo mode says it is a demo; connected
 * mode speaks to the user's workspace. No transport, adapter, or provider
 * vocabulary leaks into the interface.
 */
export interface TaskRuntimePresentation {
  taskConnectionLabel: string;
  taskOriginLabel: string;
  dispatchTargetLabel: string;
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

// Shared, mode-independent copy: the user doesn't care how the task is routed.
const START_A_TASK = "Start a task";
const DESCRIBE_TASK =
  "Describe what you want done. Deep Work suggests a plan and checks with you before it starts.";
const APPROVALS =
  "When a task needs your go-ahead, it waits here. You decide what happens next — nothing runs without you.";
const INBOX_DESCRIPTION = "Hand off a task, watch it work, adjust the plan, and get the result.";
const INBOX_EMPTY =
  "Start your first task. Describe what you want, and Deep Work plans it, checks with you, then does it.";
const RUN_EVENTS = "as the task runs";
const SETTINGS_MODE =
  "Demo runs in your browser with sample data. Connected runs your tasks through your Deep Work workspace.";

export function taskRuntimePresentation(
  mode: ClientMode,
  apiBaseUrl = "your workspace",
): TaskRuntimePresentation {
  if (mode === "fixture") {
    return {
      taskConnectionLabel: "Mode",
      taskOriginLabel: "Demo",
      dispatchTargetLabel: "Agent",
      newTaskDescription: DESCRIBE_TASK,
      sourceSelectionDescription: "Demo mode — sample data, no account needed.",
      commandNewTaskHint: START_A_TASK,
      approvalsDescription: APPROVALS,
      activityDescription: "Everything Deep Work has done on your tasks, most recent first.",
      activitySessionNote: "This is a demo — your tasks reset when you reload the page.",
      inboxEyebrow: "Demo",
      inboxDescription: INBOX_DESCRIPTION,
      inboxScope: "Search covers the tasks in this demo.",
      inboxEmptyDescription: INBOX_EMPTY,
      runEventSource: RUN_EVENTS,
      runFilesDescription:
        "Files show up here when a task changes code. This demo returns a written answer only.",
      runFooter: "Demo · sample data",
      settingsModeDescription: SETTINGS_MODE,
      settingsConnectionTarget: "demo",
      settingsStatusSourceDescription: "This status is from the demo.",
    };
  }

  return {
    taskConnectionLabel: "Mode",
    taskOriginLabel: "Connected",
    dispatchTargetLabel: "Agent",
    newTaskDescription: DESCRIBE_TASK,
    sourceSelectionDescription: "Connected to your Deep Work workspace.",
    commandNewTaskHint: START_A_TASK,
    approvalsDescription: APPROVALS,
    activityDescription: "Everything Deep Work has done on your tasks, most recent first.",
    activitySessionNote: "Live updates appear while a task is open.",
    inboxEyebrow: "Workspace",
    inboxDescription: INBOX_DESCRIPTION,
    inboxScope: "Search covers your tasks.",
    inboxEmptyDescription: INBOX_EMPTY,
    runEventSource: RUN_EVENTS,
    runFilesDescription: "Files show up here when a task changes code.",
    runFooter: "Connected to your workspace",
    settingsModeDescription: SETTINGS_MODE,
    settingsConnectionTarget: apiBaseUrl,
    settingsStatusSourceDescription: "This status is live from your workspace.",
  };
}

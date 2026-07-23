export const TASK_EVENT_NAMES = [
  "task.created",
  "run.started",
  "content.delta",
  "plan.proposed",
  "interrupt.requested",
  "decision.recorded",
  "run.completed",
] as const;

export const PROMPT_MAX_LENGTH = 8_000;

export type TaskEventName = (typeof TASK_EVENT_NAMES)[number];

export type TaskStatus =
  | "queued"
  | "running"
  | "waiting-approval"
  | "completed"
  | "rejected"
  | "failed"
  | "cancelled"
  | "unknown";

export type ClientMode = "api" | "fixture";

export type ConnectionState =
  | "connecting"
  | "connected"
  | "reconnecting"
  | "closed";

export interface TaskSummary {
  taskId: string;
  runId?: string;
  title: string;
  prompt?: string;
  status: TaskStatus;
  createdAt?: string;
  updatedAt?: string;
}

export interface TaskDetail extends TaskSummary {
  result?: string;
}

export interface CreateTaskResult {
  taskId: string;
  runId: string;
  status: "queued";
}

export interface TaskEvent {
  id: string;
  name: TaskEventName;
  data: Record<string, unknown>;
}

export interface DecisionInput {
  interruptId: string;
  decision: "approve" | "reject";
  comment?: string;
}

export interface TaskEventHandlers {
  onConnectionChange: (state: ConnectionState) => void;
  onError: (message: string) => void;
  onEvent: (event: TaskEvent) => void;
}

export interface TaskClient {
  readonly mode: ClientMode;
  readonly apiBaseUrl: string;
  createTask(prompt: string, signal?: AbortSignal): Promise<CreateTaskResult>;
  decide(
    taskId: string,
    input: DecisionInput,
    signal?: AbortSignal,
  ): Promise<void>;
  getTask(taskId: string, signal?: AbortSignal): Promise<TaskDetail>;
  listTasks(signal?: AbortSignal): Promise<TaskSummary[]>;
  subscribe(taskId: string, handlers: TaskEventHandlers): () => void;
}

export interface ActiveInterrupt {
  interruptId: string;
  title: string;
  question: string;
}

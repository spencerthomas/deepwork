export const TASK_EVENT_NAMES = [
  "task.created",
  "run.started",
  "content.delta",
  "plan.proposed",
  "plan.updated",
  "evidence.recorded",
  "interrupt.requested",
  "decision.recorded",
  "run.completed",
] as const;

export const PROMPT_MAX_LENGTH = 8_000;
export const DECISION_COMMENT_MAX_LENGTH = 1_000;
export const PLAN_STEP_MAX_LENGTH = 1_000;
export const PLAN_STEP_MAX_COUNT = 8;

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

export type ConnectionState = "connecting" | "connected" | "reconnecting" | "closed";

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
  evidence?: EvidenceRecord[];
  pendingInterrupt?: ActiveInterrupt;
  proposedPlan?: ProposedPlan;
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
  decision: "approve" | "reject" | "respond";
  comment?: string;
}

export interface DecisionResult {
  decision: DecisionInput["decision"];
  duplicate: boolean;
  interruptId: string;
  runId: string;
  status: "accepted";
  taskId: string;
}

export interface PlanUpdateInput {
  interruptId: string;
  expectedRevision: number;
  steps: string[];
}

export interface PlanUpdateResult {
  taskId: string;
  runId: string;
  interruptId: string;
  plan: ProposedPlan;
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
  decide(taskId: string, input: DecisionInput, signal?: AbortSignal): Promise<DecisionResult>;
  getTask(taskId: string, signal?: AbortSignal): Promise<TaskDetail>;
  listTasks(signal?: AbortSignal): Promise<TaskSummary[]>;
  subscribe(taskId: string, handlers: TaskEventHandlers): () => void;
  updatePlan(
    taskId: string,
    input: PlanUpdateInput,
    signal?: AbortSignal,
  ): Promise<PlanUpdateResult>;
}

export interface ActiveInterrupt {
  decisions: DecisionInput["decision"][];
  interruptId: string;
  planRevision?: number;
  title: string;
  question: string;
}

export interface ProposedPlan {
  evidenceRefs: string[];
  revision: number;
  steps: string[];
  title: string;
}

export interface EvidenceRecord {
  evidenceId: string;
  kind: string;
  source: string;
  summary: string;
  verified: boolean;
}

import type {
  CancelResult,
  CreateTaskResult,
  DecisionInput,
  DecisionResult,
  EvidenceRecord,
  PlanUpdateInput,
  PlanUpdateResult,
  ProposedPlan,
  TaskClient,
  TaskDetail,
  TaskEvent,
  TaskEventHandlers,
  TaskStatus,
  TaskSummary,
} from "./task-types";
import { validateDecisionInput, validatePlanSteps, validatePrompt } from "./task-normalizers";

const TERMINAL_STATUSES: ReadonlySet<TaskStatus> = new Set<TaskStatus>([
  "completed",
  "rejected",
  "failed",
  "cancelled",
]);

function isTerminalFixtureStatus(status: TaskStatus): boolean {
  return TERMINAL_STATUSES.has(status);
}

interface FixtureTask extends TaskDetail {
  events: TaskEvent[];
  interruptId: string;
  responseNumber: number;
}

const tasks = new Map<string, FixtureTask>();
const subscribers = new Map<string, Set<TaskEventHandlers>>();
let nextTaskNumber = 1;

function emit(task: FixtureTask, name: TaskEvent["name"], data: TaskEvent["data"]) {
  const event: TaskEvent = {
    id: `${task.taskId}:${task.events.length + 1}`,
    name,
    data,
  };
  task.events.push(event);
  for (const handler of subscribers.get(task.taskId) ?? []) {
    handler.onEvent(event);
  }
}

function updateStatus(task: FixtureTask, status: TaskStatus) {
  task.status = status;
  task.updatedAt = new Date().toISOString();
}

function scheduleRun(task: FixtureTask) {
  const steps: ReadonlyArray<readonly [number, () => void]> = [
    [
      180,
      () => {
        updateStatus(task, "running");
        emit(task, "run.started", {
          runId: task.runId,
          status: "running",
        });
      },
    ],
    [
      300,
      () => {
        const evidence: EvidenceRecord = {
          evidenceId: `${task.taskId}:request`,
          kind: "fixture",
          summary: "The deterministic local runner inspected the sanitized task request.",
          source: "deterministic-local-runner",
          verified: false,
        };
        task.evidence = [evidence];
        emit(task, "evidence.recorded", { ...evidence });
      },
    ],
    [
      420,
      () => {
        const plan: ProposedPlan = {
          revision: 1,
          title: "Review the proposed local plan",
          steps: ["Inspect the request", "Execute the bounded work", "Verify the result"],
          evidenceRefs: [`${task.taskId}:request`],
        };
        task.proposedPlan = plan;
        emit(task, "plan.proposed", {
          ...plan,
          evidenceClass: "fixture",
        });
      },
    ],
    [
      680,
      () =>
        emit(task, "content.delta", {
          delta: "I’ve prepared a short plan and reached a gated action.",
        }),
    ],
    [
      940,
      () => {
        updateStatus(task, "waiting-approval");
        emit(task, "interrupt.requested", {
          interruptId: task.interruptId,
          title: "Approve the proposed action",
          question:
            "Review or edit the plan, approve it, reject it, or respond with requested changes.",
          decisions: ["approve", "reject", "respond"],
          planRevision: task.proposedPlan?.revision,
        });
      },
    ],
  ];

  for (const [delay, callback] of steps) {
    globalThis.setTimeout(() => {
      // A cancelled (or otherwise terminal) task must never be re-animated by a
      // still-pending scheduled step.
      if (isTerminalFixtureStatus(task.status)) return;
      callback();
    }, delay);
  }
}

function publicTask(task: FixtureTask): TaskDetail {
  return {
    taskId: task.taskId,
    runId: task.runId,
    title: task.title,
    prompt: task.prompt,
    status: task.status,
    createdAt: task.createdAt,
    updatedAt: task.updatedAt,
    result: task.result,
    proposedPlan: task.proposedPlan,
    evidence: task.evidence,
  };
}

export function createFixtureTaskClient(): TaskClient {
  return {
    mode: "fixture",
    apiBaseUrl: "local fixture adapter",

    async listTasks(): Promise<TaskSummary[]> {
      return [...tasks.values()].reverse().map((task) => publicTask(task));
    },

    async getTask(taskId: string): Promise<TaskDetail> {
      const task = tasks.get(taskId);
      if (!task) {
        throw new Error("The fixture task could not be found.");
      }
      return publicTask(task);
    },

    async createTask(prompt: string): Promise<CreateTaskResult> {
      const normalizedPrompt = validatePrompt(prompt);
      const sequence = nextTaskNumber++;
      const taskId = `fixture-task-${sequence}`;
      const runId = `fixture-run-${sequence}`;
      const createdAt = new Date().toISOString();
      const task: FixtureTask = {
        taskId,
        runId,
        title: normalizedPrompt,
        prompt: normalizedPrompt,
        status: "queued",
        createdAt,
        updatedAt: createdAt,
        events: [],
        interruptId: `fixture-interrupt-${sequence}`,
        responseNumber: 0,
      };
      tasks.set(taskId, task);
      emit(task, "task.created", { taskId, runId, status: "queued" });
      scheduleRun(task);
      return { taskId, runId, status: "queued" };
    },

    async decide(taskId: string, input: DecisionInput): Promise<DecisionResult> {
      const decision = validateDecisionInput(input);
      const task = tasks.get(taskId);
      if (!task) {
        throw new Error("The fixture task could not be found.");
      }
      if (task.status !== "waiting-approval") {
        throw new Error("This fixture task is not waiting for a decision.");
      }
      if (input.interruptId !== task.interruptId) {
        throw new Error("The decision does not match the active interrupt.");
      }

      emit(task, "decision.recorded", {
        interruptId: input.interruptId,
        decision: input.decision,
        commentProvided: decision.comment !== undefined,
        responseProvided: input.decision === "respond",
      });

      if (input.decision === "respond") {
        updateStatus(task, "running");
        globalThis.setTimeout(() => {
          if (isTerminalFixtureStatus(task.status)) return;
          task.responseNumber += 1;
          const currentPlan = task.proposedPlan;
          if (!currentPlan) {
            throw new Error("The fixture task has no plan to revise.");
          }
          const plan: ProposedPlan = {
            ...currentPlan,
            revision: currentPlan.revision + 1,
            title: "Revised local plan",
          };
          task.proposedPlan = plan;
          task.interruptId = `fixture-interrupt-${task.taskId}-${task.responseNumber + 1}`;
          emit(task, "content.delta", {
            text: "The local runner recorded the response without exposing its text.",
            evidenceClass: "fixture",
          });
          emit(task, "plan.updated", { ...plan, evidenceClass: "fixture" });
          updateStatus(task, "waiting-approval");
          emit(task, "interrupt.requested", {
            interruptId: task.interruptId,
            title: "Review the revised plan",
            question: "The response was applied safely. Review the revised plan before continuing.",
            decisions: ["approve", "reject", "respond"],
            planRevision: plan.revision,
          });
        }, 300);
        return {
          taskId: task.taskId,
          runId: task.runId ?? "",
          interruptId: input.interruptId,
          decision: input.decision,
          status: "accepted",
          duplicate: false,
        };
      }

      globalThis.setTimeout(() => {
        if (isTerminalFixtureStatus(task.status)) return;
        const status = input.decision === "approve" ? "completed" : "rejected";
        updateStatus(task, status);
        task.result =
          status === "completed"
            ? `First-pass result for “${task.prompt}”\n\nThe request was framed as a concrete outcome, divided into inspect, execute, and verify stages, and released only after reviewer approval. This fixture demonstrates the complete supervised run path; it does not claim live provider work.`
            : `The fixture run for “${task.prompt}” stopped after the proposal was rejected. No provider work was claimed or performed.`;
        emit(task, "run.completed", {
          runId: task.runId,
          status,
          summary: task.result,
        });
      }, 420);
      return {
        taskId: task.taskId,
        runId: task.runId ?? "",
        interruptId: input.interruptId,
        decision: input.decision,
        status: "accepted",
        duplicate: false,
      };
    },

    async cancelTask(taskId: string): Promise<CancelResult> {
      const task = tasks.get(taskId);
      if (!task) {
        throw new Error("The fixture task could not be found.");
      }
      const runId = task.runId ?? "";
      if (task.status === "cancelled") {
        return { taskId: task.taskId, runId, status: "cancelled", duplicate: true };
      }
      if (isTerminalFixtureStatus(task.status)) {
        throw new Error("This fixture task already finished and can no longer be cancelled.");
      }
      updateStatus(task, "cancelled");
      emit(task, "run.completed", {
        runId: task.runId,
        status: "cancelled",
        resultAvailable: false,
      });
      return { taskId: task.taskId, runId, status: "cancelled", duplicate: false };
    },

    async updatePlan(taskId: string, input: PlanUpdateInput): Promise<PlanUpdateResult> {
      const steps = validatePlanSteps(input.steps);
      const task = tasks.get(taskId);
      if (!task) {
        throw new Error("The fixture task could not be found.");
      }
      if (task.status !== "waiting-approval" || input.interruptId !== task.interruptId) {
        throw new Error("The plan edit does not match the active interrupt.");
      }
      if (!task.proposedPlan || input.expectedRevision !== task.proposedPlan.revision) {
        throw new Error("The plan changed. Reload the current revision before editing again.");
      }

      const plan: ProposedPlan = {
        ...task.proposedPlan,
        revision: task.proposedPlan.revision + 1,
        steps,
      };
      task.proposedPlan = plan;
      emit(task, "plan.updated", { ...plan, evidenceClass: "fixture" });
      return {
        taskId: task.taskId,
        runId: task.runId ?? "",
        interruptId: task.interruptId,
        plan,
      };
    },

    subscribe(taskId: string, handlers: TaskEventHandlers): () => void {
      const task = tasks.get(taskId);
      handlers.onConnectionChange("connecting");

      if (!task) {
        handlers.onError("The fixture task could not be found.");
        handlers.onConnectionChange("closed");
        return () => undefined;
      }

      const taskSubscribers = subscribers.get(taskId) ?? new Set();
      taskSubscribers.add(handlers);
      subscribers.set(taskId, taskSubscribers);
      queueMicrotask(() => {
        handlers.onConnectionChange("connected");
        for (const event of task.events) {
          handlers.onEvent(event);
        }
      });

      return () => {
        taskSubscribers.delete(handlers);
        handlers.onConnectionChange("closed");
      };
    },
  };
}

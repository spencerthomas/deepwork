import type {
  CreateTaskResult,
  DecisionInput,
  TaskClient,
  TaskDetail,
  TaskEvent,
  TaskEventHandlers,
  TaskStatus,
  TaskSummary,
} from "./task-types";
import { validatePrompt } from "./task-normalizers";

interface FixtureTask extends TaskDetail {
  events: TaskEvent[];
  interruptId: string;
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
      420,
      () =>
        emit(task, "plan.proposed", {
          summary: "Inspect the request, prepare the work, then verify the result.",
          steps: ["Inspect", "Execute", "Verify"],
        }),
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
            "The run is ready to continue. Approve the plan, or reject it with an optional note.",
        });
      },
    ],
  ];

  for (const [delay, callback] of steps) {
    globalThis.setTimeout(callback, delay);
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
  };
}

export function createFixtureTaskClient(): TaskClient {
  return {
    mode: "fixture",
    apiBaseUrl: "local fixture adapter",

    async listTasks(): Promise<TaskSummary[]> {
      return [...tasks.values()]
        .reverse()
        .map((task) => publicTask(task));
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
      };
      tasks.set(taskId, task);
      emit(task, "task.created", { taskId, runId, status: "queued" });
      scheduleRun(task);
      return { taskId, runId, status: "queued" };
    },

    async decide(taskId: string, input: DecisionInput): Promise<void> {
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
        ...(input.comment ? { comment: input.comment } : {}),
      });

      globalThis.setTimeout(() => {
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

import type {
  CancelResult,
  CodingOutcome,
  CreateTaskResult,
  DecisionInput,
  DecisionBatchInput,
  DecisionBatchResult,
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
import {
  validateDecisionBatchInput,
  validateDecisionInput,
  validatePlanSteps,
  validatePrompt,
} from "./task-normalizers";

const TERMINAL_STATUSES: ReadonlySet<TaskStatus> = new Set<TaskStatus>([
  "completed",
  "rejected",
  "failed",
  "cancelled",
]);

function isTerminalFixtureStatus(status: TaskStatus): boolean {
  return TERMINAL_STATUSES.has(status);
}

interface FixtureTask extends Omit<TaskDetail, "runId"> {
  runId: string;
  events: TaskEvent[];
  interruptId: string;
  responseNumber: number;
  batchReceipts: Map<string, { digest: string; receipt: DecisionBatchResult }>;
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

function installCodingOutcome(task: FixtureTask) {
  if (task.journey !== "coding") return;
  const coding: CodingOutcome = {
    evidenceClass: "fixture",
    repositoryId: "fixture_repo_deepwork",
    repository: "deepwork-fixtures/sample-app",
    baseBranch: "main",
    baseSha: "5d8f2de17703cb32fc4c6f6d7af0258ddf5f0f17",
    headSha: "bb525814d85c6e2e35233d703e0a4069dd625d75",
    environment: "Deep Work Node fixture",
    environmentVersion: 1,
    snapshotDigest: "sha256:4e7d3f64f7df824d",
    sandboxState: "cleaned",
    setupStatus: "passed",
    changedFiles: ["src/session.ts", "tests/session.test.ts"],
    draftPrNumber: 17,
    draftPrStatus: "draft",
    prCreateAttempts: 2,
    reconciledAfterTimeout: true,
    checks: ["lint:passed", "tests:passed"],
    mergeState: "unavailable",
  };
  task.coding = coding;
  emit(task, "coding.completed", { ...coding });
}

function installPendingInterrupt(task: FixtureTask, title: string, question: string) {
  const revision = task.proposedPlan?.revision ?? 1;
  const steps = task.proposedPlan?.steps ?? [];
  task.pendingInterrupt = {
    interruptId: task.interruptId,
    version: `${task.interruptId}:${revision}`,
    title,
    question,
    decisions: ["approve", "reject", "respond"],
    planRevision: revision,
    actionRequests: steps.map((text, index) => ({
      name: "execute_plan_step",
      description: `Plan step ${index + 1}`,
      args: { position: index + 1, text },
    })),
    reviewConfigs: steps.map(() => ({
      actionName: "execute_plan_step",
      allowedDecisions: ["approve", "edit", "reject"],
    })),
  };
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
          taskId: task.taskId,
          runId: task.runId,
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
        const title = "Approve the proposed action";
        const question =
          "Review each ordered action, approve or edit it, or reject the batch before work continues.";
        installPendingInterrupt(task, title, question);
        emit(task, "interrupt.requested", {
          interruptId: task.interruptId,
          title,
          question,
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
    pendingInterrupt: task.pendingInterrupt,
    journey: task.journey,
    coding: task.coding,
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

    async createTask(prompt: string, options = {}): Promise<CreateTaskResult> {
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
        ...(options.journey === "coding" ? { journey: "coding" as const } : {}),
        events: [],
        interruptId: `fixture-interrupt-${sequence}`,
        responseNumber: 0,
        batchReceipts: new Map(),
      };
      tasks.set(taskId, task);
      emit(task, "task.created", {
        taskId,
        runId,
        status: "queued",
        ...(options.journey === "coding"
          ? { journey: "coding", repositoryId: "fixture_repo_deepwork" }
          : {}),
      });
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
      task.pendingInterrupt = undefined;

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
          const title = "Review the revised plan";
          const question =
            "The response was applied safely. Review the revised plan before continuing.";
          installPendingInterrupt(task, title, question);
          emit(task, "interrupt.requested", {
            interruptId: task.interruptId,
            title,
            question,
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

      if (input.decision === "approve") {
        // Match the API contract: accepting the plan resumes the run before
        // the deterministic completion arrives, so live progress is visible.
        updateStatus(task, "running");
      }

      globalThis.setTimeout(() => {
        if (isTerminalFixtureStatus(task.status)) return;
        const status = input.decision === "approve" ? "completed" : "rejected";
        updateStatus(task, status);
        task.result =
          status === "completed"
            ? `First-pass result for “${task.prompt}”\n\nThe request was framed as a concrete outcome, divided into inspect, execute, and verify stages, and released only after reviewer approval. This fixture demonstrates the complete supervised run path; it does not claim live provider work.`
            : `The fixture run for “${task.prompt}” stopped after the proposal was rejected. No provider work was claimed or performed.`;
        if (status === "completed") installCodingOutcome(task);
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

    async decideBatch(taskId: string, input: DecisionBatchInput): Promise<DecisionBatchResult> {
      const task = tasks.get(taskId);
      if (!task) throw new Error("The fixture task could not be found.");
      const digest = JSON.stringify(input);
      const previous = task.batchReceipts.get(input.idempotencyKey);
      if (previous) {
        if (previous.digest !== digest) {
          throw new Error("The idempotency key was already used for a different decision batch.");
        }
        return { ...previous.receipt, duplicate: true };
      }
      if (task.status !== "waiting-approval" || !task.pendingInterrupt) {
        throw new Error("This fixture task is not waiting for an ordered decision.");
      }
      const batch = validateDecisionBatchInput(task.pendingInterrupt, input);
      const rejected = batch.decisions.some((decision) => decision.type === "reject");
      const nextSteps = task.proposedPlan?.steps.map((step, index) => {
        const decision = batch.decisions[index];
        if (decision?.type !== "edit") return step;
        const text = decision.editedAction.args.text;
        if (typeof text !== "string" || text.trim() === "") {
          throw new Error(`Edited action ${index + 1} requires a nonblank text argument.`);
        }
        return text;
      });
      if (nextSteps && task.proposedPlan) {
        task.proposedPlan = { ...task.proposedPlan, steps: nextSteps };
      }
      const receipt: DecisionBatchResult = {
        taskId: task.taskId,
        runId: task.runId ?? "",
        interruptId: batch.interruptId,
        version: batch.expectedVersion,
        decisionTypes: batch.decisions.map((decision) => decision.type),
        status: "accepted",
        duplicate: false,
      };
      task.batchReceipts.set(batch.idempotencyKey, { digest, receipt });
      task.pendingInterrupt = undefined;
      emit(task, "decision.recorded", {
        interruptId: batch.interruptId,
        version: batch.expectedVersion,
        decisionTypes: receipt.decisionTypes,
      });
      updateStatus(task, "running");
      globalThis.setTimeout(() => {
        if (task.status !== "running") return;
        const status = rejected ? "rejected" : "completed";
        updateStatus(task, status);
        const steps = task.proposedPlan?.steps.join("; ") ?? "No plan steps were available.";
        task.result = rejected
          ? `The fixture run for “${task.prompt}” stopped after the ordered proposal was rejected. No provider work was claimed or performed.`
          : `First-pass result for “${task.prompt}”\n\nApproved plan executed in order: ${steps}. The fixture proves the supervised batch path; it does not claim live provider work.`;
        if (status === "completed") installCodingOutcome(task);
        emit(task, "run.completed", {
          runId: task.runId,
          status,
          summary: task.result,
        });
      }, 420);
      return receipt;
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
      if (task.pendingInterrupt) {
        installPendingInterrupt(task, task.pendingInterrupt.title, task.pendingInterrupt.question);
      }
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

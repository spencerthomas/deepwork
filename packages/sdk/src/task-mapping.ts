import {
  applicationEventId,
  decisionInput,
  displayText,
  evidenceId,
  evidenceRecord,
  EVENT_SEQUENCE_MAX,
  interruptId,
  isTaskDecision,
  objectiveText,
  pendingInterrupt,
  planEditInput,
  proposedPlan,
  resultText,
  runId,
  sourceId,
  sourceApplicationEventKey,
  sourceEvidenceKey,
  sourceInterruptKey,
  sourceRunKey,
  sourceThreadKey,
  taskAccepted,
  taskDetail,
  taskId,
  taskResult,
  taskSummary,
  threadId,
  type DecisionInput,
  type DecisionReceipt,
  type EvidenceClass,
  type EvidenceRecord,
  type PlanEditInput,
  type PlanEditReceipt,
  type PendingInterrupt,
  type SourceRunKey,
  type SourceThreadKey,
  type TaskAccepted,
  type TaskApplicationEvent,
  type TaskDetail,
  type TaskEventName,
  type TaskId,
  type TaskResult,
  type TaskStateFacts,
  type TaskSummary,
} from "@deepwork/domain";

import { contractError, type SdkResult } from "./result.js";

const TASK_ID_PATTERN = /^task_[0-9]{8}$/;
const SOURCE_SAFE_IDENTIFIER_PATTERN = /^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$/;
const EVIDENCE_ID_PATTERN = /^evidence_[0-9]{8}(?:_[0-9]{2})?$/;
const MAX_TASK_LIST_ITEMS = 500;

const WIRE_TASK_STATUSES = Object.freeze([
  "queued",
  "running",
  "waiting-approval",
  "completed",
  "rejected",
  "failed",
] as const);

type WireTaskStatus = (typeof WIRE_TASK_STATUSES)[number];

export interface TaskBindingResolver {
  resolveTask(task: TaskId): SourceThreadKey | undefined;
}

export interface TaskEventMappingContext {
  readonly taskId: TaskId;
  readonly sourceThread: SourceThreadKey;
  readonly run: SourceRunKey;
}

export interface TaskMutationBindingResolver extends TaskBindingResolver {
  resolveCurrentInterrupt(task: TaskId): PendingInterrupt | undefined;
}

function success<T>(value: T): SdkResult<T> {
  return Object.freeze({ ok: true, value });
}

function fail<T>(message: string): SdkResult<T> {
  return Object.freeze({ ok: false, error: contractError(message) });
}

function evidenceClass(value: unknown, label: string): EvidenceClass {
  if (value !== "fixture" && value !== "local-source") {
    throw new TypeError(`${label} is invalid.`);
  }
  return value;
}

function attempt<T>(map: () => T, context: string): SdkResult<T> {
  try {
    return success(map());
  } catch {
    return fail(`${context} did not match the accepted task contract.`);
  }
}

function record(
  value: unknown,
  required: readonly string[],
  context: string,
): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new TypeError(`${context} must be a record.`);
  }
  const keys = Object.keys(value).sort();
  const accepted = [...required].sort();
  if (keys.length !== accepted.length || keys.some((key, index) => key !== accepted[index])) {
    throw new TypeError(`${context} contains unknown or missing fields.`);
  }
  return value as Record<string, unknown>;
}

function string(value: unknown, label: string, maximum: number): string {
  if (typeof value !== "string" || value.trim().length === 0 || [...value].length > maximum) {
    throw new TypeError(`${label} is not a bounded non-blank string.`);
  }
  return value;
}

function identifier(value: unknown, label: string, pattern: RegExp): string {
  const parsed = string(value, label, 200);
  if (!pattern.test(parsed)) {
    throw new TypeError(`${label} is not an accepted opaque identifier.`);
  }
  return parsed;
}

function positiveInteger(value: unknown, label: string): number {
  if (!Number.isSafeInteger(value) || Number(value) < 1) {
    throw new TypeError(`${label} must be a positive safe integer.`);
  }
  return Number(value);
}

function boolean(value: unknown, label: string): boolean {
  if (typeof value !== "boolean") {
    throw new TypeError(`${label} must be boolean.`);
  }
  return value;
}

function wireStatus(value: unknown): WireTaskStatus {
  if (typeof value !== "string" || !(WIRE_TASK_STATUSES as readonly string[]).includes(value)) {
    throw new TypeError("Task status is not accepted.");
  }
  return value as WireTaskStatus;
}

function factsForWireStatus(status: WireTaskStatus): TaskStateFacts {
  return Object.freeze({
    cancellationConfirmed: false,
    pendingCurrentInterrupt: status === "waiting-approval",
    runActive: status === "running" || status === "waiting-approval",
    queued: status === "queued",
    terminalFailure: status === "failed" || status === "rejected",
    terminalSuccess: status === "completed",
  });
}

function bindingFor(id: TaskId, resolver: TaskBindingResolver): SourceThreadKey {
  const binding = resolver.resolveTask(id);
  if (binding === undefined) {
    throw new TypeError("Task source/thread binding is unavailable.");
  }
  return sourceThreadKey(
    sourceId(string(binding.sourceId, "Task source identifier", 200)),
    threadId(string(binding.threadId, "Task thread identifier", 200)),
  );
}

function canonicalEventContext(context: TaskEventMappingContext): TaskEventMappingContext {
  const mappedTaskId = taskId(identifier(context.taskId, "Task identifier", TASK_ID_PATTERN));
  const sourceThread = sourceThreadKey(
    sourceId(string(context.sourceThread.sourceId, "Task source identifier", 200)),
    threadId(string(context.sourceThread.threadId, "Task thread identifier", 200)),
  );
  const mappedRunId = runId(
    identifier(context.run.runId, "Run identifier", SOURCE_SAFE_IDENTIFIER_PATTERN),
  );
  if (
    context.run.sourceId !== sourceThread.sourceId ||
    context.run.threadId !== sourceThread.threadId
  ) {
    throw new TypeError("Task event source/thread/run binding is incoherent.");
  }
  return Object.freeze({
    taskId: mappedTaskId,
    sourceThread,
    run: sourceRunKey(sourceThread.sourceId, sourceThread.threadId, mappedRunId),
  });
}

function mapSummaryRecord(value: unknown, resolver: TaskBindingResolver): TaskSummary {
  const wire = record(
    value,
    ["taskId", "runId", "title", "objective", "status", "lastEventId"],
    "Task summary",
  );
  const mappedTaskId = taskId(identifier(wire.taskId, "Task identifier", TASK_ID_PATTERN));
  const sourceThread = bindingFor(mappedTaskId, resolver);
  const mappedRunId = runId(
    identifier(wire.runId, "Run identifier", SOURCE_SAFE_IDENTIFIER_PATTERN),
  );
  const run = sourceRunKey(sourceThread.sourceId, sourceThread.threadId, mappedRunId);
  const lastEventSequence = positiveInteger(wire.lastEventId, "Last event identifier");
  const lastEvent = sourceApplicationEventKey(
    sourceThread.sourceId,
    mappedTaskId,
    sourceThread.threadId,
    mappedRunId,
    applicationEventId(String(lastEventSequence)),
  );
  return taskSummary({
    taskId: mappedTaskId,
    sourceThread,
    run,
    title: displayText(string(wire.title, "Task title", 80), "Task title", 80),
    objective: objectiveText(string(wire.objective, "Task objective", 8_000)),
    facts: factsForWireStatus(wireStatus(wire.status)),
    lastEvent,
    lastEventSequence,
  });
}

function mapPlan(
  value: unknown,
  task: TaskId,
  sourceThread: SourceThreadKey,
  run: SourceRunKey,
): ReturnType<typeof proposedPlan> {
  const wire = record(value, ["revision", "title", "steps", "evidenceRefs"], "Proposed plan");
  if (
    !Array.isArray(wire.steps) ||
    wire.steps.length < 1 ||
    wire.steps.length > 8 ||
    !wire.steps.every((step) => typeof step === "string")
  ) {
    throw new TypeError("Proposed plan steps are invalid.");
  }
  if (!Array.isArray(wire.evidenceRefs) || wire.evidenceRefs.length > 64) {
    throw new TypeError("Proposed plan evidence references are invalid.");
  }
  const references = wire.evidenceRefs.map((reference) =>
    sourceEvidenceKey(
      sourceThread.sourceId,
      task,
      sourceThread.threadId,
      run.runId,
      evidenceId(identifier(reference, "Evidence identifier", EVIDENCE_ID_PATTERN)),
    ),
  );
  return proposedPlan({
    revision: positiveInteger(wire.revision, "Plan revision"),
    title: string(wire.title, "Plan title", 100),
    steps: wire.steps,
    evidenceRefs: references,
  });
}

function mapEvidence(
  value: unknown,
  task: TaskId,
  sourceThread: SourceThreadKey,
  run: SourceRunKey,
  observedThrough: "task-detail" | "application-event",
): EvidenceRecord {
  const wire = record(
    value,
    ["evidenceId", "kind", "summary", "source", "verified"],
    "Evidence record",
  );
  if (wire.kind !== "fixture") {
    throw new TypeError("Evidence kind is not accepted.");
  }
  if (wire.source !== "deterministic-local-runner" && wire.source !== "reviewer-response") {
    throw new TypeError("Evidence source is not accepted.");
  }
  return evidenceRecord({
    identity: sourceEvidenceKey(
      sourceThread.sourceId,
      task,
      sourceThread.threadId,
      run.runId,
      evidenceId(identifier(wire.evidenceId, "Evidence identifier", EVIDENCE_ID_PATTERN)),
    ),
    kind: wire.kind,
    summary: string(wire.summary, "Evidence summary", 300),
    source: wire.source,
    verified: boolean(wire.verified, "Evidence verified flag"),
    provenance: {
      sourceThread,
      observedThrough,
      ...(observedThrough === "application-event" ? { evidenceClass: "fixture" as const } : {}),
    },
  });
}

function mapInterrupt(
  value: unknown,
  task: TaskId,
  sourceThread: SourceThreadKey,
  run: SourceRunKey,
): ReturnType<typeof pendingInterrupt> {
  const wire = record(value, ["interruptId", "decisions", "planRevision"], "Pending interrupt");
  if (!Array.isArray(wire.decisions) || !wire.decisions.every(isTaskDecision)) {
    throw new TypeError("Pending interrupt decisions are invalid.");
  }
  return pendingInterrupt({
    identity: sourceInterruptKey(
      sourceThread.sourceId,
      task,
      sourceThread.threadId,
      run.runId,
      interruptId(
        identifier(wire.interruptId, "Interrupt identifier", SOURCE_SAFE_IDENTIFIER_PATTERN),
      ),
    ),
    decisions: wire.decisions,
    planRevision: positiveInteger(wire.planRevision, "Interrupt plan revision"),
  });
}

export function mapTaskAccepted(
  value: unknown,
  resolver: TaskBindingResolver,
): SdkResult<TaskAccepted> {
  return attempt(() => {
    const wire = record(value, ["taskId", "runId", "status"], "Create-task receipt");
    if (wire.status !== "queued") {
      throw new TypeError("Create-task status must be queued.");
    }
    const mappedTaskId = taskId(identifier(wire.taskId, "Task identifier", TASK_ID_PATTERN));
    const binding = bindingFor(mappedTaskId, resolver);
    return taskAccepted({
      taskId: mappedTaskId,
      run: sourceRunKey(
        binding.sourceId,
        binding.threadId,
        runId(identifier(wire.runId, "Run identifier", SOURCE_SAFE_IDENTIFIER_PATTERN)),
      ),
      facts: factsForWireStatus("queued"),
    });
  }, "Create-task receipt");
}

export function mapTaskList(
  value: unknown,
  resolver: TaskBindingResolver,
): SdkResult<readonly TaskSummary[]> {
  return attempt(() => {
    const wire = record(value, ["items"], "Task list");
    if (!Array.isArray(wire.items) || wire.items.length > MAX_TASK_LIST_ITEMS) {
      throw new TypeError("Task list items are invalid.");
    }
    return Object.freeze(wire.items.map((item) => mapSummaryRecord(item, resolver)));
  }, "Task list");
}

export function mapTaskDetail(
  value: unknown,
  resolver: TaskBindingResolver,
): SdkResult<TaskDetail> {
  return attempt(() => {
    const wire = record(
      value,
      [
        "taskId",
        "runId",
        "title",
        "objective",
        "status",
        "lastEventId",
        "pendingInterrupt",
        "proposedPlan",
        "evidence",
        "result",
      ],
      "Task detail",
    );
    const summary = mapSummaryRecord(
      {
        taskId: wire.taskId,
        runId: wire.runId,
        title: wire.title,
        objective: wire.objective,
        status: wire.status,
        lastEventId: wire.lastEventId,
      },
      resolver,
    );
    const status = wireStatus(wire.status);
    if (!Array.isArray(wire.evidence) || wire.evidence.length > 256) {
      throw new TypeError("Task detail evidence is invalid.");
    }
    const interrupt =
      wire.pendingInterrupt === null
        ? undefined
        : mapInterrupt(wire.pendingInterrupt, summary.taskId, summary.sourceThread, summary.run);
    const plan =
      wire.proposedPlan === null
        ? undefined
        : mapPlan(wire.proposedPlan, summary.taskId, summary.sourceThread, summary.run);
    if (
      (summary.status === "needs-review") !== (interrupt !== undefined) ||
      (interrupt !== undefined && plan === undefined) ||
      (interrupt !== undefined && plan !== undefined && interrupt.planRevision !== plan.revision)
    ) {
      throw new TypeError("Task detail interrupt/plan state is incoherent.");
    }
    if (
      (status === "completed" && wire.result === null) ||
      (status !== "completed" && wire.result !== null)
    ) {
      throw new TypeError("Task detail status/result state is incoherent.");
    }
    return taskDetail({
      ...summary,
      ...(interrupt === undefined ? {} : { pendingInterrupt: interrupt }),
      ...(plan === undefined ? {} : { proposedPlan: plan }),
      evidence: wire.evidence.map((item) =>
        mapEvidence(item, summary.taskId, summary.sourceThread, summary.run, "task-detail"),
      ),
      ...(wire.result === null
        ? {}
        : {
            result: resultText(string(wire.result, "Task result", 18_048)),
          }),
    });
  }, "Task detail");
}

export function mapTaskResult(
  value: unknown,
  resolver: TaskBindingResolver,
): SdkResult<TaskResult> {
  return attempt(() => {
    const wire = record(value, ["taskId", "runId", "status", "result"], "Task result");
    if (wire.status !== "completed") {
      throw new TypeError("Task result status must be completed.");
    }
    const mappedTaskId = taskId(identifier(wire.taskId, "Task identifier", TASK_ID_PATTERN));
    const binding = bindingFor(mappedTaskId, resolver);
    return taskResult({
      taskId: mappedTaskId,
      run: sourceRunKey(
        binding.sourceId,
        binding.threadId,
        runId(identifier(wire.runId, "Run identifier", SOURCE_SAFE_IDENTIFIER_PATTERN)),
      ),
      result: resultText(string(wire.result, "Task result", 18_048)),
    });
  }, "Task result");
}

export function mapDecisionReceipt(
  value: unknown,
  task: TaskId,
  request: DecisionInput,
): SdkResult<DecisionReceipt> {
  return attempt(() => {
    const correlatedInterrupt = sourceInterruptKey(
      sourceId(string(request.interrupt.sourceId, "Task source identifier", 200)),
      taskId(identifier(request.interrupt.taskId, "Task identifier", TASK_ID_PATTERN)),
      threadId(string(request.interrupt.threadId, "Task thread identifier", 200)),
      runId(identifier(request.interrupt.runId, "Run identifier", SOURCE_SAFE_IDENTIFIER_PATTERN)),
      interruptId(
        identifier(
          request.interrupt.interruptId,
          "Interrupt identifier",
          SOURCE_SAFE_IDENTIFIER_PATTERN,
        ),
      ),
    );
    const wire = record(
      value,
      ["taskId", "runId", "interruptId", "decision", "status", "duplicate"],
      "Decision receipt",
    );
    if (
      wire.status !== "accepted" ||
      !isTaskDecision(wire.decision) ||
      wire.taskId !== task ||
      correlatedInterrupt.taskId !== task ||
      wire.runId !== correlatedInterrupt.runId ||
      wire.interruptId !== correlatedInterrupt.interruptId ||
      wire.decision !== request.decision
    ) {
      throw new TypeError("Decision receipt correlation failed.");
    }
    return Object.freeze({
      taskId: task,
      run: sourceRunKey(
        correlatedInterrupt.sourceId,
        correlatedInterrupt.threadId,
        correlatedInterrupt.runId,
      ),
      interrupt: correlatedInterrupt,
      decision: request.decision,
      status: "accepted",
      duplicate: boolean(wire.duplicate, "Decision duplicate flag"),
    });
  }, "Decision receipt");
}

export function mapPlanEditReceipt(
  value: unknown,
  task: TaskId,
  request: PlanEditInput,
): SdkResult<PlanEditReceipt> {
  return attempt(() => {
    const correlatedInterrupt = sourceInterruptKey(
      sourceId(string(request.interrupt.sourceId, "Task source identifier", 200)),
      taskId(identifier(request.interrupt.taskId, "Task identifier", TASK_ID_PATTERN)),
      threadId(string(request.interrupt.threadId, "Task thread identifier", 200)),
      runId(identifier(request.interrupt.runId, "Run identifier", SOURCE_SAFE_IDENTIFIER_PATTERN)),
      interruptId(
        identifier(
          request.interrupt.interruptId,
          "Interrupt identifier",
          SOURCE_SAFE_IDENTIFIER_PATTERN,
        ),
      ),
    );
    const wire = record(value, ["taskId", "runId", "interruptId", "plan"], "Plan-edit receipt");
    if (
      wire.taskId !== task ||
      correlatedInterrupt.taskId !== task ||
      wire.runId !== correlatedInterrupt.runId ||
      wire.interruptId !== correlatedInterrupt.interruptId
    ) {
      throw new TypeError("Plan-edit receipt correlation failed.");
    }
    const run = sourceRunKey(
      correlatedInterrupt.sourceId,
      correlatedInterrupt.threadId,
      correlatedInterrupt.runId,
    );
    const plan = mapPlan(
      wire.plan,
      task,
      {
        sourceId: correlatedInterrupt.sourceId,
        threadId: correlatedInterrupt.threadId,
      },
      run,
    );
    if (plan.revision !== request.expectedRevision + 1) {
      throw new TypeError("Plan-edit receipt revision correlation failed.");
    }
    return Object.freeze({
      taskId: task,
      run,
      interrupt: correlatedInterrupt,
      plan,
    });
  }, "Plan-edit receipt");
}

function eventBase(
  name: TaskEventName,
  id: unknown,
  context: TaskEventMappingContext,
): {
  readonly identity: ReturnType<typeof sourceApplicationEventKey>;
  readonly sequence: number;
  readonly taskId: TaskId;
  readonly sourceThread: SourceThreadKey;
  readonly run: SourceRunKey;
  readonly name: TaskEventName;
} {
  const canonical = canonicalEventContext(context);
  const parsedId = identifier(id, "Application event identifier", /^[1-9][0-9]*$/);
  const sequence = positiveInteger(Number(parsedId), "Event sequence");
  if (sequence > EVENT_SEQUENCE_MAX) {
    throw new TypeError("Event sequence exceeds the accepted bound.");
  }
  return {
    identity: sourceApplicationEventKey(
      canonical.sourceThread.sourceId,
      canonical.taskId,
      canonical.sourceThread.threadId,
      canonical.run.runId,
      applicationEventId(parsedId),
    ),
    sequence,
    taskId: canonical.taskId,
    sourceThread: canonical.sourceThread,
    run: canonical.run,
    name,
  };
}

export function mapTaskEvent(
  name: unknown,
  id: unknown,
  data: unknown,
  context: TaskEventMappingContext,
): SdkResult<TaskApplicationEvent> {
  return attempt(() => {
    if (
      typeof name !== "string" ||
      ![
        "task.created",
        "run.started",
        "content.delta",
        "plan.proposed",
        "plan.updated",
        "evidence.recorded",
        "interrupt.requested",
        "decision.recorded",
        "run.completed",
      ].includes(name)
    ) {
      throw new TypeError("Task event name is not accepted.");
    }
    const eventName = name as TaskEventName;
    const canonical = canonicalEventContext(context);
    const base = eventBase(eventName, id, canonical);

    switch (eventName) {
      case "task.created": {
        const wire = record(data, ["taskId", "runId", "status"], "task.created event");
        if (
          wire.taskId !== canonical.taskId ||
          wire.runId !== canonical.run.runId ||
          wire.status !== "queued"
        ) {
          throw new TypeError("task.created event correlation failed.");
        }
        return Object.freeze({ ...base, name: eventName });
      }
      case "run.started": {
        const wire = record(data, ["runId", "status"], "run.started event");
        if (wire.runId !== canonical.run.runId || wire.status !== "running") {
          throw new TypeError("run.started event correlation failed.");
        }
        return Object.freeze({ ...base, name: eventName });
      }
      case "content.delta": {
        const wire = record(data, ["text", "evidenceClass"], "content.delta event");
        return Object.freeze({
          ...base,
          name: eventName,
          text: resultText(string(wire.text, "Content delta", 18_048)),
          evidenceClass: evidenceClass(wire.evidenceClass, "content.delta evidence class"),
        });
      }
      case "plan.proposed":
      case "plan.updated": {
        const wire = record(
          data,
          ["title", "steps", "revision", "evidenceRefs", "evidenceClass"],
          `${eventName} event`,
        );
        return Object.freeze({
          ...base,
          name: eventName,
          plan: mapPlan(
            {
              title: wire.title,
              steps: wire.steps,
              revision: wire.revision,
              evidenceRefs: wire.evidenceRefs,
            },
            canonical.taskId,
            canonical.sourceThread,
            canonical.run,
          ),
          evidenceClass: evidenceClass(wire.evidenceClass, `${eventName} evidence class`),
        });
      }
      case "evidence.recorded":
        return Object.freeze({
          ...base,
          name: eventName,
          evidence: mapEvidence(
            data,
            canonical.taskId,
            canonical.sourceThread,
            canonical.run,
            "application-event",
          ),
        });
      case "interrupt.requested": {
        const wire = record(
          data,
          ["interruptId", "question", "decisions", "planRevision"],
          "interrupt.requested event",
        );
        const interrupt = mapInterrupt(
          {
            interruptId: wire.interruptId,
            decisions: wire.decisions,
            planRevision: wire.planRevision,
          },
          canonical.taskId,
          canonical.sourceThread,
          canonical.run,
        );
        return Object.freeze({
          ...base,
          name: eventName,
          interrupt: Object.freeze({
            ...interrupt,
            question: displayText(
              string(wire.question, "Interrupt question", 200),
              "Interrupt question",
              200,
            ),
          }),
        });
      }
      case "decision.recorded": {
        const wire = record(
          data,
          ["interruptId", "decision", "commentProvided", "responseProvided"],
          "decision.recorded event",
        );
        if (!isTaskDecision(wire.decision)) {
          throw new TypeError("Recorded decision is invalid.");
        }
        const commentProvided = boolean(wire.commentProvided, "Decision commentProvided");
        const responseProvided = boolean(wire.responseProvided, "Decision responseProvided");
        if (
          (wire.decision === "respond") !== responseProvided ||
          (wire.decision === "respond" && !commentProvided)
        ) {
          throw new TypeError("Respond decision correlation failed.");
        }
        return Object.freeze({
          ...base,
          name: eventName,
          interrupt: sourceInterruptKey(
            canonical.sourceThread.sourceId,
            canonical.taskId,
            canonical.sourceThread.threadId,
            canonical.run.runId,
            interruptId(
              identifier(wire.interruptId, "Interrupt identifier", SOURCE_SAFE_IDENTIFIER_PATTERN),
            ),
          ),
          decision: wire.decision,
          commentProvided,
          responseProvided,
        });
      }
      case "run.completed": {
        const wire = record(
          data,
          ["runId", "status", "safeReason", "resultAvailable"],
          "run.completed event",
        );
        if (
          wire.runId !== canonical.run.runId ||
          (wire.status !== "completed" && wire.status !== "rejected" && wire.status !== "failed")
        ) {
          throw new TypeError("run.completed event correlation failed.");
        }
        const resultAvailable = boolean(wire.resultAvailable, "Completion resultAvailable");
        if ((wire.status === "completed") !== resultAvailable) {
          throw new TypeError("run.completed result availability is incoherent.");
        }
        return Object.freeze({
          ...base,
          name: eventName,
          outcome:
            wire.status === "completed"
              ? "success"
              : wire.status === "rejected"
                ? "rejected"
                : "failure",
          safeReason: displayText(
            string(wire.safeReason, "Completion safe reason", 200),
            "Completion safe reason",
            200,
          ),
          resultAvailable,
        });
      }
    }
  }, "Task event");
}

export function createDecisionInput(
  interrupt: DecisionInput["interrupt"],
  expectedPlanRevision: number,
  decision: DecisionInput["decision"],
  comment?: string,
): DecisionInput {
  return decisionInput({
    interrupt,
    expectedPlanRevision,
    decision,
    ...(comment === undefined ? {} : { comment }),
  });
}

export function createPlanEditInput(
  interrupt: PlanEditInput["interrupt"],
  expectedRevision: number,
  steps: readonly string[],
): PlanEditInput {
  return planEditInput({ interrupt, expectedRevision, steps });
}

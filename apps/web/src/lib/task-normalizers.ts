import type {
  ActiveInterrupt,
  CancelResult,
  CreateTaskResult,
  DecisionInput,
  DecisionResult,
  EvidenceRecord,
  PlanUpdateResult,
  ProposedPlan,
  TaskDetail,
  TaskEvent,
  TaskStatus,
  TaskSummary,
} from "./task-types";
import {
  DECISION_COMMENT_MAX_LENGTH,
  PLAN_STEP_MAX_COUNT,
  PLAN_STEP_MAX_LENGTH,
  PROMPT_MAX_LENGTH,
} from "./task-types";

export class ContractError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ContractError";
  }
}

export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function validatePrompt(prompt: string): string {
  const normalized = prompt.trim();
  if (normalized === "") {
    throw new ContractError("Task prompt cannot be empty.");
  }
  if (unicodeLength(normalized) > PROMPT_MAX_LENGTH) {
    throw new ContractError(
      `Task prompt cannot exceed ${PROMPT_MAX_LENGTH.toLocaleString("en-US")} characters.`,
    );
  }
  return normalized;
}

export function unicodeLength(value: string): number {
  return [...value].length;
}

export function validateDecisionComment(comment: string | undefined): string | undefined {
  const normalized = comment?.trim();
  if (!normalized) {
    return undefined;
  }
  if (unicodeLength(normalized) > DECISION_COMMENT_MAX_LENGTH) {
    throw new ContractError(
      `Decision note cannot exceed ${DECISION_COMMENT_MAX_LENGTH.toLocaleString("en-US")} characters.`,
    );
  }
  return normalized;
}

export function validateDecisionInput(input: DecisionInput): DecisionInput {
  const comment = validateDecisionComment(input.comment);
  if (input.decision === "respond" && !comment) {
    throw new ContractError("A response is required when answering the agent’s request.");
  }
  return { ...input, ...(comment ? { comment } : { comment: undefined }) };
}

function hasUnsafeControls(value: string): boolean {
  return [...value].some((character) => {
    const codePoint = character.codePointAt(0) ?? 0;
    return codePoint < 32 && character !== "\t" && character !== "\n" && character !== "\r";
  });
}

export type PlanStepIssue = "blank" | "too-long" | "unsafe";

/**
 * The first rule a single plan step violates, or undefined when it is
 * acceptable. {@link validatePlanSteps} applies these same per-step checks; the
 * plan editor uses this to mark exactly the offending step for assistive tech.
 */
export function planStepIssue(step: string): PlanStepIssue | undefined {
  if (step.trim() === "") return "blank";
  if (unicodeLength(step) > PLAN_STEP_MAX_LENGTH) return "too-long";
  if (hasUnsafeControls(step)) return "unsafe";
  return undefined;
}

export function validatePlanSteps(steps: readonly string[]): string[] {
  if (steps.length < 1 || steps.length > PLAN_STEP_MAX_COUNT) {
    throw new ContractError(`A plan must contain between 1 and ${PLAN_STEP_MAX_COUNT} steps.`);
  }

  return steps.map((step, index) => {
    switch (planStepIssue(step)) {
      case "blank":
        throw new ContractError(`Plan step ${index + 1} cannot be blank.`);
      case "too-long":
        throw new ContractError(
          `Plan step ${index + 1} cannot exceed ${PLAN_STEP_MAX_LENGTH.toLocaleString("en-US")} characters.`,
        );
      case "unsafe":
        throw new ContractError(`Plan step ${index + 1} contains unsupported control characters.`);
      default:
        return step;
    }
  });
}

function requiredString(record: Record<string, unknown>, key: string, context: string): string {
  const value = record[key];
  if (typeof value !== "string" || value.trim() === "") {
    throw new ContractError(`${context} is missing a valid ${key}.`);
  }
  return value;
}

function optionalString(record: Record<string, unknown>, key: string): string | undefined {
  const value = record[key];
  return typeof value === "string" && value.trim() !== "" ? value : undefined;
}

export function normalizeTaskStatus(value: unknown): TaskStatus {
  if (typeof value !== "string") {
    return "unknown";
  }

  switch (value.toLowerCase().replaceAll("_", "-")) {
    case "queued":
      return "queued";
    case "active":
    case "in-progress":
    case "running":
      return "running";
    case "awaiting-approval":
    case "blocked":
    case "interrupted":
    case "needs-review":
    case "waiting-approval":
      return "waiting-approval";
    case "complete":
    case "completed":
    case "succeeded":
      return "completed";
    case "declined":
    case "rejected":
      return "rejected";
    case "error":
    case "failed":
      return "failed";
    case "canceled":
    case "cancelled":
      return "cancelled";
    default:
      return "unknown";
  }
}

export function normalizeTaskSummary(value: unknown, context = "Task"): TaskSummary {
  if (!isRecord(value)) {
    throw new ContractError(`${context} must be an object.`);
  }

  const taskId = requiredString(value, "taskId", context);
  // The API returns the full sanitized request as `objective`; keep it as the
  // task's prompt so re-dispatch and the detail subtitle use the real text
  // rather than the display title, which the server truncates.
  const prompt = optionalString(value, "prompt") ?? optionalString(value, "objective");
  const explicitTitle = optionalString(value, "title");
  const fallbackTitle = prompt ?? `Task ${taskId.slice(0, 8)}`;

  return {
    taskId,
    runId: optionalString(value, "runId"),
    title: explicitTitle ?? fallbackTitle,
    prompt,
    status: normalizeTaskStatus(value.status),
    createdAt: optionalString(value, "createdAt"),
    updatedAt: optionalString(value, "updatedAt"),
  };
}

export function normalizeTaskDetail(value: unknown): TaskDetail {
  if (!isRecord(value)) {
    throw new ContractError("Task detail must be an object.");
  }

  return {
    ...normalizeTaskSummary(value, "Task detail"),
    evidence:
      value.evidence === undefined
        ? undefined
        : normalizeEvidenceList(value.evidence, "Task detail evidence"),
    pendingInterrupt:
      value.pendingInterrupt === undefined || value.pendingInterrupt === null
        ? undefined
        : normalizePendingInterrupt(value.pendingInterrupt),
    proposedPlan:
      value.proposedPlan === undefined || value.proposedPlan === null
        ? undefined
        : normalizeProposedPlan(value.proposedPlan, "Task detail proposedPlan"),
    result:
      getResultText(value.result) ?? getResultText(value.output) ?? getResultText(value.summary),
  };
}

function normalizeDecisions(value: unknown, absentDefaults: boolean): DecisionInput["decision"][] {
  if (value === undefined && absentDefaults) {
    return ["approve", "reject"];
  }
  if (
    !Array.isArray(value) ||
    value.length === 0 ||
    !value.every(
      (decision) => decision === "approve" || decision === "reject" || decision === "respond",
    )
  ) {
    return [];
  }
  return value as DecisionInput["decision"][];
}

function normalizePendingInterrupt(value: unknown): ActiveInterrupt {
  if (!isRecord(value)) {
    throw new ContractError("Task detail pendingInterrupt must be an object.");
  }
  return {
    interruptId: requiredString(value, "interruptId", "Task detail pendingInterrupt"),
    decisions: normalizeDecisions(value.decisions, true),
    planRevision:
      Number.isInteger(value.planRevision) && Number(value.planRevision) >= 1
        ? Number(value.planRevision)
        : undefined,
    title: "Approval required",
    question: "Review the current plan and choose one of the actions offered by the agent.",
  };
}

export function normalizeTaskList(value: unknown): TaskSummary[] {
  if (!isRecord(value) || !Array.isArray(value.items)) {
    throw new ContractError("Task list response must contain an items array.");
  }

  return value.items.map((item, index) =>
    normalizeTaskSummary(item, `Task list item ${index + 1}`),
  );
}

export function normalizeCreateTaskResult(value: unknown): CreateTaskResult {
  if (!isRecord(value)) {
    throw new ContractError("Create-task response must be an object.");
  }

  const status = requiredString(value, "status", "Create-task response");
  if (status !== "queued") {
    throw new ContractError(`Create-task response status must be queued, received ${status}.`);
  }

  return {
    taskId: requiredString(value, "taskId", "Create-task response"),
    runId: requiredString(value, "runId", "Create-task response"),
    status,
  };
}

export function normalizeCancelResult(value: unknown): CancelResult {
  if (!isRecord(value)) {
    throw new ContractError("Cancel response must be an object.");
  }

  const status = requiredString(value, "status", "Cancel response");
  if (status !== "cancelled") {
    throw new ContractError(`Cancel response status must be cancelled, received ${status}.`);
  }
  if (typeof value.duplicate !== "boolean") {
    throw new ContractError("Cancel response is missing a valid duplicate flag.");
  }

  return {
    taskId: requiredString(value, "taskId", "Cancel response"),
    runId: requiredString(value, "runId", "Cancel response"),
    status,
    duplicate: value.duplicate,
  };
}

export function normalizeProposedPlan(value: unknown, context = "Proposed plan"): ProposedPlan {
  if (!isRecord(value)) {
    throw new ContractError(`${context} must be an object.`);
  }
  if (!Number.isInteger(value.revision) || Number(value.revision) < 1) {
    throw new ContractError(`${context} is missing a valid revision.`);
  }
  if (!Array.isArray(value.steps)) {
    throw new ContractError(`${context} is missing a steps array.`);
  }
  if (value.steps.some((step) => typeof step !== "string")) {
    throw new ContractError(`${context} steps must all be strings.`);
  }
  const evidenceRefs = value.evidenceRefs;
  if (
    !Array.isArray(evidenceRefs) ||
    evidenceRefs.some((item) => typeof item !== "string" || item.trim() === "")
  ) {
    throw new ContractError(`${context} is missing valid evidenceRefs.`);
  }

  return {
    revision: Number(value.revision),
    title: requiredString(value, "title", context),
    steps: validatePlanSteps(value.steps as string[]),
    evidenceRefs: [...evidenceRefs],
  };
}

export function normalizePlanUpdateResult(value: unknown): PlanUpdateResult {
  if (!isRecord(value)) {
    throw new ContractError("Plan update response must be an object.");
  }
  return {
    taskId: requiredString(value, "taskId", "Plan update response"),
    runId: requiredString(value, "runId", "Plan update response"),
    interruptId: requiredString(value, "interruptId", "Plan update response"),
    plan: normalizeProposedPlan(value.plan, "Plan update response plan"),
  };
}

export function normalizeDecisionResult(value: unknown): DecisionResult {
  if (!isRecord(value)) {
    throw new ContractError("Decision response must be an object.");
  }
  const decision = requiredString(value, "decision", "Decision response");
  if (decision !== "approve" && decision !== "reject" && decision !== "respond") {
    throw new ContractError("Decision response contains an unsupported decision.");
  }
  if (value.status !== "accepted" || typeof value.duplicate !== "boolean") {
    throw new ContractError("Decision response is missing a valid receipt status.");
  }
  return {
    taskId: requiredString(value, "taskId", "Decision response"),
    runId: requiredString(value, "runId", "Decision response"),
    interruptId: requiredString(value, "interruptId", "Decision response"),
    decision,
    status: "accepted",
    duplicate: value.duplicate,
  };
}

function normalizeEvidence(value: unknown, context: string): EvidenceRecord {
  if (!isRecord(value)) {
    throw new ContractError(`${context} must be an object.`);
  }
  if (typeof value.verified !== "boolean") {
    throw new ContractError(`${context} is missing a valid verified flag.`);
  }
  return {
    evidenceId: requiredString(value, "evidenceId", context),
    kind: requiredString(value, "kind", context),
    summary: requiredString(value, "summary", context),
    source: requiredString(value, "source", context),
    verified: value.verified,
  };
}

function normalizeEvidenceList(value: unknown, context: string): EvidenceRecord[] {
  if (!Array.isArray(value)) {
    throw new ContractError(`${context} must be an array.`);
  }
  return value.map((item, index) => normalizeEvidence(item, `${context} item ${index + 1}`));
}

export function getEventText(event: TaskEvent): string | undefined {
  for (const key of ["delta", "text", "content", "summary", "message", "result", "output"]) {
    const text = getResultText(event.data[key]);
    if (text) {
      return text;
    }
  }
  return undefined;
}

export function getCompletionResultText(event: TaskEvent): string | undefined {
  if (event.name !== "run.completed") {
    return undefined;
  }
  for (const key of ["result", "output", "summary", "content", "text"]) {
    const text = getResultText(event.data[key]);
    if (text) {
      return text;
    }
  }
  return undefined;
}

export function terminalEventNeedsDetail(event: TaskEvent): boolean {
  return event.name === "run.completed" && !getCompletionResultText(event);
}

export function getResultText(value: unknown): string | undefined {
  if (typeof value === "string" && value.trim() !== "") {
    return value;
  }
  if (Array.isArray(value)) {
    const lines = value
      .map((item) => getResultText(item))
      .filter((item): item is string => item !== undefined);
    return lines.length > 0 ? lines.join("\n") : undefined;
  }
  if (isRecord(value)) {
    for (const key of ["summary", "output", "text", "content", "message"]) {
      const text = getResultText(value[key]);
      if (text) {
        return text;
      }
    }
  }
  return undefined;
}

export function getActiveInterrupt(events: readonly TaskEvent[]): ActiveInterrupt | undefined {
  let active: ActiveInterrupt | undefined;

  for (const event of events) {
    active = interruptAfterEvent(active, event);
  }

  return active;
}

export function interruptAfterEvent(
  active: ActiveInterrupt | undefined,
  event: TaskEvent,
): ActiveInterrupt | undefined {
  if (event.name === "interrupt.requested") {
    const interruptId = event.data.interruptId;
    if (typeof interruptId !== "string" || interruptId.trim() === "") {
      return active;
    }
    return {
      interruptId,
      decisions: normalizeDecisions(event.data.decisions, true),
      planRevision:
        Number.isInteger(event.data.planRevision) && Number(event.data.planRevision) >= 1
          ? Number(event.data.planRevision)
          : undefined,
      title: typeof event.data.title === "string" ? event.data.title : "Approval required",
      question:
        typeof event.data.question === "string"
          ? event.data.question
          : typeof event.data.prompt === "string"
            ? event.data.prompt
            : typeof event.data.message === "string"
              ? event.data.message
              : "Review the proposed plan before this run continues.",
    };
  }
  if (
    event.name === "plan.updated" &&
    active &&
    Number.isInteger(event.data.revision) &&
    Number(event.data.revision) >= 1
  ) {
    return { ...active, planRevision: Number(event.data.revision) };
  }
  if (
    event.name === "decision.recorded" &&
    active &&
    event.data.interruptId === active.interruptId &&
    (event.data.decision === "approve" ||
      event.data.decision === "reject" ||
      event.data.decision === "respond")
  ) {
    return undefined;
  }
  if (event.name === "run.completed" && isTerminalStatus(normalizeTaskStatus(event.data.status))) {
    return undefined;
  }
  return active;
}

export function statusAfterEvent(
  current: TaskStatus,
  event: TaskEvent,
  activeInterrupt?: ActiveInterrupt,
): TaskStatus {
  switch (event.name) {
    case "task.created":
      return "queued";
    case "run.started":
    case "content.delta":
    case "plan.proposed":
      return "running";
    case "plan.updated":
    case "evidence.recorded":
      return current;
    case "interrupt.requested":
      return "waiting-approval";
    case "decision.recorded":
      return (event.data.decision === "approve" ||
        event.data.decision === "reject" ||
        event.data.decision === "respond") &&
        typeof event.data.interruptId === "string" &&
        activeInterrupt?.interruptId === event.data.interruptId
        ? "running"
        : current;
    case "run.completed": {
      const normalized = normalizeTaskStatus(event.data.status);
      return isTerminalStatus(normalized) ? normalized : "unknown";
    }
    default:
      return current;
  }
}

export function getLatestPlan(
  detailPlan: ProposedPlan | undefined,
  events: readonly TaskEvent[],
): ProposedPlan | undefined {
  let plan = detailPlan;
  for (const event of events) {
    if (event.name !== "plan.proposed" && event.name !== "plan.updated") {
      continue;
    }
    try {
      const candidate = normalizeProposedPlan(event.data, `${event.name} event`);
      if (!plan || candidate.revision > plan.revision) {
        plan = candidate;
      }
      // A revision is immutable. Equal or older conflicting stream payloads never
      // overwrite an authoritative or previously accepted plan.
    } catch {
      // A malformed streamed plan is ignored; authoritative detail remains available.
    }
  }
  return plan;
}

export function getEvidenceRecords(
  detailEvidence: readonly EvidenceRecord[] | undefined,
  events: readonly TaskEvent[],
): EvidenceRecord[] {
  const records = new Map((detailEvidence ?? []).map((record) => [record.evidenceId, record]));

  for (const event of events) {
    if (event.name === "evidence.recorded") {
      try {
        const record = normalizeEvidence(event.data, "evidence.recorded event");
        records.set(record.evidenceId, record);
      } catch {
        // Do not replace authoritative evidence with malformed stream content.
      }
      continue;
    }

    const evidenceClass = event.data.evidenceClass;
    if (typeof evidenceClass === "string" && evidenceClass.trim() !== "") {
      const evidenceId = `event:${event.id}`;
      records.set(evidenceId, {
        evidenceId,
        kind: evidenceClass,
        source: "normalized task event",
        summary: getEventText(event) ?? `${event.name} reported ${evidenceClass} evidence.`,
        verified: false,
      });
    }
  }

  return [...records.values()];
}

export function isTerminalStatus(status: TaskStatus): boolean {
  return (
    status === "completed" || status === "rejected" || status === "failed" || status === "cancelled"
  );
}

export function reduceEventsIntoDetail(task: TaskDetail, events: readonly TaskEvent[]): TaskDetail {
  return events.reduce<TaskDetail>((current, event) => {
    const eventResult = event.name === "run.completed" ? getCompletionResultText(event) : undefined;
    return {
      ...current,
      status: statusAfterEvent(current.status, event, current.pendingInterrupt),
      pendingInterrupt: interruptAfterEvent(current.pendingInterrupt, event),
      result: eventResult ?? current.result,
    };
  }, task);
}

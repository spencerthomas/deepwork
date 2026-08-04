import type {
  ActionRequest,
  ActiveInterrupt,
  CancelResult,
  CodingOutcome,
  CreateTaskResult,
  DecisionBatchInput,
  DecisionBatchResult,
  DecisionInput,
  DecisionResult,
  EvidenceRecord,
  HitlDecisionType,
  JsonValue,
  OrderedDecision,
  PlanUpdateResult,
  ProposedPlan,
  ReviewConfig,
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
import { isRecord } from "./wire-utils";

export { isRecord };

export class ContractError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ContractError";
  }
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

const HITL_DECISION_TYPES: readonly HitlDecisionType[] = ["approve", "edit", "reject", "respond"];

function normalizeJsonValue(value: unknown, context: string): JsonValue {
  if (value === null || typeof value === "boolean" || typeof value === "string") return value;
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (Array.isArray(value)) {
    return value.map((item, index) => normalizeJsonValue(item, `${context}[${index}]`));
  }
  if (isRecord(value)) {
    return Object.fromEntries(
      Object.entries(value).map(([key, item]) => [
        key,
        normalizeJsonValue(item, `${context}.${key}`),
      ]),
    );
  }
  throw new ContractError(`${context} must contain only JSON-safe values.`);
}

function normalizeActionRequest(value: unknown, context: string): ActionRequest {
  if (!isRecord(value)) throw new ContractError(`${context} must be an object.`);
  if (!isRecord(value.args)) throw new ContractError(`${context} is missing valid args.`);
  const args = normalizeJsonValue(value.args, `${context} args`);
  if (!isRecord(args)) throw new ContractError(`${context} args must be an object.`);
  return {
    name: requiredString(value, "name", context),
    args: args as Record<string, JsonValue>,
    ...(optionalString(value, "description")
      ? { description: optionalString(value, "description") }
      : {}),
  };
}

function normalizeReviewConfig(value: unknown, context: string): ReviewConfig {
  if (!isRecord(value)) throw new ContractError(`${context} must be an object.`);
  if (
    !Array.isArray(value.allowedDecisions) ||
    value.allowedDecisions.length === 0 ||
    value.allowedDecisions.some(
      (decision) =>
        typeof decision !== "string" || !HITL_DECISION_TYPES.includes(decision as HitlDecisionType),
    )
  ) {
    throw new ContractError(`${context} contains an unsupported decision.`);
  }
  let argsSchema: Record<string, JsonValue> | undefined;
  if (value.argsSchema !== undefined) {
    if (!isRecord(value.argsSchema))
      throw new ContractError(`${context} argsSchema must be an object.`);
    argsSchema = normalizeJsonValue(value.argsSchema, `${context} argsSchema`) as Record<
      string,
      JsonValue
    >;
  }
  return {
    actionName: requiredString(value, "actionName", context),
    allowedDecisions: [...value.allowedDecisions] as HitlDecisionType[],
    ...(argsSchema ? { argsSchema } : {}),
  };
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
  if (value.journey !== undefined && value.journey !== "coding") {
    throw new ContractError(`${context} contains an unsupported journey.`);
  }

  return {
    taskId,
    runId: optionalString(value, "runId"),
    agentId: optionalString(value, "agentId"),
    title: explicitTitle ?? fallbackTitle,
    prompt,
    status: normalizeTaskStatus(value.status),
    createdAt: optionalString(value, "createdAt"),
    lastEventId:
      Number.isInteger(value.lastEventId) && Number(value.lastEventId) >= 1
        ? Number(value.lastEventId)
        : undefined,
    updatedAt: optionalString(value, "updatedAt"),
    ...(value.journey === "coding" ? { journey: "coding" as const } : {}),
  };
}

function normalizeCodingOutcome(value: unknown): CodingOutcome {
  if (!isRecord(value)) {
    throw new ContractError("Task detail coding outcome must be an object.");
  }
  const positiveInteger = (key: string): number => {
    const candidate = value[key];
    if (!Number.isSafeInteger(candidate) || Number(candidate) < 1) {
      throw new ContractError(`Task detail coding outcome is missing a valid ${key}.`);
    }
    return Number(candidate);
  };
  const stringList = (key: string, maximum: number): string[] => {
    const candidate = value[key];
    if (
      !Array.isArray(candidate) ||
      candidate.length < 1 ||
      candidate.length > maximum ||
      candidate.some((item) => typeof item !== "string" || item.trim() === "")
    ) {
      throw new ContractError(`Task detail coding outcome is missing valid ${key}.`);
    }
    return [...candidate] as string[];
  };
  const baseSha = requiredString(value, "baseSha", "Task detail coding outcome");
  const headSha = requiredString(value, "headSha", "Task detail coding outcome");
  const snapshotDigest = requiredString(value, "snapshotDigest", "Task detail coding outcome");
  if (
    value.evidenceClass !== "fixture" ||
    value.repositoryId !== "fixture_repo_deepwork" ||
    !/^[a-f0-9]{40}$/.test(baseSha) ||
    !/^[a-f0-9]{40}$/.test(headSha) ||
    baseSha === headSha ||
    !/^sha256:[a-f0-9]{16,64}$/.test(snapshotDigest) ||
    value.sandboxState !== "cleaned" ||
    value.setupStatus !== "passed" ||
    value.draftPrStatus !== "draft" ||
    value.mergeState !== "unavailable" ||
    typeof value.reconciledAfterTimeout !== "boolean"
  ) {
    throw new ContractError("Task detail coding outcome state is invalid.");
  }
  return {
    evidenceClass: "fixture",
    repositoryId: "fixture_repo_deepwork",
    repository: requiredString(value, "repository", "Task detail coding outcome"),
    baseBranch: requiredString(value, "baseBranch", "Task detail coding outcome"),
    baseSha,
    headSha,
    environment: requiredString(value, "environment", "Task detail coding outcome"),
    environmentVersion: positiveInteger("environmentVersion"),
    snapshotDigest,
    sandboxState: "cleaned",
    setupStatus: "passed",
    changedFiles: stringList("changedFiles", 100),
    draftPrNumber: positiveInteger("draftPrNumber"),
    draftPrStatus: "draft",
    prCreateAttempts: positiveInteger("prCreateAttempts"),
    reconciledAfterTimeout: value.reconciledAfterTimeout,
    checks: stringList("checks", 50),
    mergeState: "unavailable",
  };
}

export function normalizeTaskDetail(value: unknown): TaskDetail {
  if (!isRecord(value)) {
    throw new ContractError("Task detail must be an object.");
  }

  const summary = normalizeTaskSummary(value, "Task detail");
  const coding =
    value.coding === undefined || value.coding === null
      ? undefined
      : normalizeCodingOutcome(value.coding);
  if (coding !== undefined && summary.journey !== "coding") {
    throw new ContractError("Task detail coding outcome has no coding journey.");
  }
  return {
    ...summary,
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
    ...(coding === undefined ? {} : { coding }),
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
  const actionRequestsValue = value.actionRequests;
  const reviewConfigsValue = value.reviewConfigs;
  const hasBatchContract = actionRequestsValue !== undefined || reviewConfigsValue !== undefined;
  if (
    hasBatchContract &&
    (!Array.isArray(actionRequestsValue) || !Array.isArray(reviewConfigsValue))
  ) {
    throw new ContractError(
      "Task detail pendingInterrupt must provide actionRequests and reviewConfigs together.",
    );
  }
  const actionRequests = Array.isArray(actionRequestsValue)
    ? actionRequestsValue.map((item, index) =>
        normalizeActionRequest(
          item,
          `Task detail pendingInterrupt actionRequests item ${index + 1}`,
        ),
      )
    : undefined;
  const reviewConfigs = Array.isArray(reviewConfigsValue)
    ? reviewConfigsValue.map((item, index) =>
        normalizeReviewConfig(item, `Task detail pendingInterrupt reviewConfigs item ${index + 1}`),
      )
    : undefined;
  if (actionRequests && reviewConfigs) {
    if (actionRequests.length === 0 || actionRequests.length !== reviewConfigs.length) {
      throw new ContractError(
        "Task detail pendingInterrupt actionRequests and reviewConfigs must have the same number of items.",
      );
    }
    actionRequests.forEach((action, index) => {
      if (reviewConfigs[index]?.actionName !== action.name) {
        throw new ContractError(
          `Task detail pendingInterrupt reviewConfigs item ${index + 1} does not match its action.`,
        );
      }
    });
  }
  const version = optionalString(value, "version");
  if (hasBatchContract && version === undefined) {
    throw new ContractError("Task detail pendingInterrupt is missing a valid version.");
  }
  return {
    interruptId: requiredString(value, "interruptId", "Task detail pendingInterrupt"),
    decisions: normalizeDecisions(value.decisions, true),
    planRevision:
      Number.isInteger(value.planRevision) && Number(value.planRevision) >= 1
        ? Number(value.planRevision)
        : undefined,
    ...(version ? { version } : {}),
    ...(actionRequests ? { actionRequests } : {}),
    ...(reviewConfigs ? { reviewConfigs } : {}),
    title: "Approval required",
    question: "Review the current plan and choose one of the actions offered by the agent.",
  };
}

function normalizeOrderedDecision(value: OrderedDecision, context: string): OrderedDecision {
  if (!isRecord(value) || !HITL_DECISION_TYPES.includes(value.type as HitlDecisionType)) {
    throw new ContractError(`${context} contains an unsupported decision.`);
  }
  switch (value.type) {
    case "approve":
      return { type: "approve" };
    case "edit":
      return {
        type: "edit",
        editedAction: normalizeActionRequest(value.editedAction, `${context} edit`),
      };
    case "reject": {
      const message = validateDecisionComment(value.message);
      return { type: "reject", ...(message ? { message } : {}) };
    }
    case "respond": {
      const message = validateDecisionComment(value.message);
      if (!message) throw new ContractError(`${context} requires a nonblank response message.`);
      return { type: "respond", message };
    }
  }
}

export function validateDecisionBatchInput(
  interrupt: ActiveInterrupt,
  input: DecisionBatchInput,
): DecisionBatchInput {
  if (!interrupt.version || !interrupt.actionRequests || !interrupt.reviewConfigs) {
    throw new ContractError("The current approval does not provide an ordered batch contract.");
  }
  if (input.interruptId !== interrupt.interruptId || input.expectedVersion !== interrupt.version) {
    throw new ContractError("The ordered approval changed before submission.");
  }
  if (input.idempotencyKey.trim() === "") {
    throw new ContractError("The ordered approval requires a valid idempotency key.");
  }
  if (input.decisions.length !== interrupt.actionRequests.length) {
    throw new ContractError("The ordered approval requires one decision per action.");
  }
  const decisions = input.decisions.map((decision, index) => {
    const normalized = normalizeOrderedDecision(decision, `Decision ${index + 1}`);
    const config = interrupt.reviewConfigs?.[index];
    const action = interrupt.actionRequests?.[index];
    if (!config || !action || !config.allowedDecisions.includes(normalized.type)) {
      throw new ContractError(`Action ${index + 1} does not allow ${normalized.type}.`);
    }
    if (normalized.type === "edit" && normalized.editedAction.name !== action.name) {
      throw new ContractError(`Action ${index + 1} edit must preserve the action name.`);
    }
    if (
      normalized.type === "edit" &&
      action.name === "execute_plan_step" &&
      normalized.editedAction.args.position !== index + 1
    ) {
      throw new ContractError(`Action ${index + 1} edit must preserve its plan position.`);
    }
    return normalized;
  });
  return { ...input, idempotencyKey: input.idempotencyKey.trim(), decisions };
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

export function normalizeDecisionBatchResult(value: unknown): DecisionBatchResult {
  if (!isRecord(value)) throw new ContractError("Decision-batch response must be an object.");
  if (
    !Array.isArray(value.decisionTypes) ||
    value.decisionTypes.length === 0 ||
    value.decisionTypes.some(
      (decision) =>
        typeof decision !== "string" || !HITL_DECISION_TYPES.includes(decision as HitlDecisionType),
    )
  ) {
    throw new ContractError("Decision-batch response contains unsupported decision types.");
  }
  if (value.status !== "accepted" || typeof value.duplicate !== "boolean") {
    throw new ContractError("Decision-batch response is missing a valid receipt status.");
  }
  return {
    taskId: requiredString(value, "taskId", "Decision-batch response"),
    runId: requiredString(value, "runId", "Decision-batch response"),
    interruptId: requiredString(value, "interruptId", "Decision-batch response"),
    version: requiredString(value, "version", "Decision-batch response"),
    decisionTypes: [...value.decisionTypes] as HitlDecisionType[],
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
    taskId: requiredString(value, "taskId", context),
    runId: requiredString(value, "runId", context),
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
    let batchFields: Pick<ActiveInterrupt, "version" | "actionRequests" | "reviewConfigs"> = {};
    if (active?.interruptId === interruptId) {
      batchFields = {
        ...(active.version ? { version: active.version } : {}),
        ...(active.actionRequests ? { actionRequests: active.actionRequests } : {}),
        ...(active.reviewConfigs ? { reviewConfigs: active.reviewConfigs } : {}),
      };
    }
    return {
      interruptId,
      decisions: normalizeDecisions(event.data.decisions, true),
      planRevision:
        Number.isInteger(event.data.planRevision) && Number(event.data.planRevision) >= 1
          ? Number(event.data.planRevision)
          : undefined,
      ...batchFields,
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
    const {
      version: _staleVersion,
      actionRequests: _staleRequests,
      reviewConfigs: _staleConfigs,
      ...legacyInterrupt
    } = active;
    return { ...legacyInterrupt, planRevision: Number(event.data.revision) };
  }
  if (
    event.name === "decision.recorded" &&
    active &&
    event.data.interruptId === active.interruptId &&
    (event.data.decision === "approve" ||
      event.data.decision === "reject" ||
      event.data.decision === "respond" ||
      (Array.isArray(event.data.decisionTypes) && event.data.decisionTypes.length > 0))
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
        event.data.decision === "respond" ||
        (Array.isArray(event.data.decisionTypes) && event.data.decisionTypes.length > 0)) &&
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
        // Generic progress events carry no authoritative task/run evidence
        // identity. Keep them inspectable, but make them ineligible for export.
        taskId: "",
        runId: "",
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

/** Convert an SSE id into the monotonic cursor carried by task projections. */
export function taskEventCursor(eventId: string): number | undefined {
  const cursor = Number(eventId);
  return Number.isSafeInteger(cursor) && cursor >= 1 ? cursor : undefined;
}

/** Preserve a newer streamed list projection when an awaited reload resolves late. */
export function summaryAfterAuthoritativeReload(
  current: TaskSummary,
  incoming: TaskSummary,
): TaskSummary {
  if (isTerminalStatus(current.status) && !isTerminalStatus(incoming.status)) {
    return current;
  }
  if (
    current.lastEventId !== undefined &&
    (incoming.lastEventId === undefined || incoming.lastEventId < current.lastEventId)
  ) {
    return current;
  }
  return incoming;
}

/**
 * Apply a newly accepted decision only while the UI is still showing the exact
 * interrupt that receipt acknowledged. A later stream event or detail reload
 * may already have completed the task or installed a newer interrupt by the
 * time the HTTP response arrives; those states are authoritative.
 */
export function detailAfterAcceptedDecision(task: TaskDetail, interruptId: string): TaskDetail {
  if (task.status !== "waiting-approval" || task.pendingInterrupt?.interruptId !== interruptId) {
    return task;
  }
  return { ...task, status: "running", pendingInterrupt: undefined };
}

/**
 * Show the accepted plan immediately, but fail closed while its versioned batch
 * contract is reloaded. Legacy singleton approvals keep their advertised verbs.
 */
export function detailAwaitingApprovalReload(
  task: TaskDetail,
  interruptId: string,
  plan: ProposedPlan,
): TaskDetail {
  const pending = task.pendingInterrupt;
  if (pending?.interruptId !== interruptId) return { ...task, proposedPlan: plan };
  if (!pending.version || !pending.actionRequests || !pending.reviewConfigs) {
    return {
      ...task,
      proposedPlan: plan,
      pendingInterrupt: { ...pending, planRevision: plan.revision },
    };
  }
  const {
    actionRequests: _actions,
    reviewConfigs: _configs,
    version: _version,
    ...legacy
  } = pending;
  return {
    ...task,
    proposedPlan: plan,
    pendingInterrupt: {
      ...legacy,
      decisions: [],
      planRevision: plan.revision,
      question: "Reloading the ordered approval for this saved plan…",
    },
  };
}

export const STALE_DECISION_MESSAGE =
  "This approval is no longer current. No decision was sent. The latest task state is shown.";

/**
 * Validate a decision against the freshly reconciled task projection. This is
 * a user-facing preflight, not the authority boundary: the API still owns the
 * atomic stale/idempotency check for a race that happens after this read.
 */
export function decisionPreflightProblem(
  task: TaskDetail,
  input: DecisionInput,
): string | undefined {
  if (task.status !== "waiting-approval" || task.pendingInterrupt === undefined) {
    return STALE_DECISION_MESSAGE;
  }
  if (task.pendingInterrupt.interruptId !== input.interruptId) {
    return "The approval changed before submission. No decision was sent. Review the latest request.";
  }
  if (!task.pendingInterrupt.decisions.includes(input.decision)) {
    return `The current approval does not offer ${input.decision}. No decision was sent.`;
  }
  return undefined;
}

export function decisionBatchPreflightProblem(
  task: TaskDetail,
  input: DecisionBatchInput,
): string | undefined {
  if (task.status !== "waiting-approval" || task.pendingInterrupt === undefined) {
    return STALE_DECISION_MESSAGE;
  }
  try {
    validateDecisionBatchInput(task.pendingInterrupt, input);
    return undefined;
  } catch (error) {
    return error instanceof ContractError
      ? `${error.message} No decision was sent.`
      : "The ordered approval could not be validated. No decision was sent.";
  }
}

/** Preserve newer streamed state when an awaited detail reload resolves late. */
export function detailAfterAuthoritativeReload(
  current: TaskDetail,
  incoming: TaskDetail,
): TaskDetail {
  if (summaryAfterAuthoritativeReload(current, incoming) === current) {
    return current;
  }
  if (
    current.status === "waiting-approval" &&
    current.pendingInterrupt !== undefined &&
    incoming.pendingInterrupt !== undefined &&
    current.pendingInterrupt.interruptId !== incoming.pendingInterrupt.interruptId &&
    (incoming.lastEventId === undefined ||
      (current.lastEventId !== undefined && incoming.lastEventId <= current.lastEventId))
  ) {
    return current;
  }
  return incoming;
}

export function reduceEventsIntoDetail(task: TaskDetail, events: readonly TaskEvent[]): TaskDetail {
  return events.reduce<TaskDetail>((current, event) => {
    const eventResult = event.name === "run.completed" ? getCompletionResultText(event) : undefined;
    const eventCursor = taskEventCursor(event.id);
    return {
      ...current,
      status: statusAfterEvent(current.status, event, current.pendingInterrupt),
      pendingInterrupt: interruptAfterEvent(current.pendingInterrupt, event),
      result: eventResult ?? current.result,
      lastEventId:
        eventCursor !== undefined &&
        (current.lastEventId === undefined || eventCursor > current.lastEventId)
          ? eventCursor
          : current.lastEventId,
    };
  }, task);
}

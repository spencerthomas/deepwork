import {
  applicationEventId,
  evidenceId,
  interruptId,
  runId,
  sourceApplicationEventKey,
  sourceEvidenceKey,
  sourceId,
  sourceInterruptKey,
  sourceRunKey,
  sourceThreadKey,
  taskId,
  threadId,
  type SourceApplicationEventKey,
  type SourceEvidenceKey,
  type SourceInterruptKey,
  type SourceRunKey,
  type SourceThreadKey,
  type TaskId,
} from "./identity.js";
import type { TaskStatus } from "./view-state.js";

export const TASK_OBJECTIVE_MAX_CODE_POINTS = 8_000;
export const PLAN_STEP_MAX_CODE_POINTS = 1_000;
export const DECISION_COMMENT_MAX_CODE_POINTS = 1_000;
export const PLAN_STEP_MAX_COUNT = 8;
export const PLAN_REVISION_MAX = 2_147_483_647;
export const EVENT_SEQUENCE_MAX = 2_147_483_647;
export const TASK_RESULT_MAX_CODE_POINTS = 18_048;
export const EVIDENCE_REF_MAX_COUNT = 64;
export const TASK_EVIDENCE_MAX_COUNT = 256;

export const TASK_DECISIONS = Object.freeze(["approve", "reject", "respond"] as const);

export type TaskDecision = (typeof TASK_DECISIONS)[number];

export const TASK_EVENT_NAMES = Object.freeze([
  "task.created",
  "run.started",
  "content.delta",
  "plan.proposed",
  "plan.updated",
  "evidence.recorded",
  "interrupt.requested",
  "decision.recorded",
  "run.completed",
] as const);

export type TaskEventName = (typeof TASK_EVENT_NAMES)[number];

export const EVIDENCE_KINDS = Object.freeze(["fixture"] as const);
export type EvidenceKind = (typeof EVIDENCE_KINDS)[number];

export const EVIDENCE_SOURCES = Object.freeze([
  "deterministic-local-runner",
  "reviewer-response",
] as const);
export type EvidenceSource = (typeof EVIDENCE_SOURCES)[number];

export const EVIDENCE_CLASSES = Object.freeze(["fixture", "local-source"] as const);
export type EvidenceClass = (typeof EVIDENCE_CLASSES)[number];

declare const objectiveTextBrand: unique symbol;
declare const planStepBrand: unique symbol;
declare const decisionCommentBrand: unique symbol;
declare const displayTextBrand: unique symbol;
declare const resultTextBrand: unique symbol;

export type ObjectiveText = string & {
  readonly [objectiveTextBrand]: "ObjectiveText";
};
export type PlanStep = string & { readonly [planStepBrand]: "PlanStep" };
export type DecisionComment = string & {
  readonly [decisionCommentBrand]: "DecisionComment";
};
export type DisplayText = string & {
  readonly [displayTextBrand]: "DisplayText";
};
export type ResultText = string & { readonly [resultTextBrand]: "ResultText" };

export interface TaskAccepted {
  readonly taskId: TaskId;
  readonly run: SourceRunKey;
  readonly facts: TaskStateFacts;
  readonly status: TaskStatus;
}

export interface TaskStateFacts {
  readonly cancellationConfirmed: boolean;
  readonly pendingCurrentInterrupt: boolean;
  readonly runActive: boolean;
  readonly queued: boolean;
  readonly terminalFailure: boolean;
  readonly terminalSuccess: boolean;
}

export interface ProposedPlan {
  readonly revision: number;
  readonly title: DisplayText;
  readonly steps: readonly PlanStep[];
  readonly evidenceRefs: readonly SourceEvidenceKey[];
}

export interface EvidenceProvenance {
  readonly sourceThread: SourceThreadKey;
  readonly observedThrough: "task-detail" | "application-event";
  readonly evidenceClass?: EvidenceClass;
}

export interface EvidenceRecord {
  readonly identity: SourceEvidenceKey;
  readonly kind: EvidenceKind;
  readonly summary: DisplayText;
  readonly source: EvidenceSource;
  readonly verified: boolean;
  readonly provenance: EvidenceProvenance;
}

export interface PendingInterrupt {
  readonly identity: SourceInterruptKey;
  readonly decisions: readonly TaskDecision[];
  readonly planRevision: number;
  readonly question?: DisplayText;
}

export interface TaskSummary {
  readonly taskId: TaskId;
  readonly sourceThread: SourceThreadKey;
  readonly run: SourceRunKey;
  // Present when the summary comes from an API snapshot; the event-sourced
  // reducer does not observe creation time, so it stays absent there.
  readonly createdAt?: string;
  readonly title: DisplayText;
  readonly objective: ObjectiveText;
  readonly facts: TaskStateFacts;
  readonly status: TaskStatus;
  readonly lastEvent: SourceApplicationEventKey;
  readonly lastEventSequence: number;
}

export interface TaskDetail extends TaskSummary {
  readonly pendingInterrupt?: PendingInterrupt;
  readonly proposedPlan?: ProposedPlan;
  readonly evidence: readonly EvidenceRecord[];
  readonly result?: ResultText;
}

export interface TaskResult {
  readonly taskId: TaskId;
  readonly run: SourceRunKey;
  readonly status: "done";
  readonly result: ResultText;
}

export interface DecisionInput {
  readonly interrupt: SourceInterruptKey;
  readonly expectedPlanRevision: number;
  readonly decision: TaskDecision;
  readonly comment?: DecisionComment;
}

export interface DecisionReceipt {
  readonly taskId: TaskId;
  readonly run: SourceRunKey;
  readonly interrupt: SourceInterruptKey;
  readonly decision: TaskDecision;
  readonly status: "accepted";
  readonly duplicate: boolean;
}

export interface PlanEditInput {
  readonly interrupt: SourceInterruptKey;
  readonly expectedRevision: number;
  readonly steps: readonly PlanStep[];
}

export interface PlanEditReceipt {
  readonly taskId: TaskId;
  readonly run: SourceRunKey;
  readonly interrupt: SourceInterruptKey;
  readonly plan: ProposedPlan;
}

export type TaskApplicationEvent =
  | TaskCreatedEvent
  | RunStartedEvent
  | ContentDeltaEvent
  | PlanChangedEvent
  | EvidenceRecordedEvent
  | InterruptRequestedEvent
  | DecisionRecordedEvent
  | RunCompletedEvent;

interface EventBase<Name extends TaskEventName> {
  readonly identity: SourceApplicationEventKey;
  readonly sequence: number;
  readonly taskId: TaskId;
  readonly sourceThread: SourceThreadKey;
  readonly name: Name;
}

export interface TaskCreatedEvent extends EventBase<"task.created"> {
  readonly run: SourceRunKey;
}

export interface RunStartedEvent extends EventBase<"run.started"> {
  readonly run: SourceRunKey;
}

export interface ContentDeltaEvent extends EventBase<"content.delta"> {
  readonly run: SourceRunKey;
  readonly text: ResultText;
  readonly evidenceClass: EvidenceClass;
}

export interface PlanChangedEvent extends EventBase<"plan.proposed" | "plan.updated"> {
  readonly run: SourceRunKey;
  readonly plan: ProposedPlan;
  readonly evidenceClass: EvidenceClass;
}

export interface EvidenceRecordedEvent extends EventBase<"evidence.recorded"> {
  readonly run: SourceRunKey;
  readonly evidence: EvidenceRecord;
}

export interface InterruptRequestedEvent extends EventBase<"interrupt.requested"> {
  readonly run: SourceRunKey;
  readonly interrupt: PendingInterrupt;
}

export interface DecisionRecordedEvent extends EventBase<"decision.recorded"> {
  readonly run: SourceRunKey;
  readonly interrupt: SourceInterruptKey;
  readonly decision: TaskDecision;
  readonly commentProvided: boolean;
  readonly responseProvided: boolean;
}

export interface RunCompletedEvent extends EventBase<"run.completed"> {
  readonly run: SourceRunKey;
  readonly outcome: "success" | "rejected" | "failure";
  readonly safeReason: DisplayText;
  readonly resultAvailable: boolean;
}

export function unicodeCodePointLength(value: string): number {
  return [...value].length;
}

function boundedText<T extends string>(value: string, label: string, maximum: number): T {
  if (value.trim().length === 0) {
    throw new TypeError(`${label} must contain visible text.`);
  }
  if (unicodeCodePointLength(value) > maximum) {
    throw new TypeError(`${label} exceeds ${maximum} Unicode code points.`);
  }
  if (
    [...value].some((character) => {
      const codePoint = character.codePointAt(0) ?? 0;
      // Reject C0 controls (allowing tab/newline/carriage return), DEL, and the
      // C1 range (0x80–0x9F) — parity with opaqueIdentifier (identity.ts) and the
      // API wire contract (_reject_unsafe_controls), which both reject 127–159.
      return (
        (codePoint < 32 && character !== "\t" && character !== "\n" && character !== "\r") ||
        (codePoint >= 127 && codePoint <= 159)
      );
    })
  ) {
    throw new TypeError(`${label} contains an unsupported control character.`);
  }
  return value as T;
}

export function objectiveText(value: string): ObjectiveText {
  return boundedText<ObjectiveText>(value, "Task objective", TASK_OBJECTIVE_MAX_CODE_POINTS);
}

export function planStep(value: string): PlanStep {
  return boundedText<PlanStep>(value, "Plan step", PLAN_STEP_MAX_CODE_POINTS);
}

export function decisionComment(value: string): DecisionComment {
  return boundedText<DecisionComment>(value, "Decision comment", DECISION_COMMENT_MAX_CODE_POINTS);
}

export function displayText(value: string, label: string, maximum: number): DisplayText {
  return boundedText<DisplayText>(value, label, maximum);
}

export function resultText(value: string): ResultText {
  return boundedText<ResultText>(value, "Task result", TASK_RESULT_MAX_CODE_POINTS);
}

export function positiveRevision(value: number, label: string): number {
  if (!Number.isSafeInteger(value) || value < 1 || value > PLAN_REVISION_MAX) {
    throw new TypeError(`${label} must be an integer from 1 through ${PLAN_REVISION_MAX}.`);
  }
  return value;
}

export function positiveEventSequence(value: number, label: string): number {
  if (!Number.isSafeInteger(value) || value < 1 || value > EVENT_SEQUENCE_MAX) {
    throw new TypeError(`${label} must be an integer from 1 through ${EVENT_SEQUENCE_MAX}.`);
  }
  return value;
}

export function deriveTaskStatus(facts: TaskStateFacts): TaskStatus {
  if (facts.cancellationConfirmed) {
    return "cancelled";
  }
  if (facts.pendingCurrentInterrupt) {
    return "needs-review";
  }
  if (facts.runActive) {
    return "running";
  }
  if (facts.queued) {
    return "queued";
  }
  if (facts.terminalFailure) {
    return "failed";
  }
  if (facts.terminalSuccess) {
    return "done";
  }
  return "status-unavailable";
}

function taskFactsAreCoherent(facts: TaskStateFacts): boolean {
  const terminalCount = Number(facts.terminalFailure) + Number(facts.terminalSuccess);
  if (terminalCount > 1) {
    return false;
  }
  if (facts.cancellationConfirmed) {
    return (
      !facts.pendingCurrentInterrupt && !facts.runActive && !facts.queued && terminalCount === 0
    );
  }
  if (facts.pendingCurrentInterrupt) {
    return facts.runActive && !facts.queued && terminalCount === 0;
  }
  if (facts.runActive) {
    return !facts.queued && terminalCount === 0;
  }
  if (facts.queued) {
    return terminalCount === 0;
  }
  return terminalCount <= 1;
}

function exactTaskFacts(facts: TaskStateFacts): TaskStateFacts {
  if (
    typeof facts.cancellationConfirmed !== "boolean" ||
    typeof facts.pendingCurrentInterrupt !== "boolean" ||
    typeof facts.runActive !== "boolean" ||
    typeof facts.queued !== "boolean" ||
    typeof facts.terminalFailure !== "boolean" ||
    typeof facts.terminalSuccess !== "boolean"
  ) {
    throw new TypeError("Task lifecycle facts must be booleans.");
  }
  const exact = Object.freeze({
    cancellationConfirmed: facts.cancellationConfirmed,
    pendingCurrentInterrupt: facts.pendingCurrentInterrupt,
    runActive: facts.runActive,
    queued: facts.queued,
    terminalFailure: facts.terminalFailure,
    terminalSuccess: facts.terminalSuccess,
  });
  if (!taskFactsAreCoherent(exact)) {
    throw new TypeError("Task lifecycle facts are incoherent.");
  }
  return exact;
}

function exactSourceThread(key: SourceThreadKey): SourceThreadKey {
  return sourceThreadKey(sourceId(key.sourceId), threadId(key.threadId));
}

function exactSourceRun(key: SourceRunKey): SourceRunKey {
  return sourceRunKey(sourceId(key.sourceId), threadId(key.threadId), runId(key.runId));
}

function exactSourceEvidence(key: SourceEvidenceKey): SourceEvidenceKey {
  return sourceEvidenceKey(
    sourceId(key.sourceId),
    taskId(key.taskId),
    threadId(key.threadId),
    runId(key.runId),
    evidenceId(key.evidenceId),
  );
}

function exactSourceInterrupt(key: SourceInterruptKey): SourceInterruptKey {
  return sourceInterruptKey(
    sourceId(key.sourceId),
    taskId(key.taskId),
    threadId(key.threadId),
    runId(key.runId),
    interruptId(key.interruptId),
  );
}

function exactSourceApplicationEvent(key: SourceApplicationEventKey): SourceApplicationEventKey {
  return sourceApplicationEventKey(
    sourceId(key.sourceId),
    taskId(key.taskId),
    threadId(key.threadId),
    runId(key.runId),
    applicationEventId(key.eventId),
  );
}

export function taskAccepted(input: Omit<TaskAccepted, "status">): TaskAccepted {
  const acceptedTaskId = taskId(input.taskId);
  const acceptedRun = exactSourceRun(input.run);
  const facts = exactTaskFacts(input.facts);
  return Object.freeze({
    taskId: acceptedTaskId,
    run: acceptedRun,
    facts,
    status: deriveTaskStatus(facts),
  });
}

export function proposedPlan(input: {
  readonly revision: number;
  readonly title: string;
  readonly steps: readonly string[];
  readonly evidenceRefs: readonly SourceEvidenceKey[];
}): ProposedPlan {
  if (input.steps.length < 1 || input.steps.length > PLAN_STEP_MAX_COUNT) {
    throw new TypeError(`A plan must contain between 1 and ${PLAN_STEP_MAX_COUNT} steps.`);
  }
  if (input.evidenceRefs.length > EVIDENCE_REF_MAX_COUNT) {
    throw new TypeError(
      `A plan cannot contain more than ${EVIDENCE_REF_MAX_COUNT} evidence references.`,
    );
  }
  return Object.freeze({
    revision: positiveRevision(input.revision, "Plan revision"),
    title: displayText(input.title, "Plan title", 100),
    steps: Object.freeze(input.steps.map(planStep)),
    evidenceRefs: Object.freeze(input.evidenceRefs.map(exactSourceEvidence)),
  });
}

export function evidenceRecord(input: {
  readonly identity: SourceEvidenceKey;
  readonly kind: EvidenceKind;
  readonly summary: string;
  readonly source: EvidenceSource;
  readonly verified: boolean;
  readonly provenance: EvidenceProvenance;
}): EvidenceRecord {
  if (!(EVIDENCE_KINDS as readonly string[]).includes(input.kind)) {
    throw new TypeError("Evidence kind is not accepted by the task contract.");
  }
  if (!(EVIDENCE_SOURCES as readonly string[]).includes(input.source)) {
    throw new TypeError("Evidence source is not accepted by the task contract.");
  }
  if (
    typeof input.verified !== "boolean" ||
    !["task-detail", "application-event"].includes(input.provenance.observedThrough) ||
    (input.provenance.evidenceClass !== undefined &&
      !(EVIDENCE_CLASSES as readonly string[]).includes(input.provenance.evidenceClass))
  ) {
    throw new TypeError("Evidence provenance is not accepted by the task contract.");
  }
  return Object.freeze({
    identity: exactSourceEvidence(input.identity),
    kind: input.kind,
    summary: displayText(input.summary, "Evidence summary", 300),
    source: input.source,
    verified: input.verified,
    provenance: Object.freeze({
      sourceThread: exactSourceThread(input.provenance.sourceThread),
      observedThrough: input.provenance.observedThrough,
      ...(input.provenance.evidenceClass === undefined
        ? {}
        : { evidenceClass: input.provenance.evidenceClass }),
    }),
  });
}

export function pendingInterrupt(input: {
  readonly identity: SourceInterruptKey;
  readonly decisions: readonly TaskDecision[];
  readonly planRevision: number;
  readonly question?: string;
}): PendingInterrupt {
  if (
    input.decisions.length < 1 ||
    input.decisions.length > TASK_DECISIONS.length ||
    new Set(input.decisions).size !== input.decisions.length ||
    !input.decisions.every((decision) => (TASK_DECISIONS as readonly string[]).includes(decision))
  ) {
    throw new TypeError("Interrupt decisions must be a non-empty unique accepted set.");
  }
  return Object.freeze({
    identity: exactSourceInterrupt(input.identity),
    decisions: Object.freeze([...input.decisions]),
    planRevision: positiveRevision(input.planRevision, "Interrupt plan revision"),
    ...(input.question === undefined
      ? {}
      : {
          question: displayText(input.question, "Interrupt question", 200),
        }),
  });
}

const ISO_8601_INSTANT_PATTERN =
  /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/;

/**
 * Accept a task creation timestamp: a bounded ISO-8601 instant with an explicit
 * offset (as produced by the API's `datetime.isoformat()`). The value is a real
 * recorded instant, never fabricated, so an unparseable or unbounded string is
 * rejected rather than coerced.
 */
export function createdAtTimestamp(value: string): string {
  const trimmed = value.trim();
  // The pattern fixes the shape and offset; Date.parse rejects impossible
  // calendar/clock values the regex alone would accept (e.g. month/day 99).
  if (
    trimmed.length > 64 ||
    !ISO_8601_INSTANT_PATTERN.test(trimmed) ||
    Number.isNaN(Date.parse(trimmed))
  ) {
    throw new TypeError("Task creation timestamp is not a valid ISO-8601 instant.");
  }
  return trimmed;
}

export function taskSummary(
  input: Omit<TaskSummary, "status" | "title" | "objective"> & {
    readonly title: string;
    readonly objective: string;
  },
): TaskSummary {
  const acceptedTaskId = taskId(input.taskId);
  const acceptedSourceThread = exactSourceThread(input.sourceThread);
  const acceptedRun = exactSourceRun(input.run);
  const acceptedLastEvent = exactSourceApplicationEvent(input.lastEvent);
  const lastEventSequence = positiveEventSequence(input.lastEventSequence, "Last event sequence");
  if (
    acceptedSourceThread.sourceId !== acceptedRun.sourceId ||
    acceptedSourceThread.threadId !== acceptedRun.threadId ||
    acceptedLastEvent.sourceId !== acceptedSourceThread.sourceId ||
    acceptedLastEvent.taskId !== acceptedTaskId ||
    acceptedLastEvent.threadId !== acceptedSourceThread.threadId ||
    acceptedLastEvent.runId !== acceptedRun.runId ||
    acceptedLastEvent.eventId !== String(lastEventSequence)
  ) {
    throw new TypeError("Task summary identity and event cursor are incoherent.");
  }
  const facts = exactTaskFacts(input.facts);
  return Object.freeze({
    taskId: acceptedTaskId,
    sourceThread: acceptedSourceThread,
    run: acceptedRun,
    ...(input.createdAt === undefined ? {} : { createdAt: createdAtTimestamp(input.createdAt) }),
    title: displayText(input.title, "Task title", 80),
    objective: objectiveText(input.objective),
    facts,
    status: deriveTaskStatus(facts),
    lastEvent: acceptedLastEvent,
    lastEventSequence,
  });
}

export function taskDetail(
  input: Omit<TaskDetail, "status" | "title" | "objective"> & {
    readonly title: string;
    readonly objective: string;
  },
): TaskDetail {
  if (input.evidence.length > TASK_EVIDENCE_MAX_COUNT) {
    throw new TypeError(
      `Task detail cannot contain more than ${TASK_EVIDENCE_MAX_COUNT} evidence records.`,
    );
  }
  const summary = taskSummary(input);
  const evidence = input.evidence.map((record) =>
    evidenceRecord({
      identity: record.identity,
      kind: record.kind,
      summary: record.summary,
      source: record.source,
      verified: record.verified,
      provenance: record.provenance,
    }),
  );
  const plan =
    input.proposedPlan === undefined
      ? undefined
      : proposedPlan({
          revision: input.proposedPlan.revision,
          title: input.proposedPlan.title,
          steps: input.proposedPlan.steps,
          evidenceRefs: input.proposedPlan.evidenceRefs,
        });
  const interrupt =
    input.pendingInterrupt === undefined
      ? undefined
      : pendingInterrupt({
          identity: input.pendingInterrupt.identity,
          decisions: input.pendingInterrupt.decisions,
          planRevision: input.pendingInterrupt.planRevision,
          ...(input.pendingInterrupt.question === undefined
            ? {}
            : { question: input.pendingInterrupt.question }),
        });
  const matchesTaskBinding = (key: SourceEvidenceKey | SourceInterruptKey): boolean =>
    key.sourceId === summary.sourceThread.sourceId &&
    key.taskId === summary.taskId &&
    key.threadId === summary.sourceThread.threadId &&
    key.runId === summary.run.runId;
  if (
    evidence.some(
      (record) =>
        !matchesTaskBinding(record.identity) ||
        record.provenance.sourceThread.sourceId !== summary.sourceThread.sourceId ||
        record.provenance.sourceThread.threadId !== summary.sourceThread.threadId ||
        (record.provenance.observedThrough === "application-event" &&
          record.provenance.evidenceClass !== "fixture"),
    ) ||
    plan?.evidenceRefs.some((reference) => !matchesTaskBinding(reference)) === true ||
    (interrupt !== undefined &&
      (!matchesTaskBinding(interrupt.identity) ||
        plan === undefined ||
        interrupt.planRevision !== plan.revision)) ||
    summary.facts.pendingCurrentInterrupt !== (interrupt !== undefined) ||
    summary.facts.terminalSuccess !== (input.result !== undefined)
  ) {
    throw new TypeError("Task detail nested state is incoherent.");
  }
  return Object.freeze({
    taskId: summary.taskId,
    sourceThread: summary.sourceThread,
    run: summary.run,
    ...(summary.createdAt === undefined ? {} : { createdAt: summary.createdAt }),
    title: summary.title,
    objective: summary.objective,
    facts: summary.facts,
    status: summary.status,
    lastEvent: summary.lastEvent,
    lastEventSequence: summary.lastEventSequence,
    ...(interrupt === undefined ? {} : { pendingInterrupt: interrupt }),
    ...(plan === undefined ? {} : { proposedPlan: plan }),
    evidence: Object.freeze(evidence),
    ...(input.result === undefined ? {} : { result: resultText(input.result) }),
  });
}

export function taskResult(
  input: Omit<TaskResult, "status" | "result"> & {
    readonly result: string;
  },
): TaskResult {
  return Object.freeze({
    taskId: taskId(input.taskId),
    run: exactSourceRun(input.run),
    status: "done",
    result: resultText(input.result),
  });
}

export function decisionInput(input: {
  readonly interrupt: SourceInterruptKey;
  readonly expectedPlanRevision: number;
  readonly decision: TaskDecision;
  readonly comment?: string;
}): DecisionInput {
  if (!(TASK_DECISIONS as readonly string[]).includes(input.decision)) {
    throw new TypeError("Decision is not accepted by the task contract.");
  }
  if (
    input.decision === "respond" &&
    (input.comment === undefined || input.comment.trim().length === 0)
  ) {
    throw new TypeError("Respond requires a non-blank decision comment.");
  }
  return Object.freeze({
    interrupt: exactSourceInterrupt(input.interrupt),
    expectedPlanRevision: positiveRevision(
      input.expectedPlanRevision,
      "Expected decision plan revision",
    ),
    decision: input.decision,
    ...(input.comment === undefined ? {} : { comment: decisionComment(input.comment) }),
  });
}

export function planEditInput(input: {
  readonly interrupt: SourceInterruptKey;
  readonly expectedRevision: number;
  readonly steps: readonly string[];
}): PlanEditInput {
  if (input.steps.length < 1 || input.steps.length > PLAN_STEP_MAX_COUNT) {
    throw new TypeError(`A plan must contain between 1 and ${PLAN_STEP_MAX_COUNT} steps.`);
  }
  return Object.freeze({
    interrupt: exactSourceInterrupt(input.interrupt),
    expectedRevision: positiveRevision(input.expectedRevision, "Expected plan revision"),
    steps: Object.freeze(input.steps.map(planStep)),
  });
}

export function isTaskDecision(value: unknown): value is TaskDecision {
  return typeof value === "string" && (TASK_DECISIONS as readonly string[]).includes(value);
}

export function isTaskEventName(value: unknown): value is TaskEventName {
  return typeof value === "string" && (TASK_EVENT_NAMES as readonly string[]).includes(value);
}

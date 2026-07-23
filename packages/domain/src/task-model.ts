import type {
  SourceApplicationEventKey,
  SourceEvidenceKey,
  SourceInterruptKey,
  SourceRunKey,
  SourceThreadKey,
  TaskId,
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

export const EVIDENCE_CLASSES = Object.freeze(["fixture"] as const);
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
  readonly evidenceClass: "fixture";
}

export interface PlanChangedEvent extends EventBase<"plan.proposed" | "plan.updated"> {
  readonly run: SourceRunKey;
  readonly plan: ProposedPlan;
  readonly evidenceClass: "fixture";
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
      return (
        (codePoint < 32 && character !== "\t" && character !== "\n" && character !== "\r") ||
        codePoint === 127
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

export function taskAccepted(input: Omit<TaskAccepted, "status">): TaskAccepted {
  const facts = Object.freeze({ ...input.facts });
  return Object.freeze({
    ...input,
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
    evidenceRefs: Object.freeze([...input.evidenceRefs]),
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
  return Object.freeze({
    identity: input.identity,
    kind: input.kind,
    summary: displayText(input.summary, "Evidence summary", 300),
    source: input.source,
    verified: input.verified,
    provenance: Object.freeze({ ...input.provenance }),
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
    identity: input.identity,
    decisions: Object.freeze([...input.decisions]),
    planRevision: positiveRevision(input.planRevision, "Interrupt plan revision"),
    ...(input.question === undefined
      ? {}
      : {
          question: displayText(input.question, "Interrupt question", 200),
        }),
  });
}

export function taskSummary(
  input: Omit<TaskSummary, "status" | "title" | "objective"> & {
    readonly title: string;
    readonly objective: string;
  },
): TaskSummary {
  if (
    input.sourceThread.sourceId !== input.run.sourceId ||
    input.sourceThread.threadId !== input.run.threadId ||
    input.lastEvent.sourceId !== input.sourceThread.sourceId ||
    input.lastEvent.taskId !== input.taskId ||
    input.lastEvent.threadId !== input.sourceThread.threadId ||
    input.lastEvent.runId !== input.run.runId ||
    input.lastEvent.eventId !== String(input.lastEventSequence)
  ) {
    throw new TypeError("Task summary identity and event cursor are incoherent.");
  }
  if (!taskFactsAreCoherent(input.facts)) {
    throw new TypeError("Task lifecycle facts are incoherent.");
  }
  const facts = Object.freeze({ ...input.facts });
  return Object.freeze({
    ...input,
    title: displayText(input.title, "Task title", 80),
    objective: objectiveText(input.objective),
    facts,
    status: deriveTaskStatus(facts),
    lastEventSequence: positiveEventSequence(input.lastEventSequence, "Last event sequence"),
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
  const matchesTaskBinding = (key: SourceEvidenceKey | SourceInterruptKey): boolean =>
    key.sourceId === summary.sourceThread.sourceId &&
    key.taskId === summary.taskId &&
    key.threadId === summary.sourceThread.threadId &&
    key.runId === summary.run.runId;
  if (
    input.evidence.some(
      (record) =>
        !matchesTaskBinding(record.identity) ||
        record.provenance.sourceThread.sourceId !== summary.sourceThread.sourceId ||
        record.provenance.sourceThread.threadId !== summary.sourceThread.threadId ||
        (record.provenance.observedThrough === "application-event" &&
          record.provenance.evidenceClass !== "fixture"),
    ) ||
    input.proposedPlan?.evidenceRefs.some((reference) => !matchesTaskBinding(reference)) === true ||
    (input.pendingInterrupt !== undefined &&
      (!matchesTaskBinding(input.pendingInterrupt.identity) ||
        input.proposedPlan === undefined ||
        input.pendingInterrupt.planRevision !== input.proposedPlan.revision)) ||
    summary.facts.pendingCurrentInterrupt !== (input.pendingInterrupt !== undefined) ||
    summary.facts.terminalSuccess !== (input.result !== undefined)
  ) {
    throw new TypeError("Task detail nested state is incoherent.");
  }
  return Object.freeze({
    ...summary,
    ...(input.pendingInterrupt === undefined ? {} : { pendingInterrupt: input.pendingInterrupt }),
    ...(input.proposedPlan === undefined ? {} : { proposedPlan: input.proposedPlan }),
    evidence: Object.freeze([...input.evidence]),
    ...(input.result === undefined ? {} : { result: resultText(input.result) }),
  });
}

export function taskResult(
  input: Omit<TaskResult, "status" | "result"> & {
    readonly result: string;
  },
): TaskResult {
  return Object.freeze({
    ...input,
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
    interrupt: input.interrupt,
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
    interrupt: input.interrupt,
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

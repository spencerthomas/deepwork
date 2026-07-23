import {
  sourceApplicationEventKeyString,
  sourceRunKeyString,
  sourceThreadKeyString,
  type SourceApplicationEventKey,
} from "./identity.js";
import type {
  EvidenceRecord,
  PendingInterrupt,
  ProposedPlan,
  TaskApplicationEvent,
  TaskDetail,
  TaskResult,
  TaskStateFacts,
} from "./task-model.js";
import type { SourceInterruptKey } from "./identity.js";
import {
  deriveTaskStatus,
  EVENT_SEQUENCE_MAX,
  PLAN_REVISION_MAX,
  TASK_EVIDENCE_MAX_COUNT,
} from "./task-model.js";
import type { TaskStatus } from "./view-state.js";

export const TASK_SOURCE_HEALTH_STATES = Object.freeze([
  "healthy",
  "degraded",
  "unavailable",
  "permission-denied",
] as const);

export type TaskSourceHealth = (typeof TASK_SOURCE_HEALTH_STATES)[number];

export type TaskProjectionFacts = TaskStateFacts;

export interface TaskProjection {
  readonly task: TaskDetail;
  readonly status: TaskStatus;
  readonly facts: TaskProjectionFacts;
  readonly reconnecting: boolean;
  readonly stale: boolean;
  readonly quarantined: boolean;
  readonly recovered: boolean;
  readonly sourceHealth: TaskSourceHealth;
  readonly planRevision?: number;
  readonly lastAppliedEvent: SourceApplicationEventKey;
  readonly lastAppliedSequence: number;
  readonly seenEventFingerprints: readonly TaskEventFingerprint[];
}

export interface TaskEventFingerprint {
  readonly key: string;
  readonly fingerprint: string | null;
}

const MAX_SEEN_EVENT_KEYS = 2_048;
const MAX_EVENT_FINGERPRINT_CODE_UNITS = 100_000;

function factsFromTask(task: TaskDetail): TaskProjectionFacts {
  return task.facts;
}

function freezeProjection(input: {
  readonly task: TaskDetail;
  readonly facts: TaskProjectionFacts;
  readonly reconnecting: boolean;
  readonly stale: boolean;
  readonly quarantined: boolean;
  readonly recovered: boolean;
  readonly sourceHealth: TaskSourceHealth;
  readonly planRevision?: number;
  readonly lastAppliedEvent: SourceApplicationEventKey;
  readonly lastAppliedSequence: number;
  readonly seenEventFingerprints: readonly TaskEventFingerprint[];
}): TaskProjection {
  return Object.freeze({
    ...input,
    recovered: input.reconnecting || input.stale ? false : input.recovered,
    status: deriveTaskStatus(input.facts),
    facts: Object.freeze({ ...input.facts }),
    seenEventFingerprints: Object.freeze(
      input.seenEventFingerprints.map((entry) => Object.freeze({ ...entry })),
    ),
  });
}

export function createTaskProjection(task: TaskDetail): TaskProjection {
  if (!taskBaseBindingValid(task) || !taskNestedBindingsValid(task)) {
    throw new TypeError("Task detail identity bindings are incoherent.");
  }
  const facts = factsFromTask(task);
  return freezeProjection({
    task,
    facts,
    reconnecting: false,
    stale: false,
    quarantined: false,
    recovered: false,
    sourceHealth: "healthy",
    ...(task.proposedPlan === undefined ? {} : { planRevision: task.proposedPlan.revision }),
    lastAppliedEvent: task.lastEvent,
    lastAppliedSequence: task.lastEventSequence,
    seenEventFingerprints: [
      Object.freeze({
        key: sourceApplicationEventKeyString(task.lastEvent),
        fingerprint: null,
      }),
    ],
  });
}

export function setTaskReconnecting(
  projection: TaskProjection,
  reconnecting: boolean,
): TaskProjection {
  if (projection.reconnecting === reconnecting) {
    return projection;
  }
  return freezeProjection({
    ...projection,
    reconnecting,
  });
}

export function setTaskSourceHealth(
  projection: TaskProjection,
  sourceHealth: TaskSourceHealth,
): TaskProjection {
  if (!(TASK_SOURCE_HEALTH_STATES as readonly string[]).includes(sourceHealth)) {
    throw new TypeError("Task source health is not accepted.");
  }
  if (projection.sourceHealth === sourceHealth) {
    return projection;
  }
  return freezeProjection({
    ...projection,
    sourceHealth,
  });
}

export function markTaskStale(projection: TaskProjection): TaskProjection {
  if (projection.stale) {
    return projection;
  }
  return freezeProjection({ ...projection, stale: true });
}

export function quarantineTaskProjection(projection: TaskProjection): TaskProjection {
  if (projection.quarantined && projection.stale && projection.reconnecting) {
    return projection;
  }
  return freezeProjection({
    ...projection,
    quarantined: true,
    stale: true,
    reconnecting: true,
  });
}

function sameBinding(projection: TaskProjection, event: TaskApplicationEvent): boolean {
  return (
    projection.task.taskId === event.taskId &&
    event.identity.taskId === event.taskId &&
    event.identity.sourceId === event.sourceThread.sourceId &&
    event.identity.threadId === event.sourceThread.threadId &&
    event.identity.runId === event.run.runId &&
    event.identity.eventId === String(event.sequence) &&
    Number.isSafeInteger(event.sequence) &&
    event.sequence >= 1 &&
    event.sequence <= EVENT_SEQUENCE_MAX &&
    event.run.sourceId === event.sourceThread.sourceId &&
    event.run.threadId === event.sourceThread.threadId &&
    sourceThreadKeyString(projection.task.sourceThread) ===
      sourceThreadKeyString(event.sourceThread) &&
    sourceRunKeyString(projection.task.run) === sourceRunKeyString(event.run)
  );
}

function taskBaseBindingValid(task: TaskDetail): boolean {
  return (
    task.sourceThread.sourceId === task.run.sourceId &&
    task.sourceThread.threadId === task.run.threadId &&
    task.lastEvent.sourceId === task.sourceThread.sourceId &&
    task.lastEvent.taskId === task.taskId &&
    task.lastEvent.threadId === task.sourceThread.threadId &&
    task.lastEvent.runId === task.run.runId &&
    task.lastEvent.eventId === String(task.lastEventSequence)
  );
}

function appendEventFingerprint(
  entries: readonly TaskEventFingerprint[],
  entry: TaskEventFingerprint,
): readonly TaskEventFingerprint[] {
  const appended = [...entries, Object.freeze({ ...entry })];
  return Object.freeze(
    appended.length > MAX_SEEN_EVENT_KEYS
      ? appended.slice(appended.length - MAX_SEEN_EVENT_KEYS)
      : appended,
  );
}

function canonicalFingerprint(value: unknown, seen: Set<object>, depth: number): string {
  if (depth > 12) {
    throw new TypeError("Task event fingerprint is too deeply nested.");
  }
  if (value === null || typeof value === "boolean") {
    return JSON.stringify(value);
  }
  if (typeof value === "string") {
    return JSON.stringify(value);
  }
  if (typeof value === "number" && Number.isFinite(value)) {
    return JSON.stringify(value);
  }
  if (typeof value !== "object") {
    throw new TypeError("Task event fingerprint contains an unsupported value.");
  }
  if (seen.has(value)) {
    throw new TypeError("Task event fingerprint contains a cycle.");
  }
  seen.add(value);
  const fingerprint = Array.isArray(value)
    ? `[${value.map((entry) => canonicalFingerprint(entry, seen, depth + 1)).join(",")}]`
    : `{${Object.keys(value)
        .sort()
        .map(
          (key) =>
            `${JSON.stringify(key)}:${canonicalFingerprint(
              (value as Record<string, unknown>)[key],
              seen,
              depth + 1,
            )}`,
        )
        .join(",")}}`;
  seen.delete(value);
  if (fingerprint.length > MAX_EVENT_FINGERPRINT_CODE_UNITS) {
    throw new TypeError("Task event fingerprint exceeds its accepted bound.");
  }
  return fingerprint;
}

function taskEventFingerprint(event: TaskApplicationEvent): string | undefined {
  try {
    return canonicalFingerprint(event, new Set<object>(), 0);
  } catch {
    return undefined;
  }
}

function samePlan(first: ProposedPlan, second: ProposedPlan): boolean {
  return (
    first.revision === second.revision &&
    first.title === second.title &&
    first.steps.length === second.steps.length &&
    first.steps.every((step, index) => step === second.steps[index]) &&
    first.evidenceRefs.length === second.evidenceRefs.length &&
    first.evidenceRefs.every(
      (reference, index) =>
        reference.sourceId === second.evidenceRefs[index]?.sourceId &&
        reference.taskId === second.evidenceRefs[index]?.taskId &&
        reference.threadId === second.evidenceRefs[index]?.threadId &&
        reference.runId === second.evidenceRefs[index]?.runId &&
        reference.evidenceId === second.evidenceRefs[index]?.evidenceId,
    )
  );
}

function sameEvidence(first: EvidenceRecord, second: EvidenceRecord): boolean {
  return (
    first.identity.sourceId === second.identity.sourceId &&
    first.identity.taskId === second.identity.taskId &&
    first.identity.threadId === second.identity.threadId &&
    first.identity.runId === second.identity.runId &&
    first.identity.evidenceId === second.identity.evidenceId &&
    first.kind === second.kind &&
    first.summary === second.summary &&
    first.source === second.source &&
    first.verified === second.verified &&
    sourceThreadKeyString(first.provenance.sourceThread) ===
      sourceThreadKeyString(second.provenance.sourceThread) &&
    first.provenance.observedThrough === second.provenance.observedThrough &&
    first.provenance.evidenceClass === second.provenance.evidenceClass
  );
}

function sameInterrupt(first: PendingInterrupt, second: PendingInterrupt): boolean {
  return (
    first.identity.sourceId === second.identity.sourceId &&
    first.identity.taskId === second.identity.taskId &&
    first.identity.threadId === second.identity.threadId &&
    first.identity.runId === second.identity.runId &&
    first.identity.interruptId === second.identity.interruptId
  );
}

function samePendingInterrupt(
  first: PendingInterrupt | undefined,
  second: PendingInterrupt | undefined,
): boolean {
  if (first === undefined || second === undefined) {
    return first === second;
  }
  return (
    sameInterrupt(first, second) &&
    first.planRevision === second.planRevision &&
    first.question === second.question &&
    first.decisions.length === second.decisions.length &&
    first.decisions.every((decision, index) => decision === second.decisions[index])
  );
}

function sameFacts(first: TaskProjectionFacts, second: TaskProjectionFacts): boolean {
  return (
    first.cancellationConfirmed === second.cancellationConfirmed &&
    first.pendingCurrentInterrupt === second.pendingCurrentInterrupt &&
    first.runActive === second.runActive &&
    first.queued === second.queued &&
    first.terminalFailure === second.terminalFailure &&
    first.terminalSuccess === second.terminalSuccess
  );
}

function evidenceBindingMatches(task: TaskDetail, evidence: EvidenceRecord): boolean {
  return (
    evidence.identity.sourceId === task.sourceThread.sourceId &&
    evidence.identity.taskId === task.taskId &&
    evidence.identity.threadId === task.sourceThread.threadId &&
    evidence.identity.runId === task.run.runId &&
    sourceThreadKeyString(evidence.provenance.sourceThread) ===
      sourceThreadKeyString(task.sourceThread) &&
    (evidence.provenance.observedThrough !== "application-event" ||
      evidence.provenance.evidenceClass === "fixture")
  );
}

function planBindingsMatch(task: TaskDetail, plan: ProposedPlan): boolean {
  return (
    Number.isSafeInteger(plan.revision) &&
    plan.revision >= 1 &&
    plan.revision <= PLAN_REVISION_MAX &&
    plan.evidenceRefs.every(
      (reference) =>
        reference.sourceId === task.sourceThread.sourceId &&
        reference.taskId === task.taskId &&
        reference.threadId === task.sourceThread.threadId &&
        reference.runId === task.run.runId,
    )
  );
}

function interruptIdentityBindingMatches(task: TaskDetail, identity: SourceInterruptKey): boolean {
  return (
    identity.sourceId === task.sourceThread.sourceId &&
    identity.taskId === task.taskId &&
    identity.threadId === task.sourceThread.threadId &&
    identity.runId === task.run.runId
  );
}

function interruptBindingMatches(task: TaskDetail, interrupt: PendingInterrupt): boolean {
  return (
    interruptIdentityBindingMatches(task, interrupt.identity) &&
    Number.isSafeInteger(interrupt.planRevision) &&
    interrupt.planRevision >= 1 &&
    interrupt.planRevision <= PLAN_REVISION_MAX
  );
}

function taskNestedBindingsValid(task: TaskDetail): boolean {
  return (
    task.evidence.every((evidence) => evidenceBindingMatches(task, evidence)) &&
    (task.proposedPlan === undefined || planBindingsMatch(task, task.proposedPlan)) &&
    (task.pendingInterrupt === undefined ||
      (interruptBindingMatches(task, task.pendingInterrupt) &&
        task.proposedPlan !== undefined &&
        task.pendingInterrupt.planRevision === task.proposedPlan.revision))
  );
}

function eventNestedBindingsValid(
  projection: TaskProjection,
  event: TaskApplicationEvent,
): boolean {
  switch (event.name) {
    case "plan.proposed":
    case "plan.updated":
      return planBindingsMatch(projection.task, event.plan);
    case "evidence.recorded":
      return (
        evidenceBindingMatches(projection.task, event.evidence) &&
        event.evidence.provenance.observedThrough === "application-event" &&
        event.evidence.provenance.evidenceClass === "fixture"
      );
    case "interrupt.requested":
      return (
        interruptBindingMatches(projection.task, event.interrupt) &&
        projection.task.proposedPlan !== undefined &&
        event.interrupt.planRevision === projection.task.proposedPlan.revision
      );
    case "decision.recorded":
      return (
        interruptIdentityBindingMatches(projection.task, event.interrupt) &&
        projection.task.pendingInterrupt !== undefined &&
        projection.task.pendingInterrupt.decisions.includes(event.decision) &&
        (event.decision === "respond") === event.responseProvided &&
        (event.decision !== "respond" || (event.commentProvided && event.responseProvided))
      );
    case "run.completed":
      return (event.outcome === "success") === event.resultAvailable;
    default:
      return true;
  }
}

function transitionAllowed(projection: TaskProjection, event: TaskApplicationEvent): boolean {
  if (projection.facts.pendingCurrentInterrupt) {
    return (
      event.name === "plan.updated" ||
      event.name === "decision.recorded" ||
      event.name === "run.completed"
    );
  }
  if (projection.facts.runActive) {
    return (
      event.name === "content.delta" ||
      event.name === "evidence.recorded" ||
      event.name === "plan.proposed" ||
      event.name === "interrupt.requested" ||
      event.name === "run.completed"
    );
  }
  if (projection.facts.queued) {
    return event.name === "run.started";
  }
  return false;
}

function sameTaskDetail(first: TaskDetail, second: TaskDetail): boolean {
  return (
    first.taskId === second.taskId &&
    sourceThreadKeyString(first.sourceThread) === sourceThreadKeyString(second.sourceThread) &&
    sourceRunKeyString(first.run) === sourceRunKeyString(second.run) &&
    first.title === second.title &&
    first.objective === second.objective &&
    first.status === second.status &&
    sameFacts(first.facts, second.facts) &&
    sourceApplicationEventKeyString(first.lastEvent) ===
      sourceApplicationEventKeyString(second.lastEvent) &&
    first.lastEventSequence === second.lastEventSequence &&
    samePendingInterrupt(first.pendingInterrupt, second.pendingInterrupt) &&
    (first.proposedPlan === undefined || second.proposedPlan === undefined
      ? first.proposedPlan === second.proposedPlan
      : samePlan(first.proposedPlan, second.proposedPlan)) &&
    first.evidence.length === second.evidence.length &&
    first.evidence.every(
      (record, index) =>
        second.evidence[index] !== undefined && sameEvidence(record, second.evidence[index]),
    ) &&
    first.result === second.result
  );
}

function eventTask(
  projection: TaskProjection,
  event: TaskApplicationEvent,
): {
  readonly task: TaskDetail;
  readonly facts: TaskProjectionFacts;
  readonly planRevision?: number;
  readonly stale: boolean;
  readonly quarantined: boolean;
} {
  let task = projection.task;
  let facts = projection.facts;
  let planRevision = projection.planRevision;
  let stale = projection.stale;
  let quarantined = projection.quarantined;

  switch (event.name) {
    case "task.created":
      facts = Object.freeze({
        cancellationConfirmed: false,
        pendingCurrentInterrupt: false,
        runActive: false,
        queued: true,
        terminalFailure: false,
        terminalSuccess: false,
      });
      task = Object.freeze({
        ...task,
        facts,
        status: deriveTaskStatus(facts),
      });
      break;
    case "run.started":
    case "content.delta":
      facts = Object.freeze({
        ...facts,
        runActive: true,
        queued: false,
        terminalFailure: false,
        terminalSuccess: false,
      });
      task = Object.freeze({
        ...task,
        facts,
        status: deriveTaskStatus(facts),
      });
      break;
    case "plan.proposed":
    case "plan.updated": {
      const current = task.proposedPlan;
      if (current === undefined || event.plan.revision > current.revision) {
        task = Object.freeze({
          ...task,
          proposedPlan: event.plan,
          ...(event.name === "plan.updated" && task.pendingInterrupt !== undefined
            ? {
                pendingInterrupt: Object.freeze({
                  ...task.pendingInterrupt,
                  planRevision: event.plan.revision,
                }),
              }
            : {}),
        });
        planRevision = event.plan.revision;
      } else if (event.plan.revision < current.revision || !samePlan(event.plan, current)) {
        stale = true;
      }
      facts = Object.freeze({
        ...facts,
        runActive: true,
        queued: false,
      });
      break;
    }
    case "evidence.recorded": {
      const existing = task.evidence.find(
        (record) =>
          record.identity.sourceId === event.evidence.identity.sourceId &&
          record.identity.taskId === event.evidence.identity.taskId &&
          record.identity.threadId === event.evidence.identity.threadId &&
          record.identity.runId === event.evidence.identity.runId &&
          record.identity.evidenceId === event.evidence.identity.evidenceId,
      );
      if (existing === undefined) {
        if (task.evidence.length >= TASK_EVIDENCE_MAX_COUNT) {
          stale = true;
          quarantined = true;
        } else {
          task = Object.freeze({
            ...task,
            evidence: Object.freeze([...task.evidence, event.evidence]),
          });
        }
      } else if (!sameEvidence(existing, event.evidence)) {
        stale = true;
      }
      break;
    }
    case "interrupt.requested": {
      const current = task.pendingInterrupt;
      if (current !== undefined && current.planRevision > event.interrupt.planRevision) {
        stale = true;
        break;
      }
      if (
        current !== undefined &&
        current.planRevision === event.interrupt.planRevision &&
        !samePendingInterrupt(current, event.interrupt)
      ) {
        stale = true;
        break;
      }
      task = Object.freeze({
        ...task,
        pendingInterrupt: event.interrupt,
      });
      facts = Object.freeze({
        ...facts,
        pendingCurrentInterrupt: true,
        runActive: true,
        queued: false,
      });
      task = Object.freeze({
        ...task,
        facts,
        status: deriveTaskStatus(facts),
      });
      break;
    }
    case "decision.recorded": {
      const current = task.pendingInterrupt;
      if (
        current === undefined ||
        !sameInterrupt(current, {
          identity: event.interrupt,
          decisions: current.decisions,
          planRevision: current.planRevision,
        })
      ) {
        stale = true;
        break;
      }
      facts = Object.freeze({
        ...facts,
        pendingCurrentInterrupt: false,
        runActive: true,
        queued: false,
      });
      const { pendingInterrupt: _removedInterrupt, ...taskWithoutInterrupt } = task;
      task = Object.freeze({
        ...taskWithoutInterrupt,
        facts,
        status: deriveTaskStatus(facts),
      });
      break;
    }
    case "run.completed":
      facts = Object.freeze({
        cancellationConfirmed: false,
        pendingCurrentInterrupt: false,
        runActive: false,
        queued: false,
        terminalFailure: event.outcome === "failure" || event.outcome === "rejected",
        terminalSuccess: event.outcome === "success",
      });
      {
        const { pendingInterrupt: _removedInterrupt, ...taskWithoutInterrupt } = task;
        task = Object.freeze({
          ...taskWithoutInterrupt,
          facts,
          status: deriveTaskStatus(facts),
        });
      }
      break;
  }

  task = Object.freeze({
    ...task,
    facts,
    status: deriveTaskStatus(facts),
  });

  return {
    task,
    facts,
    ...(planRevision === undefined ? {} : { planRevision }),
    stale,
    quarantined,
  };
}

export function reduceTaskEvent(
  projection: TaskProjection,
  event: TaskApplicationEvent,
): TaskProjection {
  if (projection.quarantined) {
    return projection;
  }
  if (!sameBinding(projection, event)) {
    return quarantineTaskProjection(projection);
  }
  if (
    !taskBaseBindingValid(projection.task) ||
    !taskNestedBindingsValid(projection.task) ||
    !eventNestedBindingsValid(projection, event)
  ) {
    return quarantineTaskProjection(projection);
  }

  const eventKey = sourceApplicationEventKeyString(event.identity);
  const fingerprint = taskEventFingerprint(event);
  if (fingerprint === undefined) {
    return quarantineTaskProjection(projection);
  }
  const seen = projection.seenEventFingerprints.find((entry) => entry.key === eventKey);
  if (seen !== undefined) {
    return seen.fingerprint === null || seen.fingerprint === fingerprint
      ? projection
      : quarantineTaskProjection(projection);
  }
  if (
    projection.facts.cancellationConfirmed ||
    projection.facts.terminalFailure ||
    projection.facts.terminalSuccess
  ) {
    return quarantineTaskProjection(projection);
  }
  if (!transitionAllowed(projection, event)) {
    return quarantineTaskProjection(projection);
  }
  if (event.sequence < projection.lastAppliedSequence) {
    return quarantineTaskProjection(projection);
  }
  if (event.sequence === projection.lastAppliedSequence) {
    return quarantineTaskProjection(projection);
  }
  if (event.sequence !== projection.lastAppliedSequence + 1) {
    return quarantineTaskProjection(projection);
  }
  if (
    event.name === "evidence.recorded" &&
    projection.task.evidence.length >= TASK_EVIDENCE_MAX_COUNT &&
    !projection.task.evidence.some(
      (record) =>
        record.identity.sourceId === event.evidence.identity.sourceId &&
        record.identity.taskId === event.evidence.identity.taskId &&
        record.identity.threadId === event.evidence.identity.threadId &&
        record.identity.runId === event.evidence.identity.runId &&
        record.identity.evidenceId === event.evidence.identity.evidenceId,
    )
  ) {
    return quarantineTaskProjection(projection);
  }

  const applied = eventTask(projection, event);
  const task = Object.freeze({
    ...applied.task,
    lastEvent: event.identity,
    lastEventSequence: event.sequence,
  });
  return freezeProjection({
    task,
    facts: applied.facts,
    reconnecting: projection.reconnecting,
    stale: applied.stale,
    quarantined: applied.quarantined,
    recovered: projection.recovered,
    sourceHealth: projection.sourceHealth,
    ...(applied.planRevision === undefined ? {} : { planRevision: applied.planRevision }),
    lastAppliedEvent: event.identity,
    lastAppliedSequence: event.sequence,
    seenEventFingerprints: appendEventFingerprint(projection.seenEventFingerprints, {
      key: eventKey,
      fingerprint,
    }),
  });
}

export function reduceTaskEvents(
  projection: TaskProjection,
  events: readonly TaskApplicationEvent[],
): TaskProjection {
  return events.reduce(reduceTaskEvent, projection);
}

export function reconcileTaskProjection(
  projection: TaskProjection,
  hydrated: TaskDetail,
): TaskProjection {
  if (
    projection.task.taskId !== hydrated.taskId ||
    sourceThreadKeyString(projection.task.sourceThread) !==
      sourceThreadKeyString(hydrated.sourceThread) ||
    sourceRunKeyString(projection.task.run) !== sourceRunKeyString(hydrated.run)
  ) {
    return markTaskStale(projection);
  }
  if (!taskBaseBindingValid(hydrated) || !taskNestedBindingsValid(hydrated)) {
    return quarantineTaskProjection(projection);
  }
  if (hydrated.lastEventSequence < projection.lastAppliedSequence) {
    return markTaskStale(projection);
  }
  if (
    hydrated.lastEventSequence === projection.lastAppliedSequence &&
    !sameTaskDetail(projection.task, hydrated)
  ) {
    return quarantineTaskProjection(projection);
  }

  const facts = factsFromTask(hydrated);
  return freezeProjection({
    task: hydrated,
    facts,
    reconnecting: false,
    stale: false,
    quarantined: false,
    recovered: true,
    sourceHealth: projection.sourceHealth,
    ...(hydrated.proposedPlan === undefined
      ? {}
      : { planRevision: hydrated.proposedPlan.revision }),
    lastAppliedEvent: hydrated.lastEvent,
    lastAppliedSequence: hydrated.lastEventSequence,
    seenEventFingerprints: appendEventFingerprint(
      projection.seenEventFingerprints.filter(
        (entry) => entry.key !== sourceApplicationEventKeyString(hydrated.lastEvent),
      ),
      {
        key: sourceApplicationEventKeyString(hydrated.lastEvent),
        fingerprint: null,
      },
    ),
  });
}

export function withTaskResult(projection: TaskProjection, result: TaskResult): TaskProjection {
  if (!projection.facts.terminalSuccess) {
    throw new TypeError("A task result can be attached only after authoritative success.");
  }
  if (
    result.taskId !== projection.task.taskId ||
    sourceRunKeyString(result.run) !== sourceRunKeyString(projection.task.run)
  ) {
    throw new TypeError("Task result identity does not match the task projection.");
  }
  return freezeProjection({
    ...projection,
    task: Object.freeze({ ...projection.task, result: result.result }),
  });
}

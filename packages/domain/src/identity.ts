declare const sourceIdBrand: unique symbol;
declare const threadIdBrand: unique symbol;
declare const runIdBrand: unique symbol;
declare const taskIdBrand: unique symbol;
declare const interruptIdBrand: unique symbol;
declare const evidenceIdBrand: unique symbol;
declare const applicationEventIdBrand: unique symbol;

export type SourceId = string & { readonly [sourceIdBrand]: "SourceId" };
export type ThreadId = string & { readonly [threadIdBrand]: "ThreadId" };
export type RunId = string & { readonly [runIdBrand]: "RunId" };
export type TaskId = string & { readonly [taskIdBrand]: "TaskId" };
export type InterruptId = string & {
  readonly [interruptIdBrand]: "InterruptId";
};
export type EvidenceId = string & { readonly [evidenceIdBrand]: "EvidenceId" };
export type ApplicationEventId = string & {
  readonly [applicationEventIdBrand]: "ApplicationEventId";
};

export interface SourceThreadKey {
  readonly sourceId: SourceId;
  readonly threadId: ThreadId;
}

export interface SourceRunKey extends SourceThreadKey {
  readonly runId: RunId;
}

export interface SourceInterruptKey extends SourceRunKey {
  readonly taskId: TaskId;
  readonly interruptId: InterruptId;
}

export interface SourceEvidenceKey extends SourceRunKey {
  readonly taskId: TaskId;
  readonly evidenceId: EvidenceId;
}

export interface SourceApplicationEventKey extends SourceRunKey {
  readonly taskId: TaskId;
  readonly eventId: ApplicationEventId;
}

export const OPAQUE_ID_MAX_CODE_POINTS = 200;

function opaqueIdentifier<T extends string>(value: string, label: string): T {
  if (
    value.length === 0 ||
    [...value].length > OPAQUE_ID_MAX_CODE_POINTS ||
    value.trim() !== value ||
    [...value].some((character) => {
      const codePoint = character.codePointAt(0) ?? 0;
      return (
        codePoint < 32 ||
        (codePoint >= 127 && codePoint <= 159) ||
        (codePoint >= 0xd800 && codePoint <= 0xdfff)
      );
    })
  ) {
    throw new TypeError(
      `${label} must be a non-empty, trimmed opaque value of at most ${OPAQUE_ID_MAX_CODE_POINTS} Unicode code points.`,
    );
  }

  return value as T;
}

export function sourceId(value: string): SourceId {
  return opaqueIdentifier<SourceId>(value, "Source identifier");
}

export function threadId(value: string): ThreadId {
  return opaqueIdentifier<ThreadId>(value, "Thread identifier");
}

export function runId(value: string): RunId {
  return opaqueIdentifier<RunId>(value, "Run identifier");
}

export function taskId(value: string): TaskId {
  return opaqueIdentifier<TaskId>(value, "Task identifier");
}

export function interruptId(value: string): InterruptId {
  return opaqueIdentifier<InterruptId>(value, "Interrupt identifier");
}

export function evidenceId(value: string): EvidenceId {
  return opaqueIdentifier<EvidenceId>(value, "Evidence identifier");
}

export function applicationEventId(value: string): ApplicationEventId {
  return opaqueIdentifier<ApplicationEventId>(value, "Application event identifier");
}

export function sourceThreadKey(source: SourceId, thread: ThreadId): SourceThreadKey {
  return Object.freeze({ sourceId: source, threadId: thread });
}

export function sourceRunKey(source: SourceId, thread: ThreadId, run: RunId): SourceRunKey {
  return Object.freeze({ sourceId: source, threadId: thread, runId: run });
}

export function sourceInterruptKey(
  source: SourceId,
  task: TaskId,
  thread: ThreadId,
  run: RunId,
  interrupt: InterruptId,
): SourceInterruptKey {
  return Object.freeze({
    sourceId: source,
    taskId: task,
    threadId: thread,
    runId: run,
    interruptId: interrupt,
  });
}

export function sourceEvidenceKey(
  source: SourceId,
  task: TaskId,
  thread: ThreadId,
  run: RunId,
  evidence: EvidenceId,
): SourceEvidenceKey {
  return Object.freeze({
    sourceId: source,
    taskId: task,
    threadId: thread,
    runId: run,
    evidenceId: evidence,
  });
}

export function sourceApplicationEventKey(
  source: SourceId,
  task: TaskId,
  thread: ThreadId,
  run: RunId,
  event: ApplicationEventId,
): SourceApplicationEventKey {
  return Object.freeze({
    sourceId: source,
    taskId: task,
    threadId: thread,
    runId: run,
    eventId: event,
  });
}

function encode(value: string): string {
  return encodeURIComponent(value);
}

export function sourceThreadKeyString(key: SourceThreadKey): string {
  return `thread:${encode(key.sourceId)}:${encode(key.threadId)}`;
}

export function sourceRunKeyString(key: SourceRunKey): string {
  return `run:${encode(key.sourceId)}:${encode(key.threadId)}:${encode(key.runId)}`;
}

export function sourceInterruptKeyString(key: SourceInterruptKey): string {
  return `interrupt:${encode(key.sourceId)}:${encode(key.taskId)}:${encode(key.threadId)}:${encode(key.runId)}:${encode(key.interruptId)}`;
}

export function sourceEvidenceKeyString(key: SourceEvidenceKey): string {
  return `evidence:${encode(key.sourceId)}:${encode(key.taskId)}:${encode(key.threadId)}:${encode(key.runId)}:${encode(key.evidenceId)}`;
}

export function sourceApplicationEventKeyString(key: SourceApplicationEventKey): string {
  return `event:${encode(key.sourceId)}:${encode(key.taskId)}:${encode(key.threadId)}:${encode(key.runId)}:${encode(key.eventId)}`;
}

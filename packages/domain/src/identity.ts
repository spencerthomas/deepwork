declare const sourceIdBrand: unique symbol;
declare const threadIdBrand: unique symbol;
declare const runIdBrand: unique symbol;

export type SourceId = string & { readonly [sourceIdBrand]: "SourceId" };
export type ThreadId = string & { readonly [threadIdBrand]: "ThreadId" };
export type RunId = string & { readonly [runIdBrand]: "RunId" };

export interface SourceThreadKey {
  readonly sourceId: SourceId;
  readonly threadId: ThreadId;
}

export interface SourceRunKey extends SourceThreadKey {
  readonly runId: RunId;
}

function opaqueIdentifier<T extends string>(value: string, label: string): T {
  if (value.length === 0 || value.trim() !== value) {
    throw new TypeError(`${label} must be a non-empty, trimmed opaque value.`);
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

export function sourceThreadKey(
  source: SourceId,
  thread: ThreadId,
): SourceThreadKey {
  return Object.freeze({ sourceId: source, threadId: thread });
}

export function sourceRunKey(
  source: SourceId,
  thread: ThreadId,
  run: RunId,
): SourceRunKey {
  return Object.freeze({ sourceId: source, threadId: thread, runId: run });
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

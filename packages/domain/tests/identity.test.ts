import {
  applicationEventId,
  evidenceId,
  interruptId,
  OPAQUE_ID_MAX_CODE_POINTS,
  runId,
  sourceId,
  sourceApplicationEventKey,
  sourceApplicationEventKeyString,
  sourceEvidenceKey,
  sourceEvidenceKeyString,
  sourceRunKey,
  sourceRunKeyString,
  sourceThreadKey,
  sourceThreadKeyString,
  taskId,
  threadId,
} from "@deepwork/domain";
import { describe, expect, it } from "vitest";

describe("source-qualified identity", () => {
  it("keeps identical upstream identifiers distinct across sources", () => {
    const upstreamThread = threadId("same-upstream-thread");
    const first = sourceThreadKey(sourceId("source-a"), upstreamThread);
    const second = sourceThreadKey(sourceId("source-b"), upstreamThread);

    expect(sourceThreadKeyString(first)).not.toBe(sourceThreadKeyString(second));
  });

  it("keeps identical thread and run identifiers distinct across sources", () => {
    const upstreamThread = threadId("same-upstream-thread");
    const upstreamRun = runId("same-upstream-run");
    const first = sourceRunKey(sourceId("source-a"), upstreamThread, upstreamRun);
    const second = sourceRunKey(sourceId("source-b"), upstreamThread, upstreamRun);

    expect(sourceRunKeyString(first)).not.toBe(sourceRunKeyString(second));
  });

  it("keeps task-scoped SSE event identifiers distinct", () => {
    const source = sourceId("source-a");
    const thread = threadId("thread-1");
    const run = runId("run-1");
    const event = applicationEventId("1");
    const first = sourceApplicationEventKey(source, taskId("task_00000001"), thread, run, event);
    const second = sourceApplicationEventKey(source, taskId("task_00000002"), thread, run, event);

    expect(sourceApplicationEventKeyString(first)).not.toBe(
      sourceApplicationEventKeyString(second),
    );
  });

  it("keeps evidence provenance distinct across owning tasks and runs", () => {
    const source = sourceId("source-a");
    const thread = threadId("thread-1");
    const evidence = evidenceId("evidence_00000001");
    const first = sourceEvidenceKey(
      source,
      taskId("task_00000001"),
      thread,
      runId("run_00000001"),
      evidence,
    );
    const second = sourceEvidenceKey(
      source,
      taskId("task_00000002"),
      thread,
      runId("run_00000002"),
      evidence,
    );

    expect(sourceEvidenceKeyString(first)).not.toBe(sourceEvidenceKeyString(second));
  });

  it("serializes only qualified identity fields deterministically", () => {
    const key = sourceRunKey(sourceId("source-a"), threadId("thread-1"), runId("run-1"));

    expect(sourceRunKeyString(key)).toBe("run:source-a:thread-1:run-1");
    expect(sourceRunKeyString(key)).not.toContain("credential");
    expect(sourceRunKeyString(key)).not.toContain("content");
  });

  it("rejects empty and padded opaque identifiers", () => {
    expect(() => sourceId("")).toThrow(TypeError);
    expect(() => threadId(" thread-1")).toThrow(TypeError);
    expect(() => applicationEventId("event\n1")).toThrow(TypeError);
    expect(() => sourceId("\ud800")).toThrow(TypeError);
    expect(() => sourceId("\udc00")).toThrow(TypeError);
  });

  it("enforces one shared Unicode code-point bound for every opaque identifier", () => {
    const accepted = "😀".repeat(OPAQUE_ID_MAX_CODE_POINTS);
    const oversized = `${accepted}x`;
    const constructors = [
      sourceId,
      threadId,
      runId,
      taskId,
      interruptId,
      evidenceId,
      applicationEventId,
    ] as const;

    for (const construct of constructors) {
      expect(construct(accepted)).toBe(accepted);
      expect(() => construct(oversized)).toThrow(TypeError);
    }
  });
});

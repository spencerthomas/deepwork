import {
  runId,
  sourceId,
  sourceRunKey,
  sourceRunKeyString,
  sourceThreadKey,
  sourceThreadKeyString,
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
    const first = sourceRunKey(
      sourceId("source-a"),
      upstreamThread,
      upstreamRun,
    );
    const second = sourceRunKey(
      sourceId("source-b"),
      upstreamThread,
      upstreamRun,
    );

    expect(sourceRunKeyString(first)).not.toBe(sourceRunKeyString(second));
  });

  it("serializes only qualified identity fields deterministically", () => {
    const key = sourceRunKey(
      sourceId("source-a"),
      threadId("thread-1"),
      runId("run-1"),
    );

    expect(sourceRunKeyString(key)).toBe(
      "run:source-a:thread-1:run-1",
    );
    expect(sourceRunKeyString(key)).not.toContain("credential");
    expect(sourceRunKeyString(key)).not.toContain("content");
  });

  it("rejects empty and padded opaque identifiers", () => {
    expect(() => sourceId("")).toThrow(TypeError);
    expect(() => threadId(" thread-1")).toThrow(TypeError);
  });
});

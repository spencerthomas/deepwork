import {
  interruptId,
  runId,
  sourceId,
  sourceInterruptKey,
  sourceRunKey,
  sourceThreadKey,
  sourceThreadKeyString,
  taskId,
  threadId,
  type SourceThreadKey,
} from "@deepwork/domain";
import {
  createDecisionInput,
  createPlanEditInput,
  mapDecisionReceipt,
  mapPlanEditReceipt,
  mapTaskDetail,
  mapTaskEvent,
  mapTaskList,
  type TaskBindingResolver,
} from "@deepwork/sdk";
import { describe, expect, it } from "vitest";

const task = taskId("task_00000001");
const run = runId("run_00000001");

function resolver(sourceName: string): TaskBindingResolver {
  const binding = sourceThreadKey(sourceId(sourceName), threadId(`thread-${sourceName}`));
  return {
    resolveTask(requested) {
      return requested === task ? binding : undefined;
    },
  };
}

const waitingDetail = {
  taskId: "task_00000001",
  runId: "run_00000001",
  createdAt: "2026-01-01T00:00:00+00:00",
  title: "Review the task",
  objective: "Inspect the accepted task contract.",
  status: "waiting-approval",
  lastEventId: 4,
  pendingInterrupt: {
    interruptId: "interrupt_00000001",
    decisions: ["approve", "reject", "respond"],
    planRevision: 2,
  },
  proposedPlan: {
    revision: 2,
    title: "Inspect and answer",
    steps: ["Inspect the accepted contract"],
    evidenceRefs: ["evidence_00000001"],
  },
  evidence: [
    {
      evidenceId: "evidence_00000001",
      kind: "fixture",
      summary: "The accepted contract was inspected.",
      source: "deterministic-local-runner",
      verified: true,
    },
  ],
  result: null,
};

describe("strict accepted task mapping", () => {
  it("maps local wire status into canonical presentation facts", () => {
    const mapped = mapTaskDetail(waitingDetail, resolver("source-a"));

    expect(mapped).toMatchObject({
      ok: true,
      value: {
        status: "needs-review",
        facts: {
          pendingCurrentInterrupt: true,
          runActive: true,
        },
      },
    });
    if (!mapped.ok) {
      throw new Error("Expected accepted task detail.");
    }
    expect(mapped.value.pendingInterrupt?.identity.taskId).toBe(task);
    expect("taskRevision" in mapped.value).toBe(false);
    expect(mapped.value.lastEventSequence).toBe(4);
    expect(mapped.value.evidence[0]?.identity).toMatchObject({
      sourceId: "source-a",
      taskId: "task_00000001",
      threadId: "thread-source-a",
      runId: "run_00000001",
      evidenceId: "evidence_00000001",
    });
  });

  it("maps the accepted local-source identifiers and evidence class", () => {
    const localDetail = {
      ...waitingDetail,
      runId: "run-local:2",
      pendingInterrupt: {
        ...waitingDetail.pendingInterrupt,
        interruptId: "srcint-3",
      },
      proposedPlan: {
        ...waitingDetail.proposedPlan,
        evidenceRefs: [],
      },
      evidence: [],
    };
    const mapped = mapTaskDetail(localDetail, resolver("local-agent-server"));
    if (!mapped.ok) {
      throw new Error("Expected accepted local-source task detail.");
    }
    expect(mapped.value.run.runId).toBe("run-local:2");
    expect(mapped.value.pendingInterrupt?.identity.interruptId).toBe("srcint-3");

    const delta = mapTaskEvent(
      "content.delta",
      "5",
      {
        text: "Local Agent Server progress received.",
        evidenceClass: "local-source",
      },
      {
        taskId: mapped.value.taskId,
        sourceThread: mapped.value.sourceThread,
        run: mapped.value.run,
      },
    );
    expect(delta).toMatchObject({
      ok: true,
      value: { evidenceClass: "local-source" },
    });

    const plan = mapTaskEvent(
      "plan.proposed",
      "6",
      {
        title: "Local Agent Server plan",
        steps: ["Inspect the accepted contract"],
        revision: 2,
        evidenceRefs: [],
        evidenceClass: "local-source",
      },
      {
        taskId: mapped.value.taskId,
        sourceThread: mapped.value.sourceThread,
        run: mapped.value.run,
      },
    );
    expect(plan).toMatchObject({
      ok: true,
      value: { evidenceClass: "local-source" },
    });
  });

  it("clones only exact public binding fields and rejects incoherent event context", () => {
    const resolverWithPrivateFields: TaskBindingResolver = {
      resolveTask(requested) {
        return requested === task
          ? ({
              sourceId: sourceId("source-a"),
              threadId: threadId("thread-a"),
              authRef: "must-not-hitchhike",
            } as SourceThreadKey)
          : undefined;
      },
    };
    const mapped = mapTaskDetail(waitingDetail, resolverWithPrivateFields);
    if (!mapped.ok) {
      throw new Error("Expected accepted task detail.");
    }

    expect(Object.keys(mapped.value.sourceThread).sort()).toEqual(["sourceId", "threadId"]);
    expect(Object.keys(mapped.value.run).sort()).toEqual(["runId", "sourceId", "threadId"]);
    expect("authRef" in mapped.value.sourceThread).toBe(false);

    const incoherent = mapTaskEvent(
      "run.started",
      "5",
      { runId: "run_00000001", status: "running" },
      {
        taskId: task,
        sourceThread: sourceThreadKey(sourceId("source-a"), threadId("thread-a")),
        run: sourceRunKey(sourceId("source-b"), threadId("thread-b"), run),
      },
    );
    expect(incoherent).toMatchObject({ ok: false, error: { category: "contract" } });
  });

  it("fails closed on unknown values, missing bindings, and extra fields", () => {
    expect(
      mapTaskDetail({ ...waitingDetail, status: "complete-ish" }, resolver("source-a")),
    ).toMatchObject({ ok: false, error: { category: "contract" } });
    expect(
      mapTaskDetail(
        { ...waitingDetail, providerPayload: { secret: "blocked" } },
        resolver("source-a"),
      ),
    ).toMatchObject({ ok: false, error: { category: "contract" } });
    expect(mapTaskDetail(waitingDetail, { resolveTask: () => undefined })).toMatchObject({
      ok: false,
      error: { category: "contract" },
    });
  });

  it("keeps identical task/run/event strings distinct across source bindings", () => {
    const first = mapTaskDetail(waitingDetail, resolver("source-a"));
    const second = mapTaskDetail(waitingDetail, resolver("source-b"));
    if (!first.ok || !second.ok) {
      throw new Error("Expected accepted task details.");
    }

    expect(sourceThreadKeyString(first.value.sourceThread)).not.toBe(
      sourceThreadKeyString(second.value.sourceThread),
    );

    const firstEvent = mapTaskEvent(
      "run.started",
      "5",
      { runId: "run_00000001", status: "running" },
      {
        taskId: first.value.taskId,
        sourceThread: first.value.sourceThread,
        run: first.value.run,
      },
    );
    const secondEvent = mapTaskEvent(
      "run.started",
      "5",
      { runId: "run_00000001", status: "running" },
      {
        taskId: second.value.taskId,
        sourceThread: second.value.sourceThread,
        run: second.value.run,
      },
    );
    expect(firstEvent).toMatchObject({ ok: true });
    expect(secondEvent).toMatchObject({ ok: true });
    if (!firstEvent.ok || !secondEvent.ok) {
      throw new Error("Expected accepted events.");
    }
    expect(firstEvent.value.identity).not.toEqual(secondEvent.value.identity);
  });

  it("rejects malformed and unknown events without a partial value", () => {
    const sourceThread = sourceThreadKey(sourceId("source-a"), threadId("thread-a"));
    const context = {
      taskId: task,
      sourceThread,
      run: sourceRunKey(sourceThread.sourceId, sourceThread.threadId, run),
    };

    expect(mapTaskEvent("provider.raw", "1", { arbitrary: true }, context)).toMatchObject({
      ok: false,
      error: { retryable: false },
    });
    expect(
      mapTaskEvent(
        "decision.recorded",
        "2",
        {
          interruptId: "interrupt_00000001",
          decision: "respond",
          commentProvided: true,
          responseProvided: false,
        },
        context,
      ),
    ).toMatchObject({ ok: false, error: { category: "contract" } });
    expect(
      mapTaskEvent(
        "decision.recorded",
        "2",
        {
          interruptId: "interrupt_00000001",
          decision: "respond",
          commentProvided: false,
          responseProvided: true,
        },
        context,
      ),
    ).toMatchObject({ ok: false, error: { category: "contract" } });
    expect(
      mapTaskEvent(
        "run.completed",
        "3",
        {
          runId: "run_00000001",
          status: "completed",
          safeReason: "Impossible result state.",
          resultAvailable: false,
        },
        context,
      ),
    ).toMatchObject({ ok: false, error: { category: "contract" } });
    expect(
      mapTaskEvent(
        "run.completed",
        "3",
        {
          runId: "run_00000001",
          status: "failed",
          safeReason: "Impossible result state.",
          resultAvailable: true,
        },
        context,
      ),
    ).toMatchObject({ ok: false, error: { category: "contract" } });
  });

  it("requires exact decision receipt correlation", () => {
    const sourceThread = sourceThreadKey(sourceId("source-a"), threadId("thread-a"));
    const interrupt = sourceInterruptKey(
      sourceThread.sourceId,
      task,
      sourceThread.threadId,
      run,
      interruptId("interrupt_00000001"),
    );
    const request = createDecisionInput(interrupt, 2, "respond", "Use the bounded correction.");

    expect(
      mapDecisionReceipt(
        {
          taskId: "task_00000001",
          runId: "run_00000001",
          interruptId: "interrupt_00000002",
          decision: "respond",
          status: "accepted",
          duplicate: false,
        },
        task,
        request,
      ),
    ).toMatchObject({ ok: false, error: { category: "contract" } });
  });

  it("keeps plan edits separate and requires the exact next revision", () => {
    const sourceThread = sourceThreadKey(sourceId("source-a"), threadId("thread-a"));
    const interrupt = sourceInterruptKey(
      sourceThread.sourceId,
      task,
      sourceThread.threadId,
      run,
      interruptId("interrupt_00000001"),
    );
    const edit = createPlanEditInput(interrupt, 2, ["Use the corrected plan"]);
    const receipt = mapPlanEditReceipt(
      {
        taskId: "task_00000001",
        runId: "run_00000001",
        interruptId: "interrupt_00000001",
        plan: {
          revision: 3,
          title: "Updated plan",
          steps: ["Use the corrected plan"],
          evidenceRefs: [],
        },
      },
      task,
      edit,
    );
    const stale = mapPlanEditReceipt(
      {
        taskId: "task_00000001",
        runId: "run_00000001",
        interruptId: "interrupt_00000001",
        plan: {
          revision: 2,
          title: "Old plan",
          steps: ["Do not accept"],
          evidenceRefs: [],
        },
      },
      task,
      edit,
    );

    expect(receipt).toMatchObject({ ok: true, value: { plan: { revision: 3 } } });
    expect(stale).toMatchObject({ ok: false, error: { category: "contract" } });
  });

  it("rejects malformed task list items instead of skipping them", () => {
    expect(
      mapTaskList(
        {
          items: [
            {
              taskId: "task_00000001",
              runId: "run_00000001",
              createdAt: "2026-01-01T00:00:00+00:00",
              title: "Task",
              objective: "Objective",
              status: "queued",
              lastEventId: 1,
            },
            { taskId: "malformed" },
          ],
        },
        resolver("source-a"),
      ),
    ).toMatchObject({ ok: false, error: { category: "contract" } });
  });

  it("maps a null createdAt to an absent creation time without fabricating one", () => {
    const summaryFor = (createdAt: string | null) =>
      mapTaskList(
        {
          items: [
            {
              taskId: "task_00000001",
              runId: "run_00000001",
              createdAt,
              title: "Task",
              objective: "Objective",
              status: "queued",
              lastEventId: 1,
            },
          ],
        },
        resolver("source-a"),
      );

    const migrated = summaryFor(null);
    if (!migrated.ok) {
      throw new Error("Expected an accepted migrated task summary.");
    }
    // A pre-timestamp task reports no creation time rather than a made-up one.
    expect(migrated.value[0]?.createdAt).toBeUndefined();
    expect("createdAt" in (migrated.value[0] ?? {})).toBe(false);

    const timestamped = summaryFor("2026-01-01T00:00:00+00:00");
    if (!timestamped.ok) {
      throw new Error("Expected an accepted timestamped task summary.");
    }
    expect(timestamped.value[0]?.createdAt).toBe("2026-01-01T00:00:00+00:00");
  });

  it("requires coherent completed/detail result state", () => {
    expect(
      mapTaskDetail(
        {
          ...waitingDetail,
          status: "completed",
          pendingInterrupt: null,
          result: null,
        },
        resolver("source-a"),
      ),
    ).toMatchObject({ ok: false, error: { category: "contract" } });
    expect(
      mapTaskDetail(
        {
          ...waitingDetail,
          status: "running",
          pendingInterrupt: null,
          result: "A result cannot appear before completion.",
        },
        resolver("source-a"),
      ),
    ).toMatchObject({ ok: false, error: { category: "contract" } });
    expect(
      mapTaskDetail(
        {
          ...waitingDetail,
          status: "completed",
          pendingInterrupt: null,
          result: "The current task completed.",
        },
        resolver("source-a"),
      ),
    ).toMatchObject({ ok: true, value: { status: "done" } });
  });

  it("accepts the maximum plan revision and rejects max plus one", () => {
    expect(
      mapTaskDetail(
        {
          ...waitingDetail,
          pendingInterrupt: {
            ...waitingDetail.pendingInterrupt,
            planRevision: 2_147_483_647,
          },
          proposedPlan: {
            ...waitingDetail.proposedPlan,
            revision: 2_147_483_647,
          },
        },
        resolver("source-a"),
      ),
    ).toMatchObject({
      ok: true,
      value: { proposedPlan: { revision: 2_147_483_647 } },
    });
    expect(
      mapTaskDetail(
        {
          ...waitingDetail,
          pendingInterrupt: {
            ...waitingDetail.pendingInterrupt,
            planRevision: 2_147_483_648,
          },
          proposedPlan: {
            ...waitingDetail.proposedPlan,
            revision: 2_147_483_648,
          },
        },
        resolver("source-a"),
      ),
    ).toMatchObject({ ok: false, error: { category: "contract" } });
  });
});

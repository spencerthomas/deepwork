import {
  interruptId,
  pendingInterrupt,
  runId,
  sourceId,
  sourceInterruptKey,
  sourceRunKey,
  sourceThreadKey,
  taskId,
  threadId,
} from "@deepwork/domain";
import {
  createDecisionInput,
  createPlanEditInput,
  createTaskMutationService,
  createTaskQueryService,
  createTaskStreamService,
  taskTransportProblem,
  type TaskBindingResolver,
  type TaskMutationBindingResolver,
  type TaskMutationTransport,
  type TaskQueryTransport,
  type TaskStreamTransport,
  type TaskStreamTransportObserver,
} from "@deepwork/sdk";
import { describe, expect, it, vi } from "vitest";

const task = taskId("task_00000001");
const run = runId("run_00000001");
const binding = sourceThreadKey(sourceId("source-a"), threadId("thread-a"));
const currentInterruptKey = sourceInterruptKey(
  binding.sourceId,
  task,
  binding.threadId,
  run,
  interruptId("interrupt_00000001"),
);
const currentInterrupt = pendingInterrupt({
  identity: currentInterruptKey,
  decisions: ["approve", "reject", "respond"],
  planRevision: 1,
});
const bindings: TaskBindingResolver = {
  resolveTask(requested) {
    return requested === task ? binding : undefined;
  },
};
const mutationBindings: TaskMutationBindingResolver = {
  ...bindings,
  resolveCurrentInterrupt(requested) {
    return requested === task ? currentInterrupt : undefined;
  },
};

function checkpointDetail(lastEventId: number) {
  return {
    taskId: "task_00000001",
    runId: "run_00000001",
    createdAt: "2026-01-01T00:00:00+00:00",
    title: "Task",
    objective: "Inspect the bounded contract.",
    status: "running",
    lastEventId,
    pendingInterrupt: null,
    proposedPlan: null,
    evidence: [],
    result: null,
  };
}

describe("separate task services", () => {
  it("keeps query transport separate and maps accepted summaries", async () => {
    const transport: TaskQueryTransport = {
      listTasks: vi.fn(async () => ({
        items: [
          {
            taskId: "task_00000001",
            runId: "run_00000001",
            createdAt: "2026-01-01T00:00:00+00:00",
            title: "Task",
            objective: "Inspect the bounded contract.",
            status: "completed",
            lastEventId: 4,
          },
        ],
      })),
      getTask: vi.fn(),
      getTaskResult: vi.fn(),
    };
    const service = createTaskQueryService(transport, bindings);
    const result = await service.listTasks();

    expect(result).toMatchObject({
      ok: true,
      value: [{ status: "done" }],
    });
    expect("decide" in service).toBe(false);
    expect("subscribe" in service).toBe(false);
  });

  it("rejects an oversized objective before calling mutation transport", async () => {
    const createTask = vi.fn();
    const transport: TaskMutationTransport = {
      createTask,
      recordDecision: vi.fn(),
      updatePlan: vi.fn(),
    };
    const service = createTaskMutationService(transport, mutationBindings);
    const result = await service.createTask("😀".repeat(8_001));

    expect(result).toMatchObject({
      ok: false,
      error: { category: "contract" },
    });
    expect(createTask).not.toHaveBeenCalled();
  });

  it("preserves respond semantics in the exact mutation request", async () => {
    const recordDecision = vi.fn(async (_taskId, request) => ({
      taskId: "task_00000001",
      runId: "run_00000001",
      interruptId: request.interruptId,
      decision: request.decision,
      status: "accepted",
      duplicate: false,
    }));
    const transport: TaskMutationTransport = {
      createTask: vi.fn(),
      recordDecision,
      updatePlan: vi.fn(),
    };
    const service = createTaskMutationService(transport, mutationBindings);
    const result = await service.decide(
      task,
      createDecisionInput(currentInterruptKey, 1, "respond", "Use the revised scope."),
    );

    expect(result).toMatchObject({
      ok: true,
      value: { decision: "respond" },
    });
    expect(recordDecision).toHaveBeenCalledWith(
      task,
      {
        interruptId: "interrupt_00000001",
        decision: "respond",
        comment: "Use the revised scope.",
      },
      undefined,
    );
  });

  it("makes stream unsubscribe idempotent and never treats it as cancel", async () => {
    const unsubscribe = vi.fn();
    let transportObserver: TaskStreamTransportObserver | undefined;
    const transport: TaskStreamTransport = {
      async subscribe(_request, observer) {
        transportObserver = observer;
        return { unsubscribe };
      },
    };
    const onEvent = vi.fn();
    const onError = vi.fn();
    const onBoundary = vi.fn();
    const service = createTaskStreamService(transport, bindings);
    const subscribed = await service.subscribe(
      {
        taskId: task,
        sourceThread: binding,
        run: sourceRunKey(binding.sourceId, binding.threadId, run),
      },
      { onEvent, onError, onBoundary },
      { afterEventId: "1" },
    );
    if (!subscribed.ok || transportObserver === undefined) {
      throw new Error("Expected stream subscription.");
    }

    transportObserver.onEvent("run.started", "2", { runId: "run_00000001", status: "running" });
    subscribed.value.unsubscribe();
    subscribed.value.unsubscribe();
    transportObserver.onEvent("run.started", "3", { runId: "run_00000001", status: "running" });

    expect(onEvent).toHaveBeenCalledTimes(1);
    expect(onError).not.toHaveBeenCalled();
    expect(onBoundary).toHaveBeenCalledWith({ kind: "connected", authoritative: false });
    expect(typeof transportObserver.onDisconnect).toBe("function");
    expect(unsubscribe).toHaveBeenCalledTimes(1);
    expect("cancel" in subscribed.value).toBe(false);
    expect(subscribed.value.isQuarantined()).toBe(false);
  });

  it("reports malformed stream values and emits no partial event", async () => {
    let transportObserver: TaskStreamTransportObserver | undefined;
    const transport: TaskStreamTransport = {
      async subscribe(_request, observer) {
        transportObserver = observer;
        return { unsubscribe() {} };
      },
    };
    const onEvent = vi.fn();
    const onError = vi.fn();
    const onBoundary = vi.fn();
    const service = createTaskStreamService(transport, bindings);
    const subscribed = await service.subscribe(
      {
        taskId: task,
        sourceThread: binding,
        run: sourceRunKey(binding.sourceId, binding.threadId, run),
      },
      { onEvent, onError, onBoundary },
    );
    if (!subscribed.ok || transportObserver === undefined) {
      throw new Error("Expected stream subscription.");
    }

    transportObserver.onEvent("provider.raw", "2", { secret: "blocked" });
    transportObserver.onEvent("run.completed", "3", {
      runId: "run_00000001",
      status: "completed",
      safeReason: "Must not pass quarantine.",
      resultAvailable: true,
    });

    expect(onEvent).not.toHaveBeenCalled();
    expect(onError).toHaveBeenCalledWith(
      expect.objectContaining({ category: "contract", retryable: false }),
    );
    expect(subscribed.value.isQuarantined()).toBe(true);
  });

  it("quarantines a stream gap before a later terminal event", async () => {
    let transportObserver: TaskStreamTransportObserver | undefined;
    const transport: TaskStreamTransport = {
      async subscribe(_request, observer) {
        transportObserver = observer;
        return { unsubscribe() {} };
      },
    };
    const onEvent = vi.fn();
    const onError = vi.fn();
    const onBoundary = vi.fn();
    const service = createTaskStreamService(transport, bindings);
    const subscribed = await service.subscribe(
      {
        taskId: task,
        sourceThread: binding,
        run: sourceRunKey(binding.sourceId, binding.threadId, run),
      },
      { onEvent, onError, onBoundary },
      { afterEventId: "1" },
    );
    if (!subscribed.ok || transportObserver === undefined) {
      throw new Error("Expected stream subscription.");
    }

    transportObserver.onEvent("run.started", "3", { runId: "run_00000001", status: "running" });
    transportObserver.onEvent("run.completed", "4", {
      runId: "run_00000001",
      status: "completed",
      safeReason: "Must wait for hydration.",
      resultAvailable: true,
    });

    expect(onEvent).not.toHaveBeenCalled();
    expect(onError).toHaveBeenCalledTimes(1);
    expect(subscribed.value.isQuarantined()).toBe(true);
  });

  it("emits an explicit connected boundary when a resumed stream opens with no event", async () => {
    const onBoundary = vi.fn();
    const transport: TaskStreamTransport = {
      async subscribe() {
        return { unsubscribe() {} };
      },
    };
    const result = await createTaskStreamService(transport, bindings).subscribe(
      {
        taskId: task,
        sourceThread: binding,
        run: sourceRunKey(binding.sourceId, binding.threadId, run),
      },
      { onEvent: vi.fn(), onError: vi.fn(), onBoundary },
      { afterEventId: "4" },
    );

    expect(result).toMatchObject({ ok: true });
    expect(onBoundary).toHaveBeenCalledTimes(1);
    expect(onBoundary).toHaveBeenCalledWith({ kind: "connected", authoritative: false });
  });

  it("preserves typed cursor-invalid and conflict recovery semantics", async () => {
    const cursorTransport: TaskStreamTransport = {
      async subscribe() {
        throw taskTransportProblem(409, "event_cursor_invalid");
      },
    };
    const cursor = await createTaskStreamService(cursorTransport, bindings).subscribe(
      {
        taskId: task,
        sourceThread: binding,
        run: sourceRunKey(binding.sourceId, binding.threadId, run),
      },
      { onEvent: vi.fn(), onError: vi.fn(), onBoundary: vi.fn() },
    );

    expect(cursor).toMatchObject({
      ok: false,
      error: {
        category: "recovery-required",
        code: "event_cursor_invalid",
        recovery: "hydrate-and-reconnect",
        retryable: false,
      },
    });

    for (const code of [
      "interrupt_mismatch",
      "interrupt_stale",
      "decision_conflict",
      "plan_revision_conflict",
    ] as const) {
      const transport: TaskMutationTransport = {
        createTask: vi.fn(),
        async recordDecision() {
          throw taskTransportProblem(409, code);
        },
        updatePlan: vi.fn(),
      };
      const result = await createTaskMutationService(transport, mutationBindings).decide(
        task,
        createDecisionInput(currentInterruptKey, 1, "approve"),
      );
      expect(result).toMatchObject({
        ok: false,
        error: {
          category: "recovery-required",
          code,
          recovery: "authoritative-refetch",
          retryable: false,
        },
      });
    }
  });

  it("fails closed for unknown transport errors", async () => {
    const transport: TaskQueryTransport = {
      async listTasks() {
        throw Object.freeze({ status: 404, code: "provider_private_not_found", secret: "blocked" });
      },
      getTask: vi.fn(),
      getTaskResult: vi.fn(),
    };

    expect(await createTaskQueryService(transport, bindings).listTasks()).toEqual({
      ok: false,
      error: {
        category: "unknown",
        safeMessage: "The Deep Work application transport failed.",
        retryable: false,
      },
    });
  });

  it("rejects same-ID mutation inputs from another source before transport", async () => {
    const recordDecision = vi.fn();
    const transport: TaskMutationTransport = {
      createTask: vi.fn(),
      recordDecision,
      updatePlan: vi.fn(),
    };
    const foreign = sourceInterruptKey(
      sourceId("source-b"),
      task,
      threadId("thread-b"),
      run,
      interruptId("interrupt_00000001"),
    );
    const result = await createTaskMutationService(transport, mutationBindings).decide(
      task,
      createDecisionInput(foreign, 1, "approve"),
    );

    expect(result).toMatchObject({ ok: false, error: { category: "contract" } });
    expect(recordDecision).not.toHaveBeenCalled();
  });

  it("rejects stale same-interrupt decisions and disallowed choices before transport", async () => {
    const recordDecision = vi.fn();
    const transport: TaskMutationTransport = {
      createTask: vi.fn(),
      recordDecision,
      updatePlan: vi.fn(),
    };
    const revisedBindings: TaskMutationBindingResolver = {
      ...bindings,
      resolveCurrentInterrupt(requested) {
        return requested === task
          ? pendingInterrupt({
              identity: currentInterruptKey,
              decisions: ["approve"],
              planRevision: 2,
            })
          : undefined;
      },
    };
    const service = createTaskMutationService(transport, revisedBindings);

    expect(
      await service.decide(task, createDecisionInput(currentInterruptKey, 1, "approve")),
    ).toMatchObject({
      ok: false,
      error: { code: "interrupt_stale", recovery: "authoritative-refetch" },
    });
    expect(
      await service.decide(task, createDecisionInput(currentInterruptKey, 2, "reject")),
    ).toMatchObject({
      ok: false,
      error: { category: "contract" },
    });
    expect(recordDecision).not.toHaveBeenCalled();
  });

  it("deduplicates exact stream replay but quarantines conflicts and arbitrary starts", async () => {
    let replayObserver: TaskStreamTransportObserver | undefined;
    const replayTransport: TaskStreamTransport = {
      async subscribe(_request, observer) {
        replayObserver = observer;
        return { unsubscribe() {} };
      },
    };
    const onEvent = vi.fn();
    const onError = vi.fn();
    const replay = await createTaskStreamService(replayTransport, bindings).subscribe(
      {
        taskId: task,
        sourceThread: binding,
        run: sourceRunKey(binding.sourceId, binding.threadId, run),
      },
      { onEvent, onError, onBoundary: vi.fn() },
    );
    if (!replay.ok || replayObserver === undefined) {
      throw new Error("Expected replay stream.");
    }
    const created = { taskId: "task_00000001", runId: "run_00000001", status: "queued" };
    replayObserver.onEvent("task.created", "1", created);
    replayObserver.onEvent("task.created", "1", created);
    replayObserver.onEvent("task.created", "1", {
      ...created,
      status: "running",
    });

    expect(onEvent).toHaveBeenCalledTimes(1);
    expect(onError).toHaveBeenCalledTimes(1);
    expect(replay.value.isQuarantined()).toBe(true);

    let gapObserver: TaskStreamTransportObserver | undefined;
    const gap = await createTaskStreamService(
      {
        async subscribe(_request, observer) {
          gapObserver = observer;
          return { unsubscribe() {} };
        },
      },
      bindings,
    ).subscribe(
      {
        taskId: task,
        sourceThread: binding,
        run: sourceRunKey(binding.sourceId, binding.threadId, run),
      },
      { onEvent: vi.fn(), onError: vi.fn(), onBoundary: vi.fn() },
    );
    if (!gap.ok || gapObserver === undefined) {
      throw new Error("Expected gap stream.");
    }
    gapObserver.onEvent("run.started", "2", {
      runId: "run_00000001",
      status: "running",
    });
    expect(gap.value.isQuarantined()).toBe(true);
  });

  it("requires an explicit authoritative boundary after disconnect and enforces the cursor maximum", async () => {
    let observer: TaskStreamTransportObserver | undefined;
    const onBoundary = vi.fn();
    const onDisconnect = vi.fn();
    const subscribe = vi.fn(async (_request, nextObserver: TaskStreamTransportObserver) => {
      observer = nextObserver;
      return { unsubscribe() {} };
    });
    const service = createTaskStreamService({ subscribe }, bindings);
    const connected = await service.subscribe(
      {
        taskId: task,
        sourceThread: binding,
        run: sourceRunKey(binding.sourceId, binding.threadId, run),
      },
      { onEvent: vi.fn(), onError: vi.fn(), onBoundary, onDisconnect },
      { afterEventId: "2147483647" },
    );
    if (!connected.ok || observer === undefined) {
      throw new Error("Expected connected stream.");
    }
    observer.onDisconnect?.();
    observer.onBoundary?.({ kind: "connected" });
    expect(onBoundary).toHaveBeenLastCalledWith({
      kind: "connected",
      authoritative: false,
    });
    observer.onBoundary?.({
      kind: "recovered",
      detail: checkpointDetail(2_147_483_647),
    });

    expect(onDisconnect).toHaveBeenCalledTimes(1);
    expect(onBoundary).toHaveBeenLastCalledWith(
      expect.objectContaining({
        kind: "recovered",
        authoritative: true,
        lastEventId: "2147483647",
        sequence: 2147483647,
        detail: expect.objectContaining({ taskId: "task_00000001" }),
      }),
    );

    const overflow = await service.subscribe(
      {
        taskId: task,
        sourceThread: binding,
        run: sourceRunKey(binding.sourceId, binding.threadId, run),
      },
      { onEvent: vi.fn(), onError: vi.fn(), onBoundary: vi.fn() },
      { afterEventId: "2147483648" },
    );
    expect(overflow).toMatchObject({ ok: false, error: { category: "contract" } });
    expect(subscribe).toHaveBeenCalledTimes(1);
  });

  it("suppresses events already covered by an asserted replay cursor", async () => {
    let observer: TaskStreamTransportObserver | undefined;
    const onEvent = vi.fn();
    const onError = vi.fn();
    const result = await createTaskStreamService(
      {
        async subscribe(_request, nextObserver) {
          observer = nextObserver;
          return { unsubscribe() {} };
        },
      },
      bindings,
    ).subscribe(
      {
        taskId: task,
        sourceThread: binding,
        run: sourceRunKey(binding.sourceId, binding.threadId, run),
      },
      { onEvent, onError, onBoundary: vi.fn() },
      { afterEventId: "2" },
    );
    if (!result.ok || observer === undefined) {
      throw new Error("Expected resumed stream.");
    }
    observer.onEvent("task.created", "1", {
      taskId: "task_00000001",
      runId: "run_00000001",
      status: "queued",
    });
    observer.onEvent("run.started", "2", {
      runId: "run_00000001",
      status: "running",
    });
    observer.onEvent("run.started", "3", {
      runId: "run_00000001",
      status: "running",
    });

    expect(onEvent).toHaveBeenCalledTimes(1);
    expect(onEvent).toHaveBeenCalledWith(expect.objectContaining({ sequence: 3 }));
    expect(onError).not.toHaveBeenCalled();
  });

  it("quarantines an unbound recovery checkpoint instead of advancing its cursor", async () => {
    let observer: TaskStreamTransportObserver | undefined;
    const onBoundary = vi.fn();
    const onError = vi.fn();
    const result = await createTaskStreamService(
      {
        async subscribe(_request, nextObserver) {
          observer = nextObserver;
          return { unsubscribe() {} };
        },
      },
      bindings,
    ).subscribe(
      {
        taskId: task,
        sourceThread: binding,
        run: sourceRunKey(binding.sourceId, binding.threadId, run),
      },
      { onEvent: vi.fn(), onError, onBoundary },
      { afterEventId: "1" },
    );
    if (!result.ok || observer === undefined) {
      throw new Error("Expected recovery stream.");
    }
    observer.onBoundary?.({
      kind: "hydrated",
      detail: { ...checkpointDetail(9), taskId: "task_00000002" },
    });

    expect(result.value.isQuarantined()).toBe(true);
    expect(onError).toHaveBeenCalledWith(
      expect.objectContaining({ category: "contract", retryable: false }),
    );
    expect(onBoundary).toHaveBeenCalledTimes(1);
  });

  it("does not trust forged Problem status/code pairs or raw transport text", async () => {
    const transport: TaskMutationTransport = {
      createTask: vi.fn(),
      async recordDecision() {
        throw taskTransportProblem(500, "interrupt_stale");
      },
      updatePlan: vi.fn(),
    };
    const result = await createTaskMutationService(transport, mutationBindings).decide(
      task,
      createDecisionInput(currentInterruptKey, 1, "approve"),
    );

    expect(result).toEqual({
      ok: false,
      error: {
        category: "unknown",
        safeMessage: "The Deep Work application transport failed.",
        retryable: false,
      },
    });
    expect(JSON.stringify(result)).not.toContain("raw");
  });

  it("rejects a plan edit at the maximum revision before transport side effects", async () => {
    const updatePlan = vi.fn();
    const transport: TaskMutationTransport = {
      createTask: vi.fn(),
      recordDecision: vi.fn(),
      updatePlan,
    };
    const maximumBindings: TaskMutationBindingResolver = {
      ...bindings,
      resolveCurrentInterrupt(requested) {
        return requested === task
          ? pendingInterrupt({
              identity: currentInterruptKey,
              decisions: ["approve"],
              planRevision: 2_147_483_647,
            })
          : undefined;
      },
    };
    const result = await createTaskMutationService(transport, maximumBindings).editPlan(
      task,
      createPlanEditInput(currentInterruptKey, 2_147_483_647, ["Do not overflow"]),
    );

    expect(result).toMatchObject({ ok: false, error: { category: "contract" } });
    expect(updatePlan).not.toHaveBeenCalled();
  });
});

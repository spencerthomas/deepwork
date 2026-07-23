import {
  applicationEventId,
  createTaskProjection,
  displayText,
  evidenceId,
  evidenceRecord,
  interruptId,
  pendingInterrupt,
  PLAN_REVISION_MAX,
  proposedPlan,
  reconcileTaskProjection,
  reduceTaskEvent,
  reduceTaskEvents,
  resultText,
  runId,
  setTaskReconnecting,
  setTaskSourceHealth,
  sourceApplicationEventKey,
  sourceEvidenceKey,
  sourceId,
  sourceInterruptKey,
  sourceRunKey,
  sourceThreadKey,
  taskDetail,
  taskId,
  taskResult,
  threadId,
  withTaskResult,
  type ProposedPlan,
  type TaskApplicationEvent,
} from "@deepwork/domain";
import { describe, expect, it } from "vitest";

const source = sourceId("source-a");
const task = taskId("task_00000001");
const thread = threadId("thread-1");
const run = runId("run_00000001");
const sourceThread = sourceThreadKey(source, thread);
const sourceRun = sourceRunKey(source, thread, run);

function eventIdentity(sequence: number) {
  return sourceApplicationEventKey(source, task, thread, run, applicationEventId(String(sequence)));
}

function initialProjection() {
  return createTaskProjection(
    taskDetail({
      taskId: task,
      sourceThread,
      run: sourceRun,
      title: "Inspect the request",
      objective: "Explain the bounded request.",
      facts: {
        cancellationConfirmed: false,
        pendingCurrentInterrupt: false,
        runActive: false,
        queued: true,
        terminalFailure: false,
        terminalSuccess: false,
      },
      lastEvent: eventIdentity(1),
      lastEventSequence: 1,
      evidence: [],
    }),
  );
}

function baseEvent(sequence: number) {
  return {
    identity: eventIdentity(sequence),
    sequence,
    taskId: task,
    sourceThread,
    run: sourceRun,
  };
}

function runningProjection() {
  return reduceTaskEvent(initialProjection(), {
    ...baseEvent(2),
    name: "run.started",
  });
}

describe("deterministic task projection", () => {
  it("deduplicates exact/checkpoint replay and quarantines same-key conflicts", () => {
    const started: TaskApplicationEvent = {
      ...baseEvent(2),
      name: "run.started",
    };
    const afterStart = reduceTaskEvent(initialProjection(), started);
    const duplicate = reduceTaskEvent(afterStart, started);
    const checkpointReplay: TaskApplicationEvent = {
      ...baseEvent(1),
      name: "task.created",
    };
    const conflictingReplay: TaskApplicationEvent = {
      ...baseEvent(2),
      name: "task.created",
    };

    expect(afterStart.status).toBe("running");
    expect(duplicate).toBe(afterStart);
    expect(reduceTaskEvent(afterStart, checkpointReplay)).toBe(afterStart);
    const quarantined = reduceTaskEvent(afterStart, conflictingReplay);
    expect(quarantined.quarantined).toBe(true);
    expect(quarantined.status).toBe("running");
  });

  it("preserves run evidence while a current interrupt owns attention", () => {
    const interrupt = pendingInterrupt({
      identity: sourceInterruptKey(source, task, thread, run, interruptId("interrupt_00000001")),
      decisions: ["approve", "reject", "respond"],
      planRevision: 1,
      question: "Continue?",
    });
    const projection = reduceTaskEvents(initialProjection(), [
      { ...baseEvent(2), name: "run.started" },
      {
        ...baseEvent(3),
        name: "plan.proposed",
        plan: proposedPlan({
          revision: 1,
          title: "Current plan",
          steps: ["Inspect current evidence"],
          evidenceRefs: [],
        }),
        evidenceClass: "fixture",
      },
      {
        ...baseEvent(4),
        name: "interrupt.requested",
        interrupt,
      },
    ]);

    expect(projection.status).toBe("needs-review");
    expect(projection.facts.runActive).toBe(true);
    expect(projection.task.pendingInterrupt).toBe(interrupt);
  });

  it("accepts only newer plan revisions and marks conflicts stale", () => {
    const revisionTwo = proposedPlan({
      revision: 2,
      title: "Current plan",
      steps: ["Inspect current evidence"],
      evidenceRefs: [],
    });
    const withCurrent = reduceTaskEvent(runningProjection(), {
      ...baseEvent(3),
      name: "plan.proposed",
      plan: revisionTwo,
      evidenceClass: "fixture",
    });
    const waiting = reduceTaskEvent(withCurrent, {
      ...baseEvent(4),
      name: "interrupt.requested",
      interrupt: pendingInterrupt({
        identity: sourceInterruptKey(source, task, thread, run, interruptId("interrupt_00000001")),
        decisions: ["approve", "reject", "respond"],
        planRevision: 2,
      }),
    });
    const older = reduceTaskEvent(waiting, {
      ...baseEvent(5),
      name: "plan.updated",
      plan: proposedPlan({
        revision: 1,
        title: "Old plan",
        steps: ["Ignore this stale edit"],
        evidenceRefs: [],
      }),
      evidenceClass: "fixture",
    });
    const equalConflict = reduceTaskEvent(older, {
      ...baseEvent(6),
      name: "plan.updated",
      plan: proposedPlan({
        revision: 2,
        title: "Conflicting plan",
        steps: ["Do not overwrite"],
        evidenceRefs: [],
      }),
      evidenceClass: "fixture",
    });
    const newer = reduceTaskEvent(equalConflict, {
      ...baseEvent(7),
      name: "plan.updated",
      plan: proposedPlan({
        revision: 3,
        title: "Reviewed plan",
        steps: ["Use the new revision"],
        evidenceRefs: [],
      }),
      evidenceClass: "fixture",
    });

    expect(older.task.proposedPlan).toBe(revisionTwo);
    expect(equalConflict.task.proposedPlan).toBe(revisionTwo);
    expect(equalConflict.stale).toBe(true);
    expect(newer.task.proposedPlan?.revision).toBe(3);
  });

  it("keeps stale or mismatched decision receipts from clearing attention", () => {
    const currentInterrupt = pendingInterrupt({
      identity: sourceInterruptKey(source, task, thread, run, interruptId("interrupt_00000001")),
      decisions: ["approve", "reject", "respond"],
      planRevision: 1,
    });
    const waiting = reduceTaskEvent(runningProjection(), {
      ...baseEvent(3),
      name: "plan.proposed",
      plan: proposedPlan({
        revision: 1,
        title: "Current plan",
        steps: ["Inspect current evidence"],
        evidenceRefs: [],
      }),
      evidenceClass: "fixture",
    });
    const interrupted = reduceTaskEvent(waiting, {
      ...baseEvent(4),
      name: "interrupt.requested",
      interrupt: currentInterrupt,
    });
    const mismatch = reduceTaskEvent(interrupted, {
      ...baseEvent(5),
      name: "decision.recorded",
      interrupt: sourceInterruptKey(source, task, thread, run, interruptId("interrupt_00000002")),
      decision: "approve",
      commentProvided: false,
      responseProvided: false,
    });
    const accepted = reduceTaskEvent(mismatch, {
      ...baseEvent(6),
      name: "decision.recorded",
      interrupt: currentInterrupt.identity,
      decision: "respond",
      commentProvided: true,
      responseProvided: true,
    });

    expect(mismatch.status).toBe("needs-review");
    expect(mismatch.stale).toBe(true);
    expect(accepted.status).toBe("running");
    expect(accepted.task.pendingInterrupt).toBeUndefined();
  });

  it("synchronizes a current interrupt guard when a newer plan is accepted", () => {
    const revisionOne = proposedPlan({
      revision: 1,
      title: "Initial plan",
      steps: ["Inspect the first version"],
      evidenceRefs: [],
    });
    const interrupt = pendingInterrupt({
      identity: sourceInterruptKey(source, task, thread, run, interruptId("interrupt_00000001")),
      decisions: ["approve", "reject", "respond"],
      planRevision: 1,
    });
    const waiting = reduceTaskEvents(runningProjection(), [
      { ...baseEvent(3), name: "plan.proposed", plan: revisionOne, evidenceClass: "fixture" },
      { ...baseEvent(4), name: "interrupt.requested", interrupt },
    ]);
    const updated = reduceTaskEvent(waiting, {
      ...baseEvent(5),
      name: "plan.updated",
      plan: proposedPlan({
        revision: 2,
        title: "Updated plan",
        steps: ["Inspect the revised version"],
        evidenceRefs: [],
      }),
      evidenceClass: "fixture",
    });

    expect(updated.planRevision).toBe(2);
    expect(updated.task.pendingInterrupt?.planRevision).toBe(2);
    expect(updated.status).toBe("needs-review");
  });

  it("keeps disconnect and source health orthogonal to durable outcome", () => {
    const completed = reduceTaskEvent(runningProjection(), {
      ...baseEvent(3),
      name: "run.completed",
      outcome: "success",
      safeReason: displayText("The bounded task completed.", "Completion safe reason", 200),
      resultAvailable: true,
    });
    const reconnecting = setTaskReconnecting(completed, true);
    const unavailable = setTaskSourceHealth(reconnecting, "unavailable");

    expect(completed.status).toBe("done");
    expect(reconnecting.status).toBe("done");
    expect(unavailable.status).toBe("done");
    expect(unavailable.reconnecting).toBe(true);
    expect(unavailable.sourceHealth).toBe("unavailable");
  });

  it("quarantines a sequence gap until authoritative hydration", () => {
    const gap = reduceTaskEvent(initialProjection(), {
      ...baseEvent(3),
      name: "run.started",
    });
    const skippedTerminal = reduceTaskEvent(gap, {
      ...baseEvent(4),
      name: "run.completed",
      outcome: "success",
      safeReason: displayText("This event must wait for hydration.", "Completion safe reason", 200),
      resultAvailable: true,
    });

    expect(gap.quarantined).toBe(true);
    expect(gap.status).toBe("queued");
    expect(skippedTerminal).toBe(gap);

    const hydrated = reconcileTaskProjection(
      gap,
      taskDetail({
        taskId: task,
        sourceThread,
        run: sourceRun,
        title: "Inspect the request",
        objective: "Explain the bounded request.",
        facts: {
          cancellationConfirmed: false,
          pendingCurrentInterrupt: false,
          runActive: false,
          queued: false,
          terminalFailure: false,
          terminalSuccess: true,
        },
        lastEvent: eventIdentity(4),
        lastEventSequence: 4,
        evidence: [],
        result: resultText("The authoritative task completed."),
      }),
    );
    expect(hydrated.quarantined).toBe(false);
    expect(hydrated.recovered).toBe(true);
    expect(hydrated.status).toBe("done");
    const anotherOutage = setTaskReconnecting(hydrated, true);
    expect(anotherOutage.reconnecting).toBe(true);
    expect(anotherOutage.recovered).toBe(false);
  });

  it("does not clear quarantine for conflicting equal-cursor hydration", () => {
    const gap = reduceTaskEvent(initialProjection(), {
      ...baseEvent(3),
      name: "run.started",
    });
    const conflict = reconcileTaskProjection(
      gap,
      taskDetail({
        taskId: task,
        sourceThread,
        run: sourceRun,
        title: "Conflicting authoritative title",
        objective: "Explain the bounded request.",
        facts: initialProjection().facts,
        lastEvent: eventIdentity(1),
        lastEventSequence: 1,
        evidence: [],
      }),
    );

    expect(conflict.quarantined).toBe(true);
    expect(conflict.stale).toBe(true);
    expect(conflict.task.title).toBe("Inspect the request");
  });

  it("quarantines rather than growing streamed evidence beyond its bound", () => {
    const evidence = Array.from({ length: 256 }, (_, index) =>
      evidenceRecord({
        identity: sourceEvidenceKey(source, task, thread, run, evidenceId(`evidence-${index}`)),
        kind: "fixture",
        summary: `Evidence ${index}`,
        source: "deterministic-local-runner",
        verified: false,
        provenance: {
          sourceThread,
          observedThrough: "application-event",
          evidenceClass: "fixture",
        },
      }),
    );
    const full = createTaskProjection(
      taskDetail({
        taskId: task,
        sourceThread,
        run: sourceRun,
        title: "Inspect the request",
        objective: "Explain the bounded request.",
        facts: {
          cancellationConfirmed: false,
          pendingCurrentInterrupt: false,
          runActive: true,
          queued: false,
          terminalFailure: false,
          terminalSuccess: false,
        },
        lastEvent: eventIdentity(1),
        lastEventSequence: 1,
        evidence,
      }),
    );
    const overflow = reduceTaskEvent(full, {
      ...baseEvent(2),
      name: "evidence.recorded",
      evidence: evidenceRecord({
        identity: sourceEvidenceKey(source, task, thread, run, evidenceId("evidence-overflow")),
        kind: "fixture",
        summary: "Overflow evidence",
        source: "deterministic-local-runner",
        verified: false,
        provenance: {
          sourceThread,
          observedThrough: "application-event",
          evidenceClass: "fixture",
        },
      }),
    });

    expect(overflow.task.evidence).toHaveLength(256);
    expect(overflow.quarantined).toBe(true);
    expect(overflow.stale).toBe(true);
  });

  it("rejects an event whose identity belongs to another task", () => {
    const otherTask = taskId("task_00000002");
    const crossTask: TaskApplicationEvent = {
      ...baseEvent(2),
      identity: sourceApplicationEventKey(source, otherTask, thread, run, applicationEventId("2")),
      name: "run.started",
    };

    const projection = reduceTaskEvent(initialProjection(), crossTask);
    expect(projection.status).toBe("queued");
    expect(projection.stale).toBe(true);
  });

  it("quarantines nested evidence, plan, and interrupt identities from another source", () => {
    const otherSource = sourceId("source-b");
    const otherThread = threadId("thread-b");
    const crossSourceEvidence = reduceTaskEvent(runningProjection(), {
      ...baseEvent(3),
      name: "evidence.recorded",
      evidence: evidenceRecord({
        identity: sourceEvidenceKey(
          otherSource,
          task,
          otherThread,
          run,
          evidenceId("evidence-shared"),
        ),
        kind: "fixture",
        summary: "Same local evidence ID, different source.",
        source: "deterministic-local-runner",
        verified: true,
        provenance: {
          sourceThread: sourceThreadKey(otherSource, otherThread),
          observedThrough: "application-event",
          evidenceClass: "fixture",
        },
      }),
    });
    const crossSourcePlan = reduceTaskEvent(runningProjection(), {
      ...baseEvent(3),
      name: "plan.proposed",
      plan: proposedPlan({
        revision: 1,
        title: "Cross-source plan",
        steps: ["Do not accept this reference"],
        evidenceRefs: [
          sourceEvidenceKey(otherSource, task, otherThread, run, evidenceId("evidence-shared")),
        ],
      }),
      evidenceClass: "fixture",
    });
    const validPlan = reduceTaskEvent(runningProjection(), {
      ...baseEvent(3),
      name: "plan.proposed",
      plan: proposedPlan({
        revision: 1,
        title: "Current plan",
        steps: ["Use the current source"],
        evidenceRefs: [],
      }),
      evidenceClass: "fixture",
    });
    const crossSourceInterrupt = reduceTaskEvent(validPlan, {
      ...baseEvent(4),
      name: "interrupt.requested",
      interrupt: pendingInterrupt({
        identity: sourceInterruptKey(
          otherSource,
          task,
          otherThread,
          run,
          interruptId("interrupt_00000001"),
        ),
        decisions: ["approve"],
        planRevision: 1,
      }),
    });

    expect(crossSourceEvidence.quarantined).toBe(true);
    expect(crossSourcePlan.quarantined).toBe(true);
    expect(crossSourceInterrupt.quarantined).toBe(true);
  });

  it("quarantines a forged plan revision above the shared maximum", () => {
    const invalidPlan = Object.freeze({
      revision: PLAN_REVISION_MAX + 1,
      title: "Overflow plan",
      steps: ["Do not apply this plan"],
      evidenceRefs: [],
    }) as unknown as ProposedPlan;
    const projection = reduceTaskEvent(runningProjection(), {
      ...baseEvent(3),
      name: "plan.proposed",
      plan: invalidPlan,
      evidenceClass: "fixture",
    });

    expect(projection.quarantined).toBe(true);
    expect(projection.task.proposedPlan).toBeUndefined();
  });

  it("attaches results only when source, task, thread, and run correlate", () => {
    const completed = reduceTaskEvent(runningProjection(), {
      ...baseEvent(3),
      name: "run.completed",
      outcome: "success",
      safeReason: displayText("The bounded task completed.", "Completion safe reason", 200),
      resultAvailable: true,
    });
    const correct = taskResult({
      taskId: task,
      run: sourceRun,
      result: "The correlated result.",
    });
    const otherTask = taskResult({
      taskId: taskId("task_00000002"),
      run: sourceRun,
      result: "Another task's result.",
    });
    const otherRun = taskResult({
      taskId: task,
      run: sourceRunKey(source, thread, runId("run_00000002")),
      result: "Another run's result.",
    });

    expect(withTaskResult(completed, correct).task.result).toBe("The correlated result.");
    expect(() => withTaskResult(completed, otherTask)).toThrow(TypeError);
    expect(() => withTaskResult(completed, otherRun)).toThrow(TypeError);
  });

  it("quarantines every new mutation after a terminal event but ignores exact replay", () => {
    const terminalEvent: TaskApplicationEvent = {
      ...baseEvent(3),
      name: "run.completed",
      outcome: "success",
      safeReason: displayText("The task is terminal.", "Completion safe reason", 200),
      resultAvailable: true,
    };
    const completed = reduceTaskEvent(runningProjection(), terminalEvent);
    const replay = reduceTaskEvent(completed, terminalEvent);
    const invalidNext = reduceTaskEvent(completed, {
      ...baseEvent(4),
      name: "run.started",
    });

    expect(replay).toBe(completed);
    expect(invalidNext.status).toBe("done");
    expect(invalidNext.quarantined).toBe(true);
  });

  it("does not overwrite equal-revision interrupt semantics", () => {
    const initial = pendingInterrupt({
      identity: sourceInterruptKey(source, task, thread, run, interruptId("interrupt_00000001")),
      decisions: ["approve", "reject"],
      planRevision: 1,
      question: "Approve the first meaning?",
    });
    const waiting = reduceTaskEvents(runningProjection(), [
      {
        ...baseEvent(3),
        name: "plan.proposed",
        plan: proposedPlan({
          revision: 1,
          title: "Current plan",
          steps: ["Keep the original semantics"],
          evidenceRefs: [],
        }),
        evidenceClass: "fixture",
      },
      { ...baseEvent(4), name: "interrupt.requested", interrupt: initial },
    ]);
    const conflict = reduceTaskEvent(waiting, {
      ...baseEvent(5),
      name: "interrupt.requested",
      interrupt: pendingInterrupt({
        identity: initial.identity,
        decisions: ["approve", "respond"],
        planRevision: 1,
        question: "Approve a changed meaning?",
      }),
    });

    expect(conflict.task.pendingInterrupt).toBe(initial);
    expect(conflict.stale).toBe(true);
  });

  it("quarantines an event whose run source/thread conflicts with its source thread", () => {
    const projection = reduceTaskEvent(initialProjection(), {
      ...baseEvent(2),
      run: sourceRunKey(sourceId("source-b"), threadId("thread-b"), run),
      name: "run.started",
    });

    expect(projection.quarantined).toBe(true);
    expect(projection.status).toBe("queued");
  });

  it("enforces the accepted local event transition matrix", () => {
    const plan = proposedPlan({
      revision: 1,
      title: "Current plan",
      steps: ["Use the accepted local sequence"],
      evidenceRefs: [],
    });
    const interrupt = pendingInterrupt({
      identity: sourceInterruptKey(source, task, thread, run, interruptId("interrupt_00000001")),
      decisions: ["approve", "reject", "respond"],
      planRevision: 1,
    });
    const running = runningProjection();
    const waiting = reduceTaskEvents(running, [
      { ...baseEvent(3), name: "plan.proposed", plan, evidenceClass: "fixture" },
      { ...baseEvent(4), name: "interrupt.requested", interrupt },
    ]);
    const cases: readonly {
      readonly label: string;
      readonly projection: ReturnType<typeof initialProjection>;
      readonly event: TaskApplicationEvent;
      readonly allowed: boolean;
    }[] = [
      {
        label: "queued to run.started",
        projection: initialProjection(),
        event: { ...baseEvent(2), name: "run.started" },
        allowed: true,
      },
      {
        label: "queued duplicate task.created",
        projection: initialProjection(),
        event: { ...baseEvent(2), name: "task.created" },
        allowed: false,
      },
      {
        label: "queued content before run.started",
        projection: initialProjection(),
        event: {
          ...baseEvent(2),
          name: "content.delta",
          text: resultText("Impossible early content."),
          evidenceClass: "fixture",
        },
        allowed: false,
      },
      {
        label: "queued terminal before run.started",
        projection: initialProjection(),
        event: {
          ...baseEvent(2),
          name: "run.completed",
          outcome: "failure",
          safeReason: displayText("Impossible early terminal.", "Completion safe reason", 200),
          resultAvailable: false,
        },
        allowed: false,
      },
      {
        label: "running content",
        projection: running,
        event: {
          ...baseEvent(3),
          name: "content.delta",
          text: resultText("Accepted active content."),
          evidenceClass: "fixture",
        },
        allowed: true,
      },
      {
        label: "running plan",
        projection: running,
        event: { ...baseEvent(3), name: "plan.proposed", plan, evidenceClass: "fixture" },
        allowed: true,
      },
      {
        label: "running decision without interrupt",
        projection: running,
        event: {
          ...baseEvent(3),
          name: "decision.recorded",
          interrupt: interrupt.identity,
          decision: "approve",
          commentProvided: false,
          responseProvided: false,
        },
        allowed: false,
      },
      {
        label: "waiting plan edit",
        projection: waiting,
        event: {
          ...baseEvent(5),
          name: "plan.updated",
          plan: proposedPlan({
            revision: 2,
            title: "Updated plan",
            steps: ["Use the accepted local edit"],
            evidenceRefs: [],
          }),
          evidenceClass: "fixture",
        },
        allowed: true,
      },
      {
        label: "waiting decision",
        projection: waiting,
        event: {
          ...baseEvent(5),
          name: "decision.recorded",
          interrupt: interrupt.identity,
          decision: "approve",
          commentProvided: false,
          responseProvided: false,
        },
        allowed: true,
      },
      {
        label: "waiting duplicate interrupt",
        projection: waiting,
        event: { ...baseEvent(5), name: "interrupt.requested", interrupt },
        allowed: false,
      },
    ];

    for (const testCase of cases) {
      const next = reduceTaskEvent(testCase.projection, testCase.event);
      expect(next.quarantined, testCase.label).toBe(!testCase.allowed);
    }
  });

  it("quarantines decisions outside the current set and incomplete respond evidence", () => {
    const interrupt = pendingInterrupt({
      identity: sourceInterruptKey(source, task, thread, run, interruptId("interrupt_00000001")),
      decisions: ["approve", "respond"],
      planRevision: 1,
    });
    const waiting = reduceTaskEvents(runningProjection(), [
      {
        ...baseEvent(3),
        name: "plan.proposed",
        plan: proposedPlan({
          revision: 1,
          title: "Current plan",
          steps: ["Use only current decisions"],
          evidenceRefs: [],
        }),
        evidenceClass: "fixture",
      },
      { ...baseEvent(4), name: "interrupt.requested", interrupt },
    ]);
    const disallowed = reduceTaskEvent(waiting, {
      ...baseEvent(5),
      name: "decision.recorded",
      interrupt: interrupt.identity,
      decision: "reject",
      commentProvided: false,
      responseProvided: false,
    });
    const incompleteRespond = reduceTaskEvent(waiting, {
      ...baseEvent(5),
      name: "decision.recorded",
      interrupt: interrupt.identity,
      decision: "respond",
      commentProvided: false,
      responseProvided: true,
    });

    expect(disallowed.quarantined).toBe(true);
    expect(incompleteRespond.quarantined).toBe(true);
  });
});

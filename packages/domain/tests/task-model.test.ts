import {
  applicationEventId,
  deriveTaskStatus,
  evidenceId,
  evidenceRecord,
  interruptId,
  objectiveText,
  pendingInterrupt,
  PLAN_REVISION_MAX,
  planEditInput,
  proposedPlan,
  resultText,
  runId,
  sourceEvidenceKey,
  sourceId,
  sourceInterruptKey,
  sourceApplicationEventKey,
  sourceRunKey,
  sourceThreadKey,
  taskAccepted,
  taskId,
  taskDetail,
  taskResult,
  taskSummary,
  threadId,
} from "@deepwork/domain";
import { describe, expect, it } from "vitest";

const source = sourceId("source-a");
const task = taskId("task_00000001");
const thread = threadId("thread-1");
const run = runId("run_00000001");
const interrupt = sourceInterruptKey(source, task, thread, run, interruptId("interrupt_00000001"));

describe("client-safe task values", () => {
  it("uses canonical presentation precedence over orthogonal facts", () => {
    expect(
      deriveTaskStatus({
        cancellationConfirmed: true,
        pendingCurrentInterrupt: true,
        runActive: true,
        queued: true,
        terminalFailure: true,
        terminalSuccess: true,
      }),
    ).toBe("cancelled");
    expect(
      deriveTaskStatus({
        cancellationConfirmed: false,
        pendingCurrentInterrupt: true,
        runActive: true,
        queued: false,
        terminalFailure: false,
        terminalSuccess: false,
      }),
    ).toBe("needs-review");
    expect(
      deriveTaskStatus({
        cancellationConfirmed: false,
        pendingCurrentInterrupt: false,
        runActive: false,
        queued: false,
        terminalFailure: false,
        terminalSuccess: true,
      }),
    ).toBe("done");
  });

  it("counts Unicode code points and never silently truncates objectives", () => {
    expect(objectiveText("😀".repeat(8_000))).toHaveLength(16_000);
    expect(() => objectiveText("😀".repeat(8_001))).toThrow(TypeError);
  });

  it("freezes plans and preserves fully qualified evidence references", () => {
    const evidence = sourceEvidenceKey(source, task, thread, run, evidenceId("evidence_00000001"));
    const plan = proposedPlan({
      revision: 1,
      title: "Inspect and answer",
      steps: ["Inspect the bounded request"],
      evidenceRefs: [evidence],
    });

    expect(Object.isFrozen(plan)).toBe(true);
    expect(Object.isFrozen(plan.steps)).toBe(true);
    expect(plan.evidenceRefs[0]).toEqual(evidence);
    expect(() =>
      proposedPlan({
        revision: 2,
        title: "Too long",
        steps: ["x".repeat(1_001)],
        evidenceRefs: [],
      }),
    ).toThrow(TypeError);
  });

  it("keeps the current local interrupt version boundary explicit", () => {
    const current = pendingInterrupt({
      identity: interrupt,
      decisions: ["approve", "reject", "respond"],
      planRevision: 3,
    });

    expect(current.identity.interruptId).toBe("interrupt_00000001");
    expect(current.planRevision).toBe(3);
    expect(Object.isFrozen(current.decisions)).toBe(true);
  });

  it("bounds every plan revision at the shared signed 32-bit maximum", () => {
    expect(
      proposedPlan({
        revision: PLAN_REVISION_MAX,
        title: "Maximum revision",
        steps: ["Keep the bounded revision"],
        evidenceRefs: [],
      }).revision,
    ).toBe(PLAN_REVISION_MAX);
    expect(() =>
      proposedPlan({
        revision: PLAN_REVISION_MAX + 1,
        title: "Overflow revision",
        steps: ["Reject this revision"],
        evidenceRefs: [],
      }),
    ).toThrow(TypeError);
    expect(() =>
      planEditInput({
        interrupt,
        expectedRevision: PLAN_REVISION_MAX + 1,
        steps: ["Reject before mutation"],
      }),
    ).toThrow(TypeError);
  });

  it("keeps plan edits distinct from respond decisions", () => {
    const edit = planEditInput({
      interrupt,
      expectedRevision: 3,
      steps: ["Use the corrected scope"],
    });

    expect(edit).toEqual({
      interrupt,
      expectedRevision: 3,
      steps: ["Use the corrected scope"],
    });
    expect("decision" in edit).toBe(false);
  });

  it("rejects incoherent task source, run, event, and cursor identities", () => {
    const sourceThread = sourceThreadKey(source, thread);
    const otherThread = threadId("thread-2");
    const lastEvent = sourceApplicationEventKey(source, task, thread, run, applicationEventId("1"));
    const input = {
      taskId: task,
      sourceThread,
      run: sourceRunKey(source, thread, run),
      title: "Bound task",
      objective: "Keep every composite identity coherent.",
      facts: {
        cancellationConfirmed: false,
        pendingCurrentInterrupt: false,
        runActive: false,
        queued: true,
        terminalFailure: false,
        terminalSuccess: false,
      },
      lastEvent,
      lastEventSequence: 1,
    };

    expect(taskSummary(input).lastEventSequence).toBe(1);
    expect(() =>
      taskSummary({
        ...input,
        run: sourceRunKey(source, otherThread, run),
      }),
    ).toThrow(TypeError);
    expect(() => taskSummary({ ...input, lastEventSequence: 2 })).toThrow(TypeError);
  });

  it("enforces lifecycle, result, plan/interrupt, and nested identity invariants at taskDetail", () => {
    const sourceThread = sourceThreadKey(source, thread);
    const lastEvent = sourceApplicationEventKey(source, task, thread, run, applicationEventId("1"));
    const base = {
      taskId: task,
      sourceThread,
      run: sourceRunKey(source, thread, run),
      title: "Bound task",
      objective: "Validate the public detail boundary.",
      facts: {
        cancellationConfirmed: false,
        pendingCurrentInterrupt: false,
        runActive: true,
        queued: false,
        terminalFailure: false,
        terminalSuccess: false,
      },
      lastEvent,
      lastEventSequence: 1,
      evidence: [],
    };

    expect(taskDetail(base).status).toBe("running");
    expect(() =>
      taskDetail({
        ...base,
        facts: {
          ...base.facts,
          pendingCurrentInterrupt: true,
          runActive: false,
        },
      }),
    ).toThrow(TypeError);
    expect(() =>
      taskDetail({
        ...base,
        result: resultText("Premature result."),
      }),
    ).toThrow(TypeError);
    expect(() =>
      taskDetail({
        ...base,
        facts: {
          ...base.facts,
          runActive: false,
          terminalSuccess: true,
        },
      }),
    ).toThrow(TypeError);

    const plan = proposedPlan({
      revision: 2,
      title: "Current plan",
      steps: ["Keep revisions coherent"],
      evidenceRefs: [],
    });
    expect(() =>
      taskDetail({
        ...base,
        facts: { ...base.facts, pendingCurrentInterrupt: true },
        proposedPlan: plan,
        pendingInterrupt: pendingInterrupt({
          identity: interrupt,
          decisions: ["approve"],
          planRevision: 1,
        }),
      }),
    ).toThrow(TypeError);

    const otherSource = sourceId("source-b");
    const otherThread = threadId("thread-b");
    expect(() =>
      taskDetail({
        ...base,
        evidence: [
          evidenceRecord({
            identity: sourceEvidenceKey(
              otherSource,
              task,
              otherThread,
              run,
              evidenceId("evidence_00000001"),
            ),
            kind: "fixture",
            summary: "Foreign evidence.",
            source: "deterministic-local-runner",
            verified: false,
            provenance: {
              sourceThread: sourceThreadKey(otherSource, otherThread),
              observedThrough: "task-detail",
            },
          }),
        ],
      }),
    ).toThrow(TypeError);
  });

  it("strips caller-only fields from every public task aggregate constructor", () => {
    const sourceThread = sourceThreadKey(source, thread);
    const sourceRun = sourceRunKey(source, thread, run);
    const lastEvent = sourceApplicationEventKey(source, task, thread, run, applicationEventId("1"));
    const facts = {
      cancellationConfirmed: false,
      pendingCurrentInterrupt: false,
      runActive: false,
      queued: true,
      terminalFailure: false,
      terminalSuccess: false,
      authRef: "facts-secret",
    };
    const summaryInput = {
      taskId: task,
      sourceThread: { ...sourceThread, authRef: "thread-secret" },
      run: { ...sourceRun, authRef: "run-secret" },
      title: "Bound task",
      objective: "Strip caller-only state.",
      facts,
      lastEvent: { ...lastEvent, authRef: "event-secret" },
      lastEventSequence: 1,
      authRef: "summary-secret",
    };
    const acceptedInput = {
      taskId: task,
      run: summaryInput.run,
      facts,
      authRef: "accepted-secret",
    };
    const detailInput = {
      ...summaryInput,
      evidence: [],
      authRef: "detail-secret",
    };
    const resultInput = {
      taskId: task,
      run: summaryInput.run,
      result: "Safe result.",
      authRef: "result-secret",
    };
    const accepted = taskAccepted(acceptedInput);
    const summary = taskSummary(summaryInput);
    const detail = taskDetail(detailInput);
    const result = taskResult(resultInput);

    for (const value of [accepted, summary, detail, result]) {
      expect(JSON.stringify(value)).not.toContain("secret");
      expect("authRef" in value).toBe(false);
      expect("authRef" in value.run).toBe(false);
    }
    expect("authRef" in summary.sourceThread).toBe(false);
    expect("authRef" in summary.lastEvent).toBe(false);
    expect("authRef" in summary.facts).toBe(false);
  });
});

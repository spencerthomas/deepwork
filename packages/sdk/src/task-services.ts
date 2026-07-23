import {
  decisionInput,
  EVENT_SEQUENCE_MAX,
  interruptId,
  objectiveText,
  pendingInterrupt,
  PLAN_REVISION_MAX,
  planEditInput,
  runId,
  sourceApplicationEventKeyString,
  sourceId,
  sourceInterruptKey,
  taskId as domainTaskId,
  threadId,
  type DecisionInput,
  type DecisionReceipt,
  type PlanEditInput,
  type PlanEditReceipt,
  type TaskAccepted,
  type TaskApplicationEvent,
  type TaskDetail,
  type TaskId,
  type TaskResult,
  type TaskSummary,
} from "@deepwork/domain";

import type { OperationOptions } from "./ports.js";
import {
  applicationProblemError,
  TaskTransportProblemError,
  type SdkError,
  type SdkResult,
} from "./result.js";
import {
  mapDecisionReceipt,
  mapPlanEditReceipt,
  mapTaskAccepted,
  mapTaskDetail,
  mapTaskEvent,
  mapTaskList,
  mapTaskResult,
  type TaskBindingResolver,
  type TaskEventMappingContext,
  type TaskMutationBindingResolver,
} from "./task-mapping.js";

export interface TaskQueryTransport {
  listTasks(options?: OperationOptions): Promise<unknown>;
  getTask(taskId: string, options?: OperationOptions): Promise<unknown>;
  getTaskResult(taskId: string, options?: OperationOptions): Promise<unknown>;
}

export interface TaskMutationTransport {
  createTask(request: Readonly<{ prompt: string }>, options?: OperationOptions): Promise<unknown>;
  recordDecision(
    taskId: string,
    request: Readonly<{
      interruptId: string;
      decision: "approve" | "reject" | "respond";
      comment?: string;
    }>,
    options?: OperationOptions,
  ): Promise<unknown>;
  updatePlan(
    taskId: string,
    request: Readonly<{
      interruptId: string;
      expectedRevision: number;
      steps: readonly string[];
    }>,
    options?: OperationOptions,
  ): Promise<unknown>;
}

export interface TaskTransportSubscription {
  unsubscribe(): void;
}

export interface TaskStreamTransportObserver {
  onEvent(name: unknown, id: unknown, data: unknown): void;
  onBoundary?(boundary: unknown): void;
  onDisconnect?(): void;
}

export interface TaskStreamTransport {
  subscribe(
    request: Readonly<{
      taskId: string;
      afterEventId?: string;
    }>,
    observer: TaskStreamTransportObserver,
    options?: OperationOptions,
  ): Promise<TaskTransportSubscription>;
}

export interface TaskQueryService {
  listTasks(options?: OperationOptions): Promise<SdkResult<readonly TaskSummary[]>>;
  getTask(taskId: TaskId, options?: OperationOptions): Promise<SdkResult<TaskDetail>>;
  getTaskResult(taskId: TaskId, options?: OperationOptions): Promise<SdkResult<TaskResult>>;
}

export interface TaskMutationService {
  createTask(objective: string, options?: OperationOptions): Promise<SdkResult<TaskAccepted>>;
  decide(
    taskId: TaskId,
    decision: DecisionInput,
    options?: OperationOptions,
  ): Promise<SdkResult<DecisionReceipt>>;
  editPlan(
    taskId: TaskId,
    edit: PlanEditInput,
    options?: OperationOptions,
  ): Promise<SdkResult<PlanEditReceipt>>;
}

export interface TaskStreamSubscription {
  readonly unsubscribe: () => void;
  readonly isQuarantined: () => boolean;
}

export interface TaskStreamObserver {
  onEvent(event: TaskApplicationEvent): void;
  onError(error: SdkError): void;
  onBoundary(boundary: TaskRecoveryBoundary): void;
  onDisconnect?(): void;
}

export const TASK_RECOVERY_BOUNDARY_KINDS = Object.freeze([
  "connected",
  "recovered",
  "hydrated",
] as const);

export type TaskRecoveryBoundaryKind = (typeof TASK_RECOVERY_BOUNDARY_KINDS)[number];

export type TaskRecoveryBoundary =
  | Readonly<{ kind: "connected"; authoritative: false }>
  | Readonly<{
      kind: "recovered" | "hydrated";
      authoritative: true;
      detail: TaskDetail;
      lastEventId: string;
      sequence: number;
    }>;

export interface TaskStreamService {
  subscribe(
    context: TaskEventMappingContext,
    observer: TaskStreamObserver,
    options?: OperationOptions & { readonly afterEventId?: string },
  ): Promise<SdkResult<TaskStreamSubscription>>;
}

function transportFailure(error: unknown): SdkResult<never> {
  if (error instanceof TaskTransportProblemError) {
    return Object.freeze({ ok: false, error: applicationProblemError(error) });
  }
  return Object.freeze({
    ok: false,
    error: Object.freeze({
      category: "unknown",
      safeMessage: "The Deep Work application transport failed.",
      retryable: false,
    }),
  });
}

function mutationInterrupt(
  task: TaskId,
  supplied: DecisionInput["interrupt"],
  bindings: TaskMutationBindingResolver,
): ReturnType<typeof pendingInterrupt> | undefined {
  const sourceThread = bindings.resolveTask(task);
  const current = bindings.resolveCurrentInterrupt(task);
  if (
    sourceThread === undefined ||
    current === undefined ||
    current.identity.taskId !== task ||
    supplied.sourceId !== sourceThread.sourceId ||
    supplied.threadId !== sourceThread.threadId ||
    current.identity.sourceId !== sourceThread.sourceId ||
    current.identity.threadId !== sourceThread.threadId ||
    current.identity.sourceId !== supplied.sourceId ||
    current.identity.taskId !== supplied.taskId ||
    current.identity.threadId !== supplied.threadId ||
    current.identity.runId !== supplied.runId ||
    current.identity.interruptId !== supplied.interruptId
  ) {
    return undefined;
  }
  try {
    return pendingInterrupt({
      identity: sourceInterruptKey(
        sourceId(current.identity.sourceId),
        domainTaskId(current.identity.taskId),
        threadId(current.identity.threadId),
        runId(current.identity.runId),
        interruptId(current.identity.interruptId),
      ),
      decisions: current.decisions,
      planRevision: current.planRevision,
      ...(current.question === undefined ? {} : { question: current.question }),
    });
  } catch {
    return undefined;
  }
}

function recoveryBoundary(
  value: unknown,
  context: TaskEventMappingContext,
  bindings: TaskBindingResolver,
): TaskRecoveryBoundary {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new TypeError("Task stream recovery boundary must be a record.");
  }
  const wire = value as Record<string, unknown>;
  if (wire.kind === "connected" && Object.keys(wire).length === 1) {
    return Object.freeze({ kind: "connected", authoritative: false });
  }
  if (
    (wire.kind === "recovered" || wire.kind === "hydrated") &&
    Object.keys(wire).length === 2 &&
    Object.hasOwn(wire, "detail")
  ) {
    const mapped = mapTaskDetail(wire.detail, bindings);
    if (
      !mapped.ok ||
      mapped.value.taskId !== context.taskId ||
      mapped.value.sourceThread.sourceId !== context.sourceThread.sourceId ||
      mapped.value.sourceThread.threadId !== context.sourceThread.threadId ||
      mapped.value.run.sourceId !== context.run.sourceId ||
      mapped.value.run.threadId !== context.run.threadId ||
      mapped.value.run.runId !== context.run.runId
    ) {
      throw new TypeError("Task stream recovery detail is not correlated.");
    }
    return Object.freeze({
      kind: wire.kind,
      authoritative: true,
      detail: mapped.value,
      lastEventId: String(mapped.value.lastEventSequence),
      sequence: mapped.value.lastEventSequence,
    });
  }
  throw new TypeError("Task stream recovery boundary is not accepted.");
}

export function createTaskQueryService(
  transport: TaskQueryTransport,
  bindings: TaskBindingResolver,
): TaskQueryService {
  return Object.freeze({
    async listTasks(options?: OperationOptions) {
      try {
        return mapTaskList(await transport.listTasks(options), bindings);
      } catch (error) {
        return transportFailure(error);
      }
    },
    async getTask(taskId: TaskId, options?: OperationOptions) {
      try {
        const mapped = mapTaskDetail(await transport.getTask(taskId, options), bindings);
        if (mapped.ok && mapped.value.taskId !== taskId) {
          return Object.freeze({
            ok: false,
            error: Object.freeze({
              category: "contract",
              safeMessage: "Task detail did not match the requested application task.",
              retryable: false,
            }),
          });
        }
        return mapped;
      } catch (error) {
        return transportFailure(error);
      }
    },
    async getTaskResult(taskId: TaskId, options?: OperationOptions) {
      try {
        const mapped = mapTaskResult(await transport.getTaskResult(taskId, options), bindings);
        if (mapped.ok && mapped.value.taskId !== taskId) {
          return Object.freeze({
            ok: false,
            error: Object.freeze({
              category: "contract",
              safeMessage: "Task result did not match the requested application task.",
              retryable: false,
            }),
          });
        }
        return mapped;
      } catch (error) {
        return transportFailure(error);
      }
    },
  });
}

export function createTaskMutationService(
  transport: TaskMutationTransport,
  bindings: TaskMutationBindingResolver,
): TaskMutationService {
  return Object.freeze({
    async createTask(objective: string, options?: OperationOptions) {
      let prompt: string;
      try {
        prompt = objectiveText(objective);
      } catch {
        return Object.freeze({
          ok: false,
          error: Object.freeze({
            category: "contract",
            safeMessage: "Task objective is invalid.",
            retryable: false,
          }),
        });
      }
      try {
        return mapTaskAccepted(
          await transport.createTask(Object.freeze({ prompt }), options),
          bindings,
        );
      } catch (error) {
        return transportFailure(error);
      }
    },
    async decide(taskId: TaskId, decision: DecisionInput, options?: OperationOptions) {
      let acceptedDecision: DecisionInput;
      try {
        acceptedDecision = decisionInput({
          interrupt: decision.interrupt,
          expectedPlanRevision: decision.expectedPlanRevision,
          decision: decision.decision,
          ...(decision.comment === undefined ? {} : { comment: decision.comment }),
        });
      } catch {
        return Object.freeze({
          ok: false,
          error: Object.freeze({
            category: "contract",
            safeMessage: "Decision input is invalid.",
            retryable: false,
          }),
        });
      }
      const currentInterrupt = mutationInterrupt(taskId, acceptedDecision.interrupt, bindings);
      if (currentInterrupt === undefined) {
        return Object.freeze({
          ok: false,
          error: Object.freeze({
            category: "contract",
            safeMessage: "Decision interrupt did not match the application task.",
            retryable: false,
          }),
        });
      }
      if (acceptedDecision.expectedPlanRevision !== currentInterrupt.planRevision) {
        return Object.freeze({
          ok: false,
          error: Object.freeze({
            category: "recovery-required",
            code: "interrupt_stale",
            recovery: "authoritative-refetch",
            safeMessage: "Interrupt is no longer actionable.",
            retryable: false,
          }),
        });
      }
      if (!currentInterrupt.decisions.includes(acceptedDecision.decision)) {
        return Object.freeze({
          ok: false,
          error: Object.freeze({
            category: "contract",
            safeMessage: "Decision is not allowed by the current interrupt.",
            retryable: false,
          }),
        });
      }
      const request = Object.freeze({
        interruptId: currentInterrupt.identity.interruptId,
        decision: acceptedDecision.decision,
        ...(acceptedDecision.comment === undefined ? {} : { comment: acceptedDecision.comment }),
      });
      try {
        return mapDecisionReceipt(
          await transport.recordDecision(taskId, request, options),
          taskId,
          Object.freeze({ ...acceptedDecision, interrupt: currentInterrupt.identity }),
        );
      } catch (error) {
        return transportFailure(error);
      }
    },
    async editPlan(taskId: TaskId, edit: PlanEditInput, options?: OperationOptions) {
      let acceptedEdit: PlanEditInput;
      try {
        acceptedEdit = planEditInput({
          interrupt: edit.interrupt,
          expectedRevision: edit.expectedRevision,
          steps: edit.steps,
        });
      } catch {
        return Object.freeze({
          ok: false,
          error: Object.freeze({
            category: "contract",
            safeMessage: "Plan edit input is invalid.",
            retryable: false,
          }),
        });
      }
      const currentInterrupt = mutationInterrupt(taskId, acceptedEdit.interrupt, bindings);
      if (currentInterrupt === undefined) {
        return Object.freeze({
          ok: false,
          error: Object.freeze({
            category: "contract",
            safeMessage: "Plan edit interrupt did not match the application task.",
            retryable: false,
          }),
        });
      }
      if (acceptedEdit.expectedRevision !== currentInterrupt.planRevision) {
        return Object.freeze({
          ok: false,
          error: Object.freeze({
            category: "recovery-required",
            code: "plan_revision_conflict",
            recovery: "authoritative-refetch",
            safeMessage: "Plan edit revision is stale; authoritative task state is required.",
            retryable: false,
          }),
        });
      }
      if (acceptedEdit.expectedRevision === PLAN_REVISION_MAX) {
        return Object.freeze({
          ok: false,
          error: Object.freeze({
            category: "contract",
            safeMessage: "Plan revision cannot advance beyond the accepted maximum.",
            retryable: false,
          }),
        });
      }
      const request = Object.freeze({
        interruptId: currentInterrupt.identity.interruptId,
        expectedRevision: acceptedEdit.expectedRevision,
        steps: Object.freeze([...acceptedEdit.steps]),
      });
      try {
        return mapPlanEditReceipt(
          await transport.updatePlan(taskId, request, options),
          taskId,
          Object.freeze({ ...acceptedEdit, interrupt: currentInterrupt.identity }),
        );
      } catch (error) {
        return transportFailure(error);
      }
    },
  });
}

export function createTaskStreamService(
  transport: TaskStreamTransport,
  bindings: TaskBindingResolver,
): TaskStreamService {
  return Object.freeze({
    async subscribe(
      context: TaskEventMappingContext,
      observer: TaskStreamObserver,
      options?: OperationOptions & { readonly afterEventId?: string },
    ) {
      let active = true;
      let quarantined = false;
      let boundaryObserved = false;
      let lastSequence: number | undefined;
      let assertedCursor: number | undefined;
      const seenEvents = new Map<string, string>();
      if (options?.afterEventId !== undefined) {
        if (
          !/^[1-9][0-9]*$/.test(options.afterEventId) ||
          !Number.isSafeInteger(Number(options.afterEventId)) ||
          Number(options.afterEventId) > EVENT_SEQUENCE_MAX
        ) {
          return Object.freeze({
            ok: false,
            error: Object.freeze({
              category: "contract",
              safeMessage: "Stream replay cursor is invalid.",
              retryable: false,
            }),
          });
        }
        lastSequence = Number(options.afterEventId);
        assertedCursor = lastSequence;
      }
      let subscription: TaskTransportSubscription;
      try {
        subscription = await transport.subscribe(
          Object.freeze({
            taskId: context.taskId,
            ...(options?.afterEventId === undefined ? {} : { afterEventId: options.afterEventId }),
          }),
          {
            onBoundary(value) {
              if (!active || quarantined) {
                return;
              }
              let mapped: TaskRecoveryBoundary;
              try {
                mapped = recoveryBoundary(value, context, bindings);
              } catch {
                quarantined = true;
                observer.onError(
                  Object.freeze({
                    category: "contract",
                    safeMessage: "Task stream recovery boundary is invalid.",
                    retryable: false,
                  }),
                );
                return;
              }
              if (
                mapped.authoritative &&
                lastSequence !== undefined &&
                mapped.sequence < lastSequence
              ) {
                quarantined = true;
                observer.onError(
                  Object.freeze({
                    category: "contract",
                    safeMessage: "Task stream recovery cursor moved backwards.",
                    retryable: false,
                  }),
                );
                return;
              }
              boundaryObserved = true;
              if (mapped.authoritative) {
                lastSequence = mapped.sequence;
                assertedCursor = mapped.sequence;
              }
              observer.onBoundary(mapped);
            },
            onEvent(name, id, data) {
              if (!active || quarantined) {
                return;
              }
              if (!boundaryObserved) {
                boundaryObserved = true;
                observer.onBoundary(Object.freeze({ kind: "connected", authoritative: false }));
              }
              const mapped = mapTaskEvent(name, id, data, context);
              if (mapped.ok) {
                const eventKey = sourceApplicationEventKeyString(mapped.value.identity);
                const fingerprint = JSON.stringify(mapped.value);
                const previous = seenEvents.get(eventKey);
                if (previous !== undefined) {
                  if (previous === fingerprint) {
                    return;
                  }
                  quarantined = true;
                  observer.onError(
                    Object.freeze({
                      category: "contract",
                      safeMessage: "Task event replay conflicts with the accepted event.",
                      retryable: false,
                    }),
                  );
                  return;
                }
                if (assertedCursor !== undefined && mapped.value.sequence <= assertedCursor) {
                  return;
                }
                if (
                  (lastSequence === undefined && mapped.value.sequence !== 1) ||
                  (lastSequence !== undefined && mapped.value.sequence !== lastSequence + 1)
                ) {
                  quarantined = true;
                  observer.onError(
                    Object.freeze({
                      category: "contract",
                      safeMessage:
                        "Task event sequence is incomplete; authoritative hydration is required.",
                      retryable: false,
                    }),
                  );
                  return;
                }
                lastSequence = mapped.value.sequence;
                seenEvents.set(eventKey, fingerprint);
                if (seenEvents.size > 2_048) {
                  const oldest = seenEvents.keys().next().value;
                  if (oldest !== undefined) {
                    seenEvents.delete(oldest);
                  }
                }
                observer.onEvent(mapped.value);
              } else {
                quarantined = true;
                observer.onError(mapped.error);
              }
            },
            onDisconnect() {
              if (active) {
                boundaryObserved = false;
                observer.onDisconnect?.();
              }
            },
          },
          options,
        );
      } catch (error) {
        return transportFailure(error);
      }
      if (active && !quarantined && !boundaryObserved) {
        boundaryObserved = true;
        observer.onBoundary(Object.freeze({ kind: "connected", authoritative: false }));
      }
      return Object.freeze({
        ok: true,
        value: Object.freeze({
          isQuarantined() {
            return quarantined;
          },
          unsubscribe() {
            if (!active) {
              return;
            }
            active = false;
            subscription.unsubscribe();
          },
        }),
      });
    },
  });
}

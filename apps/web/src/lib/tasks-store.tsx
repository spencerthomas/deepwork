"use client";

import type { ReactNode } from "react";
import { usePathname } from "next/navigation";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  recoverCurrentTaskAfterDecisionProblem,
  recoverCurrentTaskAfterPlanProblem,
} from "./plan-recovery";
import { taskClient } from "./task-client";
import {
  detailAfterAcceptedDecision,
  detailAfterAuthoritativeReload,
  detailAwaitingApprovalReload,
  decisionBatchPreflightProblem,
  decisionPreflightProblem,
  getActiveInterrupt,
  getCompletionResultText,
  interruptAfterEvent,
  isTerminalStatus,
  reduceEventsIntoDetail,
  statusAfterEvent,
  summaryAfterAuthoritativeReload,
  taskEventCursor,
} from "./task-normalizers";
import { appendUniqueTaskEvent } from "./task-event-index";
import {
  sameTaskDetailProjection,
  sameTaskSummaryProjection,
  shouldRefreshAuthoritativeTask,
} from "./task-refresh-policy";
import type {
  ConnectionState,
  DecisionBatchInput,
  DecisionInput,
  PlanUpdateInput,
  TaskDetail,
  TaskEvent,
  TaskSummary,
} from "./task-types";

const AUTHORITATIVE_REFRESH_INTERVAL_MS = 2_000;

function messageFrom(error: unknown): string {
  return error instanceof Error ? error.message : "Something unexpected happened.";
}

function replaceTask(
  tasks: TaskSummary[],
  taskId: string,
  update: (task: TaskSummary) => TaskSummary,
): TaskSummary[] {
  let changed = false;
  const next = tasks.map((task) => {
    if (task.taskId !== taskId) return task;
    const updated = update(task);
    changed ||= updated !== task;
    return updated;
  });
  return changed ? next : tasks;
}

export interface TasksStore {
  tasks: TaskSummary[];
  loadingTasks: boolean;
  listError?: string;
  refreshList: () => void;

  creating: boolean;
  createError?: string;
  createTask: (
    prompt: string,
    agentId?: string,
    journey?: "general" | "coding",
  ) => Promise<TaskSummary | undefined>;

  detailsByTask: Record<string, TaskDetail>;
  eventsByTask: Record<string, TaskEvent[]>;
  loadDetail: (taskId: string) => Promise<TaskDetail | undefined>;

  activeTaskId?: string;
  setActiveTaskId: (taskId: string | undefined) => void;
  connectionState: ConnectionState;
  streamRecovery?: {
    taskId: string;
    state: "recovering" | "recovered" | "unconfirmed" | "failed";
    message: string;
  };
  detailError?: string;
  streamError?: string;
  actionError?: string;
  planError?: string;
  cancelError?: string;
  submittingDecision: boolean;
  submittedDecision?: DecisionInput["decision"];
  updatingPlan: boolean;
  cancelling: boolean;
  decide: (input: DecisionInput) => Promise<void>;
  decideForTask: (taskId: string, input: DecisionInput) => Promise<string | undefined>;
  decideBatch: (input: DecisionBatchInput) => Promise<void>;
  decideBatchForTask: (taskId: string, input: DecisionBatchInput) => Promise<string | undefined>;
  updatePlan: (input: PlanUpdateInput) => Promise<boolean>;
  cancelTask: (taskId: string) => Promise<string | undefined>;

  mode: typeof taskClient.mode;
  apiBaseUrl: string;
}

const TasksStoreContext = createContext<TasksStore | undefined>(undefined);

export function TasksProvider({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const sessionRequired = pathname !== "/login";
  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [activeTaskId, setActiveTaskId] = useState<string>();
  const [detailsByTask, setDetailsByTask] = useState<Record<string, TaskDetail>>({});
  const [eventsByTask, setEventsByTask] = useState<Record<string, TaskEvent[]>>({});
  const [connectionState, setConnectionState] = useState<ConnectionState>("closed");
  const [streamRecovery, setStreamRecovery] = useState<TasksStore["streamRecovery"]>();
  const [listError, setListError] = useState<string>();
  const [detailError, setDetailError] = useState<string>();
  const [streamError, setStreamError] = useState<string>();
  const [createError, setCreateError] = useState<string>();
  const [actionError, setActionError] = useState<string>();
  const [planError, setPlanError] = useState<string>();
  const [cancelError, setCancelError] = useState<string>();
  const [loadingTasks, setLoadingTasks] = useState(true);
  const [creating, setCreating] = useState(false);
  const [submittingDecision, setSubmittingDecision] = useState(false);
  const [updatingPlan, setUpdatingPlan] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const [submittedDecision, setSubmittedDecision] = useState<DecisionInput["decision"]>();
  const [listAttempt, setListAttempt] = useState(0);
  const eventsByTaskRef = useRef<Record<string, TaskEvent[]>>({});
  const seenEventIdsByTaskRef = useRef<Record<string, Set<string>>>({});
  const decisionRequestRef = useRef(0);
  const decisionSubmissionRef = useRef<{ requestId: number; taskId: string } | undefined>(
    undefined,
  );
  const taskDecisionSubmissionIdsRef = useRef<Set<string>>(new Set());
  const pendingDecisionRef = useRef<
    | {
        interruptId: string;
        requestId: number;
        taskId: string;
      }
    | undefined
  >(undefined);
  const activeTaskIdRef = useRef<string | undefined>(activeTaskId);
  activeTaskIdRef.current = activeTaskId;
  const detailsByTaskRef = useRef(detailsByTask);
  detailsByTaskRef.current = detailsByTask;
  const tasksRef = useRef(tasks);
  tasksRef.current = tasks;

  useEffect(() => {
    if (!sessionRequired) {
      setLoadingTasks(false);
      return;
    }
    const controller = new AbortController();
    setLoadingTasks(true);
    setListError(undefined);

    void taskClient
      .listTasks(controller.signal)
      .then((items) => {
        setTasks((current) => {
          const currentById = new Map(current.map((task) => [task.taskId, task] as const));
          const incomingIds = new Set(items.map((task) => task.taskId));
          return [
            ...items.map((task) => {
              const existing = currentById.get(task.taskId);
              return existing ? { ...task, status: existing.status } : task;
            }),
            ...current.filter((task) => !incomingIds.has(task.taskId)),
          ];
        });
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          setListError(messageFrom(error));
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setLoadingTasks(false);
        }
      });

    return () => controller.abort();
  }, [listAttempt, sessionRequired]);

  useEffect(() => {
    if (!activeTaskId) {
      setConnectionState("closed");
      return;
    }

    const controller = new AbortController();
    setDetailError(undefined);
    setStreamError(undefined);
    setStreamRecovery(undefined);
    setSubmittedDecision(undefined);
    setSubmittingDecision(false);
    setActionError(undefined);
    setPlanError(undefined);
    setCancelError(undefined);
    setCancelling(false);
    decisionRequestRef.current += 1;
    pendingDecisionRef.current = undefined;

    let recoveryStarted = false;
    const applyAuthoritativeTask = (task: TaskDetail) => {
      if (controller.signal.aborted || activeTaskIdRef.current !== activeTaskId) return;
      const taskWithEarlyEvents = reduceEventsIntoDetail(
        task,
        eventsByTaskRef.current[activeTaskId] ?? [],
      );
      const currentDetails = detailsByTaskRef.current;
      const existing = currentDetails[activeTaskId];
      const nextTask = existing
        ? sameTaskDetailProjection(existing, taskWithEarlyEvents)
          ? existing
          : detailAfterAuthoritativeReload(existing, taskWithEarlyEvents)
        : taskWithEarlyEvents;
      if (nextTask !== existing) {
        const nextDetails = { ...currentDetails, [activeTaskId]: nextTask };
        detailsByTaskRef.current = nextDetails;
        setDetailsByTask(nextDetails);
      }
      const nextTasks = replaceTask(tasksRef.current, activeTaskId, (current) =>
        sameTaskSummaryProjection(current, taskWithEarlyEvents)
          ? current
          : summaryAfterAuthoritativeReload(current, taskWithEarlyEvents),
      );
      if (nextTasks !== tasksRef.current) {
        tasksRef.current = nextTasks;
        setTasks(nextTasks);
      }
    };
    void taskClient
      .getTask(activeTaskId, controller.signal)
      .then(applyAuthoritativeTask)
      .catch((error: unknown) => {
        if (!controller.signal.aborted && !recoveryStarted) {
          setDetailError(messageFrom(error));
        }
      });

    let disconnectEpisodeOpen = false;
    let recoveryRequest = 0;
    let recoveryController: AbortController | undefined;
    const recoverFromDisconnect = () => {
      if (disconnectEpisodeOpen) return;
      disconnectEpisodeOpen = true;
      recoveryStarted = true;
      const request = recoveryRequest + 1;
      recoveryRequest = request;
      recoveryController?.abort();
      recoveryController = new AbortController();
      const recoverySignal = AbortSignal.any([
        controller.signal,
        recoveryController.signal,
        AbortSignal.timeout(15_000),
      ]);
      setStreamRecovery({
        taskId: activeTaskId,
        state: "recovering",
        message: "Checking the API for the latest durable task state…",
      });

      void taskClient
        .getTask(activeTaskId, recoverySignal)
        .then((authoritativeTask) => {
          if (
            controller.signal.aborted ||
            activeTaskIdRef.current !== activeTaskId ||
            recoveryRequest !== request
          ) {
            return;
          }
          const retainedEvents = eventsByTaskRef.current[activeTaskId] ?? [];
          const eventsAfterSnapshot = retainedEvents.filter((event) => {
            const cursor = taskEventCursor(event.id);
            return (
              authoritativeTask.lastEventId === undefined ||
              cursor === undefined ||
              cursor > authoritativeTask.lastEventId
            );
          });
          const reducedTask = reduceEventsIntoDetail(authoritativeTask, eventsAfterSnapshot);
          const currentDetails = detailsByTaskRef.current;
          const streamed = currentDetails[activeTaskId];
          const nextTask = streamed
            ? detailAfterAuthoritativeReload(streamed, reducedTask)
            : reducedTask;
          const currentTasks = tasksRef.current;
          const currentSummary = currentTasks.find((task) => task.taskId === activeTaskId);
          const nextSummary = currentSummary
            ? summaryAfterAuthoritativeReload(currentSummary, reducedTask)
            : undefined;
          const recoveryConfirmed =
            (streamed === undefined || nextTask === reducedTask) &&
            (currentSummary === undefined || nextSummary === reducedTask);
          if (nextTask !== streamed) {
            const nextDetails = { ...currentDetails, [activeTaskId]: nextTask };
            detailsByTaskRef.current = nextDetails;
            setDetailsByTask(nextDetails);
          }
          const nextTasks = replaceTask(currentTasks, activeTaskId, (current) =>
            summaryAfterAuthoritativeReload(current, reducedTask),
          );
          if (nextTasks !== currentTasks) {
            tasksRef.current = nextTasks;
            setTasks(nextTasks);
          }
          setStreamRecovery(
            recoveryConfirmed
              ? {
                  taskId: activeTaskId,
                  state: "recovered",
                  message:
                    "Recovered current task state from the API while the live stream reconnects.",
                }
              : {
                  taskId: activeTaskId,
                  state: "unconfirmed",
                  message:
                    "The live stream is newer than the API snapshot. The last known state is shown, but durable recovery is not yet confirmed.",
                },
          );
        })
        .catch((error: unknown) => {
          if (
            controller.signal.aborted ||
            activeTaskIdRef.current !== activeTaskId ||
            recoveryRequest !== request
          ) {
            return;
          }
          setStreamRecovery({
            taskId: activeTaskId,
            state: "failed",
            message: `Could not recover current task state from the API. The last known state is still shown while the live stream reconnects. ${messageFrom(error)}`,
          });
        });
    };

    let lastSourceActivityAt = Date.now();
    let closeStream: () => void = () => undefined;
    closeStream = taskClient.subscribe(activeTaskId, {
      onConnectionChange: (state) => {
        setConnectionState(state);
        if (state === "connected") {
          lastSourceActivityAt = Date.now();
          disconnectEpisodeOpen = false;
          setStreamError(undefined);
        } else if (state === "reconnecting") {
          recoverFromDisconnect();
        }
      },
      onError: setStreamError,
      onEvent: (event) => {
        lastSourceActivityAt = Date.now();
        const streamedCursor = taskEventCursor(event.id);
        const eventsBeforeEvent = eventsByTaskRef.current[activeTaskId] ?? [];
        const seenEventIds =
          seenEventIdsByTaskRef.current[activeTaskId] ??
          new Set(eventsBeforeEvent.map((candidate) => candidate.id));
        seenEventIdsByTaskRef.current[activeTaskId] = seenEventIds;
        const nextTaskEvents = appendUniqueTaskEvent(eventsBeforeEvent, seenEventIds, event);
        if (nextTaskEvents === undefined) {
          // A reopened completed task may replay its retained terminal event.
          // The state transition is already applied, but this new subscription
          // still needs to close instead of remaining connected forever.
          if (event.name === "run.completed") {
            setStreamError(undefined);
            closeStream();
          }
          return;
        }
        setStreamRecovery((current) =>
          current?.taskId === activeTaskId && current.state !== "recovered" ? undefined : current,
        );
        const activeBeforeEvent = getActiveInterrupt(eventsBeforeEvent);
        const nextEventsByTask = {
          ...eventsByTaskRef.current,
          [activeTaskId]: nextTaskEvents,
        };
        eventsByTaskRef.current = nextEventsByTask;
        setEventsByTask(nextEventsByTask);
        setDetailsByTask((current) => {
          const task = current[activeTaskId];
          if (!task) {
            return current;
          }
          const eventResult =
            event.name === "run.completed" ? getCompletionResultText(event) : undefined;
          const streamedTask = {
            ...task,
            pendingInterrupt: interruptAfterEvent(task.pendingInterrupt, event),
            status: statusAfterEvent(task.status, event, task.pendingInterrupt),
            result: eventResult ?? task.result,
            lastEventId: streamedCursor ?? task.lastEventId,
          };
          const nextTask =
            streamedCursor !== undefined &&
            task.lastEventId !== undefined &&
            streamedCursor <= task.lastEventId
              ? detailAfterAuthoritativeReload(task, streamedTask)
              : streamedTask;
          if (nextTask === task) return current;
          return {
            ...current,
            [activeTaskId]: nextTask,
          };
        });
        setTasks((current) =>
          replaceTask(current, activeTaskId, (task) => {
            const streamedTask = {
              ...task,
              status: statusAfterEvent(task.status, event, activeBeforeEvent),
              lastEventId: streamedCursor ?? task.lastEventId,
            };
            return streamedCursor !== undefined &&
              task.lastEventId !== undefined &&
              streamedCursor <= task.lastEventId
              ? summaryAfterAuthoritativeReload(task, streamedTask)
              : streamedTask;
          }),
        );
        if (event.name === "decision.recorded") {
          const pending = pendingDecisionRef.current;
          if (
            pending?.taskId === activeTaskId &&
            event.data.interruptId === pending.interruptId &&
            (event.data.decision === "approve" ||
              event.data.decision === "reject" ||
              event.data.decision === "respond")
          ) {
            pendingDecisionRef.current = undefined;
            setSubmittedDecision(undefined);
            setSubmittingDecision(false);
            setActionError(undefined);
          }
        }
        if (event.name === "run.completed") {
          const streamedResult = getCompletionResultText(event);
          const streamedStatus = statusAfterEvent("running", event);
          setStreamError(undefined);
          closeStream();
          if (!isTerminalStatus(streamedStatus)) {
            setDetailError(
              "The completion event did not include a valid terminal status. Checking the authoritative task result…",
            );
          }
          void taskClient
            .getTask(activeTaskId, controller.signal)
            .then((authoritativeTask) => {
              const reducedTask = reduceEventsIntoDetail(
                authoritativeTask,
                eventsByTaskRef.current[activeTaskId] ?? [],
              );
              const finalTask = {
                ...reducedTask,
                status: isTerminalStatus(streamedStatus)
                  ? streamedStatus
                  : isTerminalStatus(authoritativeTask.status)
                    ? authoritativeTask.status
                    : reducedTask.status,
                result: authoritativeTask.result ?? reducedTask.result,
              };
              setDetailsByTask((current) => ({
                ...current,
                [activeTaskId]: finalTask,
              }));
              setTasks((current) => replaceTask(current, activeTaskId, () => finalTask));
              setDetailError(
                isTerminalStatus(finalTask.status)
                  ? undefined
                  : "The API returned a nonterminal status after the run stream completed.",
              );
            })
            .catch((error: unknown) => {
              if (
                !controller.signal.aborted &&
                (!streamedResult || !isTerminalStatus(streamedStatus))
              ) {
                setDetailError(
                  `The run completed, but its result could not be loaded. ${messageFrom(error)}`,
                );
              }
            });
        }
      },
    });

    let authoritativeRefreshInFlight = false;
    let authoritativeRefreshErrorActive = false;
    const authoritativeRefresh = window.setInterval(() => {
      const current = detailsByTaskRef.current[activeTaskId];
      if (
        !shouldRefreshAuthoritativeTask(current, {
          inFlight: authoritativeRefreshInFlight,
          silentForMs: Date.now() - lastSourceActivityAt,
        })
      ) {
        return;
      }
      authoritativeRefreshInFlight = true;
      void taskClient
        .getTask(activeTaskId, controller.signal)
        .then((task) => {
          applyAuthoritativeTask(task);
          lastSourceActivityAt = Date.now();
          if (authoritativeRefreshErrorActive) {
            authoritativeRefreshErrorActive = false;
            setDetailError(undefined);
          }
        })
        .catch((error: unknown) => {
          lastSourceActivityAt = Date.now();
          if (controller.signal.aborted || activeTaskIdRef.current !== activeTaskId) return;
          authoritativeRefreshErrorActive = true;
          setDetailError(
            `Live progress could not be reconciled with the task API. ${messageFrom(error)}`,
          );
        })
        .finally(() => {
          authoritativeRefreshInFlight = false;
        });
    }, AUTHORITATIVE_REFRESH_INTERVAL_MS);

    return () => {
      window.clearInterval(authoritativeRefresh);
      controller.abort();
      recoveryController?.abort();
      closeStream();
    };
  }, [activeTaskId]);

  const refreshList = useCallback(() => {
    setListAttempt((current) => current + 1);
  }, []);

  const loadDetail = useCallback(async (taskId: string): Promise<TaskDetail | undefined> => {
    try {
      const task = await taskClient.getTask(taskId);
      const reduced = reduceEventsIntoDetail(task, eventsByTaskRef.current[taskId] ?? []);
      setDetailsByTask((current) => ({ ...current, [taskId]: reduced }));
      setTasks((current) => replaceTask(current, taskId, () => reduced));
      return reduced;
    } catch {
      return undefined;
    }
  }, []);

  const createTask = useCallback(
    async (
      prompt: string,
      agentId?: string,
      journey: "general" | "coding" = "general",
    ): Promise<TaskSummary | undefined> => {
      setCreating(true);
      setCreateError(undefined);
      try {
        // Stamp the dispatch instant *before* awaiting the create call, so the
        // optimistic createdAt reflects when this task was dispatched rather than
        // when the response happened to arrive — concurrent creates then keep
        // dispatch order in the newest-first "Recent" view. It is the client's
        // firsthand time of its own action, not a guessed value, and is replaced by
        // the server's authoritative createdAt on the next list refresh.
        const dispatchedAt = new Date().toISOString();
        const created = await taskClient.createTask(prompt, {
          ...(agentId ? { agentId } : {}),
          ...(journey === "coding" ? { journey: "coding" as const } : {}),
        });
        const optimisticTask: TaskSummary = {
          ...created,
          agentId,
          title: prompt,
          prompt,
          createdAt: dispatchedAt,
          ...(journey === "coding" ? { journey: "coding" as const } : {}),
        };
        setDetailsByTask((current) => ({
          ...current,
          [created.taskId]: optimisticTask,
        }));
        setTasks((current) => [
          optimisticTask,
          ...current.filter((task) => task.taskId !== created.taskId),
        ]);
        setListError(undefined);
        return optimisticTask;
      } catch (error) {
        setCreateError(messageFrom(error));
        return undefined;
      } finally {
        setCreating(false);
      }
    },
    [],
  );

  const reconcileTaskSnapshot = useCallback(
    (taskId: string, authoritativeTask: TaskDetail): TaskDetail => {
      const currentDetails = detailsByTaskRef.current;
      const streamedDetail = currentDetails[taskId];
      const currentTask = streamedDetail
        ? detailAfterAuthoritativeReload(streamedDetail, authoritativeTask)
        : authoritativeTask;
      if (currentTask !== streamedDetail) {
        const nextDetails = { ...currentDetails, [taskId]: currentTask };
        detailsByTaskRef.current = nextDetails;
        setDetailsByTask(nextDetails);
      }

      const currentTasks = tasksRef.current;
      const nextTasks = replaceTask(currentTasks, taskId, (streamedSummary) =>
        summaryAfterAuthoritativeReload(streamedSummary, currentTask),
      );
      if (nextTasks !== currentTasks) {
        tasksRef.current = nextTasks;
        setTasks(nextTasks);
      }
      return currentTask;
    },
    [],
  );

  const decide = useCallback(
    async (input: DecisionInput): Promise<void> => {
      const taskId = activeTaskIdRef.current;
      if (!taskId) {
        return;
      }
      if (decisionSubmissionRef.current?.taskId === taskId) return;

      const requestId = decisionRequestRef.current + 1;
      decisionRequestRef.current = requestId;
      decisionSubmissionRef.current = { taskId, requestId };
      pendingDecisionRef.current = {
        taskId,
        interruptId: input.interruptId,
        requestId,
      };
      setSubmittingDecision(true);
      setActionError(undefined);
      try {
        const authoritativeTask = await taskClient.getTask(taskId, AbortSignal.timeout(15_000));
        const currentTask = reconcileTaskSnapshot(taskId, authoritativeTask);
        if (
          activeTaskIdRef.current !== taskId ||
          pendingDecisionRef.current?.requestId !== requestId
        ) {
          return;
        }
        const preflightProblem =
          decisionPreflightProblem(authoritativeTask, input) ??
          decisionPreflightProblem(currentTask, input);
        if (preflightProblem !== undefined) {
          pendingDecisionRef.current = undefined;
          setSubmittedDecision(undefined);
          setSubmittingDecision(false);
          setActionError(preflightProblem);
          return;
        }
        const receipt = await taskClient.decide(taskId, input);
        const expectedRunId =
          detailsByTaskRef.current[taskId]?.runId ??
          tasksRef.current.find((task) => task.taskId === taskId)?.runId;
        if (
          receipt.taskId !== taskId ||
          receipt.interruptId !== input.interruptId ||
          receipt.decision !== input.decision ||
          (expectedRunId !== undefined && receipt.runId !== expectedRunId)
        ) {
          throw new Error(
            "The decision receipt did not match the selected task, run, and interrupt.",
          );
        }
        if (receipt.duplicate) {
          reconcileTaskSnapshot(taskId, await taskClient.getTask(taskId));
        } else {
          // A matching new receipt means the authoritative API accepted this
          // interrupt and resumed the task. Reflect that running state immediately
          // while SSE carries the same decision event and eventual completion.
          setDetailsByTask((current) => {
            const task = current[taskId];
            if (!task) {
              return current;
            }
            const updated = detailAfterAcceptedDecision(task, input.interruptId);
            if (updated === task) return current;
            return {
              ...current,
              [taskId]: updated,
            };
          });
          // Do not optimistically rewrite the list summary: a decision event may
          // already have advanced it to a newer interrupt or terminal state.
          // The active detail above is enough for immediate feedback, and the
          // authoritative stream/detail reload owns the summary.
        }
        if (
          pendingDecisionRef.current?.requestId === requestId &&
          activeTaskIdRef.current === taskId
        ) {
          setSubmittedDecision(input.decision);
        }
      } catch (error) {
        if (
          pendingDecisionRef.current?.requestId === requestId &&
          activeTaskIdRef.current === taskId
        ) {
          try {
            const currentTask = await recoverCurrentTaskAfterDecisionProblem(
              taskClient,
              taskId,
              error,
            );
            if (currentTask) {
              reconcileTaskSnapshot(taskId, currentTask);
              pendingDecisionRef.current = undefined;
              setSubmittedDecision(undefined);
              setSubmittingDecision(false);
              setActionError(
                `${messageFrom(error)} The current task and interruption were reloaded. Review the available actions before deciding again.`,
              );
            } else {
              setActionError(messageFrom(error));
            }
          } catch (refreshError) {
            setActionError(
              `${messageFrom(error)} Deep Work could not reload the current interruption: ${messageFrom(refreshError)}`,
            );
          }
        }
      } finally {
        if (decisionSubmissionRef.current?.requestId === requestId) {
          decisionSubmissionRef.current = undefined;
        }
        if (
          pendingDecisionRef.current?.requestId === requestId &&
          activeTaskIdRef.current === taskId
        ) {
          setSubmittingDecision(false);
        }
      }
    },
    [reconcileTaskSnapshot],
  );

  /**
   * Decision path for tasks that are not the streaming active task (the
   * approvals inbox). Returns an error message on failure, undefined on
   * success. Always reloads the task detail afterwards so callers see the
   * authoritative state.
   */
  const decideForTask = useCallback(
    async (taskId: string, input: DecisionInput): Promise<string | undefined> => {
      if (taskDecisionSubmissionIdsRef.current.has(taskId)) {
        return "A decision is already being checked for this approval. No second decision was sent.";
      }
      taskDecisionSubmissionIdsRef.current.add(taskId);
      try {
        const authoritativeTask = await taskClient.getTask(taskId, AbortSignal.timeout(15_000));
        const currentTask = reconcileTaskSnapshot(taskId, authoritativeTask);
        const preflightProblem =
          decisionPreflightProblem(authoritativeTask, input) ??
          decisionPreflightProblem(currentTask, input);
        if (preflightProblem !== undefined) {
          return preflightProblem;
        }
        const receipt = await taskClient.decide(taskId, input);
        const expectedRunId =
          detailsByTaskRef.current[taskId]?.runId ??
          tasksRef.current.find((task) => task.taskId === taskId)?.runId;
        if (
          receipt.taskId !== taskId ||
          receipt.interruptId !== input.interruptId ||
          receipt.decision !== input.decision ||
          (expectedRunId !== undefined && receipt.runId !== expectedRunId)
        ) {
          return "The decision receipt did not match the task, run, and interrupt.";
        }
        await loadDetail(taskId);
        return undefined;
      } catch (error) {
        try {
          const currentTask = await recoverCurrentTaskAfterDecisionProblem(
            taskClient,
            taskId,
            error,
          );
          if (currentTask) {
            reconcileTaskSnapshot(taskId, currentTask);
            return `${messageFrom(error)} The task was reloaded — review it before deciding again.`;
          }
        } catch {
          // fall through to the original error
        }
        return messageFrom(error);
      } finally {
        taskDecisionSubmissionIdsRef.current.delete(taskId);
      }
    },
    [loadDetail, reconcileTaskSnapshot],
  );

  const decideBatch = useCallback(
    async (input: DecisionBatchInput): Promise<void> => {
      const taskId = activeTaskIdRef.current;
      if (!taskId || decisionSubmissionRef.current?.taskId === taskId) return;
      const requestId = decisionRequestRef.current + 1;
      decisionRequestRef.current = requestId;
      decisionSubmissionRef.current = { taskId, requestId };
      pendingDecisionRef.current = { taskId, interruptId: input.interruptId, requestId };
      setSubmittingDecision(true);
      setSubmittedDecision(undefined);
      setActionError(undefined);
      try {
        const authoritativeTask = await taskClient.getTask(taskId, AbortSignal.timeout(15_000));
        const currentTask = reconcileTaskSnapshot(taskId, authoritativeTask);
        if (
          activeTaskIdRef.current !== taskId ||
          pendingDecisionRef.current?.requestId !== requestId
        ) {
          return;
        }
        const problem =
          decisionBatchPreflightProblem(authoritativeTask, input) ??
          decisionBatchPreflightProblem(currentTask, input);
        if (problem) {
          setActionError(problem);
          return;
        }
        const receipt = await taskClient.decideBatch(taskId, input);
        const expectedRunId =
          detailsByTaskRef.current[taskId]?.runId ??
          tasksRef.current.find((task) => task.taskId === taskId)?.runId;
        if (
          receipt.taskId !== taskId ||
          receipt.interruptId !== input.interruptId ||
          receipt.version !== input.expectedVersion ||
          (expectedRunId !== undefined && receipt.runId !== expectedRunId)
        ) {
          throw new Error(
            "The ordered decision receipt did not match the selected task, run, interrupt, and version.",
          );
        }
        if (receipt.duplicate) {
          reconcileTaskSnapshot(taskId, await taskClient.getTask(taskId));
        } else {
          setDetailsByTask((current) => {
            const task = current[taskId];
            if (!task) return current;
            const updated = detailAfterAcceptedDecision(task, input.interruptId);
            return updated === task ? current : { ...current, [taskId]: updated };
          });
        }
      } catch (error) {
        if (
          pendingDecisionRef.current?.requestId === requestId &&
          activeTaskIdRef.current === taskId
        ) {
          try {
            const currentTask = await recoverCurrentTaskAfterDecisionProblem(
              taskClient,
              taskId,
              error,
            );
            if (currentTask) {
              reconcileTaskSnapshot(taskId, currentTask);
              setActionError(
                `${messageFrom(error)} The current task and ordered approval were reloaded. Review every action before submitting again.`,
              );
            } else {
              setActionError(messageFrom(error));
            }
          } catch (refreshError) {
            setActionError(
              `${messageFrom(error)} Deep Work could not reload the current ordered approval: ${messageFrom(refreshError)}`,
            );
          }
        }
      } finally {
        if (decisionSubmissionRef.current?.requestId === requestId)
          decisionSubmissionRef.current = undefined;
        if (pendingDecisionRef.current?.requestId === requestId)
          pendingDecisionRef.current = undefined;
        if (activeTaskIdRef.current === taskId) setSubmittingDecision(false);
      }
    },
    [reconcileTaskSnapshot],
  );

  const decideBatchForTask = useCallback(
    async (taskId: string, input: DecisionBatchInput): Promise<string | undefined> => {
      if (taskDecisionSubmissionIdsRef.current.has(taskId)) {
        return "A decision is already being checked for this approval. No second decision was sent.";
      }
      taskDecisionSubmissionIdsRef.current.add(taskId);
      try {
        const authoritativeTask = await taskClient.getTask(taskId, AbortSignal.timeout(15_000));
        const currentTask = reconcileTaskSnapshot(taskId, authoritativeTask);
        const problem =
          decisionBatchPreflightProblem(authoritativeTask, input) ??
          decisionBatchPreflightProblem(currentTask, input);
        if (problem) return problem;
        const receipt = await taskClient.decideBatch(taskId, input);
        const expectedRunId =
          detailsByTaskRef.current[taskId]?.runId ??
          tasksRef.current.find((task) => task.taskId === taskId)?.runId;
        if (expectedRunId !== undefined && receipt.runId !== expectedRunId) {
          return "The ordered decision receipt did not match the task and run.";
        }
        await loadDetail(taskId);
        return undefined;
      } catch (error) {
        try {
          const currentTask = await recoverCurrentTaskAfterDecisionProblem(
            taskClient,
            taskId,
            error,
          );
          if (currentTask) {
            reconcileTaskSnapshot(taskId, currentTask);
            return `${messageFrom(error)} The task was reloaded — review every action before deciding again.`;
          }
        } catch {
          // Return the original error when recovery also fails.
        }
        return messageFrom(error);
      } finally {
        taskDecisionSubmissionIdsRef.current.delete(taskId);
      }
    },
    [loadDetail, reconcileTaskSnapshot],
  );

  const updatePlan = useCallback(
    async (input: PlanUpdateInput): Promise<boolean> => {
      const taskId = activeTaskIdRef.current;
      if (!taskId) {
        return false;
      }
      setUpdatingPlan(true);
      setPlanError(undefined);
      try {
        const updated = await taskClient.updatePlan(taskId, input);
        const expectedRunId =
          detailsByTaskRef.current[taskId]?.runId ??
          tasksRef.current.find((task) => task.taskId === taskId)?.runId;
        if (
          updated.taskId !== taskId ||
          updated.interruptId !== input.interruptId ||
          updated.plan.revision !== input.expectedRevision + 1 ||
          (expectedRunId !== undefined && updated.runId !== expectedRunId)
        ) {
          throw new Error("The plan receipt did not match the selected task, run, and revision.");
        }
        const currentDetails = detailsByTaskRef.current;
        const currentTask = currentDetails[taskId];
        if (currentTask) {
          const waitingForApproval = detailAwaitingApprovalReload(
            currentTask,
            input.interruptId,
            updated.plan,
          );
          const nextDetails = { ...currentDetails, [taskId]: waitingForApproval };
          detailsByTaskRef.current = nextDetails;
          setDetailsByTask(nextDetails);
        }
        try {
          const authoritativeTask = await taskClient.getTask(taskId, AbortSignal.timeout(15_000));
          reconcileTaskSnapshot(taskId, authoritativeTask);
        } catch (refreshError) {
          if (activeTaskIdRef.current === taskId) {
            setPlanError(
              `The plan was saved, but Deep Work could not reload its ordered approval. Reload the task before deciding. ${messageFrom(refreshError)}`,
            );
          }
        }
        return true;
      } catch (error) {
        if (activeTaskIdRef.current === taskId) {
          try {
            const currentTask = await recoverCurrentTaskAfterPlanProblem(taskClient, taskId, error);
            if (currentTask) {
              if (activeTaskIdRef.current === taskId) {
                setDetailsByTask((current) => ({ ...current, [taskId]: currentTask }));
                setTasks((current) => replaceTask(current, taskId, () => currentTask));
                setPlanError(
                  `${messageFrom(error)} The current task, plan revision, and interrupt were reloaded. Review them before trying again.`,
                );
              }
            } else {
              setPlanError(messageFrom(error));
            }
          } catch (refreshError) {
            if (activeTaskIdRef.current === taskId) {
              setPlanError(
                `${messageFrom(error)} Deep Work could not reload the current task: ${messageFrom(refreshError)}`,
              );
            }
          }
        }
        return false;
      } finally {
        if (activeTaskIdRef.current === taskId) {
          setUpdatingPlan(false);
        }
      }
    },
    [reconcileTaskSnapshot],
  );

  /**
   * Cancel a live task. The authoritative terminal state arrives over the
   * stream as a run.completed(cancelled) event, but we also reload the detail so
   * a non-streaming caller (or a task whose stream already closed) reflects the
   * cancelled state immediately. Returns an error message on failure.
   */
  const cancelTask = useCallback(
    async (taskId: string): Promise<string | undefined> => {
      setCancelling(true);
      setCancelError(undefined);
      try {
        const receipt = await taskClient.cancelTask(taskId);
        const expectedRunId =
          detailsByTaskRef.current[taskId]?.runId ??
          tasksRef.current.find((task) => task.taskId === taskId)?.runId;
        if (
          receipt.taskId !== taskId ||
          (expectedRunId !== undefined && receipt.runId !== expectedRunId)
        ) {
          const mismatch = "The cancel receipt did not match the selected task and run.";
          setCancelError(mismatch);
          return mismatch;
        }
        await loadDetail(taskId);
        return undefined;
      } catch (error) {
        const message = messageFrom(error);
        setCancelError(message);
        return message;
      } finally {
        setCancelling(false);
      }
    },
    [loadDetail],
  );

  const store = useMemo<TasksStore>(
    () => ({
      tasks,
      loadingTasks,
      listError,
      refreshList,
      creating,
      createError,
      createTask,
      detailsByTask,
      eventsByTask,
      loadDetail,
      activeTaskId,
      setActiveTaskId,
      connectionState,
      streamRecovery,
      detailError,
      streamError,
      actionError,
      planError,
      cancelError,
      submittingDecision,
      submittedDecision,
      updatingPlan,
      cancelling,
      decide,
      decideForTask,
      decideBatch,
      decideBatchForTask,
      updatePlan,
      cancelTask,
      mode: taskClient.mode,
      apiBaseUrl: taskClient.apiBaseUrl,
    }),
    [
      tasks,
      loadingTasks,
      listError,
      refreshList,
      creating,
      createError,
      createTask,
      detailsByTask,
      eventsByTask,
      loadDetail,
      activeTaskId,
      connectionState,
      streamRecovery,
      detailError,
      streamError,
      actionError,
      planError,
      cancelError,
      submittingDecision,
      submittedDecision,
      updatingPlan,
      cancelling,
      decide,
      decideForTask,
      decideBatch,
      decideBatchForTask,
      updatePlan,
      cancelTask,
    ],
  );

  return <TasksStoreContext.Provider value={store}>{children}</TasksStoreContext.Provider>;
}

export function useTasksStore(): TasksStore {
  const store = useContext(TasksStoreContext);
  if (!store) {
    throw new Error("useTasksStore must be used within a TasksProvider");
  }
  return store;
}

/** Bind the store's streaming slot to a route's task id for the lifetime of the page. */
export function useActiveTask(taskId: string): TasksStore {
  const store = useTasksStore();
  const { setActiveTaskId } = store;
  useEffect(() => {
    setActiveTaskId(taskId);
    return () => setActiveTaskId(undefined);
  }, [taskId, setActiveTaskId]);
  return store;
}

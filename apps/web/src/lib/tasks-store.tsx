"use client";

import type { ReactNode } from "react";
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
  getActiveInterrupt,
  getCompletionResultText,
  interruptAfterEvent,
  isTerminalStatus,
  reduceEventsIntoDetail,
  statusAfterEvent,
} from "./task-normalizers";
import type {
  ConnectionState,
  DecisionInput,
  PlanUpdateInput,
  TaskDetail,
  TaskEvent,
  TaskSummary,
} from "./task-types";

function messageFrom(error: unknown): string {
  return error instanceof Error ? error.message : "Something unexpected happened.";
}

function replaceTask(
  tasks: readonly TaskSummary[],
  taskId: string,
  update: (task: TaskSummary) => TaskSummary,
): TaskSummary[] {
  return tasks.map((task) => (task.taskId === taskId ? update(task) : task));
}

export interface TasksStore {
  tasks: TaskSummary[];
  loadingTasks: boolean;
  listError?: string;
  refreshList: () => void;

  creating: boolean;
  createError?: string;
  createTask: (prompt: string) => Promise<TaskSummary | undefined>;

  detailsByTask: Record<string, TaskDetail>;
  eventsByTask: Record<string, TaskEvent[]>;
  loadDetail: (taskId: string) => Promise<TaskDetail | undefined>;

  activeTaskId?: string;
  setActiveTaskId: (taskId: string | undefined) => void;
  connectionState: ConnectionState;
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
  updatePlan: (input: PlanUpdateInput) => Promise<boolean>;
  cancelTask: (taskId: string) => Promise<string | undefined>;

  mode: typeof taskClient.mode;
  apiBaseUrl: string;
}

const TasksStoreContext = createContext<TasksStore | undefined>(undefined);

export function TasksProvider({ children }: { children: ReactNode }) {
  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [activeTaskId, setActiveTaskId] = useState<string>();
  const [detailsByTask, setDetailsByTask] = useState<Record<string, TaskDetail>>({});
  const [eventsByTask, setEventsByTask] = useState<Record<string, TaskEvent[]>>({});
  const [connectionState, setConnectionState] = useState<ConnectionState>("closed");
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
  const decisionRequestRef = useRef(0);
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
  }, [listAttempt]);

  useEffect(() => {
    if (!activeTaskId) {
      setConnectionState("closed");
      return;
    }

    const controller = new AbortController();
    setDetailError(undefined);
    setStreamError(undefined);
    setSubmittedDecision(undefined);
    setSubmittingDecision(false);
    setActionError(undefined);
    setPlanError(undefined);
    setCancelError(undefined);
    setCancelling(false);
    decisionRequestRef.current += 1;
    pendingDecisionRef.current = undefined;

    void taskClient
      .getTask(activeTaskId, controller.signal)
      .then((task) => {
        const taskWithEarlyEvents = reduceEventsIntoDetail(
          task,
          eventsByTaskRef.current[activeTaskId] ?? [],
        );
        setDetailsByTask((current) => {
          const existing = current[activeTaskId];
          return {
            ...current,
            [activeTaskId]: existing
              ? {
                  ...taskWithEarlyEvents,
                  result: existing.result ?? taskWithEarlyEvents.result,
                }
              : taskWithEarlyEvents,
          };
        });
        setTasks((current) => replaceTask(current, activeTaskId, () => taskWithEarlyEvents));
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          setDetailError(messageFrom(error));
        }
      });

    let closeStream: () => void = () => undefined;
    closeStream = taskClient.subscribe(activeTaskId, {
      onConnectionChange: (state) => {
        setConnectionState(state);
        if (state === "connected") {
          setStreamError(undefined);
        }
      },
      onError: setStreamError,
      onEvent: (event) => {
        const eventsBeforeEvent = eventsByTaskRef.current[activeTaskId] ?? [];
        const activeBeforeEvent = getActiveInterrupt(eventsBeforeEvent);
        setEventsByTask((current) => {
          const taskEvents = current[activeTaskId] ?? [];
          const next = taskEvents.some((candidate) => candidate.id === event.id)
            ? current
            : {
                ...current,
                [activeTaskId]: [...taskEvents, event],
              };
          eventsByTaskRef.current = next;
          return next;
        });
        setDetailsByTask((current) => {
          const task = current[activeTaskId];
          if (!task) {
            return current;
          }
          const eventResult =
            event.name === "run.completed" ? getCompletionResultText(event) : undefined;
          return {
            ...current,
            [activeTaskId]: {
              ...task,
              pendingInterrupt: interruptAfterEvent(task.pendingInterrupt, event),
              status: statusAfterEvent(task.status, event, task.pendingInterrupt),
              result: eventResult ?? task.result,
            },
          };
        });
        setTasks((current) =>
          replaceTask(current, activeTaskId, (task) => ({
            ...task,
            status: statusAfterEvent(task.status, event, activeBeforeEvent),
          })),
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

    return () => {
      controller.abort();
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

  const createTask = useCallback(async (prompt: string): Promise<TaskSummary | undefined> => {
    setCreating(true);
    setCreateError(undefined);
    try {
      const created = await taskClient.createTask(prompt);
      const optimisticTask: TaskSummary = {
        ...created,
        title: prompt,
        prompt,
        // Record the moment this create actually happened so a freshly dispatched
        // task stays at the top of the newest-first "Recent" inbox view instead of
        // sinking below older tasks while its server timestamp is still in flight.
        // This is the client's firsthand time of its own action, not a guessed
        // value, and it is replaced by the server's authoritative createdAt on the
        // next list refresh.
        createdAt: new Date().toISOString(),
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
  }, []);

  const decide = useCallback(async (input: DecisionInput): Promise<void> => {
    const taskId = activeTaskIdRef.current;
    if (!taskId) {
      return;
    }

    const requestId = decisionRequestRef.current + 1;
    decisionRequestRef.current = requestId;
    pendingDecisionRef.current = {
      taskId,
      interruptId: input.interruptId,
      requestId,
    };
    setSubmittingDecision(true);
    setActionError(undefined);
    try {
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
            setDetailsByTask((current) => ({ ...current, [taskId]: currentTask }));
            setTasks((current) => replaceTask(current, taskId, () => currentTask));
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
      if (
        pendingDecisionRef.current?.requestId === requestId &&
        activeTaskIdRef.current === taskId
      ) {
        setSubmittingDecision(false);
      }
    }
  }, []);

  /**
   * Decision path for tasks that are not the streaming active task (the
   * approvals inbox). Returns an error message on failure, undefined on
   * success. Always reloads the task detail afterwards so callers see the
   * authoritative state.
   */
  const decideForTask = useCallback(
    async (taskId: string, input: DecisionInput): Promise<string | undefined> => {
      try {
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
            setDetailsByTask((current) => ({ ...current, [taskId]: currentTask }));
            setTasks((current) => replaceTask(current, taskId, () => currentTask));
            return `${messageFrom(error)} The task was reloaded — review it before deciding again.`;
          }
        } catch {
          // fall through to the original error
        }
        return messageFrom(error);
      }
    },
    [loadDetail],
  );

  const updatePlan = useCallback(async (input: PlanUpdateInput): Promise<boolean> => {
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
      if (activeTaskIdRef.current === taskId) {
        setDetailsByTask((current) => {
          const task = current[taskId];
          return task
            ? {
                ...current,
                [taskId]: { ...task, proposedPlan: updated.plan },
              }
            : current;
        });
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
  }, []);

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

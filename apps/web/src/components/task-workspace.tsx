"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { AppHeader } from "./app-header";
import { TaskComposer } from "./task-composer";
import { TaskDetail } from "./task-detail";
import { TaskList } from "./task-list";
import {
  getActiveInterrupt,
  getCompletionResultText,
  getEvidenceRecords,
  getLatestPlan,
  interruptAfterEvent,
  isTerminalStatus,
  reduceEventsIntoDetail,
  statusAfterEvent,
} from "../lib/task-normalizers";
import { taskClient } from "../lib/task-client";
import {
  recoverCurrentTaskAfterDecisionProblem,
  recoverCurrentTaskAfterPlanProblem,
} from "../lib/plan-recovery";
import type {
  ConnectionState,
  DecisionInput,
  PlanUpdateInput,
  TaskDetail as TaskDetailType,
  TaskEvent,
  TaskSummary,
} from "../lib/task-types";

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

export function TaskWorkspace() {
  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<string>();
  const [detailsByTask, setDetailsByTask] = useState<Record<string, TaskDetailType>>({});
  const [eventsByTask, setEventsByTask] = useState<Record<string, TaskEvent[]>>({});
  const [connectionState, setConnectionState] = useState<ConnectionState>("closed");
  const [listError, setListError] = useState<string>();
  const [detailError, setDetailError] = useState<string>();
  const [streamError, setStreamError] = useState<string>();
  const [createError, setCreateError] = useState<string>();
  const [actionError, setActionError] = useState<string>();
  const [planError, setPlanError] = useState<string>();
  const [loadingTasks, setLoadingTasks] = useState(true);
  const [creating, setCreating] = useState(false);
  const [submittingDecision, setSubmittingDecision] = useState(false);
  const [updatingPlan, setUpdatingPlan] = useState(false);
  const [submittedDecision, setSubmittedDecision] = useState<DecisionInput["decision"]>();
  const [listAttempt, setListAttempt] = useState(0);
  const detailRef = useRef<HTMLElement | null>(null);
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
  const selectedTaskIdRef = useRef<string | undefined>(selectedTaskId);
  selectedTaskIdRef.current = selectedTaskId;

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
        setSelectedTaskId((current) => {
          if (current) {
            return current;
          }
          const storedTaskId = window.sessionStorage.getItem("deepwork.selectedTaskId");
          return items.some((task) => task.taskId === storedTaskId)
            ? (storedTaskId ?? undefined)
            : items.at(0)?.taskId;
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
    if (!selectedTaskId) {
      setConnectionState("closed");
      return;
    }

    window.sessionStorage.setItem("deepwork.selectedTaskId", selectedTaskId);
    const controller = new AbortController();
    setDetailError(undefined);
    setStreamError(undefined);
    setSubmittedDecision(undefined);
    setSubmittingDecision(false);
    setActionError(undefined);
    setPlanError(undefined);
    decisionRequestRef.current += 1;
    pendingDecisionRef.current = undefined;

    void taskClient
      .getTask(selectedTaskId, controller.signal)
      .then((task) => {
        const taskWithEarlyEvents = reduceEventsIntoDetail(
          task,
          eventsByTaskRef.current[selectedTaskId] ?? [],
        );
        setDetailsByTask((current) => {
          const existing = current[selectedTaskId];
          return {
            ...current,
            [selectedTaskId]: existing
              ? {
                  ...taskWithEarlyEvents,
                  result: existing.result ?? taskWithEarlyEvents.result,
                }
              : taskWithEarlyEvents,
          };
        });
        setTasks((current) => replaceTask(current, selectedTaskId, () => taskWithEarlyEvents));
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          setDetailError(messageFrom(error));
        }
      });

    let closeStream: () => void = () => undefined;
    closeStream = taskClient.subscribe(selectedTaskId, {
      onConnectionChange: (state) => {
        setConnectionState(state);
        if (state === "connected") {
          setStreamError(undefined);
        }
      },
      onError: setStreamError,
      onEvent: (event) => {
        const eventsBeforeEvent = eventsByTaskRef.current[selectedTaskId] ?? [];
        const activeBeforeEvent = getActiveInterrupt(eventsBeforeEvent);
        setEventsByTask((current) => {
          const taskEvents = current[selectedTaskId] ?? [];
          const next = taskEvents.some((candidate) => candidate.id === event.id)
            ? current
            : {
                ...current,
                [selectedTaskId]: [...taskEvents, event],
              };
          eventsByTaskRef.current = next;
          return next;
        });
        setDetailsByTask((current) => {
          const task = current[selectedTaskId];
          if (!task) {
            return current;
          }
          const eventResult =
            event.name === "run.completed" ? getCompletionResultText(event) : undefined;
          return {
            ...current,
            [selectedTaskId]: {
              ...task,
              pendingInterrupt: interruptAfterEvent(task.pendingInterrupt, event),
              status: statusAfterEvent(task.status, event, task.pendingInterrupt),
              result: eventResult ?? task.result,
            },
          };
        });
        setTasks((current) =>
          replaceTask(current, selectedTaskId, (task) => ({
            ...task,
            status: statusAfterEvent(task.status, event, activeBeforeEvent),
          })),
        );
        if (event.name === "decision.recorded") {
          const pending = pendingDecisionRef.current;
          if (
            pending?.taskId === selectedTaskId &&
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
            .getTask(selectedTaskId, controller.signal)
            .then((authoritativeTask) => {
              const reducedTask = reduceEventsIntoDetail(
                authoritativeTask,
                eventsByTaskRef.current[selectedTaskId] ?? [],
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
                [selectedTaskId]: finalTask,
              }));
              setTasks((current) => replaceTask(current, selectedTaskId, () => finalTask));
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
  }, [selectedTaskId]);

  const selected = tasks.find((task) => task.taskId === selectedTaskId);
  const detail = selectedTaskId ? detailsByTask[selectedTaskId] : undefined;
  const events = selectedTaskId ? (eventsByTask[selectedTaskId] ?? []) : [];
  const activeInterrupt = useMemo(
    () => (detail ? detail.pendingInterrupt : getActiveInterrupt(events)),
    [detail, events],
  );
  const plan = useMemo(
    () => getLatestPlan(detail?.proposedPlan, events),
    [detail?.proposedPlan, events],
  );
  const evidence = useMemo(
    () => getEvidenceRecords(detail?.evidence, events),
    [detail?.evidence, events],
  );

  async function createTask(prompt: string): Promise<boolean> {
    setCreating(true);
    setCreateError(undefined);
    try {
      const created = await taskClient.createTask(prompt);
      const optimisticTask: TaskSummary = {
        ...created,
        title: prompt,
        prompt,
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
      setSelectedTaskId(created.taskId);
      window.requestAnimationFrame(() => detailRef.current?.focus());
      return true;
    } catch (error) {
      setCreateError(messageFrom(error));
      return false;
    } finally {
      setCreating(false);
    }
  }

  async function decide(input: DecisionInput): Promise<void> {
    if (!selectedTaskId) {
      return;
    }

    const taskId = selectedTaskId;
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
        detailsByTask[taskId]?.runId ?? tasks.find((task) => task.taskId === taskId)?.runId;
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
        selectedTaskIdRef.current === taskId
      ) {
        setSubmittedDecision(input.decision);
      }
    } catch (error) {
      if (
        pendingDecisionRef.current?.requestId === requestId &&
        selectedTaskIdRef.current === taskId
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
        selectedTaskIdRef.current === taskId
      ) {
        setSubmittingDecision(false);
      }
    }
  }

  async function updatePlan(input: PlanUpdateInput): Promise<boolean> {
    if (!selectedTaskId) {
      return false;
    }
    const taskId = selectedTaskId;
    setUpdatingPlan(true);
    setPlanError(undefined);
    try {
      const updated = await taskClient.updatePlan(taskId, input);
      const expectedRunId =
        detailsByTask[taskId]?.runId ?? tasks.find((task) => task.taskId === taskId)?.runId;
      if (
        updated.taskId !== taskId ||
        updated.interruptId !== input.interruptId ||
        updated.plan.revision !== input.expectedRevision + 1 ||
        (expectedRunId !== undefined && updated.runId !== expectedRunId)
      ) {
        throw new Error("The plan receipt did not match the selected task, run, and revision.");
      }
      if (selectedTaskIdRef.current === taskId) {
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
      if (selectedTaskIdRef.current === taskId) {
        try {
          const currentTask = await recoverCurrentTaskAfterPlanProblem(taskClient, taskId, error);
          if (currentTask) {
            if (selectedTaskIdRef.current === taskId) {
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
          if (selectedTaskIdRef.current === taskId) {
            setPlanError(
              `${messageFrom(error)} Deep Work could not reload the current task: ${messageFrom(refreshError)}`,
            );
          }
        }
      }
      return false;
    } finally {
      if (selectedTaskIdRef.current === taskId) {
        setUpdatingPlan(false);
      }
    }
  }

  function selectTask(taskId: string) {
    setSelectedTaskId(taskId);
    window.requestAnimationFrame(() => detailRef.current?.focus());
  }

  return (
    <div className="app-shell">
      <AppHeader mode={taskClient.mode} apiBaseUrl={taskClient.apiBaseUrl} />
      <main id="main-content" className="main-content">
        <header className="page-header">
          <div>
            <p className="eyebrow">Workspace · local / product</p>
            <h1>Tasks</h1>
            <p>
              Delegate meaningful work, follow honest progress, steer the plan, and inspect the
              evidence behind the result.
            </p>
          </div>
          <div className="outcome-badge" aria-label="Current product outcome">
            <span className="outcome-badge-mark" aria-hidden="true">
              2
            </span>
            <span>
              <strong>Trust and steer</strong>
              <small>Local product session</small>
            </span>
          </div>
        </header>

        <TaskComposer busy={creating} onCreate={createTask} />
        {createError ? (
          <div className="create-error" role="alert">
            <strong>Task was not created.</strong>
            <span>{createError}</span>
          </div>
        ) : null}

        <div className="workspace-grid">
          <TaskList
            tasks={tasks}
            selectedTaskId={selectedTaskId}
            onSelect={selectTask}
            loading={loadingTasks}
            error={listError}
            onRetry={() => setListAttempt((current) => current + 1)}
          />
          <TaskDetail
            detailRef={detailRef}
            selected={selected}
            detail={detail}
            events={events}
            evidence={evidence}
            connectionState={connectionState}
            detailError={detailError}
            streamError={streamError}
            activeInterrupt={activeInterrupt}
            submittingDecision={submittingDecision}
            submittedDecision={submittedDecision}
            actionError={actionError}
            onDecide={decide}
            plan={plan}
            planError={planError}
            updatingPlan={updatingPlan}
            onUpdatePlan={updatePlan}
          />
        </div>
      </main>
      <footer className="app-footer">
        <span>deepwork</span>
        <span>Human-supervised local task execution · external providers unavailable</span>
      </footer>
    </div>
  );
}

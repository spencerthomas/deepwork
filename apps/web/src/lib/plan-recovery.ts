import { isRecoverableDecisionProblem, isRecoverablePlanProblem } from "./http-task-client";
import type { TaskClient, TaskDetail } from "./task-types";

export async function recoverCurrentTaskAfterPlanProblem(
  client: TaskClient,
  taskId: string,
  error: unknown,
): Promise<TaskDetail | undefined> {
  if (!isRecoverablePlanProblem(error)) {
    return undefined;
  }
  return client.getTask(taskId);
}

export async function recoverCurrentTaskAfterDecisionProblem(
  client: TaskClient,
  taskId: string,
  error: unknown,
): Promise<TaskDetail | undefined> {
  if (!isRecoverableDecisionProblem(error)) {
    return undefined;
  }
  return client.getTask(taskId);
}

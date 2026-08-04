import type {
  ActiveInterrupt,
  DecisionInput,
  HitlDecisionType,
  OrderedDecision,
  ProposedPlan,
  TaskDetail,
  TaskSummary,
} from "../../lib/task-types";

export type DecisionVerb = DecisionInput["decision"];
export type ApprovalCapability = HitlDecisionType;
export type ApprovalResolution = DecisionVerb | "batch";

export type ApprovalCapabilityFilter = "all" | ApprovalCapability;

/** Canonical button order. Only verbs advertised by the interrupt are rendered. */
export const DECISION_VERB_ORDER: readonly DecisionVerb[] = ["approve", "reject", "respond"];
export const APPROVAL_CAPABILITY_ORDER: readonly ApprovalCapability[] = [
  "approve",
  "edit",
  "reject",
  "respond",
];

export interface ApprovalRow {
  interrupt?: ActiveInterrupt;
  plan?: ProposedPlan;
  task: TaskSummary;
}

/** Trailing digits of an id ("task_00000003" → 3). Undefined when there are none. */
export function trailingNumber(id: string): number | undefined {
  const match = /(\d+)$/.exec(id);
  return match ? Number.parseInt(match[1], 10) : undefined;
}

/**
 * Oldest dispatch first, using only the numeric task id — the runner assigns
 * ids in dispatch order, so no timestamps need to be invented. Ids without
 * trailing digits sort after numbered ids, lexicographically.
 */
export function compareTaskIdsOldestFirst(a: string, b: string): number {
  const numericA = trailingNumber(a);
  const numericB = trailingNumber(b);
  if (numericA !== undefined && numericB !== undefined && numericA !== numericB) {
    return numericA - numericB;
  }
  if (numericA !== undefined && numericB === undefined) {
    return -1;
  }
  if (numericA === undefined && numericB !== undefined) {
    return 1;
  }
  return a < b ? -1 : a > b ? 1 : 0;
}

/**
 * The approvals queue: exactly the tasks the store reports as
 * waiting-approval, oldest dispatch first. Interrupt and plan attach once
 * loadDetail has hydrated the task. Rows whose interrupt was already decided
 * in this session are dropped even if a stale detail read resurrects them.
 */
export function deriveApprovalRows(
  tasks: readonly TaskSummary[],
  detailsByTask: Readonly<Record<string, TaskDetail>>,
  resolvedInterruptIds?: ReadonlySet<string>,
): ApprovalRow[] {
  return tasks
    .filter((task) => task.status === "waiting-approval")
    .sort((a, b) => compareTaskIdsOldestFirst(a.taskId, b.taskId))
    .map((task) => {
      const detail = detailsByTask[task.taskId];
      return { task, interrupt: detail?.pendingInterrupt, plan: detail?.proposedPlan };
    })
    .filter(
      (row) =>
        row.interrupt === undefined ||
        !(resolvedInterruptIds?.has(row.interrupt.interruptId) ?? false),
    );
}

/** Waiting tasks whose pending interrupt has not been hydrated via loadDetail yet. */
export function waitingTaskIdsNeedingDetail(
  tasks: readonly TaskSummary[],
  detailsByTask: Readonly<Record<string, TaskDetail>>,
): string[] {
  return tasks
    .filter(
      (task) =>
        task.status === "waiting-approval" &&
        detailsByTask[task.taskId]?.pendingInterrupt === undefined,
    )
    .map((task) => task.taskId);
}

/** Decision verbs to render, in canonical order and deduplicated — never invented. */
export function orderedDecisions(interrupt: ActiveInterrupt): DecisionVerb[] {
  return DECISION_VERB_ORDER.filter((verb) => interrupt.decisions.includes(verb));
}

export function isOrderedApproval(interrupt: ActiveInterrupt): boolean {
  return (
    interrupt.version !== undefined &&
    interrupt.actionRequests !== undefined &&
    interrupt.reviewConfigs !== undefined &&
    interrupt.actionRequests.length > 0 &&
    interrupt.actionRequests.length === interrupt.reviewConfigs.length
  );
}

/** Capabilities the actionable contract actually offers, independent of legacy fallback verbs. */
export function approvalCapabilities(interrupt: ActiveInterrupt): ApprovalCapability[] {
  if (!isOrderedApproval(interrupt)) return orderedDecisions(interrupt);
  const offered = new Set(interrupt.reviewConfigs!.flatMap((config) => config.allowedDecisions));
  return APPROVAL_CAPABILITY_ORDER.filter((capability) => offered.has(capability));
}

/** Whether one keyboard verb can safely fill every position in the current contract. */
export function supportsUniformDecision(
  interrupt: ActiveInterrupt,
  decision: "approve" | "reject",
): boolean {
  return isOrderedApproval(interrupt)
    ? interrupt.reviewConfigs!.every((config) => config.allowedDecisions.includes(decision))
    : interrupt.decisions.includes(decision);
}

/** Honest inbox confirmation for an accepted positional decision vector. */
export function batchResolution(decisions: readonly OrderedDecision[]): ApprovalResolution {
  if (decisions.some((decision) => decision.type === "reject")) return "reject";
  if (decisions.every((decision) => decision.type === "approve")) return "approve";
  if (decisions.every((decision) => decision.type === "respond")) return "respond";
  return "batch";
}

/** How many pending rows offer each verb, for the capability sidebar counts. */
export function approvalCapabilityCounts(
  rows: readonly ApprovalRow[],
): Record<ApprovalCapability, number> {
  const counts: Record<ApprovalCapability, number> = {
    approve: 0,
    edit: 0,
    reject: 0,
    respond: 0,
  };
  for (const row of rows) {
    if (!row.interrupt) continue;
    const offered = approvalCapabilities(row.interrupt);
    for (const capability of APPROVAL_CAPABILITY_ORDER) {
      if (offered.includes(capability)) {
        counts[capability] += 1;
      }
    }
  }
  return counts;
}

/**
 * Capability filter. "all" keeps every pending row, including rows still
 * hydrating; a verb filter keeps only rows whose loaded interrupt offers it.
 */
export function filterRowsByCapability(
  rows: readonly ApprovalRow[],
  filter: ApprovalCapabilityFilter,
): ApprovalRow[] {
  if (filter === "all") {
    return [...rows];
  }
  return rows.filter(
    (row) => row.interrupt !== undefined && approvalCapabilities(row.interrupt).includes(filter),
  );
}

export const PLAN_PREVIEW_STEP_COUNT = 3;

export interface PlanPreview {
  remaining: number;
  steps: string[];
}

/** First steps of the proposed plan for the card summary, plus how many are hidden. */
export function planPreview(plan: ProposedPlan, maxSteps = PLAN_PREVIEW_STEP_COUNT): PlanPreview {
  return {
    steps: plan.steps.slice(0, maxSteps),
    remaining: Math.max(0, plan.steps.length - maxSteps),
  };
}

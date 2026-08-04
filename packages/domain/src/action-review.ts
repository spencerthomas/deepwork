import {
  interruptId,
  runId,
  sourceId,
  sourceInterruptKey,
  sourceRunKey,
  taskId,
  threadId,
  type SourceInterruptKey,
  type SourceRunKey,
  type TaskId,
} from "./identity.js";

export const ACTION_NAME_MAX_CODE_POINTS = 128;
export const ACTION_DESCRIPTION_MAX_CODE_POINTS = 300;
export const ACTION_DECISION_MESSAGE_MAX_CODE_POINTS = 1_000;
export const IDEMPOTENCY_KEY_MAX_CODE_POINTS = 128;
export const INTERRUPT_VERSION_MAX = 2_147_483_647;
export const ACTION_REVIEW_MAX_COUNT = 8;
export const JSON_VALUE_MAX_DEPTH = 20;
export const JSON_VALUE_MAX_NODES = 10_000;
export const JSON_STRING_MAX_CODE_POINTS = 64_000;

const SAFE_ACTION_NAME_PATTERN = /^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/;
const UNSAFE_JSON_KEYS = new Set(["__proto__", "constructor", "prototype"]);

export type JsonPrimitive = string | number | boolean | null;
export type JsonValue = JsonPrimitive | JsonObject | readonly JsonValue[];
export interface JsonObject {
  readonly [key: string]: JsonValue;
}

export const ACTION_DECISION_TYPES = Object.freeze([
  "approve",
  "edit",
  "reject",
  "respond",
] as const);
export type ActionDecisionType = (typeof ACTION_DECISION_TYPES)[number];

export interface ActionRequest {
  readonly name: string;
  readonly args: JsonObject;
  readonly description?: string;
}

export interface ReviewConfig {
  readonly actionName: string;
  readonly allowedDecisions: readonly ActionDecisionType[];
  readonly argsSchema?: JsonObject;
}

export type ActionDecision =
  | Readonly<{ type: "approve" }>
  | Readonly<{ type: "edit"; editedAction: ActionRequest }>
  | Readonly<{ type: "reject"; message?: string }>
  | Readonly<{ type: "respond"; message: string }>;

export interface BatchDecisionInput {
  readonly interrupt: SourceInterruptKey;
  readonly expectedVersion: string;
  readonly idempotencyKey: string;
  readonly decisions: readonly ActionDecision[];
}

export interface BatchDecisionReceipt {
  readonly taskId: TaskId;
  readonly run: SourceRunKey;
  readonly interrupt: SourceInterruptKey;
  readonly version: string;
  readonly decisionTypes: readonly ActionDecisionType[];
  readonly status: "accepted";
  readonly duplicate: boolean;
}

export interface OrderedActionInterrupt {
  readonly identity: SourceInterruptKey;
  readonly version?: string;
  readonly actionRequests?: readonly ActionRequest[];
  readonly reviewConfigs?: readonly ReviewConfig[];
}

function exactKeys(
  input: object,
  required: readonly string[],
  optional: readonly string[],
  label: string,
): void {
  const keys = Object.keys(input);
  if (
    required.some((key) => !keys.includes(key)) ||
    keys.some((key) => !required.includes(key) && !optional.includes(key))
  ) {
    throw new TypeError(`${label} contains unknown or missing fields.`);
  }
}

function boundedText(value: unknown, label: string, maximum: number): string {
  if (typeof value !== "string" || value.trim().length === 0 || [...value].length > maximum) {
    throw new TypeError(`${label} must be a bounded non-blank string.`);
  }
  if (hasUnsupportedControl(value, true)) {
    throw new TypeError(`${label} contains an unsupported control character.`);
  }
  return value;
}

function hasUnsupportedControl(value: string, allowTextWhitespace: boolean): boolean {
  return [...value].some((character) => {
    const codePoint = character.codePointAt(0) ?? 0;
    return (
      (codePoint < 32 &&
        (!allowTextWhitespace ||
          (character !== "\t" && character !== "\n" && character !== "\r"))) ||
      (codePoint >= 127 && codePoint <= 159)
    );
  });
}

export function interruptVersion(value: unknown, label = "Interrupt version"): string {
  if (
    typeof value !== "string" ||
    !/^[1-9][0-9]*$/.test(value) ||
    !Number.isSafeInteger(Number(value)) ||
    Number(value) > INTERRUPT_VERSION_MAX
  ) {
    throw new TypeError(
      `${label} must be a canonical decimal string from 1 through ${INTERRUPT_VERSION_MAX}.`,
    );
  }
  return value;
}

function actionName(value: unknown, label: string): string {
  const accepted = boundedText(value, label, ACTION_NAME_MAX_CODE_POINTS);
  if (!SAFE_ACTION_NAME_PATTERN.test(accepted)) {
    throw new TypeError(`${label} is not an accepted safe identifier.`);
  }
  return accepted;
}

function snapshotJson(
  value: unknown,
  state: { nodes: number; readonly ancestors: Set<object> },
  depth: number,
): JsonValue {
  state.nodes += 1;
  if (state.nodes > JSON_VALUE_MAX_NODES || depth > JSON_VALUE_MAX_DEPTH) {
    throw new TypeError("JSON value exceeds the accepted size boundary.");
  }
  if (value === null || typeof value === "boolean") {
    return value;
  }
  if (typeof value === "string") {
    if ([...value].length > JSON_STRING_MAX_CODE_POINTS) {
      throw new TypeError("JSON string exceeds the accepted size boundary.");
    }
    return value;
  }
  if (typeof value === "number") {
    if (!Number.isFinite(value)) {
      throw new TypeError("JSON numbers must be finite.");
    }
    return value;
  }
  if (typeof value !== "object") {
    throw new TypeError("Action values must contain JSON-safe data only.");
  }
  if (state.ancestors.has(value)) {
    throw new TypeError("Action values cannot contain cycles.");
  }
  state.ancestors.add(value);
  try {
    if (Array.isArray(value)) {
      return Object.freeze(value.map((item) => snapshotJson(item, state, depth + 1)));
    }
    const prototype = Object.getPrototypeOf(value);
    if (prototype !== Object.prototype && prototype !== null) {
      throw new TypeError("JSON objects must be plain records.");
    }
    const output: Record<string, JsonValue> = {};
    for (const [key, item] of Object.entries(value)) {
      if (
        UNSAFE_JSON_KEYS.has(key) ||
        key.length === 0 ||
        [...key].length > 200 ||
        hasUnsupportedControl(key, false)
      ) {
        throw new TypeError("JSON object contains an unsafe key.");
      }
      output[key] = snapshotJson(item, state, depth + 1);
    }
    return Object.freeze(output);
  } finally {
    state.ancestors.delete(value);
  }
}

export function jsonObjectSnapshot(value: unknown, label = "Action arguments"): JsonObject {
  const snapshot = snapshotJson(value, { nodes: 0, ancestors: new Set<object>() }, 0);
  if (snapshot === null || typeof snapshot !== "object" || Array.isArray(snapshot)) {
    throw new TypeError(`${label} must be a JSON object.`);
  }
  return snapshot as JsonObject;
}

export function actionRequest(input: {
  readonly name: string;
  readonly args: unknown;
  readonly description?: string;
}): ActionRequest {
  exactKeys(input, ["name", "args"], ["description"], "Action request");
  return Object.freeze({
    name: actionName(input.name, "Action name"),
    args: jsonObjectSnapshot(input.args),
    ...(input.description === undefined
      ? {}
      : {
          description: boundedText(
            input.description,
            "Action description",
            ACTION_DESCRIPTION_MAX_CODE_POINTS,
          ),
        }),
  });
}

export function reviewConfig(input: {
  readonly actionName: string;
  readonly allowedDecisions: readonly ActionDecisionType[];
  readonly argsSchema?: unknown;
}): ReviewConfig {
  exactKeys(input, ["actionName", "allowedDecisions"], ["argsSchema"], "Review config");
  if (
    !Array.isArray(input.allowedDecisions) ||
    input.allowedDecisions.length < 1 ||
    input.allowedDecisions.length > ACTION_DECISION_TYPES.length ||
    new Set(input.allowedDecisions).size !== input.allowedDecisions.length ||
    !input.allowedDecisions.every((decision) =>
      (ACTION_DECISION_TYPES as readonly string[]).includes(decision),
    )
  ) {
    throw new TypeError("Review config decisions must be a non-empty unique accepted set.");
  }
  return Object.freeze({
    actionName: actionName(input.actionName, "Review action name"),
    allowedDecisions: Object.freeze([...input.allowedDecisions]),
    ...(input.argsSchema === undefined
      ? {}
      : { argsSchema: jsonObjectSnapshot(input.argsSchema, "Action arguments schema") }),
  });
}

export function orderedActionReview(input: {
  readonly version: unknown;
  readonly actionRequests: readonly ActionRequest[];
  readonly reviewConfigs: readonly ReviewConfig[];
}): Readonly<{
  version: string;
  actionRequests: readonly ActionRequest[];
  reviewConfigs: readonly ReviewConfig[];
}> {
  if (
    !Array.isArray(input.actionRequests) ||
    !Array.isArray(input.reviewConfigs) ||
    input.actionRequests.length < 1 ||
    input.actionRequests.length > ACTION_REVIEW_MAX_COUNT ||
    input.actionRequests.length !== input.reviewConfigs.length
  ) {
    throw new TypeError(
      "Ordered action requests and review configs must be non-empty and aligned.",
    );
  }
  const requests = input.actionRequests.map((request) => actionRequest(request));
  const configs = input.reviewConfigs.map((config) => reviewConfig(config));
  if (requests.some((request, index) => configs[index]?.actionName !== request.name)) {
    throw new TypeError("Every review config must match its indexed action request.");
  }
  return Object.freeze({
    version: interruptVersion(input.version),
    actionRequests: Object.freeze(requests),
    reviewConfigs: Object.freeze(configs),
  });
}

function exactInterrupt(key: SourceInterruptKey): SourceInterruptKey {
  return sourceInterruptKey(
    sourceId(key.sourceId),
    taskId(key.taskId),
    threadId(key.threadId),
    runId(key.runId),
    interruptId(key.interruptId),
  );
}

function decision(value: ActionDecision, request: ActionRequest): ActionDecision {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new TypeError("Action decision must be a record.");
  }
  if (!(ACTION_DECISION_TYPES as readonly string[]).includes(value.type)) {
    throw new TypeError("Action decision type is not accepted.");
  }
  switch (value.type) {
    case "approve":
      exactKeys(value, ["type"], [], "Approve decision");
      return Object.freeze({ type: "approve" });
    case "edit": {
      exactKeys(value, ["type", "editedAction"], [], "Edit decision");
      const editedAction = actionRequest(value.editedAction);
      if (editedAction.name !== request.name) {
        throw new TypeError("Edited action name must match its indexed request.");
      }
      return Object.freeze({ type: "edit", editedAction });
    }
    case "reject":
      exactKeys(value, ["type"], ["message"], "Reject decision");
      return Object.freeze({
        type: "reject",
        ...(value.message === undefined
          ? {}
          : {
              message: boundedText(
                value.message,
                "Rejection message",
                ACTION_DECISION_MESSAGE_MAX_CODE_POINTS,
              ),
            }),
      });
    case "respond":
      exactKeys(value, ["type", "message"], [], "Respond decision");
      return Object.freeze({
        type: "respond",
        message: boundedText(
          value.message,
          "Response message",
          ACTION_DECISION_MESSAGE_MAX_CODE_POINTS,
        ),
      });
  }
}

export function batchDecisionInput(
  pending: OrderedActionInterrupt,
  input: {
    readonly expectedVersion: string;
    readonly idempotencyKey: string;
    readonly decisions: readonly ActionDecision[];
  },
): BatchDecisionInput {
  exactKeys(input, ["expectedVersion", "idempotencyKey", "decisions"], [], "Batch decision");
  if (
    pending.version === undefined ||
    pending.actionRequests === undefined ||
    pending.reviewConfigs === undefined
  ) {
    throw new TypeError("Batch decisions require an ordered pending interrupt.");
  }
  const current = orderedActionReview({
    version: pending.version,
    actionRequests: pending.actionRequests,
    reviewConfigs: pending.reviewConfigs,
  });
  const expectedVersion = interruptVersion(input.expectedVersion, "Expected interrupt version");
  if (expectedVersion !== current.version) {
    throw new TypeError("Expected interrupt version does not match the pending interrupt.");
  }
  const idempotencyKey = boundedText(
    input.idempotencyKey,
    "Idempotency key",
    IDEMPOTENCY_KEY_MAX_CODE_POINTS,
  );
  if (!Array.isArray(input.decisions) || input.decisions.length !== current.actionRequests.length) {
    throw new TypeError("Batch decisions must provide one decision for every action request.");
  }
  const decisions = input.decisions.map((item, index) => {
    const accepted = decision(item, current.actionRequests[index]!);
    if (!current.reviewConfigs[index]!.allowedDecisions.includes(accepted.type)) {
      throw new TypeError("Action decision is not allowed at its indexed review config.");
    }
    return accepted;
  });
  return Object.freeze({
    interrupt: exactInterrupt(pending.identity),
    expectedVersion,
    idempotencyKey,
    decisions: Object.freeze(decisions),
  });
}

export function batchDecisionReceipt(input: {
  readonly taskId: TaskId;
  readonly run: SourceRunKey;
  readonly interrupt: SourceInterruptKey;
  readonly version: string;
  readonly decisionTypes: readonly ActionDecisionType[];
  readonly status: "accepted";
  readonly duplicate: boolean;
}): BatchDecisionReceipt {
  exactKeys(
    input,
    ["taskId", "run", "interrupt", "version", "decisionTypes", "status", "duplicate"],
    [],
    "Batch decision receipt",
  );
  const acceptedInterrupt = exactInterrupt(input.interrupt);
  if (
    input.status !== "accepted" ||
    typeof input.duplicate !== "boolean" ||
    input.taskId !== acceptedInterrupt.taskId ||
    input.run.sourceId !== acceptedInterrupt.sourceId ||
    input.run.threadId !== acceptedInterrupt.threadId ||
    input.run.runId !== acceptedInterrupt.runId ||
    !Array.isArray(input.decisionTypes) ||
    input.decisionTypes.length < 1 ||
    !input.decisionTypes.every((item) =>
      (ACTION_DECISION_TYPES as readonly string[]).includes(item),
    )
  ) {
    throw new TypeError("Batch decision receipt is incoherent.");
  }
  return Object.freeze({
    taskId: taskId(input.taskId),
    run: sourceRunKey(
      sourceId(input.run.sourceId),
      threadId(input.run.threadId),
      runId(input.run.runId),
    ),
    interrupt: acceptedInterrupt,
    version: interruptVersion(input.version, "Receipt interrupt version"),
    decisionTypes: Object.freeze([...input.decisionTypes]),
    status: "accepted",
    duplicate: input.duplicate,
  });
}

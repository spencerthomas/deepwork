import {
  TASK_EVENT_NAMES,
  type TaskEvent,
  type TaskEventHandlers,
  type TaskEventName,
} from "./task-types";
import { isRecord } from "./task-normalizers";

const eventNames = new Set<string>(TASK_EVENT_NAMES);

export function isTaskEventName(value: string): value is TaskEventName {
  return eventNames.has(value);
}

export function decodeTaskEvent(name: string, id: string, rawData: string): TaskEvent {
  if (!isTaskEventName(name)) {
    throw new Error(`Unsupported task event: ${name}`);
  }
  if (id.trim() === "") {
    throw new Error(`The ${name} event is missing its SSE id.`);
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(rawData);
  } catch {
    throw new Error(`The ${name} event contained invalid JSON.`);
  }

  if (!isRecord(parsed)) {
    throw new Error(`The ${name} event data must be an object.`);
  }
  if (
    (name === "interrupt.requested" || name === "decision.recorded") &&
    (typeof parsed.interruptId !== "string" || parsed.interruptId.trim() === "")
  ) {
    throw new Error(`The ${name} event is missing a valid interruptId.`);
  }
  if (
    name === "decision.recorded" &&
    parsed.decision !== "approve" &&
    parsed.decision !== "reject" &&
    parsed.decision !== "respond"
  ) {
    throw new Error("The decision.recorded event must contain approve, reject, or respond.");
  }

  return {
    id,
    name,
    data: parsed,
  };
}

export function subscribeToTaskEvents(url: string, handlers: TaskEventHandlers): () => void {
  handlers.onConnectionChange("connecting");
  const source = new EventSource(url);

  source.onopen = () => {
    handlers.onConnectionChange("connected");
  };
  source.onerror = () => {
    handlers.onConnectionChange("reconnecting");
    handlers.onError("The event stream disconnected. Reconnecting…");
  };

  const listeners = TASK_EVENT_NAMES.map((name) => {
    const listener = (event: Event) => {
      const messageEvent = event as MessageEvent<string>;
      try {
        handlers.onEvent(decodeTaskEvent(name, messageEvent.lastEventId, messageEvent.data));
      } catch (error) {
        handlers.onError(
          error instanceof Error ? error.message : "A streamed event could not be read.",
        );
      }
    };
    source.addEventListener(name, listener);
    return [name, listener] as const;
  });

  return () => {
    for (const [name, listener] of listeners) {
      source.removeEventListener(name, listener);
    }
    source.close();
    handlers.onConnectionChange("closed");
  };
}

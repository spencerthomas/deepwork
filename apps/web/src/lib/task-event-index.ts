import type { TaskEvent } from "./task-types";

/**
 * Append one streamed event without rescanning the complete retained history.
 * The caller owns the task-scoped id set and uses the returned array as the
 * next immutable React snapshot.
 */
export function appendUniqueTaskEvent(
  events: readonly TaskEvent[],
  seenEventIds: Set<string>,
  event: TaskEvent,
): TaskEvent[] | undefined {
  if (seenEventIds.has(event.id)) return undefined;
  seenEventIds.add(event.id);
  return [...events, event];
}

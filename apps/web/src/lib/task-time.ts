/**
 * A short, honest "age" label for a task's real creation time, e.g. "5m ago".
 *
 * The value is derived from the API-recorded `createdAt`; when it is absent,
 * unparseable, or (defensively) in the future, this returns `undefined` so the
 * caller renders nothing rather than a fabricated or nonsensical age. `now` is
 * injectable so the pure formatting is deterministic under test.
 */
export function formatTaskAge(
  createdAt: string | undefined,
  now: number = Date.now(),
): string | undefined {
  if (createdAt === undefined) {
    return undefined;
  }
  const created = Date.parse(createdAt);
  if (Number.isNaN(created) || created > now) {
    return undefined;
  }
  const seconds = Math.floor((now - created) / 1000);
  if (seconds < 60) {
    return "just now";
  }
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) {
    return `${minutes}m ago`;
  }
  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    return `${hours}h ago`;
  }
  const days = Math.floor(hours / 24);
  if (days < 30) {
    return `${days}d ago`;
  }
  const months = Math.floor(days / 30);
  if (months < 12) {
    return `${months}mo ago`;
  }
  return `${Math.floor(days / 365)}y ago`;
}

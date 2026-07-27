/** The largest exact count shown before collapsing to an overflow marker. */
export const NAV_BADGE_MAX = 9;

/**
 * The badge text for a pending count, or null when there is nothing to show.
 * Counts above the cap collapse to "9+" so the badge never grows unbounded.
 * A negative or non-finite count is treated as nothing pending.
 */
export function formatPendingCount(count: number): string | null {
  if (!Number.isFinite(count) || count <= 0) {
    return null;
  }
  const whole = Math.floor(count);
  return whole > NAV_BADGE_MAX ? `${NAV_BADGE_MAX}+` : String(whole);
}

/**
 * The accessible name for the Approvals destination, folding the pending count
 * into the label so assistive tech announces it without relying on the visual
 * badge. Zero (or invalid) leaves the plain label.
 */
export function approvalsNavLabel(count: number): string {
  if (!Number.isFinite(count) || count <= 0) {
    return "Approvals";
  }
  const whole = Math.floor(count);
  return `Approvals, ${whole} ${whole === 1 ? "task needs" : "tasks need"} review`;
}

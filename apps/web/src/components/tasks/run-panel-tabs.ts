/** The run panel's tab identities and labels, in display order. */
export type PanelTab = "status" | "stream" | "evidence" | "files" | "git" | "trace";

export const PANEL_TABS: readonly { key: PanelTab; label: string }[] = [
  { key: "status", label: "Status" },
  { key: "stream", label: "Stream" },
  { key: "evidence", label: "Evidence" },
  { key: "files", label: "Files" },
  { key: "git", label: "Git" },
  { key: "trace", label: "Trace" },
];

const PANEL_TAB_KEYS: readonly PanelTab[] = PANEL_TABS.map((tab) => tab.key);

/**
 * The tab a roving-focus keystroke should move to inside the tablist, following
 * the WAI-ARIA tabs pattern: Left/Right step and wrap horizontally, Home/End
 * jump to the ends. Any other key returns null so the caller leaves it alone.
 */
export function nextPanelTab(current: PanelTab, key: string): PanelTab | null {
  const index = PANEL_TAB_KEYS.indexOf(current);
  if (index === -1) return null;
  const last = PANEL_TAB_KEYS.length - 1;
  switch (key) {
    case "ArrowRight":
      return PANEL_TAB_KEYS[index === last ? 0 : index + 1];
    case "ArrowLeft":
      return PANEL_TAB_KEYS[index === 0 ? last : index - 1];
    case "Home":
      return PANEL_TAB_KEYS[0];
    case "End":
      return PANEL_TAB_KEYS[last];
    default:
      return null;
  }
}

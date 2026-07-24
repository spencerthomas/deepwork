/**
 * Pure settings-section catalog and URL resolution for /settings/{section}.
 * Only sections that really work in the local product are listed.
 */

export const SETTINGS_SECTION_IDS = ["appearance", "runtime", "about"] as const;

export type SettingsSectionId = (typeof SETTINGS_SECTION_IDS)[number];

export interface SettingsSectionDef {
  id: SettingsSectionId;
  label: string;
  /** Extra terms the nav search matches, so a section is found by what it holds. */
  keywords: readonly string[];
}

export interface SettingsGroup {
  label: string;
  items: SettingsSectionDef[];
}

export const SETTINGS_GROUPS: readonly SettingsGroup[] = [
  {
    label: "Workspace",
    items: [
      {
        id: "appearance",
        label: "Appearance",
        keywords: ["theme", "dark", "light", "system", "color", "colour", "contrast", "display"],
      },
      {
        id: "runtime",
        label: "Runtime",
        keywords: ["diagnostics", "capabilities", "connection", "api", "adapter", "provider", "health", "status"],
      },
      {
        id: "about",
        label: "About",
        keywords: ["version", "license", "open source", "oss", "credits", "legal", "build"],
      },
    ],
  },
];

export const ALL_SETTINGS_SECTIONS: readonly SettingsSectionDef[] = SETTINGS_GROUPS.flatMap(
  (group) => group.items,
);

export function isSettingsSectionId(value: string): value is SettingsSectionId {
  return (SETTINGS_SECTION_IDS as readonly string[]).includes(value);
}

/**
 * Resolve the optional catch-all route segments to a section id. Unknown or
 * missing sections default to "appearance"; only the first segment counts.
 */
export function resolveSettingsSection(segments: readonly string[] | undefined): SettingsSectionId {
  const first = segments?.[0]?.toLowerCase();
  return first !== undefined && isSettingsSectionId(first) ? first : "appearance";
}

/**
 * Case-insensitive filter for the settings nav search box. Matches a section by
 * its label or any of its keywords, so searching "theme" finds Appearance and
 * "version" finds About — not only the exact section names.
 */
export function filterSettingsGroups(query: string): SettingsGroup[] {
  const needle = query.trim().toLowerCase();
  if (needle === "") {
    return [...SETTINGS_GROUPS];
  }
  const matches = (item: SettingsSectionDef): boolean =>
    item.label.toLowerCase().includes(needle) ||
    item.keywords.some((keyword) => keyword.includes(needle));
  return SETTINGS_GROUPS.map((group) => ({
    ...group,
    items: group.items.filter(matches),
  })).filter((group) => group.items.length > 0);
}

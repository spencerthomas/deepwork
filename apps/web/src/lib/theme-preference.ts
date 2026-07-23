/**
 * Theme preference logic shared by the settings Appearance section and tests.
 * The stored contract matches the header ThemeToggle: localStorage "dw-theme"
 * holds "light" or "dark"; absence means follow the system preference.
 */

export type ThemePreference = "system" | "light" | "dark";

export const THEME_STORAGE_KEY = "dw-theme";

/** Interpret a raw localStorage value; anything unexpected means "system". */
export function readThemePreference(storedValue: string | null): ThemePreference {
  return storedValue === "light" || storedValue === "dark" ? storedValue : "system";
}

export function resolveIsDark(preference: ThemePreference, systemPrefersDark: boolean): boolean {
  if (preference === "system") {
    return systemPrefersDark;
  }
  return preference === "dark";
}

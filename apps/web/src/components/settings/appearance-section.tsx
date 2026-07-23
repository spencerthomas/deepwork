"use client";

import { useEffect, useState } from "react";

import {
  readThemePreference,
  resolveIsDark,
  THEME_STORAGE_KEY,
  type ThemePreference,
} from "@/lib/theme-preference";

import { Card, GroupLabel, Row, Segmented, SettingsHeader } from "./settings-ui";

const themeOptions: { value: ThemePreference; label: string }[] = [
  { value: "system", label: "System" },
  { value: "light", label: "Light" },
  { value: "dark", label: "Dark" },
];

/**
 * Real theme control. "Light"/"Dark" store an override in localStorage
 * ("dw-theme", the same key the header toggle writes); "System" removes the
 * override and follows the operating system preference.
 */
export function AppearanceSection() {
  const [preference, setPreference] = useState<ThemePreference>("system");

  useEffect(() => {
    setPreference(readThemePreference(window.localStorage.getItem(THEME_STORAGE_KEY)));
  }, []);

  // While "System" is selected, follow OS changes live.
  useEffect(() => {
    if (preference !== "system") {
      return;
    }
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const apply = () => document.documentElement.classList.toggle("dark", media.matches);
    apply();
    media.addEventListener("change", apply);
    return () => media.removeEventListener("change", apply);
  }, [preference]);

  function choose(next: ThemePreference) {
    setPreference(next);
    if (next === "system") {
      window.localStorage.removeItem(THEME_STORAGE_KEY);
    } else {
      window.localStorage.setItem(THEME_STORAGE_KEY, next);
    }
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    document.documentElement.classList.toggle("dark", resolveIsDark(next, prefersDark));
  }

  return (
    <section>
      <SettingsHeader
        title="Appearance"
        description="How Deep Work looks in this browser. The choice is stored locally and applies immediately."
      />
      <GroupLabel>Theme</GroupLabel>
      <Card>
        <Row
          title="Interface theme"
          description="System follows your operating system preference. The sun/moon toggle in the header sets an explicit Light or Dark override."
          control={<Segmented value={preference} options={themeOptions} onChange={choose} />}
        />
      </Card>
    </section>
  );
}

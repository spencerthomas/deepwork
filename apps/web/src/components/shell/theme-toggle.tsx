"use client";

import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";

import { readThemePreference, resolveIsDark, THEME_STORAGE_KEY } from "@/lib/theme-preference";

export function ThemeToggle() {
  const [dark, setDark] = useState(false);

  useEffect(() => {
    const root = document.documentElement;
    const media = window.matchMedia("(prefers-color-scheme: dark)");

    // Keep the icon mirroring the theme that is actually applied, whoever set
    // it — this toggle, the Settings Appearance section (same tab), or another
    // tab. Watching the class rather than local state avoids a stale sun/moon.
    const syncIcon = () => setDark(root.classList.contains("dark"));

    // Re-resolve from the stored preference. While "System" is selected this is
    // how an OS light/dark switch takes effect on every page — the header is
    // mounted app-wide, whereas the Settings section only exists on its route.
    const applyFromStorage = () => {
      const preference = readThemePreference(window.localStorage.getItem(THEME_STORAGE_KEY));
      root.classList.toggle("dark", resolveIsDark(preference, media.matches));
    };

    const onStorage = (event: StorageEvent) => {
      if (event.key === null || event.key === THEME_STORAGE_KEY) applyFromStorage();
    };

    syncIcon();
    const observer = new MutationObserver(syncIcon);
    observer.observe(root, { attributes: true, attributeFilter: ["class"] });
    media.addEventListener("change", applyFromStorage);
    window.addEventListener("storage", onStorage);
    return () => {
      observer.disconnect();
      media.removeEventListener("change", applyFromStorage);
      window.removeEventListener("storage", onStorage);
    };
  }, []);

  function toggle() {
    // The header sets an explicit override, opposite the theme in effect. The
    // MutationObserver above updates the icon once the class flips.
    const next = !document.documentElement.classList.contains("dark");
    window.localStorage.setItem(THEME_STORAGE_KEY, next ? "dark" : "light");
    document.documentElement.classList.toggle("dark", next);
  }

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label="Toggle theme"
      className="flex size-8 items-center justify-center rounded-xl text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
    >
      {dark ? <Moon className="size-4" /> : <Sun className="size-4" />}
    </button>
  );
}

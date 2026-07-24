import "@fontsource-variable/inter";
import "@fontsource/ibm-plex-mono/400.css";
import "@fontsource/ibm-plex-mono/500.css";
import "@fontsource/ibm-plex-mono/600.css";

import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";

import { TasksProvider } from "@/lib/tasks-store";

import "./globals.css";

export const metadata: Metadata = {
  title: "Deep Work — an operations room for your agents",
  description:
    "Delegate meaningful work, supervise execution live, approve what matters, and inspect the evidence behind every result.",
};

export const viewport: Viewport = {
  colorScheme: "light dark",
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#020509" },
  ],
};

/**
 * Applies the persisted (or system) theme before first paint, so dark-mode
 * users don't see a light flash before ThemeToggle hydrates. Mirrors the same
 * `dw-theme` storage key and precedence the toggle uses.
 */
const THEME_INIT = `(function(){try{var s=localStorage.getItem("dw-theme");var d=s?s==="dark":window.matchMedia("(prefers-color-scheme: dark)").matches;if(d)document.documentElement.classList.add("dark");}catch(e){}})();`;

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    // The pre-paint script below sets the `dark` class from client-only state
    // (localStorage / prefers-color-scheme), so the server can't match it.
    // suppressHydrationWarning scopes that expected <html> mismatch — without
    // it React logs a recoverable hydration error that fails strict page-error
    // assertions (e.g. the demo acceptance journey) whenever CI runs dark.
    <html lang="en" className="bg-background" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT }} />
      </head>
      <body className="font-sans antialiased">
        <TasksProvider>{children}</TasksProvider>
      </body>
    </html>
  );
}

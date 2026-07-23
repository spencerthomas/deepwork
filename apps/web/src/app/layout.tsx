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
    <html lang="en" className="bg-background">
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT }} />
      </head>
      <body className="font-sans antialiased">
        <TasksProvider>{children}</TasksProvider>
      </body>
    </html>
  );
}

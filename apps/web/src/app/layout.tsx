import "@fontsource-variable/inter";
import "@fontsource/ibm-plex-mono/400.css";
import "@fontsource/ibm-plex-mono/500.css";
import "@fontsource/ibm-plex-mono/600.css";

import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";

import { TasksProvider } from "@/lib/tasks-store";

import "@deepwork/ui/status-panel.css";
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

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en" className="bg-background">
      <body className="font-sans antialiased">
        <TasksProvider>{children}</TasksProvider>
      </body>
    </html>
  );
}

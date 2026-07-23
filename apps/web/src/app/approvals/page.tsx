import type { Metadata } from "next";

import { ApprovalsView } from "@/components/approvals/approvals-view";

export const metadata: Metadata = {
  title: "Approvals — Deep Work",
  description: "Every run the local runner has paused for a human decision.",
};

export default function ApprovalsPage() {
  return <ApprovalsView />;
}

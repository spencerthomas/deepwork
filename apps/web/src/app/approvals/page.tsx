import type { Metadata } from "next";

import { ApprovalsView } from "@/components/approvals/approvals-view";

export const metadata: Metadata = {
  title: "Approvals — Deep Work",
  description: "Human decisions requested by task runs.",
};

export default function ApprovalsPage() {
  return <ApprovalsView />;
}

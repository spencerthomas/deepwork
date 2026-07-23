import { notFound } from "next/navigation";

import { AgentDetail } from "@/components/agents/agent-detail";

export const metadata = {
  title: "Local deterministic runner — Deep Work",
};

/** Only the embedded local runner exists; every other id is a real 404. */
export default async function AgentPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  if (id !== "local") {
    notFound();
  }
  return <AgentDetail />;
}

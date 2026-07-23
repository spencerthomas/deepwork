import type { Metadata } from "next";

import { ActivityFeed } from "@/components/activity/activity-feed";

export const metadata: Metadata = {
  title: "Activity — Deep Work",
  description: "Task status and events observed by this browser session.",
};

export default function ActivityPage() {
  return <ActivityFeed />;
}

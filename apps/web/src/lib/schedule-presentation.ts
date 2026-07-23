import type { CapabilityState } from "./demo-status";

export interface SchedulePresentation {
  heading: string;
  description: string;
  actionReason: string;
}

/**
 * Keep schedule copy aligned with the reported durable-jobs capability while
 * treating schedule authoring as a separate, currently unavailable feature.
 */
export function schedulePresentation(
  loading: boolean,
  durableJobs: CapabilityState,
): SchedulePresentation {
  if (loading) {
    return {
      heading: "Checking schedule availability",
      description:
        "Waiting for the runtime to report durable job support. No execution or durability state is assumed.",
      actionReason: "Schedule authoring is unavailable while capability status is loading.",
    };
  }

  if (durableJobs === "available") {
    return {
      heading: "Durable jobs are reported available",
      description:
        "The runtime reports durable job support, but schedule authoring has not shipped in this client. No schedule can be created here yet.",
      actionReason: "Schedule authoring has not shipped in this client.",
    };
  }

  if (durableJobs === "unavailable") {
    return {
      heading: "Schedules are unavailable",
      description:
        "The runtime reports durable jobs unavailable. No schedule can be created, stored, or dispatched here.",
      actionReason: "The runtime reports durable jobs unavailable.",
    };
  }

  return {
    heading: "Schedule availability is unknown",
    description:
      "The runtime did not report durable job support. Nothing is assumed, and schedule authoring remains unavailable in this client.",
    actionReason: "Durable job support is unknown and schedule authoring is unavailable.",
  };
}

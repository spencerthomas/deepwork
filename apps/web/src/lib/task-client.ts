import { createFixtureTaskClient } from "./fixture-task-client";
import { createHttpTaskClient } from "./http-task-client";

export const taskClient =
  process.env.NEXT_PUBLIC_DEMO_MODE === "fixture"
    ? createFixtureTaskClient()
    : createHttpTaskClient();

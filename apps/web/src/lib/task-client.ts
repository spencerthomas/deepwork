import { webRuntimeConfig } from "../../config/runtime";
import { createFixtureTaskClient } from "./fixture-task-client";
import { createHttpTaskClient } from "./http-task-client";

export const taskClient =
  webRuntimeConfig.demoMode === "fixture"
    ? createFixtureTaskClient()
    : createHttpTaskClient(webRuntimeConfig.apiBaseUrl);

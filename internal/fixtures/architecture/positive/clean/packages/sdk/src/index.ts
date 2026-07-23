import type { WorkId } from "@deepwork/domain";
import { applicationPath } from "./transport.js";

export type WorkReference = { id: WorkId };
export const workPath = applicationPath;

import type { SourceProbeResult } from "@deepwork/domain";
import {
  createSourceProbeService,
  sourceProbeTransportProblem,
  type OperationOptions,
  type SourceProbeTransport,
} from "@deepwork/sdk";

import { isRecord } from "./wire-utils";

export type { SourceProbeResult, SourceProbeState } from "@deepwork/domain";

const SOURCE_PROBE_TIMEOUT_MS = 15_000;

async function responseValue(response: Response): Promise<unknown> {
  const text = await response.text();
  if (text === "") return undefined;
  try {
    return JSON.parse(text);
  } catch {
    return undefined;
  }
}

function createHttpSourceProbeTransport(apiBaseUrl: string): SourceProbeTransport {
  const url = `${apiBaseUrl.replace(/\/+$/, "")}/api/v1/sources/probes`;
  return Object.freeze({
    async check(request: Parameters<SourceProbeTransport["check"]>[0], options?: OperationOptions) {
      const response = await fetch(url, {
        method: "POST",
        credentials: "include",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(request),
        signal: options?.signal,
      });
      const value = await responseValue(response);
      if (!response.ok) {
        const code = isRecord(value) && typeof value.code === "string" ? value.code : "";
        throw sourceProbeTransportProblem(response.status, code);
      }
      return value;
    },
  });
}

export async function probeClassicSource(
  apiBaseUrl: string,
  input: { assistantId: string },
  signal?: AbortSignal,
): Promise<SourceProbeResult> {
  const deadline = new AbortController();
  let timedOut = false;
  const timeout = globalThis.setTimeout(() => {
    timedOut = true;
    deadline.abort();
  }, SOURCE_PROBE_TIMEOUT_MS);
  const abortFromCaller = () => deadline.abort();
  signal?.addEventListener("abort", abortFromCaller, { once: true });
  if (signal?.aborted) deadline.abort();
  try {
    const result = await createSourceProbeService(createHttpSourceProbeTransport(apiBaseUrl)).check(
      input,
      { signal: deadline.signal },
    );
    if (timedOut) throw new Error("The source check timed out. Try again.");
    if (!result.ok) throw new Error(result.error.safeMessage);
    return result.value;
  } finally {
    globalThis.clearTimeout(timeout);
    signal?.removeEventListener("abort", abortFromCaller);
  }
}

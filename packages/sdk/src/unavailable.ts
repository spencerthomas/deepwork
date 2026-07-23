import type { UnavailableCapabilitySummary } from "@deepwork/domain";

import type { MutationPort, QueryPort, StreamPort } from "./ports.js";
import { capabilityUnavailableError, type SdkResult } from "./result.js";

function unavailable<T>(capability: UnavailableCapabilitySummary): SdkResult<T> {
  return {
    ok: false,
    error: capabilityUnavailableError(capability),
  };
}

export function unavailableQueryPort<Request, Response>(
  capability: UnavailableCapabilitySummary,
): QueryPort<Request, Response> {
  return Object.freeze({
    query: async () => unavailable<Response>(capability),
  });
}

export function unavailableMutationPort<Request, Response>(
  capability: UnavailableCapabilitySummary,
): MutationPort<Request, Response> {
  return Object.freeze({
    mutate: async () => unavailable<Response>(capability),
  });
}

export function unavailableStreamPort<Request, Event>(
  capability: UnavailableCapabilitySummary,
): StreamPort<Request, Event> {
  return Object.freeze({
    open: async () => unavailable<AsyncIterable<Event>>(capability),
  });
}

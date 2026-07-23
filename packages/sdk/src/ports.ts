import type { SdkResult } from "./result.js";

export interface OperationOptions {
  readonly signal?: AbortSignal;
}

export interface QueryPort<Request, Response> {
  query(request: Request, options?: OperationOptions): Promise<SdkResult<Response>>;
}

export interface MutationPort<Request, Response> {
  mutate(request: Request, options?: OperationOptions): Promise<SdkResult<Response>>;
}

export interface StreamPort<Request, Event> {
  open(request: Request, options?: OperationOptions): Promise<SdkResult<AsyncIterable<Event>>>;
}

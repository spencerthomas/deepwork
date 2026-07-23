import type { SdkResult } from "./result.js";

export interface ContractMapper<WireValue, DomainValue> {
  map(value: WireValue): SdkResult<DomainValue>;
}

export interface GeneratedQueryTransport<Request, WireResponse> {
  execute(
    request: Request,
    options?: { readonly signal?: AbortSignal },
  ): Promise<WireResponse>;
}

export interface GeneratedMutationTransport<Request, WireResponse> {
  execute(
    request: Request,
    options?: { readonly signal?: AbortSignal },
  ): Promise<WireResponse>;
}

export interface GeneratedStreamTransport<Request, WireEvent> {
  open(
    request: Request,
    options?: { readonly signal?: AbortSignal },
  ): Promise<AsyncIterable<WireEvent>>;
}

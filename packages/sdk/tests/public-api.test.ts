import type {
  GeneratedMutationTransport,
  MutationPort,
  QueryPort,
  StreamPort,
} from "@deepwork/sdk";
import { describe, expectTypeOf, it } from "vitest";

describe("public contracts", () => {
  it("exposes framework-neutral ports without deep imports", () => {
    expectTypeOf<QueryPort<unknown, unknown>>().toBeObject();
    expectTypeOf<MutationPort<unknown, unknown>>().toBeObject();
    expectTypeOf<StreamPort<unknown, unknown>>().toBeObject();
    expectTypeOf<GeneratedMutationTransport<unknown, unknown>>().toBeObject();
  });
});

import {
  availableCapability,
  capabilitySummary,
  CAPABILITY_EVIDENCE_CLASSES,
  CAPABILITY_SAFE_REASONS,
  CAPABILITY_STATES,
  isCapabilityAvailable,
  rfc3339Instant,
  type CapabilityEvidence,
  type CapabilitySummary,
  unavailableCapability,
} from "@deepwork/domain";
import { describe, expect, expectTypeOf, it } from "vitest";

const metadata = {
  observedAt: "2026-07-23T00:00:00.000Z",
  adapterVersion: "adapter-contract-1",
  contractVersion: "normalized-contract-1",
  evidenceClass: "documented" as const,
};

describe("capability evidence", () => {
  it("keeps unknown support explicitly unavailable", () => {
    const evidence = unavailableCapability("unknown", "contract-not-verified", metadata);

    expect(isCapabilityAvailable(evidence)).toBe(false);
    expect(evidence.safeReason).toBe("contract-not-verified");
  });

  it("omits capability values from safe summaries", () => {
    const evidence = availableCapability({ privatePayload: "must-not-be-summarized" }, metadata);

    expect(capabilitySummary(evidence)).toEqual({
      state: "available",
      ...metadata,
    });
    expect(JSON.stringify(capabilitySummary(evidence))).not.toContain("privatePayload");
  });

  it("preserves a safe summary type for union evidence", () => {
    const evidence = unavailableCapability(
      "unknown",
      "contract-not-verified",
      metadata,
    ) as CapabilityEvidence<string>;

    expectTypeOf(capabilitySummary(evidence)).toEqualTypeOf<CapabilitySummary>();
  });

  it("snapshots and deeply freezes supported evidence values", () => {
    const original = {
      modes: ["read", "write"],
      policy: { enabled: true },
    };
    const evidence = availableCapability(original, metadata);

    original.modes.push("mutated");
    original.policy.enabled = false;

    expect(evidence.value).toEqual({
      modes: ["read", "write"],
      policy: { enabled: true },
    });
    expect(Object.isFrozen(evidence.value)).toBe(true);
    expect(Object.isFrozen(evidence.value.modes)).toBe(true);
    expect(Object.isFrozen(evidence.value.policy)).toBe(true);
    expect(() => {
      (evidence.value.modes as string[]).push("blocked");
    }).toThrow(TypeError);
  });

  it("rejects unsupported, cyclic, and non-finite evidence values", () => {
    const cyclic: Record<string, unknown> = {};
    cyclic.self = cyclic;
    const unsupported = [undefined, 1n, Symbol("unsupported"), () => "unsupported"];
    const symbolKeyed = {
      [Symbol("unsupported")]: true,
    };

    expect(() => availableCapability(Number.NaN, metadata)).toThrow(TypeError);
    expect(() => availableCapability(new Date() as never, metadata)).toThrow(TypeError);
    expect(() => availableCapability(cyclic as never, metadata)).toThrow(TypeError);
    for (const value of unsupported) {
      expect(() => availableCapability(value as never, metadata)).toThrow(TypeError);
    }
    expect(() => availableCapability({ nested: undefined } as never, metadata)).toThrow(TypeError);
    expect(() => availableCapability([true, , false] as never, metadata)).toThrow(TypeError);
    expect(() => availableCapability(symbolKeyed as never, metadata)).toThrow(TypeError);
  });

  it("accepts only declared JSON-compatible evidence classes at runtime", () => {
    for (const evidenceClass of CAPABILITY_EVIDENCE_CLASSES) {
      const acceptedMetadata = { ...metadata, evidenceClass };
      const available = availableCapability(true, acceptedMetadata);
      const unavailable = unavailableCapability(
        "unknown",
        "contract-not-verified",
        acceptedMetadata,
      );

      expect(JSON.parse(JSON.stringify(available))).toEqual(available);
      expect(JSON.parse(JSON.stringify(unavailable))).toEqual(unavailable);
    }

    for (const evidenceClass of [
      undefined,
      null,
      "unverified",
      0,
      {},
      [],
      Symbol("unsupported"),
      () => "unsupported",
    ]) {
      const invalidMetadata = {
        ...metadata,
        evidenceClass,
      } as never;
      expect(() => availableCapability(true, invalidMetadata)).toThrow(TypeError);
      expect(() =>
        unavailableCapability("unknown", "contract-not-verified", invalidMetadata),
      ).toThrow(TypeError);
    }
  });

  it("rejects incoherent unavailable state and reason pairs", () => {
    expect(() =>
      unavailableCapability("permission-denied", "source-unavailable", metadata),
    ).toThrow(TypeError);
    expect(() => unavailableCapability("unknown", "source-unavailable", metadata)).toThrow(
      TypeError,
    );
  });

  it("freezes exported vocabularies", () => {
    expect(Object.isFrozen(CAPABILITY_STATES)).toBe(true);
    expect(Object.isFrozen(CAPABILITY_EVIDENCE_CLASSES)).toBe(true);
    expect(Object.isFrozen(CAPABILITY_SAFE_REASONS)).toBe(true);
    expect(() => {
      (CAPABILITY_STATES as unknown as string[]).push("mutated");
    }).toThrow(TypeError);
  });

  it("validates and normalizes canonical RFC3339 instants", () => {
    expect(rfc3339Instant("2026-07-23T10:30:15.25+10:00")).toBe("2026-07-23T00:30:15.250Z");
    expect(rfc3339Instant("2024-02-29T00:00:00Z")).toBe("2024-02-29T00:00:00.000Z");
    expect(
      availableCapability(true, {
        ...metadata,
        observedAt: "2026-07-23T10:30:15+10:00",
      }).observedAt,
    ).toBe("2026-07-23T00:30:15.000Z");

    for (const invalid of [
      "2026-07-23",
      "2026-07-23 00:00:00Z",
      "2026-07-23T00:00:00z",
      "2026-02-30T00:00:00Z",
      "2026-07-23T00:00:00.1234Z",
      "2026-07-23T24:00:00Z",
      "0001-01-01T00:00:00+23:59",
      "9999-12-31T23:59:59-23:59",
    ]) {
      expect(() => rfc3339Instant(invalid)).toThrow(TypeError);
    }
    expect(() =>
      unavailableCapability("unknown", "contract-not-verified", {
        ...metadata,
        observedAt: "2026-02-30T00:00:00Z",
      }),
    ).toThrow(TypeError);
  });
});

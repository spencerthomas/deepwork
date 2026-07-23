import dgram from "node:dgram";
import http from "node:http";
import https from "node:https";
import net from "node:net";
import tls from "node:tls";

import { describe, expect, it } from "vitest";

const message = "Outbound network access is denied in SDK unit tests.";

describe("global SDK unit network denial", () => {
  it("guards browser network primitives for every test", () => {
    expect(() => globalThis.fetch("https://fixture.invalid")).toThrow(message);
    expect(() => new globalThis.XMLHttpRequest()).toThrow(message);
    expect(() => new globalThis.WebSocket("wss://fixture.invalid")).toThrow(message);
    expect(() => new globalThis.EventSource("https://fixture.invalid")).toThrow(message);
  });

  it("guards Node HTTP and socket escape paths", () => {
    for (const escape of [
      () => http.request("https://fixture.invalid"),
      () => http.get("https://fixture.invalid"),
      () => https.request("https://fixture.invalid"),
      () => https.get("https://fixture.invalid"),
      () => net.connect(443, "fixture.invalid"),
      () => net.createConnection(443, "fixture.invalid"),
      () => new net.Socket().connect(443, "fixture.invalid"),
      () => tls.connect(443, "fixture.invalid"),
      () => dgram.createSocket("udp4"),
      () => new dgram.Socket("udp4").bind(0),
      () => new dgram.Socket("udp4").connect(53, "fixture.invalid"),
      () => new dgram.Socket("udp4").send("blocked", 53, "fixture.invalid"),
      () => new http.Agent().createConnection({ host: "fixture.invalid" }),
      () => new https.Agent().createConnection({ host: "fixture.invalid" }),
    ]) {
      expect(escape).toThrow(message);
    }
  });

  it("publishes the complete immutable guard inventory", () => {
    expect(globalThis.__DEEPWORK_NETWORK_DENIAL__.guarded).toHaveLength(18);
    expect(Object.isFrozen(globalThis.__DEEPWORK_NETWORK_DENIAL__)).toBe(true);
  });
});

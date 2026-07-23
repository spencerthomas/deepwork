import dgram from "node:dgram";
import http from "node:http";
import https from "node:https";
import { syncBuiltinESMExports } from "node:module";
import net from "node:net";
import tls from "node:tls";

const MESSAGE = "Outbound network access is denied in SDK unit tests.";

function denyNetwork() {
  throw new Error(MESSAGE);
}

class DeniedNetworkConstructor {
  constructor() {
    denyNetwork();
  }
}

Object.defineProperties(globalThis, {
  fetch: {
    configurable: true,
    writable: true,
    value: denyNetwork,
  },
  XMLHttpRequest: {
    configurable: true,
    writable: true,
    value: DeniedNetworkConstructor,
  },
  WebSocket: {
    configurable: true,
    writable: true,
    value: DeniedNetworkConstructor,
  },
  EventSource: {
    configurable: true,
    writable: true,
    value: DeniedNetworkConstructor,
  },
});

http.request = denyNetwork;
http.get = denyNetwork;
https.request = denyNetwork;
https.get = denyNetwork;
net.connect = denyNetwork;
net.createConnection = denyNetwork;
net.Socket.prototype.connect = denyNetwork;
tls.connect = denyNetwork;
dgram.createSocket = denyNetwork;
dgram.Socket.prototype.bind = denyNetwork;
dgram.Socket.prototype.connect = denyNetwork;
dgram.Socket.prototype.send = denyNetwork;
http.Agent.prototype.createConnection = denyNetwork;
https.Agent.prototype.createConnection = denyNetwork;
syncBuiltinESMExports();

globalThis.__DEEPWORK_NETWORK_DENIAL__ = Object.freeze({
  message: MESSAGE,
  guarded: Object.freeze([
    "fetch",
    "XMLHttpRequest",
    "WebSocket",
    "EventSource",
    "node:http.request",
    "node:http.get",
    "node:https.request",
    "node:https.get",
    "node:net.connect",
    "node:net.createConnection",
    "node:net.Socket.prototype.connect",
    "node:tls.connect",
    "node:dgram.createSocket",
    "node:dgram.Socket.prototype.bind",
    "node:dgram.Socket.prototype.connect",
    "node:dgram.Socket.prototype.send",
    "node:http.Agent.prototype.createConnection",
    "node:https.Agent.prototype.createConnection",
  ]),
});

import { isRecord } from "./task-normalizers";

export type LoginResult = { ok: true } | { ok: false; reason: "rejected" | "failed" };

export interface Session {
  actorId: string;
  expiresAt: number;
}

function toSession(value: unknown): Session {
  if (!isRecord(value)) {
    throw new Error("The API returned a malformed session.");
  }
  const actorId = value["actorId"];
  const expiresAt = value["expiresAt"];
  if (typeof actorId !== "string" || typeof expiresAt !== "number") {
    throw new Error("The API returned a malformed session.");
  }
  return { actorId, expiresAt };
}

/** Exchange an access key through the same-origin API proxy for an HttpOnly session. */
export async function loginWithAccessKey(accessKey: string): Promise<LoginResult> {
  const response = await fetch("/api/v1/auth/login", {
    method: "POST",
    credentials: "include",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ accessKey }),
    signal: AbortSignal.timeout(15_000),
  });
  if (response.ok) return { ok: true };
  return { ok: false, reason: response.status === 401 ? "rejected" : "failed" };
}

/** Read the browser's current authenticated session through the same-origin proxy. */
export async function getSession(signal?: AbortSignal): Promise<Session> {
  const response = await fetch("/api/v1/auth/session", {
    credentials: "include",
    signal,
  });
  if (!response.ok) {
    throw new Error(`The API returned HTTP ${response.status}.`);
  }
  return toSession(await response.json());
}

/** Clear the HttpOnly session cookie server-side. */
export async function logout(signal?: AbortSignal): Promise<void> {
  await fetch("/api/v1/auth/logout", {
    method: "POST",
    credentials: "include",
    signal,
  });
}

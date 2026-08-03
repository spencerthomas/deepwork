export type LoginResult = { ok: true } | { ok: false; reason: "rejected" | "failed" };

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

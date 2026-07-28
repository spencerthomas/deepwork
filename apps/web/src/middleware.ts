import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import { webRuntimeConfig } from "../config/runtime";

const SESSION_COOKIE = "deepwork_session";

export type SessionGateTarget = "/login" | "/tasks" | null;

/**
 * Decide whether a browser route needs an authentication redirect.
 *
 * The fixture harness is intentionally credential-free and never calls the API,
 * so requiring an API session there would make `pnpm demo:web` unusable.
 */
export function sessionGateTarget(
  pathname: string,
  hasSession: boolean,
  fixtureMode: boolean,
): SessionGateTarget {
  if (fixtureMode) {
    return pathname === "/login" ? "/tasks" : null;
  }
  if (!hasSession && pathname !== "/login") {
    return "/login";
  }
  if (hasSession && pathname === "/login") {
    return "/tasks";
  }
  return null;
}

// Gate the app on the presence of the session cookie. The cookie is HttpOnly and
// set by the API's /api/v1/auth/login (proxied same-origin), so it is readable
// here on the server but not from client JS. /api/* is excluded so the login
// request itself and the proxied API calls pass through.
export function middleware(request: NextRequest): NextResponse {
  const hasSession = request.cookies.has(SESSION_COOKIE);
  const { pathname } = request.nextUrl;
  const fixtureMode = webRuntimeConfig.demoMode === "fixture";
  const target = sessionGateTarget(pathname, hasSession, fixtureMode);

  if (target !== null) {
    return NextResponse.redirect(new URL(target, request.url));
  }
  return NextResponse.next();
}

export const config = {
  // Run on all routes except API proxy, Next internals, and static files.
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico|.*\\.).*)"],
};

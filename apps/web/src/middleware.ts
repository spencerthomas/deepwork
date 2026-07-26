import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const SESSION_COOKIE = "deepwork_session";

// Gate the app on the presence of the session cookie. The cookie is HttpOnly and
// set by the API's /api/v1/auth/login (proxied same-origin), so it is readable
// here on the server but not from client JS. /api/* is excluded so the login
// request itself and the proxied API calls pass through.
export function middleware(request: NextRequest): NextResponse {
  const hasSession = request.cookies.has(SESSION_COOKIE);
  const { pathname } = request.nextUrl;

  if (!hasSession && pathname !== "/login") {
    return NextResponse.redirect(new URL("/login", request.url));
  }
  if (hasSession && pathname === "/login") {
    return NextResponse.redirect(new URL("/tasks", request.url));
  }
  return NextResponse.next();
}

export const config = {
  // Run on all routes except API proxy, Next internals, and static files.
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico|.*\\.).*)"],
};

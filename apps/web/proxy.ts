import { NextResponse, type NextRequest } from "next/server";

const SESSION_COOKIE_NAME = "vesta_admin_session";

export function proxy(request: NextRequest) {
  if (request.cookies.has(SESSION_COOKIE_NAME)) {
    return NextResponse.next();
  }
  return NextResponse.redirect(new URL("/admin/login", request.url));
}

export const config = {
  matcher: ["/admin/((?!login).*)"],
};

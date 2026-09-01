import { NextResponse } from "next/server";

import { isAllowedAdminMutationOrigin } from "@/lib/admin-origin";

export function rejectCrossSiteMutation(request: Request) {
  if (!isAllowedAdminMutationOrigin(request)) {
    return NextResponse.json({ detail: "invalid_origin" }, { status: 403 });
  }
  return null;
}

export async function proxyAdminRequest(
  request: Request,
  path: string,
  method: "GET" | "POST" | "PUT",
) {
  const apiUrl = process.env.VESTA_API_URL ?? "http://localhost:8000";
  try {
    const response = await fetch(`${apiUrl}${path}`, {
      method,
      headers: {
        cookie: request.headers.get("cookie") ?? "",
        ...(method === "GET" ? {} : { "Content-Type": "application/json" }),
      },
      body: method === "GET" ? undefined : await request.text(),
      cache: "no-store",
    });
    return new NextResponse(await response.text(), {
      status: response.status,
      headers: {
        "Cache-Control": "no-store",
        "Content-Type": "application/json",
      },
    });
  } catch {
    return NextResponse.json(
      { detail: "admin_service_unavailable" },
      { status: 503 },
    );
  }
}

import { NextResponse } from "next/server";

export async function POST(request: Request) {
  const apiUrl = process.env.VESTA_API_URL ?? "http://localhost:8000";

  try {
    const response = await fetch(`${apiUrl}/v1/admin/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: await request.text(),
      cache: "no-store",
    });

    const nextResponse = new NextResponse(await response.text(), {
      status: response.status,
      headers: {
        "Cache-Control": "no-store",
        "Content-Type": "application/json",
      },
    });
    const setCookie = response.headers.get("set-cookie");
    if (setCookie) {
      nextResponse.headers.set("set-cookie", setCookie);
    }
    const retryAfter = response.headers.get("retry-after");
    if (retryAfter) {
      nextResponse.headers.set("retry-after", retryAfter);
    }
    return nextResponse;
  } catch {
    return NextResponse.json({ detail: "admin_service_unavailable" }, { status: 503 });
  }
}

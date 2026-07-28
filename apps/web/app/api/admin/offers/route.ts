import { NextResponse } from "next/server";

export async function GET(request: Request) {
  const apiUrl = process.env.VESTA_API_URL ?? "http://localhost:8000";
  const { search } = new URL(request.url);

  try {
    const response = await fetch(`${apiUrl}/v1/admin/offers${search}`, {
      method: "GET",
      headers: { cookie: request.headers.get("cookie") ?? "" },
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
    return NextResponse.json({ detail: "admin_service_unavailable" }, { status: 503 });
  }
}

import { NextResponse } from "next/server";

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const apiUrl = process.env.VESTA_API_URL ?? "http://localhost:8000";

  try {
    const response = await fetch(
      `${apiUrl}/v1/admin/ai-audit-workflows/${encodeURIComponent(id)}`,
      {
        method: "GET",
        headers: { cookie: request.headers.get("cookie") ?? "" },
        cache: "no-store",
      },
    );

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

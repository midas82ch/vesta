import { NextResponse } from "next/server";

export async function GET(request: Request) {
  const apiUrl = process.env.VESTA_API_URL ?? "http://localhost:8000";
  const language = new URL(request.url).searchParams.get("language") ?? "de";
  try {
    const response = await fetch(
      `${apiUrl}/v1/catalog/categories?language=${encodeURIComponent(language)}`,
      { cache: "no-store" },
    );
    return new NextResponse(await response.text(), {
      status: response.status,
      headers: {
        "Cache-Control": "no-store",
        "Content-Type": "application/json",
      },
    });
  } catch {
    return NextResponse.json(
      { detail: "catalog_service_unavailable" },
      { status: 503 },
    );
  }
}

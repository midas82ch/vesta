import { NextResponse } from "next/server";


export async function POST(request: Request) {
  const apiUrl = process.env.VESTA_API_URL ?? "http://localhost:8000";

  try {
    const response = await fetch(`${apiUrl}/v1/dialogue/interpret`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: await request.text(),
      cache: "no-store",
    });

    return new NextResponse(await response.text(), {
      status: response.status,
      headers: { "Content-Type": "application/json" },
    });
  } catch {
    return NextResponse.json(
      { detail: "dialogue_service_unavailable" },
      { status: 503 },
    );
  }
}

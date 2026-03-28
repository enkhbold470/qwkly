import { NextRequest, NextResponse } from "next/server";

const backendBaseUrl =
  process.env.REELFORGE_BACKEND_URL ||
  process.env.NEXT_PUBLIC_REELFORGE_API_URL ||
  "http://127.0.0.1:8000";

export async function POST(request: NextRequest) {
  const body = await request.text();
  const authorization = request.headers.get("authorization");

  const response = await fetch(`${backendBaseUrl}/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(authorization ? { Authorization: authorization } : {})
    },
    body,
    cache: "no-store"
  });

  if (!response.ok || !response.body) {
    const text = await response.text();
    return NextResponse.json(
      {
        error: text || "Failed to reach qwkly core API."
      },
      { status: response.status || 500 }
    );
  }

  return new Response(response.body, {
    status: response.status,
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive"
    }
  });
}

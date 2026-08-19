import { NextRequest, NextResponse } from "next/server";
import { authHeader, backendFetch } from "@/lib/backend";

export async function POST(request: NextRequest) {
  const token = request.cookies.get("session")?.value;

  if (!token) {
    return NextResponse.json({ error: "Not authenticated" }, { status: 401 });
  }

  let body: { message?: string; conversation_id?: string };

  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      { error: "Request body must be valid JSON." },
      { status: 400 }
    );
  }

  if (!body.message || typeof body.message !== "string") {
    return NextResponse.json(
      { error: "A non-empty 'message' string is required." },
      { status: 400 }
    );
  }

  const result = await backendFetch("/service-desk", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeader(token) },
    body: JSON.stringify({
      message: body.message,
      conversation_id: body.conversation_id ?? null,
    }),
  });

  if (!result.ok) return result.response;
  return NextResponse.json(result.data);
}

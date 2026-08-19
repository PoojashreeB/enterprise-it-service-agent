import { NextRequest, NextResponse } from "next/server";
import { authHeader, backendFetch } from "@/lib/backend";

export async function GET(request: NextRequest) {
  const token = request.cookies.get("session")?.value;

  if (!token) {
    return NextResponse.json({ error: "Not authenticated" }, { status: 401 });
  }

  const result = await backendFetch("/conversations", {
    headers: authHeader(token),
  });
  if (!result.ok) return result.response;

  return NextResponse.json(result.data);
}

export async function POST(request: NextRequest) {
  const token = request.cookies.get("session")?.value;

  if (!token) {
    return NextResponse.json({ error: "Not authenticated" }, { status: 401 });
  }

  const result = await backendFetch("/conversations", {
    method: "POST",
    headers: authHeader(token),
  });
  if (!result.ok) return result.response;

  return NextResponse.json(result.data);
}

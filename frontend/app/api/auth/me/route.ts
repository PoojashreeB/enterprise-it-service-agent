import { NextRequest, NextResponse } from "next/server";
import { authHeader, backendFetch } from "@/lib/backend";

export async function GET(request: NextRequest) {
  const token = request.cookies.get("session")?.value;

  if (!token) {
    return NextResponse.json({ error: "Not authenticated" }, { status: 401 });
  }

  const result = await backendFetch("/auth/me", { headers: authHeader(token) });
  if (!result.ok) return result.response;

  return NextResponse.json({ user: result.data });
}

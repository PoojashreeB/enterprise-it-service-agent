import { NextRequest, NextResponse } from "next/server";
import { authHeader, backendFetch } from "@/lib/backend";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const token = request.cookies.get("session")?.value;

  if (!token) {
    return NextResponse.json({ error: "Not authenticated" }, { status: 401 });
  }

  const { id } = await params;
  const result = await backendFetch(`/conversations/${id}`, {
    headers: authHeader(token),
  });
  if (!result.ok) return result.response;

  return NextResponse.json(result.data);
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const token = request.cookies.get("session")?.value;

  if (!token) {
    return NextResponse.json({ error: "Not authenticated" }, { status: 401 });
  }

  const { id } = await params;
  const result = await backendFetch(`/conversations/${id}`, {
    method: "DELETE",
    headers: authHeader(token),
  });
  if (!result.ok) return result.response;

  return NextResponse.json({ ok: true });
}

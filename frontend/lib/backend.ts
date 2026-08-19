import { NextResponse } from "next/server";

export const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

type BackendResult =
  | { ok: true; data: unknown }
  | { ok: false; response: NextResponse };

export async function backendFetch(
  path: string,
  init: RequestInit = {}
): Promise<BackendResult> {
  let res: Response;

  try {
    res = await fetch(`${BACKEND_URL}${path}`, init);
  } catch {
    return {
      ok: false,
      response: NextResponse.json(
        { error: "Could not reach the service desk backend." },
        { status: 502 }
      ),
    };
  }

  const raw = await res.text();
  let data: unknown = null;

  if (raw) {
    try {
      data = JSON.parse(raw);
    } catch {
      return {
        ok: false,
        response: NextResponse.json(
          { error: "The backend returned an unexpected response." },
          { status: 502 }
        ),
      };
    }
  }

  if (!res.ok) {
    const detail =
      typeof data === "object" && data !== null && "detail" in data
        ? (data as { detail?: string }).detail
        : undefined;

    return {
      ok: false,
      response: NextResponse.json(
        { error: detail || "The backend returned an error." },
        { status: res.status }
      ),
    };
  }

  return { ok: true, data };
}

export function authHeader(token: string): Record<string, string> {
  return { Authorization: `Bearer ${token}` };
}

export function buildAuthResponse(data: unknown): NextResponse {
  const { access_token, user } = data as {
    access_token: string;
    user: unknown;
  };

  const response = NextResponse.json({ user });
  response.cookies.set("session", access_token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24 * 7,
  });
  return response;
}

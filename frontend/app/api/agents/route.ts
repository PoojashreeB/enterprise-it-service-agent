import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function POST(request: NextRequest) {
  let message: string;

  try {
    const body = await request.json();
    message = body.message;
  } catch {
    return NextResponse.json(
      { error: "Request body must be valid JSON." },
      { status: 400 }
    );
  }

  if (!message || typeof message !== "string") {
    return NextResponse.json(
      { error: "A non-empty 'message' string is required." },
      { status: 400 }
    );
  }

  let backendResponse: Response;

  try {
    backendResponse = await fetch(`${BACKEND_URL}/service-desk`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
  } catch (err) {
    console.error("Failed to reach service desk backend:", err);
    return NextResponse.json(
      { error: "Could not reach the service desk agent backend." },
      { status: 502 }
    );
  }

  const rawBody = await backendResponse.text();
  let data: unknown;

  try {
    data = JSON.parse(rawBody);
  } catch {
    console.error(
      `Service desk backend returned non-JSON response (status ${backendResponse.status}):`,
      rawBody
    );
    return NextResponse.json(
      { error: "The service desk agent returned an unexpected response." },
      { status: 502 }
    );
  }

  if (!backendResponse.ok) {
    const detail =
      typeof data === "object" && data !== null && "detail" in data
        ? (data as { detail?: string }).detail
        : undefined;

    return NextResponse.json(
      { error: detail || "The service desk agent returned an error." },
      { status: backendResponse.status }
    );
  }

  return NextResponse.json(data);
}

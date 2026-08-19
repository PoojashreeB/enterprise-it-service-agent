export interface ServiceDeskResult {
  user_query?: string;
  intent?: string;
  category?: string;
  subcategory?: string;
  confidence?: number;
  impact?: string;
  urgency?: string;
  priority?: string;
  justification?: string;
  decision?: string;
  knowledge?: string;
  clarification_question?: string;
  ticket_number?: string;
  final_response?: string;
}

export async function sendServiceDeskMessage(
  message: string
): Promise<ServiceDeskResult> {
  const response = await fetch("/api/agents", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data?.error || "Something went wrong.");
  }

  return data as ServiceDeskResult;
}

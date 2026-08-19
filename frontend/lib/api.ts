import { Conversation, ConversationDetail, User } from "./types";

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
  conversation_id?: string;
}

async function parseOrThrow<T>(response: Response): Promise<T> {
  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(data?.error || "Something went wrong.");
  }

  return data as T;
}

export async function sendServiceDeskMessage(
  message: string,
  conversationId?: string
): Promise<ServiceDeskResult> {
  const response = await fetch("/api/agents", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, conversation_id: conversationId }),
  });

  return parseOrThrow<ServiceDeskResult>(response);
}

export async function login(email: string, password: string): Promise<{ user: User }> {
  const response = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  return parseOrThrow<{ user: User }>(response);
}

export async function signup(email: string, password: string): Promise<{ user: User }> {
  const response = await fetch("/api/auth/signup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  return parseOrThrow<{ user: User }>(response);
}

export async function logout(): Promise<void> {
  await fetch("/api/auth/logout", { method: "POST" });
}

export async function fetchMe(): Promise<{ user: User }> {
  const response = await fetch("/api/auth/me");
  return parseOrThrow<{ user: User }>(response);
}

export async function fetchConversations(): Promise<Conversation[]> {
  const response = await fetch("/api/conversations");
  return parseOrThrow<Conversation[]>(response);
}

export async function createConversation(): Promise<Conversation> {
  const response = await fetch("/api/conversations", { method: "POST" });
  return parseOrThrow<Conversation>(response);
}

export async function fetchConversation(id: string): Promise<ConversationDetail> {
  const response = await fetch(`/api/conversations/${id}`);
  return parseOrThrow<ConversationDetail>(response);
}

export async function deleteConversation(id: string): Promise<void> {
  const response = await fetch(`/api/conversations/${id}`, { method: "DELETE" });
  await parseOrThrow<{ ok: boolean }>(response);
}

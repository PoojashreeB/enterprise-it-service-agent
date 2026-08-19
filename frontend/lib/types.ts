import { ServiceDeskResult } from "./api";

export interface ChatMessage {
  id: string;
  role: "user" | "agent" | "error";
  content: string;
  result?: ServiceDeskResult;
}

export interface User {
  id: string;
  email: string;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ConversationMessage {
  id: string;
  role: string;
  content: string;
  meta?: {
    category?: string;
    subcategory?: string;
    priority?: string;
    decision?: string;
    ticket_number?: string;
  } | null;
  created_at: string;
}

export interface ConversationDetail extends Conversation {
  messages: ConversationMessage[];
}

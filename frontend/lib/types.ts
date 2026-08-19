import { ServiceDeskResult } from "./api";

export interface ChatMessage {
  id: string;
  role: "user" | "agent" | "error";
  content: string;
  result?: ServiceDeskResult;
}

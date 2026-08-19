"use client";

import { useEffect, useRef, useState } from "react";
import ChatMessage from "@/components/ChatMessage";
import ChatInput from "@/components/ChatInput";
import { sendServiceDeskMessage } from "@/lib/api";
import { ChatMessage as ChatMessageType } from "@/lib/types";

function makeId() {
  return Math.random().toString(36).slice(2);
}

export default function Home() {
  const [messages, setMessages] = useState<ChatMessageType[]>([
    {
      id: makeId(),
      role: "agent",
      content:
        "Hi, I'm the IT Service Desk assistant. Describe the issue you're running into and I'll help you sort it out.",
    },
  ]);
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function handleSend(message: string) {
    setMessages((prev) => [
      ...prev,
      { id: makeId(), role: "user", content: message },
    ]);
    setLoading(true);

    try {
      const result = await sendServiceDeskMessage(message);

      setMessages((prev) => [
        ...prev,
        {
          id: makeId(),
          role: "agent",
          content:
            result.final_response ??
            "Sorry, I didn't get a usable response that time.",
          result,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: makeId(),
          role: "error",
          content:
            err instanceof Error
              ? err.message
              : "Something went wrong talking to the service desk agent.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex h-screen flex-col bg-slate-950">
      <header className="border-b border-slate-800 px-6 py-4">
        <h1 className="text-lg font-semibold text-slate-100">
          Enterprise IT Service Desk
        </h1>
        <p className="text-xs text-slate-500">
          AI-assisted triage, troubleshooting, and ticketing
        </p>
      </header>

      <div className="flex-1 space-y-4 overflow-y-auto px-6 py-6">
        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="rounded-2xl rounded-bl-sm bg-slate-800 px-4 py-3 text-sm text-slate-400">
              <span className="inline-flex gap-1">
                <span className="animate-bounce [animation-delay:-0.3s]">.</span>
                <span className="animate-bounce [animation-delay:-0.15s]">.</span>
                <span className="animate-bounce">.</span>
              </span>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <ChatInput onSend={handleSend} disabled={loading} />
    </main>
  );
}

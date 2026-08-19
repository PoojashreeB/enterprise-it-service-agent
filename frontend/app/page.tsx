"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import ChatMessage from "@/components/ChatMessage";
import ChatInput from "@/components/ChatInput";
import Sidebar from "@/components/Sidebar";
import {
  fetchConversation,
  fetchConversations,
  fetchMe,
  logout,
  sendServiceDeskMessage,
} from "@/lib/api";
import {
  ChatMessage as ChatMessageType,
  Conversation,
  User,
} from "@/lib/types";

function makeId() {
  return Math.random().toString(36).slice(2);
}

const GREETING: ChatMessageType = {
  id: "greeting",
  role: "agent",
  content:
    "Hi, I'm the IT Service Desk assistant. Describe the issue you're running into and I'll help you sort it out.",
};

export default function Home() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<
    string | null
  >(null);
  const [messages, setMessages] = useState<ChatMessageType[]>([GREETING]);
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchMe()
      .then(({ user }) => {
        setUser(user);
        return fetchConversations();
      })
      .then((convos) => setConversations(convos))
      .catch(() => {
        router.push("/login");
      })
      .finally(() => setCheckingAuth(false));
  }, [router]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function refreshConversations() {
    try {
      const convos = await fetchConversations();
      setConversations(convos);
    } catch {
      // Non-fatal: sidebar just won't update this time.
    }
  }

  function handleNewChat() {
    setActiveConversationId(null);
    setMessages([GREETING]);
  }

  async function handleSelectConversation(id: string) {
    setActiveConversationId(id);

    try {
      const detail = await fetchConversation(id);

      setMessages(
        detail.messages.map((m) => ({
          id: m.id,
          role: m.role === "user" ? "user" : "agent",
          content: m.content,
          result: m.meta
            ? {
                category: m.meta.category,
                subcategory: m.meta.subcategory,
                priority: m.meta.priority,
                decision: m.meta.decision,
                ticket_number: m.meta.ticket_number,
              }
            : undefined,
        }))
      );
    } catch (err) {
      setMessages([
        {
          id: makeId(),
          role: "error",
          content:
            err instanceof Error
              ? err.message
              : "Could not load this conversation.",
        },
      ]);
    }
  }

  async function handleSend(message: string) {
    setMessages((prev) => [
      ...prev,
      { id: makeId(), role: "user", content: message },
    ]);
    setLoading(true);

    try {
      const result = await sendServiceDeskMessage(
        message,
        activeConversationId ?? undefined
      );

      if (!activeConversationId && result.conversation_id) {
        setActiveConversationId(result.conversation_id);
      }

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

      refreshConversations();
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

  async function handleLogout() {
    await logout();
    router.push("/login");
  }

  if (checkingAuth) {
    return (
      <main className="flex h-screen items-center justify-center bg-slate-50">
        <p className="text-sm text-slate-400">Loading…</p>
      </main>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="flex h-screen bg-slate-50">
      <Sidebar
        user={user}
        conversations={conversations}
        activeConversationId={activeConversationId}
        onSelectConversation={handleSelectConversation}
        onNewChat={handleNewChat}
        onLogout={handleLogout}
      />

      <main className="flex h-screen flex-1 flex-col">
        <header className="border-b border-slate-200 bg-white px-6 py-4 shadow-sm">
          <h1 className="text-lg font-semibold text-slate-900">
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
              <div className="rounded-2xl rounded-bl-sm border border-slate-200 bg-white px-4 py-3 text-sm text-slate-400 shadow-sm">
                <span className="inline-flex gap-1">
                  <span className="animate-bounce [animation-delay:-0.3s]">
                    .
                  </span>
                  <span className="animate-bounce [animation-delay:-0.15s]">
                    .
                  </span>
                  <span className="animate-bounce">.</span>
                </span>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        <ChatInput onSend={handleSend} disabled={loading} />
      </main>
    </div>
  );
}

"use client";

import { useState } from "react";
import { ChatMessage as ChatMessageType } from "@/lib/types";

const DECISION_LABEL: Record<string, string> = {
  knowledge: "Resolved with guidance",
  clarification: "Needs clarification",
  ticket: "Ticket raised",
};

function DetailsPanel({ result }: { result: NonNullable<ChatMessageType["result"]> }) {
  const [open, setOpen] = useState(false);

  const hasDetails =
    result.category || result.priority || result.decision || result.ticket_number;

  if (!hasDetails) return null;

  return (
    <div className="mt-2 text-xs">
      <button
        onClick={() => setOpen((v) => !v)}
        className="text-slate-400 hover:text-slate-200 underline underline-offset-2"
      >
        {open ? "Hide details" : "Show details"}
      </button>

      {open && (
        <dl className="mt-2 grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 rounded-lg bg-slate-900/60 p-3 text-slate-300">
          {result.decision && (
            <>
              <dt className="text-slate-500">Outcome</dt>
              <dd>{DECISION_LABEL[result.decision] ?? result.decision}</dd>
            </>
          )}
          {result.category && (
            <>
              <dt className="text-slate-500">Category</dt>
              <dd>
                {result.category}
                {result.subcategory ? ` — ${result.subcategory}` : ""}
              </dd>
            </>
          )}
          {result.priority && (
            <>
              <dt className="text-slate-500">Priority</dt>
              <dd>{result.priority}</dd>
            </>
          )}
          {result.ticket_number && (
            <>
              <dt className="text-slate-500">Ticket</dt>
              <dd className="font-mono">{result.ticket_number}</dd>
            </>
          )}
        </dl>
      )}
    </div>
  );
}

export default function ChatMessage({ message }: { message: ChatMessageType }) {
  const isUser = message.role === "user";
  const isError = message.role === "error";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
          isUser
            ? "bg-blue-600 text-white rounded-br-sm"
            : isError
            ? "bg-red-950/60 text-red-300 border border-red-900 rounded-bl-sm"
            : "bg-slate-800 text-slate-100 rounded-bl-sm"
        }`}
      >
        {message.content}
        {!isUser && !isError && message.result && (
          <DetailsPanel result={message.result} />
        )}
      </div>
    </div>
  );
}

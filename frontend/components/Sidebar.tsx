"use client";

import { Conversation, User } from "@/lib/types";

export default function Sidebar({
  user,
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewChat,
  onLogout,
}: {
  user: User;
  conversations: Conversation[];
  activeConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onNewChat: () => void;
  onLogout: () => void;
}) {
  return (
    <aside className="flex h-full w-64 shrink-0 flex-col border-r border-slate-200 bg-white">
      <div className="border-b border-slate-200 p-4">
        <h2 className="text-sm font-semibold text-slate-900">
          IT Service Desk
        </h2>
        <button
          onClick={onNewChat}
          className="mt-3 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
        >
          + New chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {conversations.length === 0 ? (
          <p className="px-2 py-4 text-xs text-slate-400">
            No conversations yet.
          </p>
        ) : (
          <ul className="space-y-1">
            {conversations.map((conversation) => (
              <li key={conversation.id}>
                <button
                  onClick={() => onSelectConversation(conversation.id)}
                  className={`w-full truncate rounded-lg px-3 py-2 text-left text-sm transition ${
                    conversation.id === activeConversationId
                      ? "bg-blue-50 text-blue-700"
                      : "text-slate-600 hover:bg-slate-50"
                  }`}
                  title={conversation.title}
                >
                  {conversation.title || "New conversation"}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="border-t border-slate-200 p-4">
        <p className="truncate text-xs text-slate-500" title={user.email}>
          {user.email}
        </p>
        <button
          onClick={onLogout}
          className="mt-2 text-sm text-slate-500 hover:text-slate-800"
        >
          Sign out
        </button>
      </div>
    </aside>
  );
}

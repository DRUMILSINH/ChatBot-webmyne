import clsx from "clsx";
import { useMemo, useState } from "react";

import { ChatSession } from "../types";
import { NewChatButton } from "./NewChatButton";

type SidebarProps = {
  chats: ChatSession[];
  activeChatId: string | null;
  onSelectChat: (chatId: string) => void;
  onNewChat: () => void;
};

export function Sidebar({ chats, activeChatId, onSelectChat, onNewChat }: SidebarProps) {
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return chats;
    return chats.filter((chat) => chat.title.toLowerCase().includes(q));
  }, [chats, search]);

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-slate-200 p-4 dark:border-slate-800">
        <h1 className="text-lg font-semibold">Company Chat</h1>
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">v2 local-first workspace</p>
        <div className="mt-3">
          <NewChatButton onClick={onNewChat} />
        </div>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search chats..."
          className="mt-3 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none ring-brand-400 focus:ring-2 dark:border-slate-700 dark:bg-slate-800"
        />
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto p-2">
        {filtered.map((chat) => (
          <button
            key={chat.id}
            onClick={() => onSelectChat(chat.id)}
            className={clsx(
              "mb-2 w-full rounded-xl border px-3 py-2 text-left transition",
              activeChatId === chat.id
                ? "border-brand-500 bg-brand-50 dark:border-brand-400 dark:bg-brand-900/30"
                : "border-slate-200 bg-white hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:hover:bg-slate-800"
            )}
          >
            <div className="truncate text-sm font-medium">{chat.title}</div>
            <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">{new Date(chat.updated_at).toLocaleString()}</div>
          </button>
        ))}
      </div>
    </div>
  );
}

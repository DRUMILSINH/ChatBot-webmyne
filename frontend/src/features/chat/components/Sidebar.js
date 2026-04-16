import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import clsx from "clsx";
import { useMemo, useState } from "react";
import { NewChatButton } from "./NewChatButton";
export function Sidebar({ chats, activeChatId, onSelectChat, onNewChat }) {
    const [search, setSearch] = useState("");
    const filtered = useMemo(() => {
        const q = search.trim().toLowerCase();
        if (!q)
            return chats;
        return chats.filter((chat) => chat.title.toLowerCase().includes(q));
    }, [chats, search]);
    return (_jsxs("div", { className: "flex h-full flex-col", children: [_jsxs("div", { className: "border-b border-slate-200 p-4 dark:border-slate-800", children: [_jsx("h1", { className: "text-lg font-semibold", children: "Company Chat" }), _jsx("p", { className: "mt-1 text-xs text-slate-500 dark:text-slate-400", children: "v2 local-first workspace" }), _jsx("div", { className: "mt-3", children: _jsx(NewChatButton, { onClick: onNewChat }) }), _jsx("input", { value: search, onChange: (e) => setSearch(e.target.value), placeholder: "Search chats...", className: "mt-3 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none ring-brand-400 focus:ring-2 dark:border-slate-700 dark:bg-slate-800" })] }), _jsx("div", { className: "min-h-0 flex-1 overflow-y-auto p-2", children: filtered.map((chat) => (_jsxs("button", { onClick: () => onSelectChat(chat.id), className: clsx("mb-2 w-full rounded-xl border px-3 py-2 text-left transition", activeChatId === chat.id
                        ? "border-brand-500 bg-brand-50 dark:border-brand-400 dark:bg-brand-900/30"
                        : "border-slate-200 bg-white hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:hover:bg-slate-800"), children: [_jsx("div", { className: "truncate text-sm font-medium", children: chat.title }), _jsx("div", { className: "mt-1 text-xs text-slate-500 dark:text-slate-400", children: new Date(chat.updated_at).toLocaleString() })] }, chat.id))) })] }));
}

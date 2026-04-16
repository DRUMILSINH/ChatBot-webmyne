import { jsx as _jsx, Fragment as _Fragment, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useRef } from "react";
import { EmptyState } from "./EmptyState";
import { MessageBubble } from "./MessageBubble";
import { RichText } from "./RichText";
export function MessageList({ messages, streamingContent, onOpenDebug }) {
    const listRef = useRef(null);
    useEffect(() => {
        if (listRef.current) {
            listRef.current.scrollTop = listRef.current.scrollHeight;
        }
    }, [messages, streamingContent]);
    return (_jsx("div", { ref: listRef, className: "min-h-0 flex-1 overflow-y-auto p-4", children: messages.length === 0 && !streamingContent ? (_jsx(EmptyState, {})) : (_jsxs(_Fragment, { children: [messages.map((message) => (_jsx(MessageBubble, { message: message, onOpenDebug: onOpenDebug }, message.id))), streamingContent ? (_jsx("div", { className: "mb-3 flex justify-start", children: _jsx("div", { className: "max-w-[82%] rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm dark:border-slate-700 dark:bg-slate-800", children: _jsx(RichText, { text: streamingContent }) }) })) : null] })) }));
}

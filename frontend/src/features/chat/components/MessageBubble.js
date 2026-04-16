import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import clsx from "clsx";
import { RichText } from "./RichText";
export function MessageBubble({ message, onOpenDebug }) {
    const isUser = message.role === "user";
    return (_jsx("div", { className: clsx("mb-3 flex", isUser ? "justify-end" : "justify-start"), children: _jsxs("div", { className: clsx("max-w-[82%] rounded-2xl px-4 py-3 text-sm leading-relaxed", isUser
                ? "bg-brand-600 text-white"
                : "border border-slate-200 bg-slate-50 text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"), children: [isUser ? _jsx("div", { className: "whitespace-pre-wrap", children: message.content }) : _jsx(RichText, { text: message.content }), !isUser && (_jsxs("div", { className: "mt-2 flex items-center justify-between gap-3 text-xs text-slate-500 dark:text-slate-400", children: [_jsx("span", { children: message.confidence !== undefined ? `Confidence: ${Math.round(message.confidence * 100)}%` : "Confidence: n/a" }), _jsx("button", { onClick: () => onOpenDebug(message.id), className: "underline underline-offset-2", children: "Debug" })] }))] }) }));
}

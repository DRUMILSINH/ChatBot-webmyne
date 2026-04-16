import { jsx as _jsx } from "react/jsx-runtime";
export function NewChatButton({ onClick }) {
    return (_jsx("button", { onClick: onClick, className: "w-full rounded-lg bg-brand-600 px-3 py-2 text-sm font-semibold text-white hover:bg-brand-700", children: "New Chat" }));
}

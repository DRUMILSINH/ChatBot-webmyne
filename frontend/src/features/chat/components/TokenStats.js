import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
export function TokenStats({ tokenUsage }) {
    if (!tokenUsage) {
        return _jsx("div", { className: "text-xs text-slate-500 dark:text-slate-400", children: "Token usage not available." });
    }
    return (_jsxs("div", { className: "grid grid-cols-3 gap-2 text-center text-xs", children: [_jsxs("div", { className: "rounded-lg bg-slate-100 p-2 dark:bg-slate-800", children: [_jsx("div", { className: "font-semibold", children: tokenUsage.prompt_tokens }), _jsx("div", { className: "text-slate-500 dark:text-slate-400", children: "Prompt" })] }), _jsxs("div", { className: "rounded-lg bg-slate-100 p-2 dark:bg-slate-800", children: [_jsx("div", { className: "font-semibold", children: tokenUsage.completion_tokens }), _jsx("div", { className: "text-slate-500 dark:text-slate-400", children: "Completion" })] }), _jsxs("div", { className: "rounded-lg bg-slate-100 p-2 dark:bg-slate-800", children: [_jsx("div", { className: "font-semibold", children: tokenUsage.total_tokens }), _jsx("div", { className: "text-slate-500 dark:text-slate-400", children: "Total" })] })] }));
}

import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { ThemeToggle } from './ThemeToggle';
export function TopBar({ title, darkMode, onToggleTheme }) {
    return (_jsxs("div", { className: "flex items-center justify-between border-b border-slate-200 px-4 py-3 dark:border-slate-800", children: [_jsxs("div", { children: [_jsx("h2", { className: "text-base font-semibold", children: title }), _jsx("p", { className: "text-xs text-slate-500 dark:text-slate-400", children: "Streaming + debug enabled" })] }), _jsx(ThemeToggle, { darkMode: darkMode, onToggle: onToggleTheme })] }));
}

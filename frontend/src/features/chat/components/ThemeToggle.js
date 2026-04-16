import { jsxs as _jsxs } from "react/jsx-runtime";
export function ThemeToggle({ darkMode, onToggle }) {
    return (_jsxs("button", { onClick: onToggle, className: "rounded-lg border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800", children: [darkMode ? 'Light' : 'Dark', " mode"] }));
}

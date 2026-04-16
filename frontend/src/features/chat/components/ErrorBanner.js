import { jsx as _jsx } from "react/jsx-runtime";
export function ErrorBanner({ message }) {
    return (_jsx("div", { className: "mx-4 mt-3 rounded-lg border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-700 dark:bg-red-950/30 dark:text-red-300", children: message }));
}

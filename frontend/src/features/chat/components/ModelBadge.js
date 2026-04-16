import { jsxs as _jsxs } from "react/jsx-runtime";
export function ModelBadge({ modelInfo }) {
    const model = modelInfo?.model || 'unknown';
    return (_jsxs("div", { className: "inline-flex rounded-full bg-brand-100 px-3 py-1 text-xs font-medium text-brand-800 dark:bg-brand-900/40 dark:text-brand-200", children: ["Model: ", model] }));
}

import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useCallback, useEffect, useMemo, useState } from "react";
import { fetchKnowledgeBaseStats } from "../api";
function StatCard({ label, value }) {
    return (_jsxs("div", { className: "rounded-lg border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-800/40", children: [_jsx("div", { className: "text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400", children: label }), _jsx("div", { className: "mt-1 text-xl font-semibold", children: value.toLocaleString() })] }));
}
export function KnowledgeBaseExplorer({ vectorId }) {
    const [stats, setStats] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const loadStats = useCallback(async () => {
        setIsLoading(true);
        setError(null);
        try {
            const payload = await fetchKnowledgeBaseStats(vectorId);
            setStats(payload);
        }
        catch (err) {
            setError(err.message);
        }
        finally {
            setIsLoading(false);
        }
    }, [vectorId]);
    useEffect(() => {
        void loadStats();
    }, [loadStats]);
    const topSources = useMemo(() => stats?.top_sources ?? [], [stats]);
    return (_jsxs("section", { className: "border-b border-slate-200 px-4 py-3 dark:border-slate-800", children: [_jsxs("div", { className: "flex flex-wrap items-center justify-between gap-2", children: [_jsxs("div", { children: [_jsx("h3", { className: "text-sm font-semibold text-slate-900 dark:text-slate-100", children: "Knowledge Base Explorer" }), _jsxs("p", { className: "text-xs text-slate-500 dark:text-slate-400", children: ["Collection: ", vectorId] })] }), _jsx("button", { type: "button", onClick: () => void loadStats(), disabled: isLoading, className: "rounded-md border border-brand-300 bg-brand-50 px-3 py-1.5 text-xs font-medium text-brand-800 transition hover:bg-brand-100 disabled:cursor-not-allowed disabled:opacity-60 dark:border-brand-700 dark:bg-brand-900/30 dark:text-brand-100 dark:hover:bg-brand-900/50", children: isLoading ? "Refreshing..." : "Refresh Stats" })] }), error ? (_jsx("div", { className: "mt-3 rounded-md border border-rose-200 bg-rose-50 p-2 text-xs text-rose-700 dark:border-rose-900/50 dark:bg-rose-900/20 dark:text-rose-200", children: error })) : null, stats ? (_jsxs("div", { className: "mt-3 space-y-3", children: [_jsxs("div", { className: "grid gap-2 sm:grid-cols-2 lg:grid-cols-4", children: [_jsx(StatCard, { label: "Total Vectors", value: stats.total_vectors }), _jsx(StatCard, { label: "Total Chunks", value: stats.total_chunks }), _jsx(StatCard, { label: "Unique URLs", value: stats.unique_urls }), _jsx(StatCard, { label: "Metadata Rows", value: stats.metadata_records })] }), _jsxs("div", { className: "grid gap-3 lg:grid-cols-2", children: [_jsxs("div", { className: "rounded-lg border border-slate-200 p-3 dark:border-slate-700", children: [_jsx("h4", { className: "text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400", children: "Top Sources" }), topSources.length === 0 ? (_jsx("p", { className: "mt-2 text-xs text-slate-500 dark:text-slate-400", children: "No source URLs found in metadata." })) : (_jsx("ul", { className: "mt-2 max-h-40 space-y-1 overflow-y-auto", children: topSources.slice(0, 8).map((source) => (_jsxs("li", { className: "flex items-start justify-between gap-3 text-xs", children: [_jsx("a", { href: source.url, target: "_blank", rel: "noreferrer", className: "line-clamp-1 break-all text-brand-700 hover:underline dark:text-brand-300", children: source.url }), _jsx("span", { className: "shrink-0 rounded bg-slate-100 px-2 py-0.5 font-medium text-slate-700 dark:bg-slate-800 dark:text-slate-300", children: source.chunk_count })] }, source.url))) }))] }), _jsxs("div", { className: "rounded-lg border border-slate-200 p-3 dark:border-slate-700", children: [_jsx("h4", { className: "text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400", children: "Coverage" }), _jsxs("div", { className: "mt-2 grid grid-cols-2 gap-2 text-xs", children: [_jsxs("div", { className: "rounded bg-slate-50 p-2 dark:bg-slate-800/40", children: [_jsx("div", { className: "text-slate-500 dark:text-slate-400", children: "With Source URL" }), _jsx("div", { className: "mt-1 text-sm font-semibold", children: stats.chunks_with_source_url.toLocaleString() })] }), _jsxs("div", { className: "rounded bg-slate-50 p-2 dark:bg-slate-800/40", children: [_jsx("div", { className: "text-slate-500 dark:text-slate-400", children: "Without Source URL" }), _jsx("div", { className: "mt-1 text-sm font-semibold", children: stats.chunks_without_source_url.toLocaleString() })] }), _jsxs("div", { className: "rounded bg-slate-50 p-2 dark:bg-slate-800/40", children: [_jsx("div", { className: "text-slate-500 dark:text-slate-400", children: "Unique Chunk IDs" }), _jsx("div", { className: "mt-1 text-sm font-semibold", children: stats.unique_chunk_ids.toLocaleString() })] }), _jsxs("div", { className: "rounded bg-slate-50 p-2 dark:bg-slate-800/40", children: [_jsx("div", { className: "text-slate-500 dark:text-slate-400", children: "Sample URLs" }), _jsx("div", { className: "mt-1 text-sm font-semibold", children: stats.sample_urls.length.toLocaleString() })] })] }), _jsxs("p", { className: "mt-2 text-[11px] text-slate-500 dark:text-slate-400", children: ["Updated: ", new Date(stats.generated_at).toLocaleString()] })] })] })] })) : (_jsx("div", { className: "mt-3 text-xs text-slate-500 dark:text-slate-400", children: isLoading ? "Loading stats..." : "No stats available." }))] }));
}

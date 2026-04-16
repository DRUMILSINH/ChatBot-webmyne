import { useCallback, useEffect, useMemo, useState } from "react";

import { fetchKnowledgeBaseStats } from "../api";
import { KnowledgeBaseStats } from "../types";

type KnowledgeBaseExplorerProps = {
  vectorId: string;
};

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-800/40">
      <div className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">{label}</div>
      <div className="mt-1 text-xl font-semibold">{value.toLocaleString()}</div>
    </div>
  );
}

export function KnowledgeBaseExplorer({ vectorId }: KnowledgeBaseExplorerProps) {
  const [stats, setStats] = useState<KnowledgeBaseStats | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadStats = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const payload = await fetchKnowledgeBaseStats(vectorId);
      setStats(payload);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setIsLoading(false);
    }
  }, [vectorId]);

  useEffect(() => {
    void loadStats();
  }, [loadStats]);

  const topSources = useMemo(() => stats?.top_sources ?? [], [stats]);

  return (
    <section className="border-b border-slate-200 px-4 py-3 dark:border-slate-800">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">Knowledge Base Explorer</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400">Collection: {vectorId}</p>
        </div>
        <button
          type="button"
          onClick={() => void loadStats()}
          disabled={isLoading}
          className="rounded-md border border-brand-300 bg-brand-50 px-3 py-1.5 text-xs font-medium text-brand-800 transition hover:bg-brand-100 disabled:cursor-not-allowed disabled:opacity-60 dark:border-brand-700 dark:bg-brand-900/30 dark:text-brand-100 dark:hover:bg-brand-900/50"
        >
          {isLoading ? "Refreshing..." : "Refresh Stats"}
        </button>
      </div>

      {error ? (
        <div className="mt-3 rounded-md border border-rose-200 bg-rose-50 p-2 text-xs text-rose-700 dark:border-rose-900/50 dark:bg-rose-900/20 dark:text-rose-200">
          {error}
        </div>
      ) : null}

      {stats ? (
        <div className="mt-3 space-y-3">
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Total Vectors" value={stats.total_vectors} />
            <StatCard label="Total Chunks" value={stats.total_chunks} />
            <StatCard label="Unique URLs" value={stats.unique_urls} />
            <StatCard label="Metadata Rows" value={stats.metadata_records} />
          </div>

          <div className="grid gap-3 lg:grid-cols-2">
            <div className="rounded-lg border border-slate-200 p-3 dark:border-slate-700">
              <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Top Sources</h4>
              {topSources.length === 0 ? (
                <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">No source URLs found in metadata.</p>
              ) : (
                <ul className="mt-2 max-h-40 space-y-1 overflow-y-auto">
                  {topSources.slice(0, 8).map((source) => (
                    <li key={source.url} className="flex items-start justify-between gap-3 text-xs">
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noreferrer"
                        className="line-clamp-1 break-all text-brand-700 hover:underline dark:text-brand-300"
                      >
                        {source.url}
                      </a>
                      <span className="shrink-0 rounded bg-slate-100 px-2 py-0.5 font-medium text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                        {source.chunk_count}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="rounded-lg border border-slate-200 p-3 dark:border-slate-700">
              <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Coverage</h4>
              <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
                <div className="rounded bg-slate-50 p-2 dark:bg-slate-800/40">
                  <div className="text-slate-500 dark:text-slate-400">With Source URL</div>
                  <div className="mt-1 text-sm font-semibold">{stats.chunks_with_source_url.toLocaleString()}</div>
                </div>
                <div className="rounded bg-slate-50 p-2 dark:bg-slate-800/40">
                  <div className="text-slate-500 dark:text-slate-400">Without Source URL</div>
                  <div className="mt-1 text-sm font-semibold">{stats.chunks_without_source_url.toLocaleString()}</div>
                </div>
                <div className="rounded bg-slate-50 p-2 dark:bg-slate-800/40">
                  <div className="text-slate-500 dark:text-slate-400">Unique Chunk IDs</div>
                  <div className="mt-1 text-sm font-semibold">{stats.unique_chunk_ids.toLocaleString()}</div>
                </div>
                <div className="rounded bg-slate-50 p-2 dark:bg-slate-800/40">
                  <div className="text-slate-500 dark:text-slate-400">Sample URLs</div>
                  <div className="mt-1 text-sm font-semibold">{stats.sample_urls.length.toLocaleString()}</div>
                </div>
              </div>
              <p className="mt-2 text-[11px] text-slate-500 dark:text-slate-400">
                Updated: {new Date(stats.generated_at).toLocaleString()}
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="mt-3 text-xs text-slate-500 dark:text-slate-400">{isLoading ? "Loading stats..." : "No stats available."}</div>
      )}
    </section>
  );
}

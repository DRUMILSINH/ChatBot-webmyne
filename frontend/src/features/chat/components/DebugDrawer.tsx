import { DebugPayload } from "../types";
import { ModelBadge } from "./ModelBadge";
import { SourceCard } from "./SourceCard";
import { TokenStats } from "./TokenStats";

type DebugDrawerProps = {
  debug: DebugPayload | null;
  selectedMessageId: number | null;
};

export function DebugDrawer({ debug, selectedMessageId }: DebugDrawerProps) {
  const hasTokenTelemetry =
    Boolean(debug?.token_usage) ||
    debug?.prompt_tokens !== undefined ||
    debug?.completion_tokens !== undefined ||
    debug?.total_tokens !== undefined;
  const tokenUsage = hasTokenTelemetry
    ? debug?.token_usage ?? {
        prompt_tokens: debug?.prompt_tokens ?? 0,
        completion_tokens: debug?.completion_tokens ?? 0,
        total_tokens: debug?.total_tokens ?? 0,
      }
    : undefined;
  const retrievedChunks =
    debug?.retrieved_chunks ?? debug?.retrieved_documents ?? debug?.sources ?? [];
  const latencyBreakdown = debug?.latency_ms ?? {};

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-slate-200 p-4 dark:border-slate-800">
        <h3 className="text-sm font-semibold">X-Ray Debug Drawer</h3>
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Telemetry, latency, and retrieved chunk evidence.</p>
      </div>
      <div className="min-h-0 flex-1 space-y-3 overflow-y-auto p-3">
        {!debug ? (
          <div className="rounded-xl border border-dashed border-slate-300 p-4 text-xs text-slate-500 dark:border-slate-700 dark:text-slate-400">
            Send a prompt or click <strong>Debug</strong> on an assistant message to inspect telemetry.
          </div>
        ) : (
          <>
            <div className="rounded-xl border border-slate-200 p-3 dark:border-slate-700">
              <div className="text-xs text-slate-500 dark:text-slate-400">Message ID</div>
              <div className="mt-1 text-sm font-semibold">{selectedMessageId}</div>
            </div>
            <div className="rounded-xl border border-slate-200 p-3 dark:border-slate-700">
              <ModelBadge modelInfo={debug.model_info} />
              <div className="mt-3 text-xs">
                Confidence:{" "}
                <span className="font-semibold">{debug.confidence !== undefined ? `${Math.round(debug.confidence * 100)}%` : "n/a"}</span>
              </div>
            </div>
            <div className="rounded-xl border border-slate-200 p-3 dark:border-slate-700">
              <h4 className="mb-2 text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">Token Usage</h4>
              <TokenStats tokenUsage={tokenUsage} />
            </div>
            <div className="rounded-xl border border-slate-200 p-3 dark:border-slate-700">
              <h4 className="mb-2 text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">Latency Breakdown</h4>
              <div className="space-y-2">
                {Object.keys(latencyBreakdown).length === 0 ? (
                  <div className="text-xs text-slate-500 dark:text-slate-400">Latency telemetry not available.</div>
                ) : (
                  Object.entries(latencyBreakdown).map(([name, value]) => (
                    <div key={name} className="flex items-center justify-between rounded-lg bg-slate-100 px-2 py-1.5 text-xs dark:bg-slate-800">
                      <span className="font-medium capitalize text-slate-700 dark:text-slate-300">{name.replace("_", " ")}</span>
                      <span className="font-semibold text-slate-900 dark:text-slate-100">{value} ms</span>
                    </div>
                  ))
                )}
              </div>
            </div>
            <div>
              <h4 className="mb-2 text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">Retrieved Chunks</h4>
              <div className="space-y-2">
                {retrievedChunks.map((source, idx) => (
                  <SourceCard key={`${source.chunk_id || idx}-${idx}`} source={source} />
                ))}
                {retrievedChunks.length === 0 ? (
                  <div className="rounded-xl border border-dashed border-slate-300 p-3 text-xs text-slate-500 dark:border-slate-700 dark:text-slate-400">
                    No retrieved chunks were returned for this answer.
                  </div>
                ) : null}
              </div>
            </div>
            {(debug.source_links || []).length > 0 ? (
              <div className="rounded-xl border border-slate-200 p-3 dark:border-slate-700">
                <h4 className="mb-2 text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">Source Links</h4>
                <div className="space-y-1 text-xs">
                  {(debug.source_links || []).map((link) => (
                    <a key={link} href={link} target="_blank" rel="noreferrer" className="block truncate text-brand-700 underline dark:text-brand-300">
                      {link}
                    </a>
                  ))}
                </div>
              </div>
            ) : null}
          </>
        )}
      </div>
    </div>
  );
}

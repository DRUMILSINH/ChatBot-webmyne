import { MessageSource } from '../types';

type SourceCardProps = {
  source: MessageSource;
};

export function SourceCard({ source }: SourceCardProps) {
  return (
    <div className="rounded-xl border border-slate-200 p-3 dark:border-slate-700">
      <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
        <span>Rank {source.rank ?? 'n/a'}</span>
        <span>Score {source.score ?? 'n/a'}</span>
      </div>
      <a
        href={source.url || '#'}
        target="_blank"
        rel="noreferrer"
        className="mt-1 line-clamp-1 block text-xs font-medium text-brand-700 underline dark:text-brand-300"
      >
        {source.url || 'No source URL'}
      </a>
      <div className="mt-2 text-xs text-slate-600 dark:text-slate-300">{source.content || 'No chunk preview available.'}</div>
      <div className="mt-2 text-[11px] text-slate-500 dark:text-slate-400">chunk_id: {source.chunk_id || 'n/a'}</div>
    </div>
  );
}

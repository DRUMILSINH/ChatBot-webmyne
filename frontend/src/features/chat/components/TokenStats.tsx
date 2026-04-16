type TokenStatsProps = {
  tokenUsage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
};

export function TokenStats({ tokenUsage }: TokenStatsProps) {
  if (!tokenUsage) {
    return <div className="text-xs text-slate-500 dark:text-slate-400">Token usage not available.</div>;
  }

  return (
    <div className="grid grid-cols-3 gap-2 text-center text-xs">
      <div className="rounded-lg bg-slate-100 p-2 dark:bg-slate-800">
        <div className="font-semibold">{tokenUsage.prompt_tokens}</div>
        <div className="text-slate-500 dark:text-slate-400">Prompt</div>
      </div>
      <div className="rounded-lg bg-slate-100 p-2 dark:bg-slate-800">
        <div className="font-semibold">{tokenUsage.completion_tokens}</div>
        <div className="text-slate-500 dark:text-slate-400">Completion</div>
      </div>
      <div className="rounded-lg bg-slate-100 p-2 dark:bg-slate-800">
        <div className="font-semibold">{tokenUsage.total_tokens}</div>
        <div className="text-slate-500 dark:text-slate-400">Total</div>
      </div>
    </div>
  );
}

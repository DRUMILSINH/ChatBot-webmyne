type ModelBadgeProps = {
  modelInfo?: Record<string, unknown>;
};

export function ModelBadge({ modelInfo }: ModelBadgeProps) {
  const model = (modelInfo?.model as string) || 'unknown';
  return (
    <div className="inline-flex rounded-full bg-brand-100 px-3 py-1 text-xs font-medium text-brand-800 dark:bg-brand-900/40 dark:text-brand-200">
      Model: {model}
    </div>
  );
}

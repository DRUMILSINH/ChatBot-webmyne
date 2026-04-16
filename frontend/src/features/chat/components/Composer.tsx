import { FormEvent, useState } from 'react';

type ComposerProps = {
  disabled?: boolean;
  onSend: (query: string) => Promise<void>;
};

export function Composer({ disabled, onSend }: ComposerProps) {
  const [value, setValue] = useState('');

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const query = value.trim();
    if (!query || disabled) return;
    setValue('');
    await onSend(query);
  };

  return (
    <form onSubmit={handleSubmit} className="border-t border-slate-200 p-3 dark:border-slate-800">
      <div className="flex gap-2">
        <input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Ask about company knowledge..."
          disabled={disabled}
          className="flex-1 rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm outline-none ring-brand-400 focus:ring-2 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-700 dark:bg-slate-800"
        />
        <button
          type="submit"
          disabled={disabled}
          className="rounded-xl bg-brand-600 px-4 py-3 text-sm font-semibold text-white hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Send
        </button>
      </div>
    </form>
  );
}

type ThemeToggleProps = {
  darkMode: boolean;
  onToggle: () => void;
};

export function ThemeToggle({ darkMode, onToggle }: ThemeToggleProps) {
  return (
    <button
      onClick={onToggle}
      className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
    >
      {darkMode ? 'Light' : 'Dark'} mode
    </button>
  );
}

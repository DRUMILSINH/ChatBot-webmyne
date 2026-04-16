import { ThemeToggle } from './ThemeToggle';

type TopBarProps = {
  title: string;
  darkMode: boolean;
  onToggleTheme: () => void;
};

export function TopBar({ title, darkMode, onToggleTheme }: TopBarProps) {
  return (
    <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3 dark:border-slate-800">
      <div>
        <h2 className="text-base font-semibold">{title}</h2>
        <p className="text-xs text-slate-500 dark:text-slate-400">Streaming + debug enabled</p>
      </div>
      <ThemeToggle darkMode={darkMode} onToggle={onToggleTheme} />
    </div>
  );
}

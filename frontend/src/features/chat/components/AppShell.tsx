import { PropsWithChildren, ReactNode } from "react";

type AppShellProps = PropsWithChildren<{
  sidebar: ReactNode;
  debugPanel?: ReactNode;
}>;

export function AppShell({ sidebar, debugPanel, children }: AppShellProps) {
  return (
    <div className="min-h-screen w-full bg-slate-100 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <div className="mx-auto flex h-screen max-w-[1600px] gap-3 p-3">
        <aside className="hidden w-72 shrink-0 rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900 lg:block">
          {sidebar}
        </aside>
        <div className="flex min-w-0 flex-1 flex-col gap-2">
          <details className="rounded-xl border border-slate-200 bg-white p-2 dark:border-slate-800 dark:bg-slate-900 lg:hidden">
            <summary className="cursor-pointer text-sm font-medium">Chat History</summary>
            <div className="mt-2 max-h-72 overflow-y-auto">{sidebar}</div>
          </details>
          <main className="flex min-h-0 flex-1 flex-col rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
            {children}
          </main>
          {debugPanel ? (
            <details className="rounded-xl border border-slate-200 bg-white p-2 dark:border-slate-800 dark:bg-slate-900 xl:hidden">
              <summary className="cursor-pointer text-sm font-medium">Debug Panel</summary>
              <div className="mt-2 max-h-80 overflow-y-auto">{debugPanel}</div>
            </details>
          ) : null}
        </div>
        {debugPanel ? (
          <aside className="hidden w-80 shrink-0 rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900 xl:block">
            {debugPanel}
          </aside>
        ) : null}
      </div>
    </div>
  );
}

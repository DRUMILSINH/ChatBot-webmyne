import { jsx as _jsx } from "react/jsx-runtime";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useMemo } from "react";
export function AppProviders({ children }) {
    const client = useMemo(() => new QueryClient({
        defaultOptions: {
            queries: { retry: 1, refetchOnWindowFocus: false },
            mutations: { retry: 0 },
        },
    }), []);
    return _jsx(QueryClientProvider, { client: client, children: children });
}

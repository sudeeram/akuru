import { QueryClient } from '@tanstack/react-query';

/** Shared server-state cache. Private data is kept in memory and never persisted. */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error) => {
        const status =
          typeof error === 'object' && error && 'status' in error
            ? Number(error.status)
            : 0;
        return status >= 400 && status < 500 ? false : failureCount < 1;
      },
      staleTime: 30_000,
      gcTime: 5 * 60_000,
      refetchOnWindowFocus: false,
    },
    mutations: { retry: false },
  },
});

/** Stop in-flight work before erasing all data owned by the current identity. */
export async function clearPrivateQueryState() {
  await queryClient.cancelQueries();
  queryClient.clear();
}

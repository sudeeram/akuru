'use client';
import { useRouter, useRouterState } from '@tanstack/react-router';
import { workspaceSearch } from './routes';

/** URL presentation state only. Call once with a batch when clearing related filters. */
export function useWorkspaceSearch<T extends Record<string, string>>(
  defaults: T,
) {
  const router = useRouter();
  const searchStr = useRouterState({
    select: (state) => state.location.searchStr,
  });
  const search = workspaceSearch(
    Object.fromEntries(new URLSearchParams(searchStr)),
  );
  const values = Object.fromEntries(
    Object.entries(defaults).map(([key, value]) => [
      key,
      typeof search[key] === 'string' ? search[key] : value,
    ]),
  ) as T;
  const update = (changes: Partial<T>) => {
    void router.navigate({
      to: router.state.location.pathname,
      replace: true,
      search: (previous: Record<string, unknown>) => {
        const next = { ...workspaceSearch(previous) };
        for (const [key, value] of Object.entries(changes)) {
          if (value == null || value === '' || value === defaults[key])
            delete next[key];
          else next[key] = String(value);
        }
        return next;
      },
    });
  };
  return [values, update] as const;
}

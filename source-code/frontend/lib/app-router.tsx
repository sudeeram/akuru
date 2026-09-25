'use client';

import type { ComponentType } from 'react';
import { createRootRoute, createRoute, createRouter, Link } from '@tanstack/react-router';
import { applicationPaths, flashcardModes } from './routes';

type PortalComponent = ComponentType;

export function createAkuruRouter(Portal: PortalComponent) {
  const rootRoute = createRootRoute({
    component: () => <Portal />,
    errorComponent: ({ reset }) => (
      <main className="main-content" id="main-content">
        <section className="panel stack" role="alert">
          <h1>AKURU could not open this page</h1>
          <p>Try the page again. If the problem continues, return to your portal home.</p>
          <button type="button" onClick={reset}>Try again</button>
          <Link to="/">Return to AKURU</Link>
        </section>
      </main>
    ),
    notFoundComponent: () => (
      <main className="main-content" id="main-content">
        <section className="panel stack" role="alert">
          <h1>Page not found</h1>
          <p>The AKURU page in this address is unavailable.</p>
          <Link to="/">Return to AKURU</Link>
        </section>
      </main>
    ),
  });
  const staticRoutes = applicationPaths.slice(1).map((path) =>
    createRoute({ getParentRoute: () => rootRoute, path }),
  );
  const deckRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: '/flashcards/decks/$deckRef',
  });
  const startRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: '/flashcards/decks/$deckRef/start',
    validateSearch: (search: Record<string, unknown>) => ({
      mode: flashcardModes.includes(search.mode as (typeof flashcardModes)[number])
        ? search.mode as (typeof flashcardModes)[number]
        : undefined,
    }),
  });
  const cardRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: '/flashcards/sessions/$sessionRef/cards/$position',
  });
  const routeTree = rootRoute.addChildren([...staticRoutes, deckRoute, startRoute, cardRoute]);
  return createRouter({ routeTree, defaultPreload: 'intent', scrollRestoration: true });
}

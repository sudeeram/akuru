'use client';

import type { ComponentType } from 'react';
import {
  createRootRoute,
  createRoute,
  createRouter,
  Link,
  useRouterState,
} from '@tanstack/react-router';
import {
  staticApplicationRoutes,
  dynamicApplicationRoutes,
  workspaceSearch,
  isApplicationPath,
} from './routes';

type PortalComponent = ComponentType;

export function createAkuruRouter(Portal: PortalComponent) {
  const rootRoute = createRootRoute({
    component: function RouteRoot() {
      const pathname = useRouterState({
        select: (state) => state.location.pathname,
      });
      return isApplicationPath(pathname) ? (
        <Portal />
      ) : (
        <main className="main-content">
          <h1>Page not found</h1>
          <p>This AKURU address is unavailable.</p>
          <Link to="/">Return to AKURU</Link>
        </main>
      );
    },
    validateSearch: workspaceSearch,
    errorComponent: ({ reset }) => (
      <main className="main-content" id="main-content">
        <section className="panel stack" role="alert">
          <h1>AKURU could not open this page</h1>
          <p>
            Try the page again. If the problem continues, return to your portal
            home.
          </p>
          <button type="button" onClick={reset}>
            Try again
          </button>
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
  const children = [
    ...staticApplicationRoutes.filter((route) => route.path !== '/'),
    ...dynamicApplicationRoutes,
  ].map(({ path }) =>
    createRoute({
      getParentRoute: () => rootRoute,
      path,
      validateSearch: workspaceSearch,
    }),
  );
  const routeTree = rootRoute.addChildren(children);
  return createRouter({
    routeTree,
    search: { strict: true },
    defaultPreload: 'intent',
    scrollRestoration: true,
  });
}

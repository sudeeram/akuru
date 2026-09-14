# AKURU frontend architecture

The frontend is a React 19 and TypeScript portal built with Vite/Vinext. `app/page.tsx` owns authentication state and role navigation; feature modules render Admin, Parent, and Student workspaces; `lib/api.ts` is the single HTTP boundary.

## API connection

The browser uses same-origin `/api/v1/*` URLs. Vite proxies this prefix to `http://127.0.0.1:8000` during local development. Production must route the same prefix to FastAPI at the reverse proxy. There are no bundled mock users, demo login buttons, or active Node mock API handlers.

FastAPI sets an HttpOnly session cookie and a readable same-site CSRF cookie. `lib/api.ts` copies the CSRF value into `X-CSRF-Token` on mutations. A 401 clears the displayed portal state and returns the user to sign-in. Users created by Admin receive a temporary password and must replace it before portal navigation becomes available. Because that user has just authenticated, the forced setup form asks only for the new password and confirmation; the backend rejects reuse of the existing password.

FastAPI validation responses may contain multiple structured field errors. `lib/api.ts` converts them into readable field-specific messages so forms explain requirements such as username format, password length, Parent selection, progression order, and subject selection.

## Current data contract

`GET /api/v1/state` returns the authenticated user, role-scoped accounts and children, the Phase 1 catalog, and feature collections. Admin can create Parent and Student accounts with `POST /api/v1/admin/accounts` and update Student family/enrolment details with `POST /api/v1/admin/students`.

The backend OpenAPI schema generates `lib/generated/api-contract.ts`. Do not edit that file directly. After changing a FastAPI route or schema, run `npm run contract:generate` from `source-code/`; CI uses `npm run contract:check` to detect drift. The API wrapper translates the backend's structured error envelope into field-specific messages for the portal.

The document, textbook-unit, coverage, question, practice, exam, recommendation-review and adaptive-plan screens use PostgreSQL-backed endpoints. The standalone legacy assignment preview remains until its service is implemented.

## Authorization boundary

The UI hides actions according to role for usability. FastAPI remains authoritative. A client-provided role, parent ID, student ID, subject, or progression never grants access. Parent and Student state is filtered by authenticated database identity.

`/ui-features` is the Admin component reference. The Admin portal links to it, and the route must successfully call `GET /api/v1/admin/ui-features` before rendering its catalog. FastAPI applies the Admin role dependency to that endpoint, so Parent and Student sessions are rejected with HTTP 403. Its responsive top navigation links to Overview, Apps, Widgets, UI, Forms & tables, Charts, Pages, and Access sections. The catalog demonstrates AKURU-owned components and synthetic example data; external design references are not copied into the codebase.

## Visual system

AKURU uses a pale blue-grey application canvas, white content cards, blue primary actions, and restrained green and amber status accents. The layout favors persistent navigation, concise dashboard cards, visible field labels, readable status text, and responsive grids. The `/ui-features` route is the review point for the current palette, typography, buttons, badges, alerts, form controls, progress indicators, tables, tabs, and AKURU BOT usage.

Every authenticated workspace uses a role-specific horizontal navigation strip below the top bar. It marks the current section with `aria-current`, exposes pending Parent reviews as a count, supports touch scrolling when the items exceed the viewport, and keeps the Admin UI reference available to Admin users. This is the portal's single primary navigation on desktop, tablet, and mobile.

`components/route-loading-overlay.tsx` provides shared page-transition feedback. It preloads and rotates five transparent AKURU BOT scenes stored in `public/akuru-loading`, handles full internal route changes and the portal's hash-based workspace navigation, and disables motion when the browser requests reduced motion. File downloads, external links, modified clicks, and same-page documentation anchors do not trigger the overlay.

## Local commands

From `source-code`:

```bash
npm run dev
npm run typecheck
npm run lint
npm run build
npm run test:frontend
```

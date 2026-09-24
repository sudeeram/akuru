# Frontend

## Stack and entry points

The portal uses React 19, TypeScript, Vite 8 and Vinext. Tailwind CSS and reusable components under `components/ui` provide the visual foundation. `app/layout.tsx` supplies the document shell and `app/page.tsx` owns login restoration, role navigation and the active hash-based workspace. `/ui-features` is an authenticated Admin component reference.

`app/page.tsx` deliberately remains the portal coordinator. Domain-sized screens belong in `features`, including Admin, Parent, Student, textbook structure, document review, assessments, flashcards and Tutor modules. Avoid adding substantial domain logic directly to the page coordinator.

## Navigation and role experience

The application uses one horizontally scrollable navigation for each role. Workspace routes are represented by URL hashes such as `/#units` and `/#library`; full page routes are reserved for independent pages such as `/ui-features`. Role-specific arrays in `app/page.tsx` define visible navigation, but backend authorization remains authoritative.

The shared route-loading overlay rotates AKURU BOT assets and respects reduced-motion preferences. Internal downloads, modified clicks and same-page documentation anchors do not trigger it.

## API boundary

All HTTP access belongs under `api/`. Feature code imports the public barrel as
`@/api`; domain operation files call the generic client in `api/core/client.ts`.
The shared client:

- prefixes requests with `/api/v1/`;
- includes the browser's HttpOnly session cookie automatically;
- copies the readable CSRF cookie into `X-CSRF-Token` for mutations;
- parses the backend error envelope into readable messages;
- clears the experience on authentication failure; and
- exposes domain-specific typed functions to features.

Do not call FastAPI with absolute production URLs or expose backend secrets through frontend environment variables. Development proxying is configured in `vite.config.ts`.

FastAPI's OpenAPI output generates `lib/generated/api-contract.ts`. Never edit it manually. Run `npm run contract:generate` at `source-code` after API contract changes. The API barrel re-exports its public generated types, and CI runs `contract:check` to reject drift.

## State and mutations

The authenticated portal state comes from the backend and is refreshed after mutations that affect several screens. Feature modules may keep temporary form state, filters and expanded panels locally. They must not treat cached role, family ownership, coverage or publication state as authorization.

For a mutation:

1. disable or mark the initiating control busy;
2. preserve form data when a recoverable request fails;
3. show the backend's actionable message;
4. refresh the smallest authoritative dataset that makes all affected labels consistent; and
5. avoid optimistic publication, marking or account changes.

## Component conventions

- Use primitives in `components/ui` before creating another button, dialog or status component.
- Keep feature-specific composition in `features/<domain>.tsx`.
- Use visible labels, not placeholders alone.
- Pair colour with status text or icons.
- Keep focus visible and ensure every operation is keyboard reachable.
- Provide alt text or a readable fallback for learning visuals.
- Do not display UUIDs, storage object keys, credential aliases intended to be private, or raw provider failures.
- Use confirmation dialogs for operations with publication, detachment or deletion impact.

## Styling

Global tokens and application layout live in `app/globals.css`. AKURU uses a light blue-grey canvas, white cards, blue primary actions and restrained semantic status colours. `/ui-features` demonstrates supported components and synthetic data. It is a reference surface, not a second product implementation.

## Production build

`npm run build` invokes the root wrapper and creates `frontend/dist`. `frontend/serve-local.mjs` starts the built Vinext server on loopback port `5181`. Nginx handles public HTTPS and routes API traffic separately.

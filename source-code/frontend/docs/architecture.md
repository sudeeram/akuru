# AKURU frontend architecture

The frontend is a React 19 and TypeScript portal built with Vite/Vinext. `app/page.tsx` owns authentication state and role navigation; feature modules render Admin, Parent, and Student workspaces. `api/index.ts` is the public browser API barrel, domain folders own their operations and types, and `api/core/client.ts` is the single JSON HTTP boundary.

## API connection

The browser uses same-origin `/api/v1/*` URLs. Vite proxies this prefix to `http://127.0.0.1:8000` during local development. Production must route the same prefix to FastAPI at the reverse proxy. There are no bundled mock users, demo login buttons, or active Node mock API handlers.

FastAPI sets an HttpOnly session cookie and a readable same-site CSRF cookie. `api/core/csrf.ts` reads the token and `api/core/client.ts` copies it into `X-CSRF-Token` on mutations. Users created by Admin receive a temporary password and must replace it before portal navigation becomes available. Because that user has just authenticated, the forced setup form asks only for the new password and confirmation; the backend rejects reuse of the existing password.

FastAPI validation responses may contain multiple structured field errors. `api/core/errors.ts` converts them into readable field-specific messages so forms explain requirements such as username format, password length, Parent selection, progression order, and subject selection.

## Current data contract

`GET /api/v1/state` returns the authenticated user, role-scoped accounts and children, the Phase 1 catalog, and feature collections. Admin can create Parent and Student accounts with `POST /api/v1/admin/accounts` and update Student family/enrolment details with `POST /api/v1/admin/students`.

The backend OpenAPI schema generates `lib/generated/api-contract.ts`. Do not edit that file directly. After changing a FastAPI route or schema, run `npm run contract:generate` from `source-code/`; CI uses `npm run contract:check` to detect drift. The API wrapper translates the backend's structured error envelope into field-specific messages for the portal.

The document, textbook-unit, coverage, question, practice, exam, recommendation-review and adaptive-plan screens use PostgreSQL-backed endpoints. The standalone legacy assignment preview remains until its service is implemented.

## Planned textbook, group and topic experience

The next content contract uses **Textbook → Section Group → Topic → Textbook Part**. `section_group` is the backend concept; the frontend must display the textbook's configured `Unit` or `Module` label everywhere. `Topic` remains consistent across books. [`TODO-TEXTBOOK-TOPICS.md`](../../todo/TODO-TEXTBOOK-TOPICS.md) is the delivery backlog for this change.

Admin creates the logical textbook and edition, selects Unit or Module terminology, defines ordered groups and topics, and uploads one or more scanned PDF parts inside a selected topic. Upload, extraction review and topic publication are separate states. The review screen presents original and normalized pages beside OCR blocks, equations, formulae, tables, diagrams, confidence, reading order and printed-page labels. A topic cannot appear ready merely because its worker job completed.

Use the visible nouns **Textbook**, the configured **Unit** or **Module**, **Topic**, and **Textbook part** consistently. Topic content states are **No document**, **Processing**, **Needs review**, **Ready to publish**, **Published**, **Failed** and **Superseded**. Empty states must name the next authorized Admin action; they must not expose UUIDs, object keys, filesystem paths or provider configuration.

Curriculum editing uses a grouped Unit/Module → Topic checklist. A new draft starts from the latest published coverage so Admin can add topics as teaching progresses. The UI distinguishes published coverage, draft additions and removals, previews cumulative eligibility and warns before moving or removing published topics. Internal UUIDs, storage paths and provider details remain hidden.

Student and Parent views show Unit or Module summaries that expand into topics. Topic mastery, weaknesses, study-plan work, Tutor context and exact citations name their parent group. Unpublished or uncovered topics remain inaccessible. Existing assessment sessions continue to show their immutable coverage snapshot after Admin publishes later coverage.

All structure, upload, review and coverage workflows require keyboard access, visible focus, screen-reader labels and status indicators that do not depend on colour. Drag-and-drop may be an enhancement but cannot be the only interaction.

## Authorization boundary

The UI hides actions according to role for usability. FastAPI remains authoritative. A client-provided role, parent ID, student ID, subject, or progression never grants access. Parent and Student state is filtered by authenticated database identity.

`/ui-features` is the Admin component reference. The Admin portal links to it, and the route must successfully call `GET /api/v1/admin/ui-features` before rendering its catalog. FastAPI applies the Admin role dependency to that endpoint, so Parent and Student sessions are rejected with HTTP 403. Its responsive top navigation links to Overview, Apps, Widgets, UI, Forms & tables, Charts, Pages, and Access sections. The catalog demonstrates AKURU-owned components and synthetic example data; external design references are not copied into the codebase.

## Visual system

AKURU uses a pale blue-grey application canvas, white content cards, blue primary actions, and restrained green and amber status accents. The layout favors persistent navigation, concise dashboard cards, visible field labels, readable status text, and responsive grids. The `/ui-features` route is the review point for the current palette, typography, buttons, badges, alerts, form controls, progress indicators, tables, tabs, and AKURU BOT usage.

Every authenticated workspace uses a role-specific horizontal navigation strip below the top bar. It marks the current section with `aria-current`, exposes pending Parent reviews as a count, supports touch scrolling when the items exceed the viewport, and keeps the Admin UI reference available to Admin users. This is the portal's single primary navigation on desktop, tablet, and mobile.

`components/route-loading-overlay.tsx` provides shared page-transition feedback. It preloads and rotates five transparent AKURU BOT scenes stored in `public/akuru-loading`, handles full internal route changes and the portal's hash-based workspace navigation, and disables motion when the browser requests reduced motion. File downloads, external links, modified clicks, and same-page documentation anchors do not trigger the overlay.

The role navigation also exposes Tutor profile setup. Students manage multiple profiles from curated AKURU BOT and persona values, Parents have read-only child-by-child visibility, and Admin controls preset availability and order. Editing creates a backend-owned immutable version; the frontend never displays internal profile identifiers or provider voice mappings. See [Tutor Step 1 profiles](tutor-step-01-profiles.md).

## Local commands

From `source-code`:

```bash
npm run dev
npm run typecheck
npm run lint
npm run build
npm run test:frontend
```

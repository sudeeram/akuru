# TanStack Router and Query foundation

**Status:** Implementation complete locally; CI and production acceptance pending.

This plan contains only the agreed foundation needed before AKURU grows its mock-exam, tutoring, study-plan and collaboration experiences. Flashcards will be the first fully routed feature. Server-side authentication, authorization and family separation remain authoritative.

## Step 1 — Introduce TanStack Router and TanStack Query

- [x] Add compatible TanStack Router v1 and TanStack Query packages to the frontend using the existing package manager and lockfile.
- [x] Create one router and one query client at the application entry boundary.
- [x] Preserve the existing authentication bootstrap, loading experience, error handling and AKURU visual design.
- [x] Configure Query defaults deliberately: bounded retry behavior, suitable stale times and no persistent storage of private Student data.
- [x] Record the chosen versions and frontend conventions in the developer documentation.

**Acceptance:** the current frontend loads through the new providers, existing role flows still work, and type checking, linting, tests and the production build pass.

## Step 2 — Centralise routes and query keys

- [x] Define routes in one discoverable route tree with typed path parameters and validated search parameters.
- [x] Define query-key factories by domain rather than writing ad hoc arrays in components.
- [x] Include the authenticated actor or an equivalent identity boundary in user-specific query keys.
- [x] Keep API calls in the existing domain API modules and use Query hooks as the server-state layer above them.
- [x] Define route-level not-found and unexpected-error experiences.

**Acceptance:** route destinations and server-state keys have one documented source of truth, invalid search parameters fail safely, and private data cannot be reused under another signed-in identity.

## Step 3 — Add authenticated role layouts

- [x] Add a public layout for login and authentication recovery.
- [x] Add a protected application layout that waits for authentication before rendering private content.
- [x] Add Admin, Parent and Student layouts that retain the shared horizontal navigation while exposing only relevant destinations.
- [x] Preserve the user’s intended destination through login when that destination is authorized.
- [x] Treat frontend guards as navigation help only; continue enforcing every permission in FastAPI.
- [x] Give unauthorized and unavailable destinations clear, accessible outcomes.

**Acceptance:** direct navigation, refresh and browser back/forward work for every role, while unauthorized roles cannot obtain protected data or render another role’s private screen.

## Step 4 — Migrate Flashcards as the first complete routed feature

- [x] Give the Flashcard library a stable route.
- [x] Give a deck or topic a stable route using an opaque public reference.
- [x] Represent study mode in a typed route or validated search parameter.
- [x] Give an active review session and card position an addressable route without exposing database IDs or answer data.
- [x] Support Quick review, Normal review, Full topic practice, Difficult cards, Due today and Unit mixed practice.
- [x] Make reload, forward/back navigation and a copied authorized URL restore the same meaningful screen.
- [x] Define safe behavior for an expired session, removed deck, invalid card position and a URL copied to a different Student.
- [x] Redirect the existing `/#flashcards` entry to the new library route so bookmarks continue to work.

**Acceptance:** a Student can open a permitted shared link, select a mode, study cards, refresh and navigate backward without losing the intended context; ownership checks still occur on the backend.

## Step 5 — Clear private query state on identity changes

- [x] Cancel active private queries before logout or identity replacement.
- [x] Clear the Query cache on logout, forced session expiry and successful login as a different user.
- [x] Reset route-bound private state and return to the appropriate public or role landing page.
- [x] Prevent late responses from the previous identity from repopulating the cache.
- [x] Do not persist authenticated Query data to browser storage at this stage.

**Acceptance:** sequential logins by two users in the same browser never display the first user’s cached Student, Parent or Admin data.

## Step 6 — Configure production route fallback

- [x] Configure the production web server to return the frontend entry document for valid client-side application routes.
- [x] Keep API, health, private-file/download and static-asset paths out of the frontend fallback.
- [x] Ensure an unknown API path remains an API 404 and is never returned as frontend HTML.
- [x] Ensure missing versioned assets remain 404s rather than loading the application shell.
- [x] Document the equivalent local preview behavior and the production web-server rule.
- [x] Include the fallback configuration in the reviewed deployment assets before release.

**Acceptance:** directly opening or refreshing a nested Flashcard URL loads AKURU, while API proxying, protected downloads, health checks and asset caching retain their existing behavior.

## Step 7 — Add routing acceptance tests

- [x] Test route matching, parameter/search validation, not-found handling and legacy hash redirects.
- [x] Test authentication loading, expired sessions, intended-destination recovery and each role boundary.
- [x] Test Flashcard library, deck, mode, session and card deep links, including refresh and browser back/forward behavior.
- [x] Test invalid, deleted and unauthorized resource references with safe user-facing outcomes.
- [x] Test logout and account switching for Query cancellation and cache isolation.
- [x] Test keyboard focus, page titles and loading/error announcements after navigation.
- [x] Add a production-like smoke test that serves the built frontend behind the route fallback and verifies nested URLs, APIs, assets and protected downloads.
- [ ] Run the frontend test suite, type check, lint, production build, generated API contract check and relevant backend authorization tests in CI.

**Acceptance:** automated checks prove deep-link reliability, role isolation, cross-user cache isolation and correct production fallback behavior before deployment.

## Release gate

- [x] Update user and developer documentation for the new URLs and navigation behavior.
- [ ] Deploy only after all seven steps pass locally and in CI.
- [ ] Run production smoke checks with Admin, Parent and Student accounts without altering learning records.
- [x] Keep a rollback path to the preceding frontend release and web-server configuration.

# Future TanStack capabilities

**Status:** Planned after the Router and Query foundation.

These items are outside the immediate routing work. Adopt each capability only when an AKURU feature needs it and after measuring the current implementation. Do not install a package merely to reserve it for future use.

## Step 1 — TanStack Table for data-heavy administration

- [ ] Evaluate Table when Admin document, user, assessment or audit screens need substantial sorting, filtering, pagination or column control.
- [ ] Keep filtering and pagination on the server for large or private datasets.
- [ ] Build accessible mobile and keyboard behavior rather than relying on a wide desktop grid.
- [ ] Migrate one representative Admin table before defining a shared table pattern.

## Step 2 — TanStack Form for complex forms

- [ ] Evaluate Form for new multi-step account, curriculum, assessment or tutor configuration workflows.
- [ ] Retain backend validation as authoritative and map field errors into accessible controls.
- [ ] Avoid rewriting small, stable forms unless the change removes measurable duplication or defects.

## Step 3 — TanStack Virtual for measured rendering limits

- [ ] Profile large transcript, OCR-review, question-bank and audit views before adding virtualisation.
- [ ] Introduce Virtual only where real data demonstrates a rendering or memory problem.
- [ ] Preserve search, keyboard navigation, focus restoration and assistive-technology access.

## Step 4 — Offline or persisted Query data

- [ ] Define an explicit child-privacy and shared-device threat model before persisting authenticated server data.
- [ ] Select only data that is safe and useful offline, with encryption, expiry, identity scoping and purge behavior.
- [ ] Exclude assessment answers, tutor transcripts and sensitive learner context unless a separate security review approves them.

## Step 5 — Pacer and client-state libraries

- [ ] Consider TanStack Pacer when search, autosave or live interactions need consistent debounce, throttle or rate limiting.
- [ ] Consider TanStack Store only if route state, Query server state, form state and local React state cannot clearly model a proven cross-feature need.
- [ ] Document ownership and reset rules before introducing any new global client state.

## Step 6 — Reassess the application framework only if architecture changes

- [ ] Keep FastAPI as AKURU’s backend and avoid introducing TanStack Start into the current architecture.
- [ ] Reassess only if AKURU later needs a JavaScript server-rendering layer with a clear operational and product benefit.
- [ ] Require a migration proposal covering authentication, FastAPI ownership, deployment, observability and rollback before such a change.

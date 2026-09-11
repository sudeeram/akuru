# AKURU frontend architecture

This file describes the current implementation. Shared requirements are authoritative in [overall architecture](../../docs/architecture.md). Future server design is in [backend architecture](../../backend/docs/architecture.md).

## Stack and structure

React and TypeScript use the existing Vinext/Vite Next-compatible starter, Tailwind styles and installed UI primitives. The repository move preserves dependencies and the package lock. There is no new frontend framework or additional dependency installation.

```text
frontend/
  app/page.tsx                   Login, role navigation, portal state and dashboards
  app/globals.css                Shared presentation and responsive layout
  features/admin.tsx             Admin workflows; read-only family courses/library
  features/parent.tsx            Family-scoped reviews and assignments
  features/student.tsx           Subjects, practice, exams, progress and plans
  features/diagram.tsx           Existing teaching visuals
  features/shared.tsx            Shared presentation and typed feature props
  features/use-portal-tools.ts   Optional authorized read-only progress tool
  lib/api.ts                     Fetch wrapper and response types
  local-server/api.mjs           Local auth, authorization, files and learning actions
  local-server/admin.mjs         Account, enrolment, unit, coverage and question writes
  local-server/curriculum.mjs    Catalog, migration and deterministic eligibility
  local-server/seed.mjs          Legacy sample material and bootstrap demo credentials
  tests/api.test.mjs             Current API integration tests
  .local-data/                   Ignored local JSON, upload bytes and migration backup
```

## Portal responsibilities

Admin navigation: Admin overview; Accounts & enrolments; Documents & textbooks; Textbook units; Grade & term coverage; Question mapping. Forms use constrained catalog choices. Parent creation precedes child creation. Grade and term are explicit fields, and the student form records every completed/current Grade + Term progression combination. A parent with no linked children sees a helpful empty state.

Admin uploads a textbook, approves it, registers units, configures grade/term coverage, uploads a same-subject paper, manually enters its questions and unit mappings, then signs off the complete paper. Marking schemes and examiner reports link to an existing same-subject paper. Question edits require renewed paper approval. A future extraction editor will add PDF-page previews, equation correction, diagram crops and question inventory; the present mapping form is manual.

Parent navigation retains family overview, read-only children/courses, read-only approved resources, assessment reviews, assignments and learning progress. Parent cannot edit enrolments or upload/approve documents. All child selectors come from authorized server state.

Student navigation retains Today, My subjects, Practice, Mock exams, My progress and Study plan. Questions are already filtered by the server for current enrolment and covered units. An empty candidate pool remains empty; no demo fallback is inserted. Student answer-working attachments are allowed, separately from Admin-only learning-document ingestion.

Role navigation is a convenience. The server must repeat every authorization check even if the UI hides a control. Never derive family membership from a browser field or storage value.

## Local API contract

The browser fetches same-origin `/api/*`. Development installs `localApi()` as Vite middleware. The built preview wraps the frontend request handler in `serve-local.mjs`. The browser does not need a separate backend URL in local mock mode.

| Endpoint | Actor / purpose |
| --- | --- |
| POST login, logout | Session lifecycle |
| GET state | Authorized records, catalog and eligible questions |
| POST admin/accounts | Admin creates parent or student; student requires parent and valid enrolment |
| POST admin/students | Admin updates student name, parent link and enrolment |
| POST admin/units | Admin registers a unit under an approved textbook |
| POST admin/coverage | Admin replaces complete covered-unit set for subject/grade/term |
| POST admin/questions | Admin enters/updates and maps a question; invalidates paper sign-off |
| POST upload | Admin learning document, or student attachment with purpose=working |
| POST documents/review | Admin holds/approves; papers require mappingComplete attestation |
| GET files/:id | Authorized original or answer attachment; assessment sources Admin-only |
| GET lesson, POST hint | Eligible question content, blocked during active mocks |
| POST drafts, attempt | Own student work; eligible current question |
| POST exams/start, exams/save, exams/submit | Own timed mock, server-selected pool and deadline |
| POST assignments, reviews | Parent's own linked children |
| POST plans | Own student or authorized parent's child |

GET state returns no password hashes. `accounts` and full `questionBank` are Admin-only. Ordinary `questions` exclude answer keys, hints, explanations and marking points. Parents see the union of their children's eligible questions; assignment choices are filtered again for the selected child. The API performs the final selected-child validation.

## Storage and migration

Default storage is `frontend/.local-data`. `PORTAL_DATA_DIR` selects an alternative directory for isolated tests/previews. Records load into memory and persist by temporary-file write plus rename. Uploaded files use UUID filenames and authenticated retrieval. This is a single-process mock; it has no multi-process locking, SQL transactions, HA, or production backup automation.

Bootstrap demo credentials remain explicitly public: admin/admin123, parent/parent123 and the existing child demos. Admin-created passwords are salted scrypt hashes persisted in private local state; their plaintext is not retained or added to demo buttons. Password reset, account disabling, forced first-login change and production Admin bootstrapping remain backend work.

Sessions use in-memory random tokens with HttpOnly/SameSite cookies, expire after 24 hours and reset on server restart. The mock accepts localhost only. A v2 migration backs up old state, preserves old profiles and work, flags existing children for Admin configuration, holds old resources and excludes legacy questions from eligible pools. Legacy active exams are archived. This migration is not a substitute for future versioned SQL migrations.

## Exam and content limitations

Current mocks contain all eligible questions for the selected subject and use a fixed 15-minute timer; they do not yet balance difficulty or target a chosen mark total. Scope captures current grade, current term, progression combinations, course and the accumulated mapped units at start. Questions cannot be edited while referenced by an active exam, and student enrolment changes are blocked until submission. Future backend must use immutable question versions, not this temporary mutation restriction.

Numeric checks recognize exact final answers; written/ambiguous answers and handwritten work require parent review. Existing SVG lessons remain available in the component code but legacy demo questions are no longer offered as compliant iGCSE content. Newly entered questions use manual text, explanation and marking points; OCR, uploaded diagram crops, rich mathematical rendering and generated media are future integrations.

## Running and checking

From `source-code`: `npm run dev` (5180), `npm run build`, `npm start` (5181), `npm test`, `npm run typecheck`. The launcher selects an already installed compatible Node; it never installs Node. Frontend-local scripts also work when using compatible Node. Stop the launched process with Ctrl+C. Do not run two servers against the same data directory.

Tests use temporary storage. Keep test document fixtures synthetic. Validate role denials, family isolation, Phase 1 catalog constraints, upload ordering, cross-subject/textbook rejections, exact grade/term coverage, all-units eligibility, publication gates, private files and exam timing. Browser QA should cover an Admin setup flow followed by a parent/student login, empty states and mobile navigation.

## Replacing the mock

Keep `lib/api.ts` as the boundary. When FastAPI is ready, use a same-origin proxy or configured API base and generated OpenAPI types, and disable the local middleware. Do not run mock and real API handlers for the same routes. Backend error codes must distinguish forbidden, invalid mapping, missing coverage, incomplete paper and insufficient eligible questions so forms can show actionable messages.

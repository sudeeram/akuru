# Textbook administration and Exam Documents experience

**Status:** Planned.

This roadmap consolidates textbook structure, source upload, extraction review and
publication into one routed Admin workspace. Past papers, marking schemes,
examiner reports and assessment reference material remain in a separate Exam
Documents workspace. Existing extraction, review, publication, provenance and
authorization rules remain authoritative; this work reorganises their user
experience without weakening those boundaries.

## Product decisions

- **Textbooks** owns textbook records, Unit or Module groups, Topics, Topic files,
  source roles, extraction review, quality gates, retrieval preflight and
  publication.
- **Exam Documents** owns past papers, marking schemes, examiner reports and
  assessment-oriented reference material.
- A subject reference book attached to textbook Topics belongs in Textbooks.
  General assessment support material remains in Exam Documents.
- The existing extraction review implementation will be reused. AKURU must not
  create a second review engine with different completion rules.
- Internal UUIDs remain hidden. Routed pages use opaque public references.
- The old Documents & Textbooks experience will be removed only after feature,
  authorization and deep-link parity is proven.

## Step 0 — Record routes, ownership and migration boundaries

- [x] Add the new information architecture to the frontend and overall
  architecture documentation.
- [x] Define canonical routes:
  - `/admin/textbooks` for View Textbooks;
  - `/admin/textbooks/new` for Add Textbook;
  - `/admin/textbooks/:textbookRef` for textbook management;
  - `/admin/textbooks/:textbookRef/topics/:topicRef` for focused Topic management;
  - `/admin/textbooks/review` for textbook review work;
  - `/admin/textbooks/review/:documentRef` for extraction review;
  - `/admin/exam-documents` and child routes for non-textbook documents.
- [x] Define redirects from current Admin routes and preserve valid shared or
  bookmarked review links.
- [x] Confirm every route is Admin-authorized in FastAPI as well as hidden from
  other role navigation.
- [x] Inventory every feature currently available under Textbook Structure and
  Documents & Textbooks before moving UI controls.

**Acceptance:** ownership and route mapping cover every existing feature and no
content type is left without an Admin home.

## Step 1 — Add routed second-level Textbook navigation

- [x] Add accessible second-level navigation for **View Textbooks**, **Add
  Textbook**, and **Review Textbooks**.
- [x] Use TanStack Router route state rather than component-only tabs or URL
  hashes.
- [x] Preserve browser Back, Forward, refresh, direct links and page titles.
- [x] Show the current subsection with `aria-current` and keyboard-visible focus.
- [x] Keep the main Admin navigation stable while moving between subsections.

**Acceptance:** each subsection has a stable URL and behaves correctly through
browser navigation and refresh.

## Step 2 — Build the View Textbooks table and explicit filters

- [x] Replace the current expanding textbook picker with an Admin table.
- [x] Add filters for subject, title/search text, edition, publication status,
  Unit or Module structure, Topic review status and publication readiness.
- [x] Apply filters only when the Admin selects **Apply filters**; provide **Clear
  filters** and a visible result count.
- [x] Add useful table columns: textbook, subject, edition, structure, Topic
  counts, review status, publication status and actions.
- [x] Add **Manage** and **Review** actions using public-reference routes.
- [x] Make **Review** open the review table already narrowed to that textbook.
- [x] Provide accessible empty, loading, error and no-filter-match states.
- [x] Support narrow screens without hiding essential status or action controls.

**Acceptance:** an Admin can locate a textbook and enter management or review
without loading every textbook's detailed controls into one page.

## Step 3 — Build the Add Textbook flow

- [x] Move textbook creation to `/admin/textbooks/new`.
- [x] Keep only subject, title, edition, publisher and Unit/Module structure type
  in the initial form.
- [x] Preserve current validation, duplicate protection and safe error messages.
- [x] After successful creation, navigate directly to the new textbook's Manage
  page.
- [x] Make cancelled or failed creation leave existing textbook data unchanged.

**Acceptance:** creation is a short standalone action and a successful result
lands on the correct Manage page.

## Step 4 — Build the focused textbook Manage page

- [x] Move all existing textbook-level actions to the routed Manage page:
  details, edit, archive, structure publication and readiness statistics.
- [x] Display Unit/Module groups and Topics in a scannable hierarchy.
- [x] Keep Add Unit/Module and Add Topic visually and semantically distinct.
- [x] Preserve group and Topic edit, ordering and protected-removal rules.
- [x] Preserve Topic source roles, detach controls, quality reports, retrieval
  preflight, visual review, independent Topic publication and launch readiness.
- [x] Allow later Units and Topics to be added without changing released Topic
  identities or historical citations.
- [x] Add focused Topic routes or sections so opening one Topic does not render
  every other Topic's full management controls.

**Acceptance:** the Manage page provides parity with the current Textbook
Structure feature while being easier to scan and navigate.

## Step 5 — Make Topic uploads destination-safe and observable

- [x] Show a prominent destination summary before file selection, for example
  `Uploading to: Unit 1 → Topic 2 — Elements, Compounds and Mixtures`.
- [x] Repeat the destination in the upload progress and completion state.
- [x] Show per-file name, current file number, total files, real transfer
  percentage, failure state, completion and `Queued for extraction` status.
- [x] Keep progress visible after the file input resets and while portal data
  refreshes.
- [x] Require an explicit confirmation when filename suggestion disagrees with
  the selected Topic.
- [x] Prevent uploading through a Topic panel until that Topic exists and the
  selected destination public reference is stable.
- [x] Add a safe Admin operation to move an unpublished, unreferenced processed
  source to another same-textbook, same-subject Topic without re-uploading.
- [x] Block a move when published content, retrieval chunks or approved visual
  dependencies exist, and audit every successful move.

**Acceptance:** the Admin always sees where a file will be attached, sees its
progress, and can safely correct an eligible mistaken attachment.

## Step 6 — Move textbook extraction review into Textbooks

- [x] Build `/admin/textbooks/review` as a table using the existing extraction
  review data and rules.
- [x] Add filters for subject, textbook, Unit/Module, Topic, filename, upload
  date and review status.
- [x] Show document, textbook, Unit/Module, Topic, page count, remaining page and
  block counts, extraction state and a **Review** action.
- [x] Reuse the current collapsible page review, reviewed-block visibility,
  formula/table/visual handling and progress summary at the routed document
  review page.
- [x] Return from review to the same filtered table or originating Manage page.
- [x] Refresh textbook and Topic readiness immediately after the final review is
  completed.
- [x] Keep document provenance, review audit events and private source access
  unchanged.

**Acceptance:** all textbook review work is available from Textbooks with no
loss of current review capability or audit evidence.

## Step 7 — Create the Exam Documents workspace

- [x] Rename Documents & Textbooks to **Exam Documents** after textbook parity is
  complete.
- [x] Add second-level areas for Past Papers, Mark Schemes, Examiner Reports,
  Reference Materials and Review Documents where appropriate.
- [x] Preserve paper-to-mark-scheme and examiner-report relationships.
- [x] Preserve official material review, question mapping, completeness sign-off,
  private downloads, retry/removal and same-subject constraints.
- [x] Exclude textbook records and textbook-upload controls from this workspace.
- [x] Document where Topic-linked reference books and general assessment
  references belong.

**Acceptance:** non-textbook documents retain every existing workflow under a
clear assessment-oriented name.

## Step 8 — Remove the legacy combined experience safely

- [x] Compare old and new workflows using a written parity checklist.
- [x] Add redirects for supported old links and an intentional not-found state
  for invalid public references.
- [x] Remove duplicated textbook controls and review rendering only after the
  routed equivalents pass acceptance.
- [x] Remove stale navigation labels, state variables and API calls.
- [x] Confirm no database records, object-storage files or audit history are
  deleted by the UI migration.

**Acceptance:** there is one supported UI for each workflow and old links fail
safely or redirect predictably.

## Step 9 — Accessibility, tests and controlled release

- [x] Test route authorization for Admin, Parent and Student accounts.
- [x] Test filters, clearing, empty results, table actions and deep links.
- [x] Test Add Textbook redirect and Manage-page feature parity.
- [x] Test upload destination display, genuine progress, multiple files,
  interrupted transfer, filename conflict and completed queue state.
- [x] Test safe source moves, blocked dependency cases and audit records.
- [x] Test textbook review counts, final completion and return navigation.
- [x] Test Exam Documents workflows after textbook controls are removed.
- [x] Verify keyboard operation, focus movement, table semantics, live progress,
  status text, colour-independent cues and responsive layouts.
- [x] Update Admin and developer documentation.
- [x] Run API contract checks, frontend/backend tests, type checking, linting,
  production build and migration drift checks.
- [x] Deploy the exact reviewed commit, run production acceptance, and verify an
  Admin textbook workflow without modifying released learning content.

**Done when:** textbook creation, management, upload and review form one clear
routed workspace; assessment documents have a separate complete workspace; and
the legacy combined page is removed without data, authorization or workflow
regression.

# AKURU frontend route audit

Date: 19 October 2026 (Asia/Colombo). Original audit below; local implementation delivery notes are appended at the end. No production deployment changes.

## Scope and evidence

Reviewed the 42 static entries in `lib/routes.ts`, the independent `/ui-features` page, four named exam-document category URLs, the supplied paper-review URL, dynamic route families, the route coordinator, shared shell and role-specific feature implementations. A read-only production check covered **48 frontend entry URLs**: all returned HTTP 200. Three missing-route boundary probes returned the expected HTTP 404; the unknown API response was JSON.

This confirms entry-point availability, not authenticated screen correctness or authorization. Signed-in visual, mobile and keyboard inspection was not available in this session. Dynamic resource patterns were reviewed in code rather than enumerating private records or inventing resource IDs. No production records were changed.

Reference direction: [PreSkool Student dashboard](https://preskool.dreamstechnologies.com/html/student-dashboard.html), adapted to AKURU's existing components and learning workflows. The existing home dashboards and official-paper review are the design baseline; learning readers and active exams need focused layouts rather than additional dashboard controls.

## Main findings, in priority order

### 1. Tighten routing consistency before broad cosmetic work

The server allow-list (`isApplicationPath`), client route registration (`createAkuruRouter`), role matching and feature dispatch are maintained separately. Explicit client dynamic routes cover Flashcard decks/sessions and Student textbook readers; Admin dynamic textbook and exam-review families are recognized elsewhere but lack corresponding explicit client route registrations. Align these definitions and test direct refresh, in-app navigation, Back/Forward and missing records for each family. This is a structural inconsistency, not proof that all those screens currently fail.

A concrete code-level problem: `/admin/exam-documents/not-a-real-section` is accepted by both the server matcher and Admin role matcher, while its unknown category resolves to the unfiltered document list. Admin role prefix matching also accepts `/admin/textbooks-not-a-route`, although the server matcher rejects it. Define valid segments and return a proper not-found experience. FastAPI remains the authorization boundary; these observations are frontend routing findings, not claims of backend permission bypass.

The Admin textbook topic pattern is accepted, but `TextbookStructureAdmin` extracts only the book reference from the path. Give a topic URL a focused topic destination or stop advertising it as a distinct supported view. Keep the existing `/admin/library` redirect and `/flashcards` bookmarks working.

### 2. Preserve navigation context

The shell breadcrumb and document title resolve primarily to the top-level sidebar label. Nested destinations need a proper trail, such as Textbooks → Book → Topic → Review, and a precise title. Lists, selected Admin records and many filters use local component state. Parent learner and subject selection are also held in the portal coordinator. Where supported by existing public references, put non-sensitive filters, selected records and safe context in validated search parameters. Refresh or sharing should reopen the intended view. Do not put answers, credentials, transcripts or private drafts in URLs.

### 3. Finish the shared presentation across real screens

Two heading systems (`Heading` and `PageHeader`) and several metric/card/table variants coexist. Many screens retain plain nested `panel` blocks and long action rows. Consolidate into shared page headers, divided card headers/bodies, semantic status chips, consistent toolbar spacing and row actions. Scope work by screen; avoid a blanket reduction of reader text, diagrams, exam controls or touch targets.

### 4. Separate queues from creation and editing

Accounts, exam documents, textbook management, Parent reviews and assignment pages combine browsing and substantial forms. Use a compact queue/list as the entry view and focused detail cards/drawers for editing. Parent reviews currently show extensive child mastery summaries before the assessment queue; bring pending tasks forward and make the summaries optional. Preserve the existing full-paper approval, reviewed-result publication and temporary-password safeguards.

### 5. Give active learning a focused mode

Practice, active mock exams, Flashcards, textbook reading and Tutor sessions should reduce surrounding navigation while keeping a clear exit. Make the question, answer/composer, timer and saved/submitted state dominant. Preserve all existing timers, navigation guards, draft restoration, protected assets and per-student state. Reader and Flashcard URLs already carry useful detail; extend that consistency carefully rather than renaming routes.

### 6. Standardize feedback and accessibility

Adopt consistent initial loading, background refresh, retry, no-results and permission states. Some older screens show empty content before async loading finishes; assess these individually. Long editor forms need visible save states and safe navigation, with failures close to affected actions. Replace native prompt-based textbook editing with labelled dialogs; retain explicit confirmation for irreversible actions. Finish phone/tablet inspection, keyboard focus/restoration, long labels and table overflow checks for the shared shell and complex workflows.

## Route-by-route inventory

`P1` = first delivery wave; `P2` = next wave; `P3` = polish/retain current foundation. Every listed URL below returned HTTP 200 from the public entry point; authentication still applies to its data and rendered workflow.

| URL | Audience | Priority | Suggested improvement |
| --- | --- | --- | --- |
| `/` | Public | P3 | Keep the login visual identity; improve first-login guidance and connection-error recovery. |
| `/login` | Public | P3 | Use one consistent sign-in/expired-session/first-password-change presentation. |
| `/admin` | Admin | P2 | Keep shared metrics; replace long procedural copy with a short readiness checklist and direct destinations. |
| `/admin/accounts` | Admin | P1 | Compact searchable account table; separate create/edit forms from the list; preserve temporary-password safeguards. |
| `/admin/library` | Admin legacy | P1 | Keep legacy redirect to Exam Documents; show canonical breadcrumbs and preserve intended context. |
| `/admin/textbooks` | Admin | P1 | Keep existing filters; use a common filter toolbar, URL-backed applied filters and consistent row actions. |
| `/admin/textbooks/new` | Admin | P2 | Focused compact creation card with field validation and a clear next step into Manage. |
| `/admin/textbooks/review` | Admin | P1 | Separate review queue from focused document work; persist textbook/status filters in URL. |
| `/admin/exam-documents` | Admin | P1 | Separate upload/setup from the review queue; standardize statuses, processing feedback and row actions. |
| `/admin/coverage` | Admin | P1 | Compact grade/term matrix with persistent selection and clear saved/unsaved feedback. |
| `/admin/questions` | Admin | P1 | Question list plus focused mapping editor/source context; persistent save feedback. |
| `/admin/flashcards` | Admin | P2 | Separate reported-card queue, release list and selected-deck detail; retain publication controls. |
| `/admin/blueprints` | Admin | P2 | Separate blueprint setup, question composition and readiness checks into cards. |
| `/admin/ai-accounts` | Admin | P2 | Compact routing-priority list and edit drawer; keep credential aliases and credentials protected. |
| `/admin/tutor-presets` | Admin | P2 | Avatar/voice/profile preview cards with distinct review and enabled states. |
| `/admin/tutor-quotas` | Admin | P2 | Child context, readable allowance/usage cards and separate audited change form. |
| `/admin/tutor-history` | Admin | P2 | Filtered summary and safety queues; audited support detail drawer; separate retention cleanup. |
| `/admin/assessment-audit` | Admin | P1 | Filterable result/version queue with source-linked detail; separate reassessment from routine review. |
| `/admin/media` | Admin | P2 | Visual grid with kind/status filters, focused review drawer and clear publication state. |
| `/admin/evaluations` | Admin | P2 | Lead with release-gate outcomes; keep corpus JSON and diagnostics in advanced sections. |
| `/admin/operations` | Admin | P2 | Adopt shared metrics/status cards; group alerts by severity and show last refresh. |
| `/admin/security` | Admin | P3 | Adopt shared card header/body spacing and consistent inline validation. |
| `/parent` | Parent | P3 | Keep the refreshed overview; make selected-child context clear when moving to other pages. |
| `/parent/students` | Parent | P2 | Readable child profiles and enrolled-course cards with consistent child switching. |
| `/parent/tutors` | Parent | P2 | Tutor preview/profile cards; compact subject/child context and edit controls. |
| `/parent/tutor-history` | Parent | P2 | Child/date filters and educational summary cards; retain private-conversation boundaries. |
| `/parent/library` | Parent | P2 | Searchable resources with subject/kind labels and clear View/Open PDF actions. |
| `/parent/reviews` | Parent | P1 | Put the pending-review queue first; move long mastery summaries to optional detail and improve review workspace layout. |
| `/parent/assignments` | Parent | P1 | Show assignments as the primary list/calendar; move creation into a drawer with explicit learner context. |
| `/parent/progress` | Parent | P2 | Shared metric cards, visible learner/subject scope and distinct mastery versus practice-score labels. |
| `/parent/security` | Parent | P3 | Consistent shared password form card and inline success/error handling. |
| `/student` | Student | P3 | Keep next-learning action prominent; avoid adding operational dashboard density. |
| `/student/subjects` | Student | P2 | Consistent subject cards and focused lesson details with a clear next learning action. |
| `/student/tutors` | Student | P2 | Tutor personality/subject previews with one obvious start/resume action. |
| `/student/tutor-room` | Student | P2 | Focus chat and composer; put sources, session settings, quota and topic tools in secondary panels. |
| `/student/textbooks` | Student | P2 | Consistent textbook/reference tiles, subject filtering and clear reader entry. |
| `/student/practice` | Student | P1 | Focused question/answer layout with visible save/submission state; retain hints, attachments and draft behavior. |
| `/student/exams` | Student | P1 | Separate available/completed mocks and active exam mode; prioritize timer, answer state and question navigation. |
| `/student/progress` | Student | P2 | Shared summaries, subject/topic filters and clear explanations of score definitions. |
| `/student/study-plan` | Student | P2 | Agenda-style next tasks and consistent completion status; keep recommendations distinguishable from assignments. |
| `/student/security` | Student | P3 | Compact readable security form; retain password requirements and session behavior. |
| `/flashcards` | Student | P2 | Keep existing mastery/session routes; unify deck cards and improve focused study presentation. |
| `/ui-features` | Admin | P3 | Keep as the reference; add representative real-workflow examples and device/keyboard acceptance scenarios. |
| `/admin/exam-documents/past-papers` | Admin | P1 | Consistent queue filters and status chips; keep exact source pairing and Review questions action obvious. |
| `/admin/exam-documents/mark-schemes` | Admin | P1 | Show related paper and pairing status prominently; use the common resource table. |
| `/admin/exam-documents/examiner-reports` | Admin | P1 | Show related paper and source role; standardize list/review actions. |
| `/admin/exam-documents/references` | Admin | P2 | Consistent searchable reference list with publication/readiness indicators. |
| `/admin/exam-documents/review/{paperId}` | Admin | P2 | Keep new workspace; verify signed-in keyboard, narrow-screen, long-name and save-error scenarios before further cosmetic changes. |

## Dynamic route families

| Pattern | Current observation | Improvement |
| --- | --- | --- |
| `/admin/textbooks/{bookRef}` | Book management selected by path | Precise breadcrumb; focus sections; separate editing and publication readiness. |
| `/admin/textbooks/{bookRef}/topics/{topicRef}` | Accepted by server; current feature extracts book reference only | Resolve and focus the requested topic or explicitly reject unsupported detail paths. |
| `/admin/textbooks/review/{documentRef}` | Focused document route recognized by feature | Consistent split source/editor layout, page navigator and persistent save state. |
| `/admin/exam-documents/review/{paperId}` | New dedicated review workspace | Validate the new layout on desktop/phone/tablet and retain backend review gates. |
| `/flashcards/decks/{deckRef}` | Explicit client route and restored detail | Shared deck/mastery cards and concise next action. |
| `/flashcards/decks/{deckRef}/start` | Mode/difficulty/count are parsed; route validation should stay consistent | Clearly communicate available set sizes and validate all supported search fields. |
| `/flashcards/sessions/{sessionRef}/cards/{position}` | Explicit session/card route | Focus mode, clear reveal/rating state and protected in-progress session behavior. |
| `/student/textbooks/{bookRef}` | Explicit book route | Readable unit/topic list with publication/version context in secondary metadata. |
| `/student/textbooks/{bookRef}/topics/{topicRef}` | Reader view/source/page carried in URL | Consistent reader controls, side table of contents and mobile action placement. |

Additional UI states without distinct record URLs include selected Parent assessment reviews, selected assessment-audit results, selected Admin Flashcard decks, Tutor session detail and media review. Consider safe public-reference deep links where existing APIs expose the necessary identities. Adding a URL alone must not broaden data access.

## Recommended delivery sequence

1. **Navigation foundation:** one route definition source, stricter missing-page handling, precise breadcrumbs/titles, safe filter and selection restoration; verify Back/Forward and direct entry.
2. **High-volume Admin work:** accounts; exam-document queues; textbook list/manage/review; coverage, mapping and assessment audit. Reuse the new paper-review layout where appropriate.
3. **Family workflows:** pending assessment queue, assignment creation/list, child-scoped progress and searchable library.
4. **Focused learning:** practice and active mocks first, then Tutor room, reader and Flashcard presentation. Retain their current domain rules.
5. **Operational consistency:** AI routing, Tutor presets/allowances/history, evaluations and media; hide technical detail until needed by an operator.
6. **Acceptance:** populated/empty/error states, correct-role/denied access, no cross-learner context leakage, keyboard operation and representative device widths.

Most layout, navigation, URL-state and component-consistency work is frontend-only using existing authorized responses. Do not promise server-side search/pagination, new aggregate statistics, cross-resource search, saved preferences across devices or new notifications without checking API support; those may require separate backend scope. Existing server filtering/pagination must be preserved. Never download broader private datasets just to add local filters.

## Production HTTP boundary results

- 48 frontend entry URLs: HTTP 200.
- `/akuru-route-audit-missing`: HTTP 404, HTML.
- `/api/v1/akuru-route-audit-missing`: HTTP 404, JSON.
- `/_next/akuru-route-audit-missing.js`: HTTP 404.

No authenticated actions, production writes, commits or deployments were performed for this audit. Existing local favicon/layout modifications were left untouched.


## Local implementation delivery — 19 October 2026

Frontend implementation is complete across the audited entries. No backend, API schema, database migration, production configuration, commit or deployment changes were made. Preexisting layout/favicon edits were preserved. This delivery means code coverage of the recommendations; it does not mean all populated workflows have passed signed-in visual acceptance.

### Route coverage

| Audited entries | Delivered frontend behavior |
| --- | --- |
| `/`, `/login` | Retained first-password-change/session-expiry presentation; added retry for connection failures. |
| `/admin` | Shared metrics and short release-readiness destinations. |
| `/admin/accounts` | Searchable account table; create/enrolment drawer; labelled actions; existing temporary-password safeguards. |
| `/admin/library` | Canonical redirect retained; shared route registry and breadcrumbs. |
| `/admin/textbooks`, `/admin/textbooks/new`, `/admin/textbooks/review` | Applied filters in URL; focused creation/review routes; labelled title/edition editors and quality report dialog. |
| `/admin/textbooks/{bookRef}`, `/admin/textbooks/{bookRef}/topics/{topicRef}` | Explicit routes and nested breadcrumbs; focused topic resolution and unavailable-topic feedback; separate editing/readiness. |
| `/admin/textbooks/review/{documentRef}` | Existing source/editor split retained; loading/retry, sticky save state, navigation protection and labelled paragraph-split dialog. |
| `/admin/exam-documents` and `/past-papers`, `/mark-schemes`, `/examiner-reports`, `/references` | Upload/setup disclosure separate from queue; common search/status/subject filters and safe selected-document URL. Existing source pairing and publication checks retained. |
| `/admin/exam-documents/review/{paperId}` | Existing dedicated review workspace retained; explicit UUID route, precise title/breadcrumb and shared responsive shell. Populated keyboard/save-error acceptance remains pending. |
| `/admin/coverage` | URL subject/term selection, existing cumulative matrix, sticky saved/unsaved feedback and draft navigation protection. |
| `/admin/questions` | Searchable question navigation, focused mapping editor and unsaved mapping protection; weighted confirmation gates retained. |
| `/admin/blueprints` | Setup in a secondary disclosure; existing composition/readiness cards retained. |
| `/admin/flashcards` | Report/release queues retained; searchable decks, loading state and URL-selected deck detail; release controls retained. |
| `/admin/ai-accounts` | Searchable priority list and configuration drawer; existing protected credential aliases retained. |
| `/admin/tutor-presets` | Existing preview/review cards retained; distinct enabled/disabled label. |
| `/admin/tutor-quotas` | URL learner selection, shared usage metrics, separate audited allowance-change form. |
| `/admin/tutor-history` | Search/date/status filters; safety queue, support-detail drawer and separate retention disclosure. |
| `/admin/assessment-audit` | Search/subject filters, selected-result URL, guarded review close and existing source/version evidence. |
| `/admin/media` | Search/kind/status grid, focused image review drawer and existing publication actions. |
| `/admin/evaluations` | Release gates remain primary; initial loading/error retry; corpus and raw observations in disclosures. |
| `/admin/operations` | Shared usage/status metrics, alert/audit cards, refresh indicator and last-refresh time. |
| `/admin/security`, `/parent/security`, `/student/security` | Shared divided-card presentation and inline success/error messages; existing password/session rules retained. |
| `/parent`, `/student` | Existing refreshed home dashboards retained; authorized learner/subject context carries into destinations. |
| `/parent/students` | Searchable learner/course profiles with consistent course labels. |
| `/parent/tutors`, `/student/tutors` | Searchable Tutor previews; focused create/edit drawer; Student start/resume action. |
| `/parent/tutor-history` | Search/date/status filters on authorized summaries; existing private-transcript boundary retained. |
| `/parent/library` | Search/subject/kind filters and explicit PDF/resource actions. |
| `/parent/reviews` | Pending review queue first; optional mastery/Tutor summaries and guarded review publication workspace. |
| `/parent/assignments` | Primary filtered assignment list; creation drawer with learner context and draft protection. |
| `/parent/progress`, `/student/progress` | Shared metrics, URL subject/topic search and distinct existing mastery/practice-score meanings. |
| `/student/subjects` | Shared heading/card presentation, topic search and existing focused lesson/next-practice action. |
| `/student/practice`, `/student/exams` | Active focus view with explicit exit and sticky answer actions; existing timers, draft restoration and submission guards retained. |
| `/student/tutor-room` | Conversation/composer before secondary tools; profile context from authorized URL selection; recoverable initial error and focus mode. |
| `/student/textbooks`, `/student/textbooks/{bookRef}`, `/student/textbooks/{bookRef}/topics/{topicRef}` | Library search, loading/retry, focus mode, existing protected reader/source URLs, page contents and sticky page controls. |
| `/student/study-plan` | Agenda orders unfinished tasks first and by schedule/due date; revision status separated from Parent assignment status. |
| `/flashcards`, `/flashcards/decks/{deckRef}`, `/flashcards/decks/{deckRef}/start`, `/flashcards/sessions/{sessionRef}/cards/{position}` | Searchable deck cards, validated learning parameters, active focus and existing reveal/rating/mastery/exit behavior. |
| `/ui-features` | Real filter/drawer/empty/loading/retry examples and device/keyboard acceptance scenarios. |

### Verification and remaining acceptance

- Typecheck, frontend lint, 71 automated tests and production build pass locally. Route tests execute all static/dynamic definitions, reject malformed/unknown destinations, check role boundaries and safe query fields, and exercise route matching with memory-history Back/Forward.
- Read-only browser inspection on the existing local server verified Admin overview → Accounts navigation, account drawer opening, URL search updates and search restoration after refresh. Desktop 1440px and phone 390px checks found no page overflow on the account queue. The existing local database contains no learner/document records.
- The browser's native discard-confirmation interaction stalled during automation. Opening the drawer and entering a draft were observed; confirmation dismissal/focus restoration is **not marked passed**. No account was created or changed.
- Populated Admin reviews, Parent and Student role screens, active exam timing, attachments, private source assets, media publication, failing saves and long-name keyboard/device scenarios still require representative local data and signed-in acceptance. No synthetic users, documents, assessments or release actions were created merely for this UI check.
- Server search/pagination, global aggregation/search, notifications and cross-device preferences remain separately scoped backend-dependent ideas, not frontend omissions or implemented features.

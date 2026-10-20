# AKURU route-wide UI component adoption plan

Date: 20 October 2026 · Status: implementation delivered locally; release and remaining populated acceptance tracked below.

## Outcome and scope

Make AKURU feel like one compact, consistent learning product across Admin, Parent and Student screens, using the 27 families now available in `/ui-features`. Retain the PreSkool-inspired divided card headers, clear hierarchy and efficient spacing, while preserving AKURU's original identity and learning workflows. Add a modest, coordinated increase in colour across all three roles so the interface feels warmer and more engaging.

This is a **frontend-only adoption and refinement plan**. No database migrations, API contracts, authorization rules, assessment logic or production configuration changes are intended. Existing API calls and mutations remain authoritative. A component catalogue does not provide new product capabilities: unsupported data, bulk actions, server pagination, attendance, presence or achievement tracking must be deferred to separate plans. The user subsequently authorized end-to-end implementation and production deployment on 20 October 2026.

## Evidence and baseline

Source inspection covers [route definitions](../../frontend/lib/routes.ts), [client routing](../../frontend/lib/app-router.tsx), the catch-all page, [portal dispatch](../../frontend/app/page.tsx), role feature modules, profiles, Community, and the [catalogue reuse guide](../../frontend/docs/ui-component-catalogue.md). Inventory: **60 registered route patterns plus the independent Admin-only `/ui-features` page = 61 entries**. Dynamic patterns represent every matching record, not additional invented URLs. Query-selected panels are listed separately below.

This is a source-based implementation plan, not a claim that all authenticated production screens were visually audited today. The [previous audit](../../frontend/docs/ROUTE-UI-AUDIT.md) records extensive delivered work and incomplete populated acceptance. Its original findings are historical; do not treat them all as current defects. Current code already has a shared route registry, stricter matching, URL context, focus modes, drawers, semantic badges and loading/retry helpers. Profile, avatar and Community features also exist.

Before beginning, reconcile the remaining acceptance in [route refresh](../ongoing/TODO-ROUTE-FRONTEND-REFRESH.md) and [UI refresh](../ongoing/TODO-UI-FEATURES-REFRESH.md). Close or carry forward named acceptance items with evidence; do not redo completed work or silently mark it accepted. The existing uncommitted sidebar hover expansion in `portal.css` and `portal-shell.tsx` is a separate local change: preserve it and review its release scope independently.

## Design rules

- Use one page header with title, short context and one primary action. Secondary actions belong beside it or in a labelled menu; keep frequent and critical actions visible.
- Adopt shared compact spacing: proposed 16px desktop card padding, 12–16px mobile padding, 16px section gaps and 8px related-control gaps. Validate against existing tokens before changing them. Divide card headers from content with a subtle line. Avoid nested decorative panels and repeated headings.
- Compact lists and administration controls, not reading text, equations, source images or active learning controls. Aim for 40–44px mobile controls; desktop targets meet at least 24px with sufficient separation. Never shrink everything through global CSS.
- Use existing semantic badges with visible labels. Do not encode readiness, errors, review state or mastery through colour alone. No new meanings inferred from label substrings.
- Original Student avatars must match the saved avatar across the ribbon, profile and permitted Community surfaces. Admin/Parent initials remain supported. Public names and private account names have different contexts.
- Tables suit comparison; cards suit people and resources. Mobile adaptation must keep labels, statuses and essential actions. Wide scientific content may scroll within a labelled region; the whole page must not overflow.
- Separate initial loading, refresh, empty account, filtered no-results, permission denial and failed requests. Keep existing content during safe refresh; put retry and validation next to the affected area.
- Prefer progressive disclosure for secondary detail. Never hide required review evidence, save failures, timers or primary task actions in tooltips or collapsed sections.

## Colour direction — added requirement

Use restrained colour throughout the live interface, beyond status badges alone. Keep AKURU blue as the primary action and navigation colour; introduce coordinated teal, violet, amber and coral accents through soft backgrounds, icons, small borders and selected decorative areas. These are proposed colour families, not final production values: choose accessible token values during the pilot and demonstrate them in `/ui-features` before broader adoption.

### Where colour belongs

| Surface | Planned treatment | Boundary |
| --- | --- | --- |
| Dashboards across all roles | Soft tinted metric icon containers, small card accents and a lightly coloured welcome area. | Avoid making every card a saturated block. Values and primary actions retain clear hierarchy. |
| Subject and resource cards | Stable subject accent applied to icon tiles, a narrow card edge or a light header tint; reuse it in related lists and detail headers. | Use a centrally defined mapping based on existing subject identifiers, with a neutral fallback. No random colours per render or database changes. Keep the subject name visible. |
| Student experience | More expressive subject tiles, agenda markers and profile accents using the same shared palette. | Practice questions, active exams, textbook prose and Tutor conversation remain on calm readable surfaces. Do not recolour scientific diagrams or source material. |
| Parent experience | Gentle accents on child summaries, learning cards and progress sections. | Child name/avatar and selected-child text remain explicit; colour is never the sole indication of which child is selected. |
| Admin experience | Restrained tinted icons, queue summaries and section accents to break up dense neutral workspaces. | Tables, evidence and editing surfaces stay mostly neutral. Decorative accents must not resemble warnings or release states. |
| Profiles and Community | Subtle banner tint or gradient, consistent avatar surrounds and quiet section accents. | Preserve original avatar artwork and skin tones. No decorative online, achievement or verification signals. |
| Navigation and tabs | Soft active-item fill, clear blue active indicator and coordinated hover/focus treatment. | Selected state must also use shape, weight or accessible state; preserve visible keyboard focus. |
| Cards and dividers | Optional lightly tinted headers with a visible neutral divider and white/neutral content body. | Maintain the compact layout and header/body separation; avoid mixing several accent colours inside one card. |

### Palette and implementation rules

- Define reusable semantic colour tokens for brand actions, decorative accents, soft surfaces, borders and text. Keep decorative accents separate from existing success/warning/error/review badge tokens. Do not scatter one-off colour literals across routes.
- Apply one dominant decorative accent per section and a limited palette per page. Small gradients are appropriate for profile/welcome decoration only; no gradients behind long text, form fields or review evidence.
- Preserve established status meanings. A coloured subject card is a category treatment, not an indication of completion, risk or approval. Progress colours must preserve their existing meaning rather than inherit a subject accent indiscriminately.
- Validate text contrast at WCAG AA: at least 4.5:1 for normal text and 3:1 for large text; required control boundaries and graphical state indicators meet 3:1 against adjacent colours. Check hover, selected, disabled and focus states, and ensure meaning survives colour-vision differences and grayscale.
- Keep this within the existing theme. A new dark mode, user-selectable themes or saved colour preferences are outside scope.

Acceptance: demonstrate the palette on Admin Accounts, Parent assignments and Student subjects, plus a dashboard/profile preview. Compare before/after at desktop and mobile widths. The result should be visibly more colourful without making task content harder to scan, weakening dividers, or confusing decoration with status. Document the chosen tokens and examples in the catalogue reuse guide so later routes follow the same approach.

## Shared implementation packages

| Package | Work | Reuse and boundaries |
| --- | --- | --- |
| S1: structure | Unify heading/card spacing, dividers, action alignment, typography, responsive grid and shared colour tokens. | Extend `PageHeader`, `DashboardCard`, `MetricCard` and existing CSS; reconcile `Heading` rather than creating a third system. |
| S2: workspace | Standard toolbar, applied filters, row actions, results footer and responsive list/detail composition. | Extend `FilterToolbar` and route adapters. Keep business queries in features. Extract proven compositions from the catalogue; never import fixture handlers into product screens. |
| S3: feedback | Common loading/empty/error/save states and mutation feedback. | Existing `LoadingState`, `ErrorState`, `EmptyState`, skeleton, alert and spinner primitives. Avoid duplicate live announcements. |
| S4: editing | Consistent drawers/dialogs, field errors, unsaved changes and focus return. | Extend `EditorDrawer`, existing dialogs and guards. A browser native discard confirmation need not be replaced unless the replacement is fully verified. |
| S5: identity/navigation | Consistent avatar sizes, badges, tabs, breadcrumbs and profile links. | Existing `StudentAvatar`, badge helpers, route registry and role-aware shell. No authorization changes. |
| S6: learning | Reader, exam, practice and flashcard action bars and progress semantics. | Preserve domain state, session ownership, timers, autosave/draft restoration and protected resources. |

No new component library, Bootstrap runtime or PreSkool assets are required. Prefer current Base UI/shadcn primitives. Keep catalogue styling scoped; promote intentional tokens/compositions into portal styles rather than importing the catalogue stylesheet globally.

## All 27 component families

| Family / catalogue ID | Intended adoption | Constraint / acceptance |
| --- | --- | --- |
| Alerts (`alerts`) | Save failures, processing problems, review blockers, session recovery. | Persistent actionable failures; concise success feedback; polite announcements unless urgent. |
| Accordion (`accordion`) | Topic groups, review evidence groups and long profile/course details. | Required content stays discoverable; keyboard operated; deep-linked section opens. |
| Avatar (`avatar`) | Profile, top ribbon, learner lists, permitted Community cards. | Original saved avatar and initials fallback; no fake presence dots. |
| Badges (`badges`) | Status, review readiness, subjects and counts. | Reuse already deployed semantic badges; fix gaps only. |
| Buttons (`buttons`) | Consistent primary, secondary, destructive and loading actions. | One clear primary action per task; disable duplicate submissions without trapping focus. |
| Button groups (`buttons-group`) | View choices, reader controls, related filters. | Named group and selected state; no excessive squeezed mobile controls. |
| Breadcrumb (`breadcrumb`) | Nested books/topics/review and flashcard routes. | Existing route helpers; meaningful authorized labels, correct parent navigation. |
| Cards (`cards`) | Dashboard, profile, resource and review sections. | Divided header/body, shared spacing; avoid unnecessary card nesting. |
| Carousel (`carousel`) | Optional nonessential onboarding/help specimen only. | No required task or learning navigation hidden in slides. Keep catalogue-only unless a real use case wins review; manual by default. |
| Collapse (`collapse`) | Advanced diagnostics, optional setup and secondary metadata. | Preserve native details where adequate; do not collapse errors or mandatory evidence. |
| Dropdowns (`dropdowns`) | Infrequent row actions, secondary resource actions. | Named trigger, keyboard navigation; destructive action still confirmed. |
| Grid (`grid`) | Adaptive dashboard/resource/profile layouts. | Logical reading order, sensible column collapse and stable widths. |
| Images (`images`) | Media review, textbook previews and original avatars. | Aspect ratio, loading/failure fallback, meaningful alt text; preserve authorized asset access. |
| Links (`links`) | View details, source links and contextual destinations. | Real navigation semantics, visible focus and descriptive labels; preserve route context. |
| List group (`list-group`) | Agendas, topic contents, Feed and readiness checklists. | Text status and clear action; distinguish links from buttons. |
| Modals (`modals`) | Small edits, confirmation, avatar editing and reports. | Focus trap/return, labelled title, errors within dialog, guarded dirty dismissal. |
| Offcanvas (`offcanvas`) | Account/assignment editors, detail inspection, mobile filters/contents. | Existing Sheet/EditorDrawer; retain full-page routes for complex review work. |
| Pagination (`pagination`) | Existing paged Community and supported resource lists. | Respect current API totals/cursors. Client paging only over a known complete authorized dataset; never claim global counts from a partial page. |
| Popovers (`popovers`) | Short explanations of mastery, allowance or review terms. | Click/touch accessible; no required forms or essential errors hidden inside. |
| Progress (`progress`) | Known completion, review coverage and measured usage. | Real numerator/denominator and text; unknown is indeterminate/no data, not invented percent. |
| Placeholders (`placeholders`) | Initial page/card/list loading. | Match final layout; nonfocusable; do not flash empty states before loading ends. |
| Workspace (`workspace`) | Admin queues, Parent reviews/assignments, resource libraries. | Compose toolbar/list/detail/footer; use only actions supported by existing services. No automatic bulk actions or fake CSV import. |
| Attendance (`attendance`) | Keep fictional register/heatmap in `/ui-features` only. | Production attendance deferred. Do not relabel study inactivity as absence or fabricate streaks. Any future activity view needs a verified data contract. |
| Spinner (`spinner`) | Local saving, refresh and processing with unknown duration. | Text equivalent and appropriate busy state; no indefinite blocked screen without recovery. |
| Nav & tabs (`nav-tabs`) | Community sections, review modes, history sections and learning panels. | Preserve query/route state, selected semantics and keyboard operation. URL navigation can remain links rather than forced ARIA tabs. |
| Tooltips (`tooltips`) | Supplementary icon help and terse label explanations. | Keyboard and touch alternative; never sole name or essential instruction. |
| Typography (`typography`) | Headers, metadata, field help, prose, equations and scores. | Clear hierarchy and readable line lengths; preserve scientific notation and existing content semantics. |

## Route-by-route delivery inventory

Every row inherits the shared design and validation requirements. Components listed are targeted opportunities, not a demand to insert every family on every page. **P1** = high-use workflows and consistency; **P2** = supporting screens; **P3** = reference/boundary polish. Begin with visual comparison: retain already compliant components and implement only the identified delta. Route-level acceptance below supplements the common acceptance matrix.

### Admin — 30 entries

| Route | Priority | Components and concrete refinement | Route acceptance |
| --- | --- | --- | --- |
| `/admin` | P1 | Cards, grid, list group, alerts: compact metrics and actionable readiness list. | Each readiness action reaches the correct queue; no invented totals. |
| `/admin/accounts` | P1 | Workspace, offcanvas, dropdowns, badges: align account rows, enrolment summaries and create/edit drawer. | Search survives refresh; temporary credentials remain protected; dirty drawer is guarded. |
| `/admin/community-reports` | P1 | Workspace, badges, modals, alerts: compact report queue with explicit status and focused evidence/action area. | Preserve moderation permissions, reason requirements and all existing report outcomes. |
| `/admin/exam-documents` | P1 | Workspace, collapse, progress, badges: compact queue with setup secondary and visible processing state. | Keep pairing, upload errors and release gates; progress uses actual available data. |
| `/admin/exam-documents/past-papers` | P1 | Workspace, badges, links: consistent paper metadata columns and direct Review action. | Paper identity and paired sources remain distinguishable. |
| `/admin/exam-documents/mark-schemes` | P1 | Workspace, badges, links: expose paired-paper context and concise row actions. | Unpaired and paired documents are not visually confused. |
| `/admin/exam-documents/examiner-reports` | P1 | Workspace, badges, links: align report source role and related paper information. | Related-paper navigation preserves the correct record. |
| `/admin/exam-documents/references` | P2 | Workspace, cards, dropdowns: consistent reference metadata and readiness. | Search/filter and protected source opening retain existing behavior. |
| `/admin/exam-documents/review/$paperId` | P1 | Cards, nav-tabs, button groups, alerts: refine existing source/editor workspace and persistent save/review actions. | Correct part/source stays selected; keyboard, mobile, save failure and publication guards pass. |
| `/admin/library` | P3 | Breadcrumb, links: retain canonical Exam Documents redirect. | Legacy bookmarks resolve correctly without a second competing layout. |
| `/admin/textbooks` | P1 | Workspace, badges, offcanvas: consistent filters, compact book rows/cards and actions. | Existing URL filters and selected book restore correctly. |
| `/admin/textbooks/new` | P2 | Cards, buttons, alerts: one focused creation form with grouped fields and clear next step. | Validation retains input; success opens the intended book. |
| `/admin/textbooks/review` | P1 | Workspace, badges, pagination where supported: align review queue and pending actions. | Status/book filters and empty/no-results states stay distinct. |
| `/admin/textbooks/$bookRef` | P1 | Breadcrumb, accordion, cards: concise book overview, topic structure and separate readiness section. | Existing topic editing, ordering and publication checks are unchanged. |
| `/admin/textbooks/$bookRef/topics/$topicRef` | P1 | Breadcrumb, cards, modals: emphasize the routed topic and compact edit controls. | Deep link focuses the exact topic; unavailable topic has recovery. |
| `/admin/textbooks/review/$documentRef` | P1 | Workspace, button groups, alerts, progress: refine source/editor split and page controls. | Dirty work, scientific content, source coordinates and final review gates survive navigation/layout changes. |
| `/admin/coverage` | P1 | Grid, cards, badges, alerts: compact labelled matrix and visible save bar. | Term/subject scope and cumulative coverage meaning remain clear; failed saves retain draft. |
| `/admin/questions` | P1 | Workspace, offcanvas, badges: tighter question navigator and mapping/evidence editor. | Question selection and weighted mapping validation remain intact. |
| `/admin/flashcards` | P2 | Nav-tabs, workspace, badges: clarify report queue, releases and selected deck. | Deck URL selection and report/publication safeguards persist. |
| `/admin/blueprints` | P2 | Cards, collapse, progress: separate setup, composition and readiness. | Actual readiness blockers remain visible and authoritative. |
| `/admin/ai-accounts` | P2 | Workspace, offcanvas, badges: readable priority list and configuration form. | Credential values never leak into list, URL, tooltip or copied UI text. |
| `/admin/tutor-presets` | P2 | Cards, images, badges: consistent preview sizes and review/enabled states. | Voice/avatar settings and review state remain distinct. |
| `/admin/tutor-quotas` | P2 | Cards, progress, popovers: clear learner context, usage definition and allowance edit. | No fake usage percentages; audited changes preserve existing reason/input requirements. |
| `/admin/tutor-history` | P2 | Workspace, offcanvas, collapse: concise summaries, safety queue and separate cleanup controls. | Support access and retention confirmations retain current restrictions. |
| `/admin/assessment-audit` | P1 | Workspace, nav-tabs, badges, alerts: align result/version details and reassessment action. | Evidence, version history and guarded reassessment remain intact. |
| `/admin/media` | P2 | Grid, images, offcanvas, badges: stable thumbnails and compact review details. | Broken/protected assets have safe fallback; publication requires existing checks. |
| `/admin/evaluations` | P2 | Cards, alerts, collapse: gate outcomes first; advanced corpus/diagnostics secondary. | Failed gates remain explicit; no technical evidence is removed. |
| `/admin/operations` | P2 | Cards, alerts, spinner: group health issues and show refresh age clearly. | Stale data cannot look like newly verified healthy state. |
| `/admin/profile` | P2 | Avatar, cards, list group: reduce repetitive metadata and align account sections. | Ribbon opens this profile; current account details and security link remain correct. |
| `/admin/security` | P2 | Cards, alerts, buttons: compact password form with adjacent validation. | Password lifecycle and session behavior unchanged; submission failure preserves usable form. |

### Parent — 10 entries

| Route | Priority | Components and concrete refinement | Route acceptance |
| --- | --- | --- | --- |
| `/parent` | P1 | Grid, cards, avatar, list group: consistent selected-child summary and next actions. | All destinations carry the intended child context. |
| `/parent/students` | P2 | Avatar, cards, accordion: compact child and enrolled-course sections. | Multiple/zero children and long course names remain readable; no cross-child information mix. |
| `/parent/tutors` | P2 | Cards, images, offcanvas: consistent tutor previews and configuration drawer. | Selected child/subject remains clear during edit and save. |
| `/parent/tutor-history` | P2 | Workspace, cards, collapse: concise educational summaries and date filters. | Existing private-conversation boundaries remain unchanged. |
| `/parent/library` | P2 | Workspace, images, badges, links: consistent resource cards and explicit PDF/open actions. | Only existing authorized resources shown; failures and empty filters are distinguishable. |
| `/parent/reviews` | P1 | Workspace, cards, nav-tabs, alerts: compact pending queue and focused review with mastery secondary. | Review publication, learner context, unsaved edits and result evidence remain correct. |
| `/parent/assignments` | P1 | Workspace, offcanvas, badges: consistent assignment rows and learner-labelled creation drawer. | Due/status meanings remain accurate; dirty form protected; no new calendar service implied. |
| `/parent/progress` | P1 | Cards, progress, popovers, accordion: readable child/subject summaries and topic details. | Mastery and practice scores stay distinct; no-data never means zero attainment. |
| `/parent/profile` | P2 | Avatar, cards, list group: concise account information and linked children. | Only permitted child details appear; profile/security navigation works. |
| `/parent/security` | P2 | Cards, alerts, buttons: same accessible password-form pattern. | Current password and session rules retained. |

### Student — 18 entries

| Route | Priority | Components and concrete refinement | Route acceptance |
| --- | --- | --- | --- |
| `/student` | P1 | Cards, grid, list group, progress: next learning task prominent with compact supporting summaries. | Active/resumable task remains easy to find; metrics retain real meanings. |
| `/student/subjects` | P1 | Cards, accordion, badges: consistent subject/topic hierarchy and learning actions. | Subject/topic selection and existing next-practice behavior stay correct. |
| `/student/community` | P1 | Nav-tabs, avatar, workspace, pagination, modals: responsive section navigation and compact learner/follow cards. | Public names only where intended; follow/back, blocks, reports and Feed states remain authoritative. |
| `/student/textbooks` | P2 | Grid, cards, images, badges: aligned book tiles and search/filter controls. | Only published authorized books; loading/no-results/resource failure remain distinct. |
| `/student/textbooks/$bookRef` | P2 | Breadcrumb, accordion, list group: readable contents and current-topic action. | Correct book/topic destination and existing publication context. |
| `/student/textbooks/$bookRef/topics/$topicRef` | P1 | Typography, button groups, offcanvas, images: readable topic content with compact page/source controls. | Text/visual view, source/page query, diagrams, protected assets and return context survive. |
| `/student/tutors` | P2 | Cards, avatar, badges: consistent tutor summaries with obvious start/resume. | Start/resume uses the correct tutor and subject. |
| `/student/tutor-room` | P1 | Cards, collapse, offcanvas, alerts: conversation/composer dominant; sources and settings secondary. | Streaming/voice, quota errors, session context and composer accessibility remain usable. |
| `/student/practice` | P1 | Nav-tabs, progress, alerts, buttons: focus question/answer and saved/submitted state. | Hints, attachments, draft recovery and submission behavior unchanged. |
| `/student/exams` | P1 | Cards, list group, progress, alerts: clear available/completed views and focused active session. | Timer never resets through layout/tab changes; answer navigation and submit/exit guards preserved. |
| `/student/progress` | P1 | Cards, progress, popovers, accordion: concise subject overview and explained topic detail. | Score definitions and no-data states remain honest and accessible. |
| `/student/study-plan` | P2 | List group, badges, cards: compact agenda with clear task type and next action. | Parent assignments differ from recommendations; no fabricated streak or attendance. |
| `/student/profile` | P1 | Avatar, cards, offcanvas, alerts: identity first; Community settings secondary; compact learning/account sections. | Avatar save updates ribbon/profile; public name settings remain subordinate and private details stay private. |
| `/student/security` | P2 | Cards, alerts, buttons: consistent accessible password form. | Password/session rules retained; no credentials in URL or telemetry. |
| `/flashcards` | P2 | Cards, grid, badges: consistent searchable deck summaries. | Existing mastery labels and deck destinations remain correct. |
| `/flashcards/decks/$deckRef` | P2 | Breadcrumb, cards, progress: compact deck summary with one study action. | Deck identity and actual mastery/session information preserved. |
| `/flashcards/decks/$deckRef/start` | P2 | Button groups, cards, alerts: accessible mode/difficulty/count selection. | Only supported combinations/counts; URL parameters restore correctly. |
| `/flashcards/sessions/$sessionRef/cards/$position` | P1 | Buttons, progress, typography: focused reveal/rating controls and clear session position. | Card navigation, reveal/rating, completed-set behavior, ownership and exit guards unchanged. |

### Public/shared/reference — 3 entries

| Route | Priority | Components and concrete refinement | Route acceptance |
| --- | --- | --- | --- |
| `/` | P3 | Cards, alerts, typography: retain sign-in identity with consistent form/error layout. | Sign-in, expired session and forced password change continue working. |
| `/login` | P3 | Same sign-in composition as root; consistent buttons and loading. | No divergence from root login behavior or unsafe return destination. |
| `/ui-features` | P3 | All 27 families: add adopted real-workflow references and usage decisions. | Admin access remains enforced; catalogue demo data never enters production services. |

### States without separate path patterns

- Community: exercise `section=discover|following|followers|feed|settings|blocked`, course selection, optional subject filter, public-name search and pagination. Discovery remains course-based, with subject filtering; no messaging, online indicators or invented exam activity. Preserve existing future expansion boundaries rather than hard-coding new course rules into cards.
- Profiles: avatar editor, save failure/reset, initials fallback and Community settings drawer; Admin and Parent do not inherit Student-only controls. Keep My profile above Community in Student navigation.
- Selected records: assessment audit result, Parent assessment review, Admin deck, Tutor history/session and media drawer. Keep only already-supported safe record references in URL state; no private drafts, transcripts or credentials.
- Learning: practice setup/active/result, mock setup/active/submitted/result, flashcard reveal/rating/completed and reader text/visual/source/page states need separate acceptance even where the path is unchanged.
- Shell: expanded/collapsed, keyboard focus, optional hover expansion pending local review, mobile menu, notifications and topbar account link for each role. Switching role/account or Parent child must not retain another person's sensitive content.
- Boundaries: unknown route, malformed dynamic parameter, missing/deleted record, unauthorized role, expired session, network failure and retry. These are states, not new routes. Preserve meaningful HTTP behavior and server authorization.

## Delivery sequence and exit gates

1. **Baseline and acceptance reconciliation.** Capture representative authorized local screenshots/data for all three roles; compare current screens with the inventory. Record each row as retain/refine with concrete evidence. Resolve earlier outstanding populated and discard-confirmation checks, or explicitly carry them into this plan. Confirm each list's API filtering/paging/total behavior. Exit: reviewed route checklist and no ambiguity over prior work or data contracts.
2. **Shared foundation pilot (S1–S5).** Pilot Accounts, Parent assignments and Student subjects to cover table, drawer and card patterns. Agree compact spacing, divided headers, the accent palette, feedback and mobile behavior. Include dashboard/profile colour previews and record contrast checks before rolling out tokens. Exit: one accessible pattern per workflow, before widening shared CSS impact.
3. **Admin queues and reviews.** Deliver P1 Admin rows, then supporting P2 operations/content screens. Keep full review workspaces for complex editing. Exit: source evidence, dirty-state handling and publication/reassessment flows pass representative local scenarios.
4. **Parent and identity/Community.** Deliver Parent rows and all three profiles/security screens; align existing Community views and avatar presentation. Exit: child isolation, public/private identity, follows, blocks/reports and profile persistence verified.
5. **Student learning.** Apply S6 to practice/exams/readers/flashcards/Tutor, then summaries/agenda/library. Exit: no regression to timers, drafts, assets, voice/streaming or session position; mobile actions stay reachable with the keyboard open.
6. **Full regression and reference update.** Validate every route row and state; update catalogue usage guidance and close the previous plans' carried acceptance. Exit: evidence table with passed/failed/deferred, no unsupported feature silently marked done.
7. **Release preparation, when authorized.** Review exact frontend diff, exclude unrelated local changes, record checks and rollback revision, then follow the existing release process. No release is part of the current planning request. Later production acceptance must include authenticated representative role checks; HTTP 200 alone is insufficient.

Each delivery slice should be reviewable on its own. No estimates are committed until baseline screenshots and representative data reveal the actual remaining delta.

## Validation matrix and definition of done

| Area | Required evidence |
| --- | --- |
| Route coverage | All 61 entries checked against registry and independent page; direct entry, refresh, in-app navigation and Back/Forward for dynamic routes/query context. Record retain/refine and outcome per row. |
| Roles/data | Admin, Parent with zero/one/multiple children, Student with/without enrolments; authorized and denied access; long names; no cross-account/child cache leakage. Use disposable local fixtures without production mutations. |
| Viewports | 1440px desktop, 1024px tablet, 390px phone and 320px narrow screen; 200% zoom/reflow; no whole-page horizontal overflow. Source tables/images get intentional local scrolling. |
| Interaction | Keyboard-only navigation, visible focus, accessible names, dialog/sheet focus return, Escape/dirty dismissal, touch controls and reduced motion. Test content under sticky headers/actions and mobile keyboard. |
| Async states | Initial load, background refresh, success, empty, no-results, denied, stale, failure, retry and long-running action. Failed save retains recoverable user input and allows retry. |
| Critical workflows | Account/enrolment safeguards; document and assessment release gates; exam timer/submission; practice drafts/attachments; protected textbook assets; flashcard session/rating; Tutor voice/session; avatar persistence; Community follow/block/report. |
| Automated checks | Existing frontend tests, typecheck, lint and production build. Explicitly lint shared component directories when changed. Add targeted behavior tests for changed state/navigation/guards; avoid tests that merely repeat markup. |
| Visual comparison | Before/after for each changed layout family and each distinct role workflow. Confirm consistent dividers/spacing and a visibly warmer, coordinated palette without reduced legibility or lost actions. Verify contrast, colour-independent states and restrained reading/review surfaces. |
| Change boundaries | No backend/API/schema changes; no new private-data fetch scope, fabricated metrics, fixture imports or added product services. Diff reviewed for unrelated local work. |

Completion means every planned row is accepted or explicitly retained with evidence, all required scenarios pass, and deferrals have a reason and separate follow-up. Attendance remains catalogue-only; carousel remains optional/reference-only unless an approved useful placement emerges. These are deliberate design decisions, not incomplete attempts to force all 27 families into live pages.

## Implementation checklist

- [ ] Reconcile older UI acceptance and create route evidence checklist.
- [ ] Inspect data contracts and classify paged/complete lists.
- [x] Verify three pilot screens and shared component decisions.
- [x] Define and document shared colour tokens; validate dashboard/profile previews, contrast and colour-independent status meanings.
- [x] Apply the coordinated colour treatments across the route inventory without changing learning/source content.
- [ ] Complete Admin route refinements and acceptance.
- [ ] Complete Parent route refinements and acceptance.
- [ ] Complete profiles, security, Community and shell acceptance.
- [ ] Complete Student learning and summary route refinements.
- [ ] Verify all dynamic, query-selected and boundary states.
- [ ] Pass checks and record device/keyboard evidence.
- [ ] Update catalogue guidance and plan status; prepare separately authorized release.

## Delivery record — 20 October 2026

The implementation deliberately builds on the already delivered route refresh rather than replacing existing workflows. Shared colour tokens, compact card/header treatments, navigation/focus states, responsive filters, profile surfaces and Community presentation now apply across the role shells. Explicit subject accents are wired to real subject IDs in subject selection, learning summaries, textbook tiles, flashcard decks and Parent course rows. Saved Student avatars now appear in Parent overview/course summaries. An empty-enrolment guard prevents the Subjects screen dereferencing an absent active subject. The catalogue Cards family demonstrates the production composition.

No backend/API/schema/dependency changes. The preexisting local sidebar hover work is excluded from this release. Existing timers, publication gates, Community services, filtering/pagination contracts and protected resource requests are retained.

### Verification

- 90 frontend tests pass, including route/role/query boundaries, avatar, profile, review presentation and two new palette/identifier checks. All six decorative text palettes pass 4.5:1 on their soft surface and white.
- Typecheck, frontend lint, explicit shared-component lint and production build pass. Existing large-chunk/static-classification advisories remain.
- Signed-in local Admin: overview, Accounts table/create drawer, all content/category queues, coverage/mapping and all supporting administration routes inspected. Admin content routes and seven supporting routes fit at 390px; Accounts fits at 320px. Supporting administration routes also checked at 1280px; Accounts/dashboard checked at 1440px.
- Signed-in local Parent: all ten routes checked at 390px, dashboard at 1440px, assignment drawer and selected-child context inspected. Original avatar renders in learner summary.
- Signed-in local Student: overview, subjects, tutors, practice entry, exams entry, progress, study plan, textbook entry, flashcards, profile, security and Community checked at 320px. Subject/profile screenshots confirm no page-wide overflow. Avatar save returned success and restored focus to Edit avatar.
- Catalogue production colour examples verified at 390px. Production checkout/services checked healthy before release.
- Local disposable QA accounts supplied an enrolled Student linked to a Parent; no production learner records were changed for testing.

### Acceptance retained for follow-up

The local database has no published textbooks, exam documents, active assessed sessions or populated review queues. Therefore this release does **not** claim new populated end-to-end verification of dynamic document/reader/flashcard routes, exam timers, publication/reassessment, Tutor streaming/voice, Community follow/block/report mutation permutations or multi-child switching. Existing route tests and unchanged domain implementations provide regression coverage, not a substitute for these scenarios. A local visual-media request also displayed its existing recoverable error state; resolving its service/data prerequisite is outside the presentation delta.

The native dirty-editor confirmation caused browser automation to stall; dismissal recovered the interface, but retain/discard focus behavior is not marked passed. The guard itself is unchanged. The earlier route-refresh acceptance remains open rather than being silently closed. Full adoption-plan acceptance stays ongoing until these cases are checked with representative content; deployment of the verified presentation delta is separately authorized.

See [route delivery coverage](../../frontend/docs/UI-ADOPTION-DELIVERY.md) for the per-route disposition and retained data contracts.

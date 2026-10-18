# UI refresh implementation and verification

Implemented 18 October 2026. Frontend only. Production release authorized by the project owner on 18 October 2026; deployment evidence is recorded by the production release procedure.

## Design and structure

PreSkool informed the grouped navigation, profile summaries and quiet dashboard cards. Academy informed subject cards and the prominent next learning action. ShadcnStore informed the collapsible application shell and table controls. These are original AKURU components; no template code or assets were copied.

`components/portal` contains the shared shell and widgets. `app/portal.css` scopes layout, semantic colours, spacing and responsive rules to the portal. Existing shadcn/Base UI primitives remain the foundation. The original component catalog and its anchors remain available within `/ui-features`.

The Admin-only preview uses synthetic fixtures and local state: role tabs, child selection, weekly activity, state examples, detail drawers, notification read status, directory layout, form validation, and resource search/filter/sort/pagination. The filter toolbar stays local to its table rather than adding an abstraction with only one consumer. Profile controls open the learner detail drawer; the header identifies the current account.

## Live data mapping

| Widget | Existing data and definition |
| --- | --- |
| Learner summary | Selected authorized `students` entry; grade, term and enrolled subject IDs |
| Questions this week | Selected learner's attempts from local Monday midnight through now |
| Active assignments | Selected learner's assignments where `completed` is false, earliest due first |
| Awaiting review | Selected learner's attempts with `needs-review` status |
| Subject performance | Sum of marks / sum of possible marks for checked, reviewed or approved attempts in that subject; unavailable without valid marks |
| Recent learning | Latest four selected learner attempts |
| Student next action | Earliest open assignment, otherwise first enrolled subject |
| Admin metrics | Existing account, learner, textbook and official-paper arrays |

No attendance, study-time, streak, mastery or trend inference was added. Weekly charts, notifications and topic completion examples remain preview-only. Existing routing, API clients, query scoping, mutations, study/exam state and navigation guards are retained. Live admin tables retain their existing data and pagination behavior.

## Verification

- Node 22: lint, TypeScript, all 62 tests and production build passed.
- Focused tests cover sibling isolation, week boundaries, assignment ordering/nonmutation and weighted marks including missing/zero/unreviewed values.
- Desktop browser checks used a loopback synthetic API fixture, with no backend connection: Parent and Student overview data, sibling switching, Parent assignment navigation and Admin overview.
- Preview checks: child/period changes, empty/no-child/error states, table search/filter/sort/pagination, notification read/unread, local validation and detail drawers. Escape closes the drawer and restores focus to its opener.
- Signed-out and non-Admin responses both show the access restriction. The local request log contains GET requests only.
- Legacy anchor restoration, reduced-motion rules, chart text equivalents, coarse-pointer 44px controls and visible-focus styles are implemented. A sticky-header focus overlap found during review was corrected and visually rechecked.
- No backend, API contract, dependencies, deployment configuration or infrastructure changes. Existing favicon changes were preserved.

## Remaining acceptance checks

Phone/tablet visual inspection is still pending: the browser viewport tool returned successfully but the rendered viewport remained 1280px, including in a new tab. Responsive rules are implemented, but this is not evidence of successful device validation. Check 390px and 768px widths, mobile drawer focus, long learner names, large counts and table scrolling in a working responsive browser before final visual acceptance. End-to-end writes against a real backend were intentionally not performed; existing workflow contracts pass.

Build emits a large-chunk advisory and Vinext's static-route classification advisory; neither fails the build.

## Compact presentation refinement — 18 October 2026

A second visual review of the PreSkool Student and Parent templates focused on small presentation details: tighter card composition, inline metric icons, compact navigation, restrained shadows and readable muted metadata. AKURU now defaults to Compact view across the real role portals and the reference workspace. The header toggle switches to Comfortable view and saves only this display preference in browser local storage; storage failure falls back to in-memory state.

Shared cards now have separate header and body containers, a subtle tinted header, and a one-pixel divider. Compact view reduces outer gutters, card padding, section gaps, sidebar row height, summary avatars and table rows while preserving text sizes and 44px coarse-pointer navigation targets. Existing panel headings receive a divider, active navigation has a blue inset marker, and resource tables have subtle row hover feedback. No vendor assets or code were copied.

Verified on the actual local Admin portal and `/ui-features`: compact rendering, card borders/body spacing, toggle state and preference persistence after reload. Lint, typecheck, 62 frontend tests, production build and diff whitespace checks pass. Phone/tablet visual acceptance remains subject to the previously recorded browser viewport limitation. No backend changes, commit or deployment.

## Official-paper review workspace refinement — 18 October 2026

The exam-document question review now uses shared page/metric/card components, an inventory status summary, collapsible blockers and source setup, a filtered question navigator, a persistent save/previous/next toolbar, and a source viewer beside the editor. Paper, scheme, report and textbook evidence have tabs; comparison mode expands the paper and scheme together. Source page controls and exact-block linking retain the existing APIs. Linked evidence switches the source tab and page, opens the extracted-block disclosure and brings the block into view.

Question wording, subpart review and visuals occupy separate cards. Crop controls are collapsed until opened or an existing crop is adjusted. The duplicate generic Admin heading and secondary navigation are omitted only on this specific workspace route. At narrow widths the source viewer stacks ahead of the editor and the question inventory becomes a horizontally scrollable list. Styles are scoped in `app/paper-review.css`.

The first saved question opens after loading. All save operations retain `expectedRevision`, status, evidence and approval validation. Question switching and portal navigation honour dirty drafts; in-flight saves prevent navigation and disable editor fields. Dirty detection includes edits made before entering a question number. No new backend endpoints, schema, authorization or publication behavior is introduced.

Verification: lint, typecheck, production build and 66 frontend tests pass, including focused cases for inventory filtering, previous/next boundaries, cancelled discards, saving locks and unnumbered drafts. Interactive browser inspection was unavailable for this follow-up; responsive rules and source-tab wiring were reviewed in code. Production activation uses the reviewed release scripts, encrypted backups and post-release route/asset/service checks.

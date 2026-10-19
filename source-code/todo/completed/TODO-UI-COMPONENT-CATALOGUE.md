# AKURU UI component catalogue

Status: [x] Completed and deployed to AKURU production on 19 October 2026.
Created: 19 October 2026
Destination: `/ui-features`

## Objective and scope

Expand AKURU’s existing Admin UI reference into a searchable, interactive component catalogue covering all 27 supplied PreSkool references. Components should be reusable in future Admin, Student and Parent work without introducing a second visual system.

This roadmap is frontend-only: no database migrations, backend changes, new API contracts, production records or new permissions. Keep the existing `getUiFeaturesAccess()` Admin gate. Role previews are sample presentations, not permission changes. Attendance, presence, awards and workspace operations are demonstrations; implementing real product workflows is separate work.

Implementation and production deployment were authorised on 19 October 2026. Preserve the existing uncommitted local sidebar hover changes. This catalogue extends the ongoing UI refresh without changing or closing that roadmap’s outstanding work.

## Research and existing AKURU foundations

All 27 linked pages below were opened and their rendered examples and descriptions reviewed in the browser. The text retrieval service could not access the reference site, so the browser was used instead. The workspace layout was also visually inspected, and the basic modal was opened to inspect its content/actions. This is a design inventory, not a claim that every reference interaction has passed accessibility testing.

The references share compact controls, pale surfaces, fine borders, divided card headers, grouped actions, small metadata and responsive compositions. Adapt those ideas to AKURU’s existing blue palette, typography, icons and original artwork. Do not import PreSkool HTML/CSS/JavaScript, Bootstrap, fonts, photos or other vendor assets.

Repository findings:

- `frontend/app/ui-features/page.tsx` checks Admin access, then combines `UiFeaturesExperience`, `WorkflowPatterns` and `ComponentGallery`.
- `frontend/features/ui-reference/experience.tsx` already provides role/scenario previews, hash navigation, sample dashboards, notifications and learning/workflow patterns. Preserve these.
- `frontend/features/ui-reference/component-gallery.tsx` already shows foundations, cards, forms, badges, progress, tables and tabs. Some specimens intentionally have disabled controls; distinguish these from the new interactive demos.
- `frontend/components/ui/` contains Base UI/shadcn primitives for most requested families. Carousel already uses the installed Embla library. Reuse their actual APIs; do not copy Bootstrap data attributes or assume Radix APIs.
- `frontend/components/portal/workspace.tsx` already supplies `FilterToolbar`, `EditorDrawer`, `AdvancedPanel`, `LoadingState` and `ErrorState`.
- `frontend/components/portal/dashboard-widgets.tsx` supplies dashboard cards, metrics, skeletons, empty states and shared learning patterns.
- `frontend/components/portal/badges.tsx`, `frontend/lib/badges.ts` and `frontend/docs/badge-system.md` are the authoritative semantic badge system. Extend its catalogue coverage rather than inventing a replacement.
- `frontend/components/portal/student-avatar.tsx` renders AKURU’s original character artwork and initials fallback. Catalogue examples must use this renderer for Student characters.

## Catalogue experience

Retain the current workspace and pattern previews. Expand “Foundations & catalog” with a component browser containing five groups:

| Group | Families |
| --- | --- |
| Foundations & layout | Typography, Grid, Images, Cards |
| Identity & feedback | Avatar, Badges, Alerts, Progress, Placeholders, Spinner |
| Actions & navigation | Buttons, Button groups, Breadcrumb, Links, List group, Pagination, Nav & tabs |
| Disclosure & overlays | Accordion, Collapse, Dropdowns, Modals, Offcanvas, Popovers, Tooltips |
| Composed patterns | Workspace, Attendance |

- Add search by family, variant and use case, visible result counts, clear/reset and no-results state.
- Give every family a stable shareable anchor such as `/ui-features#ui-catalog-alerts`. Preserve existing anchors and reconcile the current hash handler so catalogue links select the correct group before scrolling. Browser Back/Forward should restore the selected family; avoid overwriting every history entry.
- On desktop use a compact component index and content panel; on mobile use an accessible selector/search panel. Keep all 27 entries inside the reference workspace rather than adding them to production role navigation.
- Each family shows purpose, recommended AKURU variants, working preview, reset control, usage guidance, import path and a minimal copyable example. Source examples must reflect real exported components and props.
- Clearly label “Reusable component”, “Composed pattern” and “Visual specimen” in catalogue documentation. Interactive controls must produce visible local results; disabled controls must explain why.
- Mount only the selected family’s heavy demos. Keep deep links usable and avoid loading every carousel, overlay and chart on initial entry.
- Keep technical usage guidance in this Admin reference; do not expose it in Student or Parent product flows.

## Design baseline: per-reference implementation inventory

Each entry records what was found, the proposed AKURU adaptation and its acceptance check. Core variants are required. Decorative options are explicitly scoped below rather than silently omitted.

### 01. Alerts

Reference: [PreSkool Alerts](https://preskool.dreamstechnologies.com/html/ui-alerts.html)

Observed: contextual alerts, dismissal, inline links, borders, extended content, icons and a live alert trigger.

- Reuse `ui/alert.tsx` for information, success, warning and error specimens; add dismissible and action-bearing compositions with AKURU icons and readable text.
- Demonstrate “Sample document ready”, “Review required” and a local retry error. Include title/body/divider, link and icon variants, plus create/dismiss/reset interaction.
- Use polite status announcements for routine updates and assertive alerts only for urgent errors. Initial catalogue rendering must not announce every specimen at once.
- Acceptance: close affects only its example; live alert can be recreated; links/actions work locally; long text wraps without hiding Close.

### 02. Accordion

Reference: [PreSkool Accordion](https://preskool.dreamstechnologies.com/html/ui-accordion.html)

Observed: standard, flush, bordered and arrowless arrangements, including an initially expanded panel.

- Reuse `ui/accordion.tsx`; show bordered FAQ, flush card sections, single-open and multiple-open examples. Include an optional arrowless specimen while retaining a clear expanded-state cue.
- Use sample exam instructions and review guidance. Explain when independent collapse is more appropriate.
- Acceptance: Enter/Space and supported arrow navigation work; state and panel relationships are announced; collapsed content leaves the tab order; resetting restores initial state.

### 03. Avatar

Reference: [PreSkool Avatar](https://preskool.dreamstechnologies.com/html/ui-avatar.html)

Observed: image/initial/icon avatars, sizes, shapes, groups and overflow counts, rings, status/count overlays, hover overlays, subject icon tiles, AI and medal tiles.

- Combine `ui/avatar.tsx` and the existing `StudentAvatar` renderer for original Student characters, generic initials/image fallback, compact/top-bar/profile sizes, circular/rounded frames and stacked groups with accessible overflow details.
- Show labelled status/count overlays as sample-only states; do not imply live presence. Subject tiles should use existing icons; AI/medal tiles are visual specimens, not new achievement or AI status features.
- Include missing/broken image, long name and keyboard-accessible edit overlay cases. Keep character proportions and head/neck distinction intact.
- Acceptance: same character configuration renders consistently across sizes; informative avatars have names and decorative duplicates are hidden from assistive technology; overflow control reveals sample members.

### 04. Badges

Reference: [PreSkool Badges](https://preskool.dreamstechnologies.com/html/ui-badges.html)

Observed: solid/soft/outline/rounded/gradient badges, metadata chips, state labels, priorities, notification counts, icon/avatar combinations, long/disabled labels and dark/RTL specimens.

- Expand the existing `StatusBadge`, `MetadataBadge`, `CountBadge` and `ReviewBadge` gallery, preserving semantic tone mapping, icons, xs/sm density and accessible true counts behind `99+`.
- Show button/tab/avatar counts, unread markers with text equivalents, long labels, unknown-state neutral fallback and priority specimens. Keep filter-chip dismissal as a button composition, not an interactive status label.
- Demonstrate gradient/decorative finishes only in an explicitly optional visual-specimen area; semantic product status stays on the established badge system. Add isolated dark-surface and RTL previews without introducing a global theme switch.
- Acceptance: no duplicate state palette; no colour-only meaning; documented contrast and wrapping rules continue to pass existing badge tests.

### 05. Buttons

Reference: [PreSkool Buttons](https://preskool.dreamstechnologies.com/html/ui-buttons.html)

Observed: compact 34px actions and 28px small actions, solid/outline/soft/rounded buttons, 3D/gradient/animation finishes, labelled icons, sizes, toggle/disabled states and full-width controls.

- Reuse `ui/button.tsx` and `ui/toggle.tsx`; document primary, secondary, outline, ghost and destructive usage, compact toolbars, icon-only labels, full-width mobile and pending states.
- Use local “Preview”, “Reset” and sample submission actions. Add optional rounded, soft and restrained 3D/gradient specimens without changing defaults application-wide; respect reduced motion for animated samples.
- Acceptance: correct button versus link semantics; disabled/pending prevents repeat activation; toggle exposes pressed state; compact visual size still provides accessible target area.

### 06. Button groups

Reference: [PreSkool Button Group](https://preskool.dreamstechnologies.com/html/ui-buttons-group.html)

Observed: date ranges, grid/list/board selection, full-width status filters, sizes, icon groups, mixed/nested dropdown actions, check/radio groups, toolbars and vertical groups.

- Reuse `ButtonGroup`, `ToggleGroup`, radio/checkbox primitives and dropdown menu. Show independent actions separately from exclusive and multiple selection.
- Build working period, density and list/card switches, a split action and vertical group; retain an accessible group label and selected-state output.
- Acceptance: exclusive choices cannot disagree, keyboard behavior matches control semantics, joined borders/focus rings remain visible and narrow layouts do not clip controls.

### 07. Breadcrumb

Reference: [PreSkool Breadcrumb](https://preskool.dreamstechnologies.com/html/ui-breadcrumb.html)

Observed: text and home-icon trails with slash, arrow and alternate separators.

- Reuse `ui/breadcrumb.tsx` for text/icon and compact overflow trails; show a sample Admin → Exam documents → Review hierarchy using reference anchors rather than production record links.
- Acceptance: named navigation, ordered hierarchy, non-link current item with `aria-current="page"`, decorative separators hidden and long trails usable on mobile.

### 08. Cards

Reference: [PreSkool Cards](https://preskool.dreamstechnologies.com/html/ui-cards.html)

Observed: directory/profile composition, flush panels, accent headers, media/horizontal cards, subtitles/actions, header/footer divisions, bordered/filled finishes, equal-height groups and a table card with toolbar/footer.

- Reuse `ui/card.tsx` and `DashboardCard`; define a compact divided header/body/footer composition with optional leading accent, actions and description.
- Show course, original-avatar profile, review summary, image, horizontal and equal-height card examples; use a workspace card for the toolbar/table/footer composition.
- Acceptance: separators align across variants, header actions wrap, nested cards avoid doubled spacing, long titles/images remain contained; shared defaults do not change unrelated routes accidentally.

### 09. Carousel

Reference: [PreSkool Carousel](https://preskool.dreamstechnologies.com/html/ui-carousel.html)

Observed: slides-only, previous/next controls, indicators, captions, crossfade, individual intervals, disabled touch swiping and dark controls.

- Reuse `ui/carousel.tsx`/installed Embla for static slides, controlled slides, indicators/captions and a compact course-card carousel using local assets.
- Default to manual advancement. Include an opt-in timed specimen with pause/resume and cleanup; respect focus, hover, reduced motion and background visibility. Treat crossfade as an optional isolated finish; avoid adding a carousel library just for it. Document touch-enabled/default and non-drag options.
- Acceptance: keyboard/buttons/touch can reach every slide; indicators announce selection; offscreen slide actions are not keyboard traps; captions remain readable and pause stops movement.

### 10. Collapse

Reference: [PreSkool Collapse](https://preskool.dreamstechnologies.com/html/ui-collapse.html)

Observed: link/button triggers, horizontal disclosure and independent/multiple targets.

- Reuse `Collapsible` and assess `AdvancedPanel`/`WorkspaceToggle` before adding a wrapper. Show help text, horizontal secondary tools and two independent regions plus a toggle-both action.
- Acceptance: triggers reflect controlled regions accurately; multiple triggers stay synchronised; hidden controls cannot receive focus; horizontal example stacks safely on small screens.

### 11. Dropdowns

Reference: [PreSkool Dropdowns](https://preskool.dreamstechnologies.com/html/ui-dropdowns.html)

Observed: solid/outline/soft and split triggers, sizes, active/disabled items, menu headers/text/forms, start/end/up/center positions, offsets and different dismissal modes.

- Reuse `ui/dropdown-menu.tsx` for action menus, grouped/icon items, checked/radio choices, disabled items and split-button actions; pair filter forms with `Popover` rather than forcing form fields into menu-item semantics.
- Show alignment/collision behavior and compact variants; dark/rounded finishes may be isolated specimens. Keep standard predictable dismissal as the recommended behavior; any manual-close specimen must have an explicit Close control.
- Acceptance: keyboard entry/navigation/Escape/focus return work; edge menus stay inside viewport; selecting a sample action reports its result without real mutation.

### 12. Grid

Reference: [PreSkool Grid](https://preskool.dreamstechnologies.com/html/ui-grid.html)

Observed: breakpoint/container reference, 12-column span combinations, gutters, nesting and ordering guidance.

- Document AKURU’s actual CSS/Tailwind layout conventions instead of importing Bootstrap breakpoints. Build equal/unequal/nested responsive grids, dashboard spans and compact/default gutter comparisons.
- Provide a contained width selector for previewing layouts; label the reference’s 12-column system as inspiration, not a requirement for every AKURU screen.
- Acceptance: 320px through wide desktop reflows without page overflow; source order remains logical; breakpoint documentation matches implementation.

### 13. Images

Reference: [PreSkool Images](https://preskool.dreamstechnologies.com/html/ui-images.html)

Observed: rounded/circular/thumbnail/pill crops, left/center/right alignment and captioned figures.

- Use native images plus `AspectRatio` where useful; show responsive media, contain versus cover, shapes, captions and missing-image fallback using AKURU-owned/local sample artwork.
- Acceptance: explicit dimensions reserve space, informative alt text/figure captions are appropriate, crops do not distort images and broken examples recover accessibly.

### 14. Links

Reference: [PreSkool Links](https://preskool.dreamstechnologies.com/html/ui-links.html)

Observed: contextual colours, opacity, underline colour/offset/opacity and hover/focus treatments; the page itself notes contrast risks.

- Define recommended inline, quiet secondary, icon/external and button-style links with AKURU’s existing Link integration. Keep ordinary text links recognisable and keyboard focus visible.
- Show underline/offset options; low-opacity styling is a documented “avoid” comparison rather than a usable low-contrast default. Keep examples on local anchors; identify any external destination/new window.
- Acceptance: every enabled link has a meaningful destination, contrast passes and actions use buttons rather than dead `href="#"` placeholders.

### 15. List group

Reference: [PreSkool List Group](https://preskool.dreamstechnologies.com/html/ui-list-group.html)

Observed: basic/active/disabled/flush/numbered/horizontal lists, linked/button rows, rich content, counts, checkbox/radio choices and dense data rows/cards with leading accents.

- Compose semantic lists from `ui/item.tsx`, separators, badges, original avatars and form primitives. Show notifications, subjects and document rows with secondary text, trailing values/actions and compact/default density.
- Acceptance: selectable, actionable and static rows have correct distinct semantics; no nested interactive targets; disabled rows cannot activate; rich rows and counts wrap on mobile.

### 16. Modals

Reference: [PreSkool Modals](https://preskool.dreamstechnologies.com/html/ui-modals.html)

Observed: basic/static-backdrop, long-scroll, grid/accordion content, modal transitions, form examples, sizes, centered/fullscreen and positioned variants. Opened the basic example: title, scrollable content, Close and Save actions.

- Reuse `Dialog` and `AlertDialog` for a sample edit form, confirmation, long scroll, size/fullscreen and two-step replacement examples. Do not introduce login/signup workflows from the template.
- Show non-dismissible-backdrop only as a documented special case with an explicit accessible escape route; prefer Sheet for edge-positioned panels. One modal is active at a time.
- Acceptance: labelled dialog, initial/trapped focus and return focus, Escape/close behavior, internal scrolling, background inertness and local form validation all work.

### 17. Offcanvas

Reference: [PreSkool Offcanvas](https://preskool.dreamstechnologies.com/html/ui-offcanvas.html)

Observed: four placements, backdrop/body-scroll options and dark panel.

- Reuse `Sheet` (already supports sides) and existing `EditorDrawer` for details, filter and sample-edit drawers. Include left/right/top/bottom specimens, long content and a contained dark-surface example.
- Recommend modal backdrop/scroll-lock for editing; keep any nonmodal details example clearly differentiated with appropriate focus behavior.
- Acceptance: close/Escape/focus restoration work, overlay stacking is consistent with existing portal navigation, mobile panels fit viewport and background scrolling behaves as documented.

### 18. Pagination

Reference: [PreSkool Pagination](https://preskool.dreamstechnologies.com/html/ui-pagination.html)

Observed: default/icon, active/disabled, size/alignment, boxed/rounded/soft and decorative colour/gradient options.

- Reuse `ui/pagination.tsx`; add controlled sample pagination with first/previous/next/last, ellipsis, page size and result summary. Show compact/rounded/soft specimens; keep gradient finish optional.
- Acceptance: current page announced, boundary controls truly disabled, filtering/page-size changes clamp/reset page correctly, empty and one-page cases are correct, mobile count/navigation fit.

### 19. Popovers

Reference: [PreSkool Popovers](https://preskool.dreamstechnologies.com/html/ui-popovers.html)

Observed: click, focus-dismiss and hover variants, four directions, coloured surfaces and disabled-trigger wrappers.

- Reuse `ui/popover.tsx` for contextual explanation and a small local filter form, plus placement/tone specimens. Prefer click/focus for useful content; hover-only samples require keyboard/touch alternatives.
- Acceptance: Escape/outside dismissal and focus restoration work; interactive content is keyboard reachable; disabled-trigger explanation is reachable through an appropriate wrapper or adjacent help control.

### 20. Progress

Reference: [PreSkool Progress](https://preskool.dreamstechnologies.com/html/ui-progress.html)

Observed: levels/colours/heights, labels, striped/animated/gradient/stacked bars and additional thin meters, circular gauges, sparklines and metric captions.

- Reuse `Progress`/label/value and existing metrics/charts for labelled study completion, processing stages, thin/segmented meters and gauge/trend specimens. Preserve distinctions between completion, scores and unknown-duration processing.
- Add isolated striped/gradient examples with motion controls. Use existing chart tooling or small semantic CSS/SVG compositions for gauge/sparkline; do not add a chart dependency.
- Acceptance: values/min/max are valid and visible; stacked segments have a textual breakdown; unknown progress is indeterminate; animated samples respect reduced motion; no fabricated live percentages.

### 21. Placeholders

Reference: [PreSkool Placeholders](https://preskool.dreamstechnologies.com/html/ui-placeholders.html)

Observed: matched loaded/loading cards, variable widths/sizes/colours, glow/wave motion, skeleton shapes and card/list/table/media skeleton layouts.

- Reuse `Skeleton` and `DashboardSkeleton`; show a loaded/loading switch for card/list/table/avatar layouts with matching dimensions. Provide neutral default plus static/pulse specimens, not a new skeleton system.
- Acceptance: loading container exposes busy state and one concise announcement; skeletons are decorative/nonfocusable; replacement content does not significantly shift layout; static reduced-motion state works.

### 22. Workspace

Reference: [PreSkool Workspace](https://preskool.dreamstechnologies.com/html/ui-workspace.html)

Observed: wrapping compact toolbar, search, quick filters/counts, removable chips, summary strip, sortable/selected/pinned table rows, card view, bulk-selection toolbar, details, paging, upload target, loading/empty states and component usage reference.

- Assemble a sample exam-document workspace from `FilterToolbar`, `Table`, badges, `EditorDrawer`, metrics, skeleton/error/empty components and the catalogue’s action/navigation controls.
- Make search, quick/advanced filters, chips, sorting, selection, density, table/card view, details, page size and pagination work on one shared in-memory fixture set. Counts and selected-record actions must agree after filtering/paging; explicitly document whether selection is current-page or all-filtered.
- Include initial loading, retryable error, empty dataset, no matches, long labels and disabled actions. Clear filters restores records. Show compact toolbar and card header/footer divisions.
- Demonstrate upload with a local file-input/dropzone preview only: file name/size/type validation and reset, no upload. Any export is limited to sample fixtures. Do not add messaging, public share, real deletion/import or identity-card issuance; the reference’s ID-card entry remains a documented future composition, not required AKURU functionality.
- Acceptance: complete sample journey from filtering to selecting a row and opening details works by keyboard; mobile card view preserves the same data/actions; loading/error/empty states have clear recovery and no backend calls beyond the existing access check.

### 23. Attendance

Reference: [PreSkool Attendance](https://preskool.dreamstechnologies.com/html/ui-attendance.html)

Observed: intensity/absence heatmap with legend and empty grid, ordered sessions, present/late/absent marking rows and locked states, comparison percentages, completion rail and headline rate composition.

- Add an explicitly labelled “Sample attendance patterns” composition with fictional learners/dates, daily cells and legend, session list, labelled P/L/A choices, locked register, comparison bars, rate block and marking-completion rail.
- Keep attendance terminology in this specimen. Separately show how the generic activity grid/session list could later support study activity without treating a missed study day as an absence.
- Mark changes update only local sample counts/percentages and reset on demand. Expose full words to assistive technology; offer a textual date/status summary rather than colour-only cells. Define denominators, unmarked days, non-session days and zero-data behavior.
- Acceptance: changing one sample mark updates all derived totals coherently; locked rows cannot change; no-data is not displayed as 0% attendance; heatmap values are readable without colour. This delivers no actual attendance tracking, analytics policy or backend persistence.

### 24. Spinner

Reference: [PreSkool Spinner](https://preskool.dreamstechnologies.com/html/ui-spinner.html)

Observed: border/growing indicators, colours, placement, sizes and loading buttons.

- Reuse `ui/spinner.tsx` and assess the existing workspace loader for consistent composition. Show inline/page/centered and button-pending examples with a restrained optional grow specimen.
- Acceptance: one accessible loading label, no repeated nested announcements, disabled pending action prevents double submission, bounded local simulation completes and can reset; reduced motion retains a static meaningful status.

### 25. Nav & tabs

Reference: [PreSkool Nav & Tabs](https://preskool.dreamstechnologies.com/html/ui-nav-tabs.html)

Observed: compact line/icon tabs, raised/outlined counted chips, icon tiles, solid/rounded/bordered/justified and left/right vertical tabs with disabled choices.

- Reuse `ui/tabs.tsx` for underline, segmented, counted, icon and vertical specimens; demonstrate sample Overview/Activity/Resources content. Keep actual route navigation as links and filter selection as a choice group when no tabpanel exists.
- Acceptance: keyboard orientation/selection behavior is correct, labelled panels match triggers, disabled tabs cannot activate, count badges stay readable and mobile overflow does not hide focused tabs.

### 26. Tooltips

Reference: [PreSkool Tooltips](https://preskool.dreamstechnologies.com/html/ui-tooltips.html)

Observed: inline-link, disabled-wrapper, hover, four-direction, rich-format/click and contextual-colour specimens.

- Reuse `Tooltip`/provider for compact icon explanations, inline terms, positions and disabled-action reasons. Use Popover for interactive/richer content rather than putting actions into a tooltip; never inject arbitrary HTML from reference examples.
- Acceptance: mouse and keyboard focus reveal concise text; Escape dismisses; label exists independently of tooltip; essential help remains available on touch; content is not clipped by cards or viewport edges.

### 27. Typography

Reference: [PreSkool Typography](https://preskool.dreamstechnologies.com/html/ui-typography.html)

Observed: eyebrow/title/subtitle panel hierarchy, headings/display scales, inline emphasis/edits/highlights, lists, abbreviations, quotes/citations, alignment and nested definition lists.

- Document AKURU’s actual heading/body/caption/label scale and line height, with compact panel headings, muted metadata, tabular numbers and long educational text.
- Include semantic inline elements, ordered/unordered/nested lists, abbreviations, quotes/citations and responsive definition lists. Display specimens should not create multiple competing page-level h1 elements merely to show sizes.
- Acceptance: meaningful heading hierarchy, readable line lengths/contrast, zoom/reflow without clipping and no global typography changes leaking from catalogue specimens.

## Implementation structure

Proposed paths are relative to `source-code/`; confirm naming against the repository before implementation.

| Location | Responsibility |
| --- | --- |
| `frontend/app/ui-features/page.tsx` | Preserve access gate; compose catalogue alongside current previews |
| `frontend/features/ui-reference/experience.tsx` | Extend existing design-system navigation/hash coordination |
| `frontend/features/ui-reference/component-gallery.tsx` | Consolidate overlapping specimens; avoid duplicate foundations |
| `frontend/features/ui-reference/catalogue/registry.ts` (new) | 27 typed entries: stable id, title, group, keywords, source, variants and loader |
| `frontend/features/ui-reference/catalogue/catalogue.tsx` (new) | Search/index, selected family, empty state and navigation |
| `frontend/features/ui-reference/catalogue/example-card.tsx` (new) | Divided compact header, preview, reset, guidance and code example |
| `frontend/features/ui-reference/catalogue/examples/` (new) | Small family modules; split workspace/attendance from basic examples |
| `frontend/features/ui-reference/fixtures.ts` | Deterministic fictional records; no production names or account data |
| `frontend/components/ui/` | Reuse primitives; add narrowly scoped backwards-compatible variants only when necessary |
| `frontend/components/portal/` | Extract reusable AKURU compositions only where a real shared contract is useful |
| `frontend/features/ui-reference/catalogue/catalogue.css` (new) | Scoped catalogue layout/specimens, using existing design tokens |
| `frontend/docs/ui-component-catalogue.md` (new) | Usage/import matrix, variant rules, accessibility and future adoption guidance |
| `frontend/tests/` | Focused behavioral/semantic coverage using the established test setup |

Do not put all examples into `experience.tsx`, add a new app shell or alter shared defaults solely to match a reference screenshot. Audit portal CSS selectors and overlay portals for leakage before extending primitives. Example source and previews must use the same exported implementations; clearly distinguish reusable exports from fixture-only demo handlers.

## Original delivery sequence (completed through the implementation below)

### Phase 1 — catalogue foundation

- Reconcile overlap with ongoing UI plans, record current screenshots and preserve unrelated local work.
- Establish registry with exactly 27 families, grouped navigation, search, stable anchors and reusable example frame.
- Set compact spacing/header rules using AKURU tokens; document approved defaults versus optional specimens.
- Add deterministic fixtures and local reset/scenario conventions. Retain Admin gate and current dashboard previews.

### Phase 2 — foundations, identity and actions

- Deliver Typography, Grid, Images, Cards, Avatar, Badges, Buttons, Button groups, Breadcrumb, Links and List group.
- Consolidate existing gallery duplication and publish real import/usage examples.
- Verify compact density, long content, contrast and mobile rendering before building composed patterns.

### Phase 3 — interactions, feedback and navigation

- Deliver Alerts, Accordion, Collapse, Dropdowns, Modals, Offcanvas, Pagination, Popovers, Progress, Placeholders, Spinner, Nav & tabs, Tooltips and Carousel.
- Check focus management, overlay collision/stacking, independent instance IDs, hidden content and reduced motion.
- All enabled demo actions have visible, reversible, fixture-only outcomes.

### Phase 4 — composed patterns

- Deliver coherent sample Workspace and Attendance experiences using the completed families.
- Exercise all populated/loading/error/empty/disabled/long-content states and document future reuse boundaries.
- Add recommended-use examples for Admin review lists, Student learning cards and Parent summaries without changing those live routes.

### Phase 5 — acceptance and handover

- Verify every reference entry has working coverage or an explicitly documented optional visual specimen; no unexplained omissions.
- Complete checks below, update usage documentation and implementation record, and present local results for review.
- Move plan to ongoing when implementation starts and completed only after acceptance passes. Commit/push/deployment require an explicit implementation delivery instruction; do not infer them from this planning request.

## Validation and completion criteria

- All 27 families can be found by search and direct link. Old UI-feature anchors and role/scenario previews still work. Unknown anchors/search terms recover cleanly.
- Check signed-out, Student, Parent and Admin access behavior; role-preview controls never bypass the Admin gate.
- Verify at 320/390px mobile, tablet and desktop; 200% zoom/reflow; long translated-style labels; collapsed/expanded sidebar and mobile navigation. Contain intentional table overflow rather than allowing page overflow.
- Keyboard walkthrough: search → family → demo → overlay → close → reset. Check visible focus, labels, heading structure, selected/disabled states and screen-reader announcements. Do not assume primitives alone guarantee correct composition.
- Contrast follows WCAG AA: normal text 4.5:1, large text 3:1 and relevant UI boundaries/state cues 3:1. Meaning is available beyond colour. Respect reduced motion and touch use; aim for at least 24px targets with sufficient spacing and larger primary mobile actions.
- Meaningful automated checks cover catalogue registry uniqueness/coverage, search/deep-link selection, workspace filter/sort/page/selection consistency, attendance calculations/reset, and important accessible control states. Use the existing frontend test approach; avoid snapshot tests that only repeat implementation markup.
- Run frontend tests, typecheck, lint and production build; review new component directories explicitly because the current lint script only names `app`, `features` and `lib`. Resolve console warnings and timer/listener cleanup issues.
- Confirm no backend/schema/API/environment/deployment files changed and no demo network mutations occur. Check browser network behavior in the reference experience.
- Capture representative local screenshots: catalogue search, compact cards/actions, original avatars/badges, an open overlay, workspace desktop/mobile, attendance, loading and no-results states.
- Deliver a reusable import/variant matrix, known limitations and a suggested adoption backlog. A later task can select live routes for adoption; building the catalogue does not automatically rewrite every AKURU page.

Completion means a usable component library and reference workspace, with consistent AKURU styling and reliable demonstrations. It does not mean implementing the template’s school-management product features.

## Implementation and acceptance record — 19 October 2026

The 27-family catalogue is implemented in `frontend/features/ui-reference/catalogue`, integrated under the existing Admin gate and design workspace. Search, family links, history restoration, resets, usage examples and lazy example modules are present. Existing previews and old anchors remain. The responsive index becomes a compact native selector on mobile.

- [x] All 27 families opened and rendered in the local browser.
- [x] Live alert creation; workspace filter/selection/preview/details; attendance mark changes (67% → 75%) and no-data behavior verified interactively.
- [x] Modal required-field validation, two-step preview, 288px dialog at a 320px viewport, Escape dismissal and menu expansion verified.
- [x] Search no-results and recovery verified. Rapid family switching exposed a hash-navigation race, corrected by synchronous history updates and notification.
- [x] Desktop and 390px/320px mobile checks. Key mobile families and workspace card view have no document overflow. Fixed an existing reference table’s absolute-label overflow with a scoped positioning rule.
- [x] Signed-out access returns 401; disposable local Student and Parent accounts return 403; local Admin catalogue opens.
- [x] Frontend tests: 88 passed. Typecheck, lint and production build passed. Build retains the existing large-chunk/static-route-classification advisories. No browser error/warning logs observed in the checked local session.
- [x] No backend/schema/API/dependency/environment changes. CSV preview reads file metadata only.
- [x] Production release `0bb95bb880f135a77a66c2d96a99ac4266a010c9` deployed with encrypted backups; release acceptance passed. `/ui-features` returns 200, signed-out catalogue API returns 401, services/timers and routing/security headers passed, no failed systemd units. Alembic stayed at `0012_student_community`; no new upgrade operations.

The prospective checklist above is the design baseline. Its optional decorative permutations are resolved through the variant policy in `frontend/docs/ui-component-catalogue.md`: AKURU ships useful accessible compositions, rather than every Bootstrap colour/animation/dismissal permutation. In particular crossfade plugins, hover-only essential content, arbitrary tooltip HTML, authentication modals and non-dismissible overlays are not promoted. Attendance/presence/award specimens remain fictional. This is not a formal screen-reader or accessibility certification.

Release evidence on the production server: `/data/akuru/release-evidence/deployed-0bb95bb880f135a77a66c2d96a99ac4266a010c9-20261019T173239Z.txt`. The existing dependency lockfile was unchanged. Installation reported 22 dependency audit findings (4 moderate, 15 high, 3 critical); those pre-existing dependency issues require a separate upgrade review, not an automatic force upgrade in this UI release.

The earlier local sidebar-hover changes remain uncommitted and were excluded from this release. The three disposable local QA accounts and their test sessions/events were removed after verification.

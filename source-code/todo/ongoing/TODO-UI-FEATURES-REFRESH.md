# AKURU UI features and portal presentation refresh

**Created:** 2026-10-18
**Status:** Implemented; final responsive visual acceptance pending. Commit and production deployment authorized on 18 October 2026.
**Scope:** Frontend only. `/ui-features` and shared presentation adopted in existing portals.

## Outcome

Turn the Admin-only UI reference into an interactive design preview for AKURU. Use PreSkool as the main presentation reference, Academy for learning progress, and ShadcnStore for application navigation and reusable UI patterns. Preserve AKURU's blue identity and mascot while improving hierarchy, readability and navigation.

## Backend boundary

- No backend code, database schema, migrations, endpoints, authentication, permissions, background jobs, infrastructure or API contract changes.
- The preview uses synthetic fixtures and local React state. Preview actions must not create, update, delete or send real records or messages.
- Preserve the existing `getUiFeaturesAccess` check and Admin-only access behavior. A role preview selector changes sample content only; it never changes permissions or impersonates a user.
- Later portal adoption uses existing authorized API responses and existing mutation behavior. Preserve query keys, identity scoping, session-expiry handling and private-cache clearing.
- Show unavailable metrics as unavailable, or omit them. Do not invent mastery, study duration, attendance, streaks or trends from unrelated data.
- If a proposed widget requires new backend data or behavior, leave it as a labelled demo and record the dependency as separate future work. It is outside this plan.

## References and adaptation

- Primary: [PreSkool](https://preskool.dreamstechnologies.com/) and its [student dashboard](https://preskool.dreamstechnologies.com/html/student-dashboard.html): role dashboards, grouped navigation, profile summaries, schedules, notification panels and consistent card composition.
- Supporting: [Academy](https://shadcnuikit.com/dashboard/academy): learning paths, subject progress and a clear next learning action.
- Supporting: [ShadcnStore](https://github.com/shadcnstore/shadcn-dashboard-landing-template): collapsible navigation, table controls and shared application structure. Its Base UI/base-nova foundation aligns with AKURU.
- Reimplement selected patterns with AKURU's existing shadcn/Base UI, Tailwind, Lucide and chart components. Avoid importing a Bootstrap theme or replacing the application framework. Check applicable licenses before reusing template code or assets.
- Prioritize learning and family workflows. School fees, payroll, transport and other unrelated ERP modules are outside scope.

## Phase 1 — Inventory and visual foundation

- [x] Inventory the current UI features sections and reusable components; retain useful existing examples.
- [~] Reference patterns reviewed and documented; phone/tablet visual validation remains pending (viewport tool limitation).
- [x] Define tokens for colours, text hierarchy, spacing, borders, corner radii, shadows and semantic statuses.
- [x] Define compact and comfortable layouts where needed; keep controls and metadata readable.
- [x] Scope preview styles so changes do not unintentionally restyle existing portal screens.
- [x] Establish shared loading, empty, error and unavailable-data presentations.

**Deliverable:** Foundation examples and a consistent component presentation within `/ui-features`.

## Phase 2 — Preview navigation and application layout

- [x] Introduce a compact header with breadcrumbs, preview search, sample notifications and profile controls.
- [x] Add grouped desktop sidebar navigation, collapsed mode and a mobile drawer.
- [x] Organize sections as Dashboard previews, Layouts, Learning widgets, People, Data & workflows, Forms & feedback, and Foundations.
- [x] Preserve existing section anchors or provide compatible destinations for existing reference links.
- [x] Label all fixtures as demo data and make the preview context visible.
- [x] Keep the Admin portal return link functional through the existing route system.

**Deliverable:** Navigable preview layout with usable desktop and mobile states.

## Phase 3 — Parent dashboard preview first

- [x] Build a child switcher and student summary with grade and enrolled subjects.
- [x] Add weekly learning summary cards, upcoming assignments and assessments awaiting review.
- [x] Add subject performance and recent activity with clearly defined sample metrics.
- [x] Make child selection update all related sample widgets consistently.
- [x] Open assignment and assessment details in a local preview drawer.
- [x] Demonstrate one-child, multiple-child, no-child, no-activity and overdue states.
- [x] Review this complete screen as the first design checkpoint before extending the visual direction.

**Deliverable:** Interactive PreSkool-inspired family dashboard, adapted to AKURU's workflows.

## Phase 4 — Student and Admin previews

- [x] Student: compact welcome, prominent Continue studying action, subject progress, study agenda and recent results.
- [x] Use Academy's learning-path presentation where it makes progress easier to understand.
- [x] Admin: operational summary, documents awaiting review, processing statuses, recent activity and a content table.
- [x] Add Student/Parent/Admin preview tabs without altering authentication or authorization.
- [x] Keep role-specific content focused; avoid presenting all application features in every dashboard.

**Deliverable:** Three coherent dashboard previews using one visual system.

## Phase 5 — Working component patterns

- [x] Extract reusable components as justified by the previews: PortalShell, PageHeader, MetricCard, StudentSummaryCard, ChildSwitcher, SubjectProgressCard, AssignmentList, ActivityTimeline and FilterToolbar.
- [x] Demonstrate local fixture search, subject/date filters, sorting and pagination.
- [x] Add list/grid switching for an appropriate directory example.
- [x] Add notification panel read/unread interactions and accessible detail drawers/dialogs.
- [x] Add form validation and loading/empty/error/populated state selectors.
- [x] Use existing chart components for accessible charts with text summaries and labelled values.
- [x] Ensure demo controls work locally or clearly explain unavailable behavior; avoid unexplained dead buttons.

**Deliverable:** Reusable components and interactive examples ready for portal integration.

## Phase 6 — Verification and preview acceptance

- [x] Run the frontend's existing lint, typecheck, build and appropriate tests. Add focused tests only for meaningful new behavior.
- [x] Verify keyboard navigation, visible focus, drawer/dialog focus restoration and screen-reader labels.
- [x] Check colour contrast, reduced motion, touch target sizes and charts that do not rely on colour alone.
- [~] Desktop and empty-data inspection complete. Phone/tablet, long-name and large-count visual checks remain pending; see verification notes.
- [x] Verify signed-out/non-Admin access remains denied and preview interactions make no mutation requests.
- [x] Confirm the implementation diff contains no backend, deployment or API contract changes.
- [x] Review the complete parent preview and then the remaining previews before production portal adoption.

**Acceptance:** `/ui-features` presents responsive, interactive, clearly labelled previews with consistent AKURU styling and unchanged access controls. No backend changes are needed to complete this milestone.

## Phase 7 — Subsequent adoption in existing portals

Implemented following desktop preview review under the user’s end-to-end authorization; final responsive acceptance is tracked below.

- [x] Map each widget to existing response fields, metric definitions and destinations before connecting real data.
- [x] Adopt shared layout and components in the parent overview first, then student home, then Admin navigation/tables.
- [x] Preserve existing URLs, role visibility, form submissions and business rules.
- [x] Retain server filtering/pagination where already present; local fixture controls must not become client-wide downloads of private datasets.
- [x] Keep study sessions, exam timers, answers, textbook-reader position and unsaved-work navigation guards intact.
- [~] Existing route/data workflows and desktop presentation checked; phone/tablet verification remains pending.
- [x] Defer widgets with missing data rather than expanding backend scope.

## Expected frontend locations

- `source-code/frontend/app/ui-features/page.tsx`: preview composition and access boundary.
- `source-code/frontend/components/`: shared preview and portal components, using existing `ui/` primitives.
- `source-code/frontend/app/globals.css` and/or scoped frontend styles: tokens and presentation.
- `source-code/frontend/features/`: later adoption within existing role workflows.
- `source-code/frontend/tests/`: focused behavior coverage where warranted.

## Completion tracking

- [~] UI reference implementation complete; responsive visual acceptance remains pending.
- [~] Portal adoption implemented; final responsive checks remain pending.
- [x] Move the roadmap through `ongoing` and `completed` according to the delivery-plan conventions; keep this document updated as work progresses.

## Delivery record

See [implementation and verification notes](../../frontend/docs/UI-REFRESH.md) for field mappings, completed checks and the remaining browser limitation. All 62 tests, lint, typecheck and production build pass. No backend changes, commit or deployment. The roadmap stays ongoing until responsive acceptance is verified.

### Compact presentation follow-up

- [x] Revisit PreSkool spacing, card composition and navigation details.
- [x] Provide shared Compact/Comfortable view controls with a browser-local preference; Compact is the default.
- [x] Separate shared card headers and bodies with a tinted header and divider.
- [x] Tighten metric cards, navigation, table rows and page spacing; preserve readable text and touch targets.
- [x] Verify the actual local Admin workspace, preview, persisted toggle and all frontend checks.

### Production release authorization — 18 October 2026

The project owner authorized committing and deploying the frontend refresh. Local lint, typecheck, 62 tests and production build pass. Use the reviewed release scripts with encrypted backups and post-release health checks. The outstanding responsive visual check remains recorded and does not represent a completed acceptance test.

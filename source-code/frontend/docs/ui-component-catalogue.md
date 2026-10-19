# UI component catalogue

The Admin-only `/ui-features#ui-catalogue` workspace contains 27 searchable component families. Direct links use `#ui-catalog-<id>`; Back/Forward restores the selected family. Existing dashboard and role previews remain available. Only selected example modules are mounted; workspace and attendance load separately.

## Reuse

Start with `components/ui` primitives, then the semantic `components/portal/badges.tsx`, original `StudentAvatar`, workspace helpers and dashboard widgets. The reference's **Usage example** disclosure contains actual import/prop examples; copy actions report failure when clipboard access is unavailable. Demo state and fixture handlers are not product services.

The registry is `features/ui-reference/catalogue/registry.ts`; each entry has a stable id, group, searchable description and primitive mapping. The example frame owns its separated header, body, guidance and source. Catalogue CSS is scoped; the sole existing-reference fix contains absolute screen-reader labels within its scrollable table.

## Variant policy

AKURU uses blue primary actions, quiet secondary actions, semantic status tones, original characters and compact divided cards. Rounded, soft, ledged/gradient buttons, decorative AI/medal tiles and a dark badge surface are isolated specimens. There is no new global dark mode, presence service or achievement system. Tooltip help has an inline touch alternative; use popovers for richer content and dialogs/sheets for editing.

The library adapts the requested families rather than cloning every Bootstrap permutation. Menu directions, dialog sizes, sheet placements, tab orientations, button states and the most useful compositions are working demos. Redundant template colour permutations, Bootstrap-only attributes, automatic timed intervals per slide, crossfade plugins, arbitrary tooltip HTML, login/signup modals and non-dismissible overlays are deliberately not promoted as product patterns. Standard predictable dismissal, manual carousels and readable semantic colours are recommended. Carousel timing is opt-in, pauses on focus/hover and respects reduced motion.

## Sample data boundaries

All new interactions use local React state. A workspace demonstrates search, status/subject filters, removable filters, summary strip, sort, current-page selection, selection across filtered pages, density, table/cards, details, pagination and recovery. Changing filters clears selection. CSV selection only checks the name/type limit and previews file metadata; no file bytes are uploaded or parsed. No real deletion, messaging or sharing action is present.

Attendance is explicitly fictional. Present and Late count as attended; the rate denominator includes only marked learners. No marked learners means **No data**, not 0%. The completion rail counts all sample learners, including unmarked ones. The fixed October history and comparison groups are separate illustrative datasets, not derived from today's editable register. A textual date/status list accompanies the heatmap. The locked row cannot be edited through its mark controls. A global reset/no-data scenario resets the entire fixture.

The existing Admin access API is unchanged. No database, backend, schema, environment or production account changes are required. Student/Parent adoption later must use authorised data through the existing role boundaries; catalogue role previews do not grant access.

## Accessibility and validation

Use real labels, named groups, selected/pressed states and visible focus. Keep compact controls at least 24px with spacing; mobile primary controls are larger. Skeletons are nonfocusable and reserve space. Default alert specimens are not all live announcements; user-triggered updates are polite. Dialogs/sheets use the existing Base UI focus and dismissal primitives. Colour supplements text, never replaces it.

Automated tests cover all 27 registry entries and hashes, search, filtering/sorting/page boundaries, and attendance calculations including absent/unmarked/no-data. Run `npm test`, `npm run typecheck`, `npm run lint`, and `npm run build` from `frontend`. Run lint explicitly on component directories when editing shared primitives because the existing lint script names app/features/lib.

## Later adoption

1. Adopt the workspace toolbar/selection/footer composition in document lists after reviewing each route's data contract.
2. Adopt divided cards and labelled progress in learning summaries and Parent overviews.
3. Use the existing shared avatars and semantic badges consistently.
4. Design attendance or study-activity persistence separately before exposing it as a real learner feature.

No live route is automatically redesigned merely because a specimen exists here.

## Import and family index

| Family | Entry id | Foundation |
| --- | --- | --- |
| Alerts | `alerts` | `alert` |
| Accordion | `accordion` | `accordion` |
| Avatar | `avatar` | `avatar` |
| Badges | `badges` | `../portal/badges` |
| Buttons | `buttons` | `button` |
| Button groups | `buttons-group` | `button-group` |
| Breadcrumb | `breadcrumb` | `breadcrumb` |
| Cards | `cards` | `card` |
| Carousel | `carousel` | `carousel` |
| Collapse | `collapse` | `collapsible` |
| Dropdowns | `dropdowns` | `dropdown-menu` |
| Grid | `grid` | `CSS grid` |
| Images | `images` | `aspect-ratio` |
| Links | `links` | `next/link` |
| List group | `list-group` | `item` |
| Modals | `modals` | `dialog` |
| Offcanvas | `offcanvas` | `sheet` |
| Pagination | `pagination` | `pagination` |
| Popovers | `popovers` | `popover` |
| Progress | `progress` | `progress` |
| Placeholders | `placeholders` | `skeleton` |
| Workspace | `workspace` | `../portal/workspace` |
| Attendance | `attendance` | `./activity-patterns` |
| Spinner | `spinner` | `spinner` |
| Nav & tabs | `nav-tabs` | `tabs` |
| Tooltips | `tooltips` | `tooltip` |
| Typography | `typography` | `Semantic HTML` |

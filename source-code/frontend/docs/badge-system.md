# Shared AKURU badges

Implemented 19 October 2026 after reviewing the PreSkool badge reference. AKURU uses original components and its existing Lucide icons; no vendor styles or assets were imported.

## Components and rules

`components/portal/badges.tsx` owns `StatusBadge`, `ReviewBadge`, `MetadataBadge` and `CountBadge`. `lib/badges.ts` maps explicit normalized status values to a tone, readable label and decorative icon. `app/badges.css` owns geometry, palette, compact size and wrapping, including badges on public sign-in/password screens outside the portal shell.

- Success/green: approved, completed, published, ready, enrolled and visible.
- Warning/amber: pending, awaiting review, partial review, correction required and approval pending.
- Danger/red: failed, rejected, blocked, overdue and high severity.
- Information/blue: processing, submitted, in progress and one-way following.
- Neutral/slate: draft, hidden, inactive, archived and metadata.
- Accent/purple: following each other.

Unknown states remain neutral. Match complete status values rather than substrings: incomplete, unpublished, unreviewed and not-ready states must never accidentally receive success styling. Labels remain visible alongside icons; colour alone never carries state. Domain wrappers may supply a precise label (for example, Parent reviewed on existing assessment results) without renaming backend statuses. Tutor low-severity notices use a neutral override; low quota remains an attention warning.

Metadata is outlined and quieter than status. Counts use their real data source, cap the displayed number at 99+, and expose the full count in the accessible label. Existing zero-count visibility rules are retained. Badges are noninteractive; original buttons and filters retain their behavior. No presence, online tracking, achievements or new activity events are introduced.

## Page audit and integration

| Area | Applied change |
| --- | --- |
| Shared status wrapper | Existing Admin, Parent, Student, Flashcard and review consumers use the shared status component. |
| Dashboard widgets | Assignment status uses explicit mapping; subject chips use compact metadata. |
| Accounts and profiles | Enrolled status, public visibility with eye/hidden icon, security and role metadata. |
| Community | Subject tags, Follows you/Following/Following each other status, unread Feed counts. |
| Admin document queues | Processing/review/publication status uses the same component. |
| Textbook and source review | Required/partial/complete review indicators, final confirmation and launch readiness retain their original decisions and labels. |
| Official-paper review | Question navigation uses compact status badges and marks metadata; selection, filters and review decisions are unchanged. |
| Parent assignments and Student practice | Completion status and question/collection/marks metadata. |
| Tutors | Voice/source/preset metadata, quota state and safety severity. |
| Media and evaluations | Separate resource type metadata from record state. |
| Navigation and notification controls | Shared count styling with accessible full counts. |
| UI reference | Live component specimens now show the same status, visibility, relationship, metadata and count variants as the actual application. |

Pages without status, metadata or count information keep their existing content; ordinary paragraphs, error alerts, progress bars and form labels are not converted into badges.

## Validation

The full local release gate passed with 85 frontend tests, 195 backend tests (one PostgreSQL-only concurrency test skipped in the default fixture), type checking, lint and production build. Badge tests cover false-success regressions, review-state rendering, safe text escaping, count bounds/full accessible count, and text contrast of at least 4.5:1 for all six palettes. Focused frontend checks were rerun after the final public-page styling and domain-label adjustment.

Signed-in local browser acceptance used disposable accounts: Student profile visibility/enrolment, live unread count, Community metadata and mutual-follow badge, plus the Admin UI reference gallery. A long public name wrapped at a 390px viewport with no horizontal overflow. Test accounts were removed after acceptance.

This release changes frontend presentation and tests/documentation only. No backend, API, schema, enrolment, privacy or notification behavior changes are included. Production activation follows the existing encrypted-backup, staged-build, rollback and release-acceptance process.

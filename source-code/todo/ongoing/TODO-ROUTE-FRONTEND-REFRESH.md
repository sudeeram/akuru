# Route-wide frontend refresh

Started 19 October 2026. Authorized scope: implement all entries in the [route audit](../../frontend/docs/ROUTE-UI-AUDIT.md), locally. Preserve unrelated favicon changes. Initial implementation was local only. The user subsequently authorized committing and deploying this frontend refresh to AKURU production.

- [x] Routing: shared registry, strict matching, nested destinations, validated URL presentation state and breadcrumbs.
- [x] Shared UI: page headers, divided cards, filtering, editing drawers, focus mode and loading/error states.
- [x] Admin: overview/readiness, accounts, document queues/reviews, textbooks/topic focus, coverage/mapping, blueprints and assessment audit.
- [x] Operational Admin: Flashcards, AI account routing, Tutor presets/allowances/history, media, evaluation gates and operations.
- [x] Parent: consistent child context, pending reviews first, assignment list/create separation, courses, library and progress.
- [x] Student: subjects, focused practice/exams/Tutor/reader/Flashcard experience, progress, agenda and security.
- [x] UI reference: real workflow patterns and acceptance scenarios.
- [x] Verify route families, role boundaries, navigation state and frontend checks; record every audited entry's implementation coverage.
- [ ] Populated signed-in role/device/keyboard acceptance: needs representative local learner/document data; see audit delivery notes. Native discard-dialog automation also remains unverified.

Backend-dependent additions in the audit (new global search/aggregation, server pagination where unsupported, new notifications, cross-device preferences) remain outside this frontend-only scope. Existing endpoint behavior and authoritative publication checks are retained.

Validation: typecheck, lint, 71 tests and production build pass. Local Admin queue/drawer/search checked in browser at desktop and phone widths. Release authorization: commit and deploy the frontend refresh; exclude the preexisting favicon/layout edits. Preserve the backend runtime and database schema.

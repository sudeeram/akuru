# Published textbook re-review and republication

**Requested:** 2026-10-03
**Started:** 2026-10-03
**Status:** Core workflow implemented locally; controlled publication and remaining usability checks are in progress.

An Admin must be able to open a published textbook review page, create an editable revision, change several page labels or content blocks, inspect the complete revised document, and publish the Topic once. Students continue to see the current version until that explicit publication succeeds. Existing citations, flashcard evidence and assessment snapshots must continue to resolve to their original reviewed source.

## 1. Immutable review revision

- [x] Add a separate review copy derived from the exact published document version, preserving its original PDF and page assets without re-running OCR.
- [x] Clone reviewed page labels, reading order, blocks, scientific notation, captions and provenance into the copy. Never mutate rows referenced by a published Topic content version.
- [x] Allow only one active review copy per source, with creator/time metadata and an audit event; reject a second concurrent draft.
- [x] Keep the published source and editable copy separate in the Admin document/source lists; retain old versions for historical citations.
- [x] Reject direct edits to published page labels, blocks and final-review confirmation.

## 2. Edit and review several sections

- [x] On the review page, add **Create review revision** for a published text source, then route to the editable copy.
- [x] Allow edits on several pages and blocks before publication with **Save all changed sections**.
- [ ] Add an atomic batch-save endpoint, clear unsaved-change indicators and optimistic concurrency checks for simultaneous Admin edits.
- [ ] Preserve the existing page-level controls, scientific superscript/subscript editor, figure/caption pairing and source-page preview in the draft.
- [ ] Show a change summary against the published version, including affected pages, blocks, labels and captions.
- [x] Let the Admin inspect the complete revised document and explicitly confirm its final content hash before publication.

## 3. Publish and downstream effects

- [ ] Require extraction quality, exact-source provenance, topic readiness and retrieval preflight against the draft. Keep the old Student version live while any gate fails.
- [x] Publish one new immutable Topic content version and retrieval index from the approved copy; atomically supersede the previous active version.
- [ ] Refresh the Student textbook version/date and citations. Preserve old source bytes, reviewed text, assessment evidence and historical flashcard sessions.
- [ ] Flag decks and learning material grounded in changed passages for Admin re-evaluation; do not silently rewrite approved cards or invalidate completed Student work.
- [ ] Document a rollback path to the prior published Topic version.

## 4. Verification and release

- [x] Test multiple edits in one review copy, published-source immutability and Topic republication through the authenticated API.
- [ ] Add browser-flow coverage, draft cancellation and save-conflict handling.
- [ ] Test historical citation immutability, Student visibility before and after publication, cross-subject authorization, Admin-only mutations, CSRF and concurrent edits.
- [ ] Run local backend/frontend tests and production-style acceptance before deployment.
- [ ] Update the Admin guide with the draft, review, preflight, publication and flashcard follow-up steps.

**Done when:** A published source can be corrected on its review page through a separate draft, multiple sections can be saved together, and one explicit Topic republication releases the reviewed result while all historical evidence remains unchanged.

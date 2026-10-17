# Official-paper visual and draft-review improvements

Created: 2026-10-17

Status: planned — open for additional findings from Admin review

## Problem and pilot example

June 2025 Chemistry 1C Question 1 depends on an atom diagram and a table on PDF page 3. AKURU retains the rendered source page, but the diagram is not isolated or linked to the draft question. The automatically detected visual regions cover most of the page and are unsuitable as the student-facing diagram. A page reference alone does not prove that the diagram and table will be legible in an assessment.

## Planned work

- [ ] Inspect how vector diagrams, embedded images and tables are extracted from official paper PDFs. Distinguish a useful bounded visual from a whole-page or margin crop; never auto-approve a broad region as a question asset.
- [ ] Add an Admin review control to select a precise rectangular crop from a source PDF page, preview it at student size, adjust or replace it, and attach it to the correct question or subpart. Preserve the exact document version, page and crop coordinates.
- [ ] Let the Admin attach an existing valid extracted visual when it is already correct. Show the selected visual beside the question wording and make removal/replacement explicit.
- [ ] Provide accessible alternative text for each approved question visual. Keep the original PDF page available as evidence, while displaying the approved crop in the student question.
- [ ] Review table handling separately: preserve rows, columns, labels and answer spaces where feasible; otherwise allow a verified page crop with accessible table description. Ensure the student can read and answer from it without opening an Admin source viewer.
- [ ] Add approval blockers for questions that refer to a required diagram or table but have no verified student-visible visual. Do not publish a page-wide crop as a substitute without an explicit Admin review decision.
- [ ] Test visual ownership, document-version changes, crop bounds, Admin-only asset access, immutable assessment snapshots, mobile scaling, keyboard access and screen-reader alternatives.
- [ ] Use Chemistry 1C Question 1 as the acceptance case: isolate its atom diagram, verify the part (b) table, link both to the correct question/subpart, and preview the complete question as a student before approval.

## Release boundary

This is a plan only. The current 1C/2C question proposals remain unapproved and unavailable to students. Additional findings from the paper review can be added here before implementation.

## Additional finding: save incomplete question reviews

The current marking-point textarea expects `code|kind|text|optional dependency` on every non-empty line. It parses each keystroke immediately into a marking-point object. A plain pasted marking-scheme sentence can become an overlong `code` with an empty `text`, producing the generic API error “code: String should have at most 30 characters; text: String should have at least 1 character.” The same problem can occur while typing a new line before all fields are complete. This blocks the intended save-and-resume review workflow.

- [ ] Allow an Admin to save an incomplete question as `unreviewed` or `needs_correction`, then reopen it with all entered work intact. Reserve strict marking-point, source and coverage completeness checks for `ready_for_approval` and `approved` transitions.
- [ ] Replace the keystroke-parsed pipe-delimited textarea with structured marking-point rows (short code, kind, wording and optional dependency), or preserve raw draft input separately until a row is complete. Do not silently rewrite partially typed text.
- [ ] Give each invalid row a specific inline message and identify the affected question/subpart. Explain the code length and required wording in plain language instead of displaying generic schema errors.
- [ ] Keep server-side validation for approved marking points. Test save, reload and edit of partial drafts; adding a row incrementally; pasting plain marking-scheme text; and later approval after correction.
- [ ] Verify existing pilot proposals and previously saved review rows still load and remain editable after the editor change. Do not change their approval state or publish them as part of this work.

## Additional finding: show exact-evidence link state

The current **Link this block** action adds a source block to the selected subpart's draft evidence, but the block list does not visibly change. An Admin cannot tell whether the click worked or which blocks are already linked.

- [ ] Show a clear `Linked to part (a)`-style state on every linked paper, scheme or report block for the currently selected question and subpart. Keep the state correct when switching parts, pages or questions and after saving/reloading the review.
- [ ] Change the action to `Remove link` for a linked block, with an immediate visible update. Prevent duplicate links and identify unsaved changes separately from saved links.
- [ ] Show a compact count/list of linked blocks beside the selected subpart, with page numbers and enough text to identify each one. Make those entries navigate to or reveal the source block.
- [ ] Provide screen-reader announcements and keyboard-operable controls for link/unlink actions; do not rely on color alone.
- [ ] Test repeated clicks, switching between subparts, save/reload, stale source versions and a failed save so the UI never implies an unsaved link was persisted.

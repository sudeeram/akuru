# Admin review workspace for official exam papers

Created: 2026-10-17

Started: 2026-10-17
Status: ongoing

Implementation progress: An Admin-only, version-bound workspace, question and subpart editor, exact source links, published-topic coverage decisions, draft-bank seed guard, approval gates and official-draft preparation are implemented with integration tests. The production pilot intake of the licensed 1C/2C PDFs and hands-on review of all 16 questions remain separate Admin content work; they are not represented as completed by the software release. The current workspace freezes on a changed source PDF and does not yet offer a version-to-version carry-forward flow.

## Goal and pilot

Let an AKURU Admin review an official question paper, its **exact** marking scheme and any examiner report in one workspace, question by question and subpart by subpart. The Admin must be able to save incomplete work, correct extraction, retain diagrams and tables, approve exact source evidence and topic coverage, and see what still blocks release. A saved or approved question must not become Student-visible merely because its own review is complete.

Use the June 2025 Pearson Chemistry `1C`/`2C` pilot to prove the workflow: `1C` Question 3 is wholly supported by currently published Topic 2, while `2C` Question 1 mixes supported, uncertain and outside-coverage parts. The private pilot bank under `/data/akuru/pilots` is **not** an official AKURU document import or release. Licensed PDFs and rendered pages stay out of Git. The current findings are in `source-code/docs/pearson-chemistry-production-coverage-review.md`.

## Existing capabilities to retain

- Admin-only document upload, extraction, original-PDF and asset access, with course/subject checks.
- Official-material draft proposal/save/publish APIs, source block and asset validation, immutable published versions, audit events and full-inventory checks.
- Published paper/scheme identity checks and equal-mark, complete-scheme reconciliation.
- Student invisibility until the relevant official source and its exact approved scheme pass release rules.

The existing generic **Official material review** form is a starting point, but it is not a practical side-by-side, per-question review workflow. Do not weaken its full-source publication checks to accommodate a partially reviewed pilot question.

## Step 0 — Design the review state and import boundary

- [ ] Trace the current `Document`, `DocumentVersion`, extraction-block/asset, `OfficialMaterialVersion`, question, scheme and examiner-comment lifecycle. Record exactly when each becomes queryable by Students, assessment generation and retrieval.
- [ ] Define a paper review workspace as an Admin-only draft tied to exact source document **versions**, session, component, variant and hashes. Companion scheme/report links must point to the matching paper; missing reports remain explicitly absent and may be attached later.
- [ ] Define statuses for each question and subpart: `unreviewed`, `needs_correction`, `ready_for_approval`, `approved` and `excluded`. Track wording, visual, exact rubric, examiner evidence and coverage decisions separately. `Excluded` requires a reason and must never silently reduce the declared source inventory.
- [ ] Define `supported`, `partial_or_uncertain` and `outside_current_coverage` as review decisions. Keep **intrinsic syllabus/topic mapping** distinct from **current Student grade/term eligibility**; publication of new textbook topics can change the latter without rewriting the historical source decision.
- [ ] Specify versioning and invalidation: edits to a source document version, diagram, question wording, scheme point or topic mapping reopen the affected approvals; published Student attempts retain their original snapshot.

## Step 1 — Build durable Admin-only review data and APIs

- [ ] Add a reviewed migration for the workspace, per-question/subpart decisions, reviewer attribution/timestamps, source links and audit history. Use source-version and subject constraints; separate provisional decisions from published `OfficialMaterialVersion` rows.
- [ ] Add authenticated, CSRF-protected Admin APIs to create/load a workspace, save one question or subpart at a time, update review decisions, link exact scheme/report entries, and obtain progress plus blocking reasons. Support optimistic concurrency so two Admin sessions cannot silently overwrite edits.
- [ ] Require source locations to resolve to pages/blocks in the selected question-paper, scheme or report version; visual assets must belong to the selected paper version. Preserve page and bounding-box references even when OCR text is corrected.
- [ ] Validate question/subpart labels, parent-child hierarchy, marks and total paper marks; prevent duplicate labels, mismatched companion identities, cross-subject topic mappings and links to unpublished topics.
- [ ] Keep draft review data out of Student, Parent, mock-generation, retrieval and assessment endpoints. Authorize every review and asset API on the server, not through frontend hiding alone.

## Step 2 — Build the review workspace in the Admin portal

- [ ] Add an Exam Documents review entry point with a paper list, completion counts and clear paper/scheme/report matching state. Resume an existing draft at the last reviewed question.
- [ ] Show the original question page, exact mark-scheme page, relevant examiner-report page and published textbook evidence side by side, with source-page navigation and zoom. Do not present lexical suggestions as approved curriculum mappings.
- [ ] Provide editable shared stem and subpart prompts; retain multiple-choice boxes, equations, tables, answer instructions and diagrams. Let the reviewer select/approve a paper asset or page crop and provide accessible text where needed.
- [ ] Review marking points, accepted alternatives, dependencies, follow-through, notation, maximum marks and examiner advice for each subpart. Make missing or mismatched evidence visible before approval.
- [ ] Let Admin mark a part as supported, uncertain or outside current coverage, link one or more **same-subject published topics**, and explain the decision. Display whether **every required part of the whole question** is covered; a partial question cannot become term-eligible.
- [ ] Save draft changes without declaring the full paper complete. Show per-question and per-paper progress, validation errors, reviewer identity and a readable change history.

## Step 3 — Controlled intake of the pilot material

- [ ] Upload the exact `1C` and `2C` question PDFs, matching schemes and reports through the Admin document intake in an isolated AKURU environment first. Verify hashes, year/session/component/variant, page counts and extraction. Do not import the private JSON pack directly into published official-material tables.
- [ ] Add a controlled Admin-only import/seed path to use the draft bank as **proposals** after the real PDFs exist. Resolve every proposed page, block and asset against those uploaded document versions; reject missing or ambiguous matches. Never fabricate source IDs, diagrams or a completed inventory.
- [ ] Load the 87-part coverage triage as reviewer suggestions only. Import the OCR-cleaned `1C` Q3 candidate as an unapproved draft; keep the other parts unapproved and mark the mixed `2C` Q1 decisions explicitly.
- [ ] Reconcile all 16 top-level questions, 87 subpart labels and 180 marks with the source PDFs and exact schemes before any paper publication is considered.

## Step 4 — Approval and release gates

- [ ] Allow an Admin to approve a single question's wording, visual, rubric, report evidence and mapping while the rest of the paper stays draft. Approval is an internal review milestone, **not** Student release.
- [ ] Publish an official paper only after its complete source inventory is attested; publish its exact scheme only after every published question has matching maximum marks and approved marking points. An optional examiner report can follow later with exact paper identity.
- [ ] Keep whole-paper original-exam practice unavailable until the complete published paper and scheme pass; allow a reviewed question to be considered for a separately controlled topic-practice release only if that product path is deliberately implemented and tested. No implicit single-question release through a partially published paper.
- [ ] Recheck Student cumulative coverage at assessment selection time. One unsupported required part holds the whole question out of term mocks, even if other parts have Topic 2 matches.
- [ ] Make release decisions auditable and reversible through a new version, without rewriting old attempts or deleting source evidence.

## Step 5 — Evaluation and acceptance

- [ ] Test Admin-only access, CSRF, concurrent edits, wrong paper/scheme/report pairings, cross-subject topics, stale source versions, invalid assets/blocks and a missing examiner report.
- [ ] Test the `1C` Q3 path with both paper pages, its chromatogram, 11 marks, exact scheme dependencies/alternatives, examiner comments and Topic 2 textbook evidence. Verify it can be fully reviewed while the 1C paper remains Student-invisible.
- [ ] Test `2C` Q1 with a supported part, three uncertain parts and outside-coverage parts. Verify its whole-question coverage gate remains closed despite lexical suggestions and related Topic 2 passages.
- [ ] Test full-paper and term-mock eligibility, Student/Parent isolation, immutable attempt snapshots, source citations and report attachment after initial paper review.
- [ ] Run a keyboard and mobile accessibility pass on page viewers, tables, diagrams, status controls and progress summaries.
- [ ] Prepare an Admin walkthrough showing how to upload sources, correct a question, review the scheme, choose a diagram, approve topic evidence and identify remaining release blockers. Only after isolated-environment acceptance, plan a reviewed production rollout; no automatic deployment or Student release is part of this TODO.

# Pearson iGCSE Chemistry past-paper intake

Started: 2026-10-05

## Goal

Make reviewed Pearson 4CH1 question papers the authoritative source for original-paper practice and generated mocks. Use each paper's exact mark scheme for marking, its examiner report when available for preparation advice, and the reviewed 2017 Chemistry specification for scope and paper format. Keep every Student's attempts and performance separate.

## Local source audit

- [x] Catalogue the local files by session, component, variant and kind; record hashes and page/text checks.
- [x] Confirm January 2020 `PaperCR` is `2CR` from PDF content.
- [x] Allow June 2021 `1C` and `2C` to have missing examiner reports, with later attachment.
- [x] Obtain the official Pearson 4CH1 specification, record its hash, and keep it separate from exam papers.
- [ ] Manually verify the internal code on the June 2019 `1C` question paper and June 2024 `1C` examiner report, where the first four pages do not expose it as text.
- [ ] Review licensing/availability before exposing original PDFs directly to students. AKURU's controlled question sessions are the current student access path.

## Pilot before bulk import

Pilot scope: June 2025 standard `1C` and `2C` only. The `1CR` and `2CR` files were inventoried during preflight but are deferred to the later bulk intake. An unreleased draft review pack is privately staged under production `/data/akuru/pilots` to compare against published textbook data; it is outside AKURU's document tables and Student APIs. Do not import or release pilot content to production as part of this phase.

- [x] Reconcile June 2025 `1C` and `2C` top-level question counts and marks against their own schemes; keep an ignored, local preflight manifest. The regional variants were also inventoried, but are outside the pilot.
- [x] Build review drafts for the 16 standard-paper top-level questions, with exact scheme text, source page ranges, candidate examiner-report pages and source identity checks. The existing worksheet also records deferred regional drafts; see `docs/pearson-chemistry-june-2025-question-review.md`.
- [x] Re-run the local manifest for `1C`/`2C` only, verify all six source hashes against the catalogue, and confirm every page renders. Initial visual checks of Question 1 on each paper found layout-sensitive diagrams, tables and shared answer choices.
- [x] Visually inventory the layout dependencies of all 16 standard-paper questions; fix six scheme references that previously omitted continuation pages. Exclude generic examiner-report introduction mentions from question-specific page candidates.
- [x] Generate an ignored, local-only draft bank with 16 top-level questions, 87 labelled subpart candidates, exact source hashes/page ranges, 35 rendered question pages and 20 rendered marking-scheme pages. Keep Student prompts, approved rubrics, report comments and mappings unset; see `docs/pearson-chemistry-draft-bank.md`.
- [x] Privately stage the unreleased 1C/2C draft pack, compare it read-only with production's two published Chemistry topics, and record conservative decisions for all 87 subparts. One whole question (1C Q3) is supported by current textbook coverage; a provisional local OCR-cleaned prompt/rubric candidate remains unreleased. See `docs/pearson-chemistry-production-coverage-review.md`.
- [ ] Pilot June 2025 `1C` and `2C` end to end, including question/subpart boundaries, marks, shared stems, diagrams, equations, page references, exact mark-scheme links and report evidence.
- [ ] Verify paper format and topic mappings against the published textbook and specification, without inventing missing materials.
- [ ] Prepare genuine Chemistry textbook/topic records in an isolated local or disposable database before any Student workflow test. The current local database has no textbook, topic or document records. Do not label unmapped questions eligible or invent topic coverage.
- [ ] Run an original-paper attempt for each eligible component and a term-filtered mock from the pilot sources; compare marking with the exact scheme and check Student isolation. Missing later textbook topics should hold ineligible full papers back, not prevent source review.
- [ ] Record extraction quality, repair effort and an import decision before proceeding to all 48 sets.

## AKURU implementation

- [x] Correct original-paper timers for Chemistry Paper 1 (120 minutes) and Paper 2 (75 minutes), while allowing a reviewed explicit duration for other papers.
- [x] Add a reviewed-reference release gate and subject-scoped Student PDF access for the specification.
- [x] Inherit companion identity from the selected paper when omitted and reject mismatched session, component, variant or year at upload/publication.
- [x] Hide official papers without an exact approved scheme and block assessed sessions lacking approved scheme entries.
- [ ] Upload, review and publish the Pearson specification through the Admin UI. A reviewed, versioned machine-readable interpretation of its mock rules remains required before specification-driven mock generation.
- [ ] Make exact source identity (specification, session, component and variant) mandatory for imported questions, schemes and reports; support attaching a missing report later.
- [ ] Gate trusted AI marking on an approved exact mark scheme. Never borrow another paper's scheme or report.
- [ ] Ground Student preparation advice in approved scheme points and examiner comments with citations; identify absent report evidence honestly.
- [ ] Ensure original-paper practice uses the complete reviewed paper and term mocks select only covered topics, preserving the source paper/version in immutable attempt snapshots.
- [ ] Add Admin import/review screens or a controlled import tool for bulk intake and reconciliation. Implementation is broken down in `../planned/TODO-OFFICIAL-PAPER-REVIEW-WORKSPACE.md`; the pilot remains open until its acceptance gates pass.

## Release evidence

- [x] Add local catalogue and component-duration regression tests.
- [ ] Add authorization, exact-pairing, missing-report, Student isolation, exam-flow and source-citation integration tests.
- [ ] Review the local pilot and all final release gates before any production import or release.
- [ ] Import and validate approved sources on production only after the pilot passes; do not publish unreviewed extraction.

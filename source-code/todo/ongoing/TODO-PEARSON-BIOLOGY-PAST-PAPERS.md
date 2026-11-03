# Pearson Edexcel iGCSE Biology past-paper intake

Created: 2026-11-04
Status: ongoing; local intake assessment completed.
Started: 2026-11-04.
Completed: not completed.

## Objective and scope

Bring the supplied **linear Pearson Edexcel International GCSE Biology 4BI1 (2017 specification)** papers into AKURU using the existing Chemistry review workflow. Students should eventually be able to practise approved original papers, receive source-backed answer feedback, ask released questions in Tutor chat and take mocks selected from their cumulative published topic coverage. These are separate release decisions; a draft import alone enables none of them.

Sources: ignored `pastpapers/igcse/biology/`. Evidence: [intake assessment](../../docs/biology-pastpaper-intake-assessment.md) and [all-file inventory](../../docs/biology-pastpaper-inventory-2026-11-04.csv).

Baseline: **132 PDFs / 3,723 pages / 44 candidate paper sets / 369 top-level question candidates**. 44 papers, 44 final schemes, two additional provisional schemes, 42 report files. All paper-total markers reconcile, but no question/subpart semantic review has been completed by this audit. The January 2020 report cover discrepancy has been resolved by an exact-source body comparison; two June 2021 reports are absent.

Apply [iGCSE intake standard 1.3.0](../../../guidelines/pastpapers/igcse/README.md), its [batch checklist](../../../guidelines/pastpapers/igcse/extraction-checklist.md) and the [shared conformance backlog](../planned/TODO-IGCSE-PASTPAPER-ANALYSIS.md). Reuse existing review, confidence/provenance, scoring and publication functionality; do not create a parallel Biology assessment implementation. Complete necessary shared work with reference cases rather than declaring the whole conformance backlog complete.

## Completed preparation

- [x] Open all 132 PDFs, extract all-page text diagnostics, calculate hashes and compare cover identities.
- [x] Catalogue 13 supplied sessions: 26 standard and 18 regional paper sets.
- [x] Reconcile 44 paper totals and identify 369 top-level question-total markers.
- [x] Identify provisional schemes, missing reports, case differences and January 2020 report conflict.
- [x] Inspect representative rendered question, scheme and report layouts and record limitations.
- [x] Compare existing Chemistry scripts, Admin review import contract and extraction guidelines.

## Step 0 — Establish the authoritative Biology catalogue

- [x] Move this plan to `todo/ongoing` when implementation starts; record start date and update the index.
- [x] Create a reproducible, read-only subject-aware catalogue adapter; accept case variations in folders and filenames. Retain originals unchanged, relative paths and SHA-256 hashes.
- [x] Use an identity key including awarding body, course, subject, qualification/specification issue, year, series, component and regional variant; retain source document versions and final/provisional status.
- [x] Verify all candidate sets against internal source headings, not filenames alone. Handle 4SD0 co-listed covers without creating duplicate Biology questions.
- [x] Resolve January 2020 `PaperBR`: accept question/scheme as 2BR only after recorded source checks; quarantine the report whose cover says 2B until authoritative verification. Missing or ambiguous reports must not block safe review of exact question/scheme pairs.
- [x] Use the June 2021 final Results schemes as authoritative after comparison; retain the two provisional schemes as historical/nonactive. Record missing reports explicitly and allow later attachment.
- [ ] Check Pearson's actual session/variant availability before calling any unsupplied year or component missing. No other downloads are assumed required by this inventory.

Acceptance: all 132 files have a recorded disposition; no silent overwrites, merged variants or inferred report pairings.

## Step 1 — Establish specification and Biology readiness

- [ ] Obtain the official 4BI1 specification from Pearson, record issue/hash/applicability, and review/publish it as an authenticated Student reference using the existing workflow.
- [x] Verify Paper 1B/1BR: 120 minutes, 110 marks; Paper 2B/2BR: 75 minutes, 70 marks. Check existing generic timer logic; remove any Chemistry-specific assumption where needed.
- [ ] Preserve Paper 2's access to all specification content, including bold B statements; do not treat it as only the textbook's later units.
- [ ] Verify current published Biology textbook, six groups, 22 topic identities/content versions, and actual cumulative student coverage. Do not grant or alter child coverage as part of source intake.
- [ ] Prepare a reviewed specification-statement-to-topic crosswalk, keeping unclear/missing coverage explicit. Record stable topic references and original visual-reference printed-page evidence where available; do not rely on mutable reflow page numbers.
- [ ] Use disposable/local fixtures for import tests. Record production prerequisites read-only before proposing any production write.

Acceptance: qualification and source versions are explicit; specification coverage is distinct from topic availability and school term coverage.

## Step 2 — Generalise and validate the extraction/import adapter

- [x] Parameterise the existing Chemistry catalogue/pilot/draft-bank scripts or provide a shared adapter for 4BI1 and B/BR components; retain Chemistry regression behaviour.
- [ ] Use native text/layout first, render source pages, and apply targeted OCR or vision to necessary image regions. Classify blank/answer-space pages separately from extraction failures.
- [ ] Detect labels/geometry, nested part boundaries and cross-page context; do not split only at mark lines or copy a hard-coded Chemistry question count.
- [x] Reuse the supported unreleased draft-bank contract and exact source-hash checks. Add dry-run validation, stable references, safe retry receipts and expected-revision conflicts without bypassing Admin APIs.
- [x] Record precise question/scheme/report provenance independently: native/OCR method, actual model identity when known, guideline/profile/schema/prompt versions, timestamps and inspected regions. Keep unknown identities unknown.
- [x] Add only migrations proven necessary by a contract gap; otherwise reuse existing tables/APIs. Document any unsupported structure and hold automatic marking instead of flattening it silently.

Acceptance: Biology proposals validate locally; malformed, cross-subject, wrong-series, wrong-variant and stale-hash payloads fail closed.

## Step 3 — Build the June 2025 standard-paper pilot

- [x] Process **all questions/subparts of 1B and 2B** with their exact final schemes and reports. Regional sources are outside this first pilot, not outside the eventual scope.
- [ ] Preserve original source PDF pages, printed labels, question totals, shared stems, passage context, complete A–D choices, tables and response slots.
- [ ] Propose focused diagram/photo/graph/table crops before Admin review. Attach at the appropriate shared/question/subpart scope; retain labels outside the figure, arrows, scale bars, axis titles/units/ticks and complete grids.
- [ ] Keep intended blank graphs, drawing spaces and tables blank. Preserve image resolution/aspect ratio and measurement scale; do not calculate measurements from an arbitrarily resized display crop.
- [ ] Extract actual marking points and instructions into each part, including any-N caps, alternatives, linked explanations, duplicate credit, tolerances, units and maximum marks. Link evidence as well as populating rules.
- [ ] Extract relevant report guidance with exact question/subpart association and continuation pages. Keep handwriting, examiner annotations, candidate answers and awarded marks distinct. Preserve uncertain spans and originals; do not convert wrong candidate examples into accepted answers.
- [ ] Propose Biology-only topic mappings using reviewed content and specification crosswalk; provide stable topic evidence and original printed-page references where available. Flag incidental word overlap and cross-topic dependencies.
- [x] Attach per-question/per-subpart accuracy-confidence estimates and reasons, independently for paper, scheme and report. They are estimates, not measured correctness; missing/unchecked evidence must be visible. Keep dedicated accuracy-page sorting and existing approvals independent.

Acceptance: every part and mark is accounted for, every essential visual is reviewable, and every uncertain source/rule has a located issue. No automatic approval.

## Step 4 — Stage and review through AKURU Admin

- [ ] Dry-run the pilot against local/disposable data and compare the staged proposal with the supported API contract.
- [x] With an explicit production intake instruction, back up and upload the two question papers, exact schemes and reports through authenticated Admin APIs; create only unpublished review workspaces/proposals. Save receipts and exact version/hash associations.
- [ ] Confirm Biology is discoverable in the existing exam-paper workspace and dedicated accuracy page. Show linked/unlinked evidence, subpart approvals, draft saves, visual statuses and toast feedback using existing UI behaviour.
- [ ] Prepopulate proposed visual descriptions, mapping reasons, rubric points and report associations for Admin verification. Do not require repeated manual evidence linking when exact links already exist.
- [ ] Let Admin save incomplete reviews and resume, approve subparts independently, and reopen corrections without silently overwriting approved content. Use existing optimistic revision controls.
- [ ] Review all pilot questions and subparts; obtain content/visual/rubric approval and separately record automatic-marking readiness. Unsupported drawings, measurement or conditional rules remain manual-only.
- [ ] AI-generated worked answers are optional, clearly labelled, confidence/provenance recorded and reviewed before use. Agree any paid generation/evaluation budget before making calls; source intake must work without paid AI.

Acceptance: the Admin can fully inspect and correct the pilot in AKURU. Neither source import nor high confidence implies Student release.

## Step 5 — Validate and release Student workflows

- [ ] Reconcile full paper completeness and totals after review, bind exact approved schemes, and publish only when all required parts are ready. No partial paper may masquerade as a complete original-paper exam.
- [ ] Verify authenticated enrolled Students can access released references/papers only as permitted; hide scheme answers, report examples and worked solutions during formal attempts.
- [ ] Test an original-paper attempt for each component, including 120/75-minute timing, saved answers, resume/expiry/submission, drawing/manual workflows and authorized feedback reveal.
- [ ] Test a cumulative-coverage mock using eligible reviewed parts only; all mapped topics and prerequisite context must be covered. Hold unsupported parts back and explain insufficient eligible material.
- [ ] Release selected self-contained parts separately to Biology Tutor chat; check subject/topic eligibility, image presentation, approved answers, exact scheme feedback and source-backed report advice. Check Biology tutor release/pilot expiry separately: importing papers does not extend it.
- [ ] Verify individual learner scoring/mastery histories and family isolation, including Laura/Roshinika and another-family fixture; do not create shared performance state.

Acceptance: an end-to-end original paper, coverage-filtered mock and released Tutor question pass, or each unavailable workflow is explicitly held back with an actionable reason. No claim of full launch while required checks remain open.

## Step 6 — Expand the remaining standard-paper collection

- [ ] After pilot acceptance, process **June 2024 1B/2B**, then remaining standard series in controlled session batches, preserving exact paper identities and review gates.
- [ ] Account for all **26 standard papers total**, including the two pilot papers. Use final June 2021 schemes and mark its reports unavailable; permit later report additions without rewriting frozen attempts.
- [ ] Produce per-batch counts, source receipts, confidence distribution, unresolved issues and manual review effort. Import as drafts and prioritize low-confidence/complex parts; sample-check higher-confidence results as well.
- [ ] Do not reimport or replace Chemistry workspaces, previously reviewed Biology questions or existing Student histories.

## Step 7 — Add regional sources safely

- [ ] Pilot June 2025 **1BR and 2BR**, then process the other regional sources in session batches: **18 regional papers total**.
- [ ] Keep regional and standard components distinct even where the syllabus is shared. Never attach a standard scheme/report simply because its year/subject match.
- [ ] Resolve or leave quarantined the January 2020 disputed report; record the final disposition. No invented matching report.
- [ ] Track possible repeated concepts without discarding distinct official source questions. Ensure UI labels and mock provenance distinguish regional variants.

## Step 8 — Regression gates, documentation and controlled rollout

- [ ] Add catalogue fixtures for case differences, PaperBR filenames, ambiguous report identity, provisional/final schemes, co-listed 4SD0 covers and absent reports.
- [ ] Add extraction fixtures for organism diagram labels/scale bars, graph axes, table continuation, multiple-choice boundaries, handwritten report examples, practical-method marking and any-N explanation caps.
- [ ] Run existing Chemistry and generic security regressions: authentication, Admin-only imports, CSRF/rate limits, family isolation, unauthorized assets, stale revisions, duplicate imports and private answer leakage.
- [ ] Verify biological notation (CO₂/O₂, powers, magnification, µm/mm, percentages and ratios) and calculation tolerances against source evidence; distinguish examiner-approved alternatives from supplementary teaching.
- [x] Update user/developer docs with actual Biology upload/review/release navigation and unsupported/manual workflows.
- [ ] For any code release, run backend/frontend tests, API-contract checks and production build, then commit/push/deploy only with rollout authorization; back up first, apply only required migrations and verify HTTPS/service/access gates.
- [ ] Record source-data imports and code deployments separately. Save non-secret evidence; keep PDFs, crops, student data, credentials and extracted licensed content out of Git.
- [ ] Reconcile final dispositions for 44 paper sets and all 132 supplied files; mark this plan completed only when accepted scope is delivered or explicit deferred items are moved to another plan.

## First implementation action

Start with **Step 0: authoritative Biology catalogue and exception handling**, then Step 1 and the June 2025 standard pilot. No need to manually reformat every source or upload all 132 files first. Admin review begins once the pilot's populated draft workspaces are ready; extraction and proposals should minimize repetitive manual work without removing human release decisions.


## Implementation evidence — 2026-11-04

- Shared native-layout builder and authenticated resumable importer implemented; [runbook](../../docs/pearson-biology-intake.md).
- All 44 local banks validate: 369 questions, 1,711 subparts, 4,726 source marking-point proposals. All question/subpart mark totals reconcile. These are extraction proposals, not 369 approved source comparisons.
- June 2025 1B/2B pilot uploaded via Admin APIs: 16 questions/76 subparts; saved records checked against local proposals. Exact paper/scheme/report companions attached; all remain unapproved and manual-only for marking.
- Official 4BI1 specification downloaded and verified as Issue 3 (56 pages); reference review/publication and an approved specification-topic crosswalk remain separate work.
- Native answer/guidance table columns, missing source numerals, repeated continuation question labels, full-question allocations, MC option retention, conservative topic hints and interrupted-save recovery are handled with synthetic regression cases.
- No paid AI calls, automatic approvals, Student releases or child-coverage changes are part of this intake. Manual crop/rubric/report/coverage acceptance remains open; do not mark the whole roadmap complete on draft ingestion alone.

- Subsequent source comparison resolved the January 2020 report identity: all six discussions match 2BR. The exact three-hash exception and original cover discrepancy are retained in [the review](../../../guidelines/pastpapers/igcse/reviews/2026-11-04-biology-january-2020-2br-report-identity.md). Final source intake therefore uses 130 exam PDFs, with the two provisional schemes remaining nonactive.

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

## June 2025 standard source-comparison acceptance — 2026-11-04

- [x] Compare 1B/2B question and scheme renders, all 22 existing question crops, typed examiner commentary and exact subpart/physical report continuation ranges; inspect selected handwritten examples without claiming a complete literal transcript.
- [x] Correct decimal splitting, non-credit rubric preambles, gap-fill continuation text, calculation/rubric guidance and missing/nonspecific report associations through Admin APIs. Replace the clipped Q7 blood-component fragments with one complete inspected crop.
- [x] Record and read back 16 append-only accuracy assessments for 76 subparts; preserve import-time extraction history and all approval/release/coverage decisions.
- [x] Add generic synthetic regressions and update extraction guidelines. Backend verification: 367 passed, one skipped.
- [ ] Admin adjudication: 1B Q4(b)(ii) paper/report three marks versus scheme four; 2B Q6(b)(i) scheme says three points versus two-mark allocation. Both remain manual-only.

Result: 14/16 questions and 74/76 subparts exceed 70%. Source fidelity confidence is separate from approval and executable scoring. See [the dated audit](../../../guidelines/pastpapers/igcse/reviews/2026-11-04-june-2025-biology-source-comparison.md). Other papers remain preliminary extraction drafts; the remaining roadmap/manual release gates stay open.


## June 2024 standard source-comparison acceptance — 2026-11-04

Started/completed this comparison batch: 2026-11-04. Whole roadmap remains ongoing.

- [x] Apply the reusable 1.4.0 source-comparison guideline to standard 1B/2B: 16 questions, 77 subparts, 180 marks; inspect all question/scheme renders, 31 saved crops, typed report commentary and 29 selected report renders.
- [x] Correct missing gap words, MC answers, notation/arrows, criteria/calculation guidance and subpart report links; replace five incomplete diagrams and assign relevant visuals per subpart through revision-protected Admin APIs.
- [x] Append and read back source-bound confidence assessments: 16/16 questions and 77/77 subparts above 70% (also above 75%); ranges 80–94% / 85–94% for 1B/2B. These are source-fidelity judgements, not measured correctness rates.
- [x] Verify six source hashes, five exact crop byte comparisons, current assessment revisions/hashes and unchanged Chemistry 1C/June 2025 Biology workspaces. Focused Biology/Chemistry intake tests: 47 passed.
- [ ] Admin acceptance remains required, including visual/coverage decisions and manual-only scoring limitations; see report wording issues at 1B Q9(b)(ii), 2B Q6(b)(iii), and original-scale measurement at 1B Q1(b)(i).
- [ ] At the end of this June 2024 batch, 40 papers remained for source comparison. Continue in verified catalogue session batches; there are no June 2023 sources in the local collection (2023 sources are January/November). Existing preliminary extraction percentages must not be raised without equivalent source checks.

See [the June 2024 audit](../../../guidelines/pastpapers/igcse/reviews/2026-11-04-june-2024-biology-source-comparison.md). This is a production source-data update only; no app deployment, restart, paid AI call, question approval or Student release.


## June 2025 regional source-comparison acceptance — 2026-11-04

Started/completed this comparison batch: 2026-11-04. Whole roadmap remains ongoing.

- [x] Source-compare 1BR/2BR separately from their standard counterparts: 16 questions, 80 subparts, 180 marks. Inspect all rendered question/scheme pages, all 30 saved crops, typed examiner commentary and 19 selected report renders.
- [x] Restore calculation/MC/rubric text, continuation criteria, ranking slots, table geometry/blank cells, relevant subpart visuals and exact report ranges through revision-protected Admin APIs.
- [x] Append 16 source-bound accuracy assessments. 15/16 questions and 79/80 subparts exceed 70% (also exceed 75%); 1BR range 80–94%, mean 90.6%; 2BR range 70–94%, mean 90.5%. Estimates are not measured accuracy or Admin approval.
- [x] Local intake regression tests: 47 passed. Production read-back passed: six source hashes, 16 current assessments, 30 unchanged crop byte comparisons and all five protected workspaces. Evidence is recorded in the batch audit.
- [ ] Admin adjudication/acceptance: 2BR Q6(b)(iii) two-point prose versus three-mark allocation; source wording errors at 1BR Q3(b)(i), Q8(c)(i), and 2BR Q1(b). All parts remain unapproved/manual-only; no Student release or coverage change.
- [ ] Continue the remaining 38 papers after these six source-compared papers. Do not raise preliminary confidence without equivalent source checks; the roadmap release and manual-review gates remain open.

See [the regional audit](../../../guidelines/pastpapers/igcse/reviews/2026-11-04-june-2025-regional-biology-source-comparison.md). No application deployment/restart or paid AI calls were needed for this production source-data update.


## November 2024 standard source-comparison acceptance — 2026-11-04

Started/completed this comparison batch: 2026-11-04. Whole roadmap remains ongoing.

- [x] Compare 1B/2B paper/scheme renders, all 21 saved crops and all 15 narrative report discussion pages: 16 questions, 74 subparts, 180 marks.
- [x] Restore lung and cloning gaps, hormone-table criteria, numeric prefixes/decimals, genetic-diagram continuation and practical criteria; reconstruct tables and formulae, and bind report paragraphs to their actual subparts.
- [x] Replace two sets of partial crops with complete inspected visuals: 1B Q3 dog diagram and 2B Q4 sweating graph with its key. Preserve original assets and assign relevant visuals per subpart.
- [x] Append and read back 16 source-specific accuracy assessments: 16/16 questions and 74/74 subparts above 70% (also above 75%). Subpart ranges 85–92% / 80–92%; means 90.5% / 90.7% for 1B/2B. Estimates are source-fidelity judgments, not approvals or measured accuracy.
- [x] Focused Biology/Chemistry intake regressions: 47 passed. Final production verification passed: six source hashes, 16 current assessments, 21 unchanged crops, two exact replacement crops and seven protected workspaces.
- [ ] Admin acceptance: inspect conditional/scoring rules, especially 2B Q1(c) point-numbering ambiguity and Q2(d)(ii) one-per-grain caps; original-scale measurement at 1B Q7(b)(i), scheme alternative at Q4(c)(ii), and mislabelled report references at Q8(b)(ii)/Q9(c)(iii). All parts remain unapproved/manual-only.
- [ ] Continue the remaining 36 source-comparison papers; the next most recent batch is June 2024 regional 1BR/2BR, followed by November 2023 standard 1B/2B. Do not treat draft ingestion or confidence as Student release.

See [the November 2024 audit](../../../guidelines/pastpapers/igcse/reviews/2026-11-04-november-2024-biology-source-comparison.md). This batch updates production source data only; no application deployment/restart, paid AI calls, question approval or Student release.


## June 2024 regional source-comparison acceptance — 2026-11-08

Started/completed this comparison batch: 2026-11-08. Whole roadmap remains ongoing.

- [x] Source-compare existing 1BR/2BR drafts against exact paper/scheme/report PDFs: 16 questions, 77 subparts, 180 marks. Inspect all question/scheme contact sheets, 36 saved crops, typed report commentary and 40 selected report renders.
- [x] Correct criteria, MC answers, decimal/standard-form calculations, notation, table contexts and exact subpart report ranges through authenticated revision-protected Admin APIs. Replace eight incomplete or uncaptioned diagram/photo groups; assign applicable visuals to subparts.
- [x] Append and verify all 16 current source-specific assessments. 13/16 questions and 74/77 subparts exceed 70% (also exceed 75%). Subpart estimates range 70–92%; means are 87.8% / 86.6% for 1BR/2BR. Historical extraction metadata is retained; these are source-fidelity estimates, not empirical accuracy or approvals.
- [x] Verify six source checksums, eight production crop files byte-for-byte, current assessment revisions/hashes and unchanged protected Chemistry workspace. Focused Biology/Chemistry intake/staging tests: 51 passed.
- [ ] Admin adjudication: 1BR Q7(b)(ii) report's lowest-risk group contradicts its graph/scheme; 2BR Q2(b)(ii) intermediate decimal/report multiplier errors; 2BR Q3(b) scheme says no age information despite the table's mean ages. These three subparts remain at 70%; all 77 parts remain manual-only and unapproved.
- [ ] Complete Admin content/visual/coverage acceptance and separate scoring/Student-release gates. Source comparison does not grant release or curriculum coverage.
- [ ] Continue the remaining 34 of 44 source-comparison papers. November 2023 standard 1B/2B is the next proposed chronological batch.

See [the June 2024 regional audit](../../../guidelines/pastpapers/igcse/reviews/2026-11-08-june-2024-regional-biology-source-comparison.md). This batch changes production source data only; no app deployment, restart or paid API calls were needed. Unrelated locally developed application features were not deployed.

## November 2023 standard source comparison and AI review — 2026-11-08

Started/completed this batch: 2026-11-08. The overall roadmap remains ongoing.

- [x] Source-compare existing 1B/2B workspaces: 16 questions, 77 subparts, 180 marks; verify all six production PDF checksums, all question/scheme source sheets and all 11 narrative report pages.
- [x] Correct tables, eight bacteria blanks, chemical/standard-form notation, exact scheme-block links, calculation alternatives and subpart-specific report summaries. Preserve source-conflict notes and historical extraction/provenance records.
- [x] Inspect and save 19 reviewed question crops plus one private official model-answer diagram. Verify all 20 production files byte-for-byte and scope question images to relevant subparts.
- [x] Check published Biology evidence: 74 supported subpart mappings; three sterilisation subparts remain partial/uncertain rather than asserting complete textbook support. Do not invent stable textbook page references.
- [x] Append 16 current source-specific accuracy assessments: 15/16 questions and 76/77 subparts above 75%; one publisher-source contradiction deliberately stays at 70%. These estimates are not empirical accuracy or human approval.
- [x] Run guarded AI review and retain the three genuine subpart blockers: 1B Q4(a) report contradiction, Q3(b)(ii) missing approved worked graph, Q5(b)(i) missing approved worked genetic-cross illustration. Scoring remains manual-only; Student release stays separate.
- [x] Fix false table-image requirements caused by “suitable”/“notable”; retain true diagram/table gates and add four regression cases. Focused tests: 74 passed.
- [x] Deploy fix `b3357ab` after encrypted backup and pass production acceptance. Re-run AI policy/read-back checks: **13/16 questions and 74/77 subparts AI-approved** (1B 7/10 and 42/45; 2B 6/6 and 32/32). Twenty crop bytes, current accuracy hashes and five protected workspaces verified; unauthenticated protected APIs return 401. Adjacent review/answer-visual tests add 21 passes, **95 relevant tests** total.
- [ ] Admin adjudication of 1B Q4(a), approved worked illustrations for Q3(b)(ii) and Q5(b)(i), plus any remaining coverage acceptance/scoring/Student-release gates.
- [ ] Continue the remaining **32 of 44** source-comparison papers. This completes the November 2023 standard batch, not the entire historical collection.

See [the November 2023 audit](../../../guidelines/pastpapers/igcse/reviews/2026-11-08-november-2023-biology-source-comparison.md). No paid API calls; unrelated local frontend work is excluded from the release.


## January 2023 standard source comparison and AI review — 2026-11-08

Started/completed this batch: 2026-11-08. The overall roadmap remains ongoing.

- [x] Source-compare existing January 2023 standard 1B/2B workspaces: **16 questions, 78 subparts, 180 marks**. Verify six production source checksums and optimistic revisions; inspect all question/scheme sheets, 31 old crops and 11 narrative report pages.
- [x] Correct structured tables, answer blanks, notation, exact scheme associations, report summaries and source-bound same-subject topic mappings. Manually resolve parser omissions/cross-question contamination caused by multiline scheme labels; preserve original source anomalies and historical extraction metadata.
- [x] Save 27 reviewed question visuals and one private official septum-answer crop; scope images to relevant parts. Verify all 28 production crop files byte-for-byte against source renders.
- [x] Append 16 current source-specific accuracy/provenance assessments: **13/16 questions and 75/78 subparts above 75%**, mean subpart estimate 88.6%. Keep three publisher-source conflicts at 70%; estimates are not empirical accuracy or human approval.
- [x] Run guarded production AI policy: **11/16 questions and 73/78 subparts AI-approved** (1B 6/10 and 43/47; 2B 5/6 and 30/31). Verify current content hashes, full assessment read-back, historical extraction metadata and seven protected workspaces.
- [x] Pass 73 focused local intake/review/accuracy/AI-policy tests. No paid model calls, app deployment, restart or migration; source corrections use authenticated Admin APIs.
- [ ] Admin adjudication: 1B Q3(a)(i) saturated-versus-total-fat scheme conflict, Q6(c)(i) sucrose/osmosis report conflict and Q7(c) prey-versus-predator report conflict.
- [ ] Approved worked-answer illustrations for 1B Q4(b)(i) plotting and 2B Q3(b)(ii) genetic cross. Keep manual-only scoring and independent Student-release gates.
- [ ] Harden the generic scheme parser for multiline question labels with January 2023 regression fixtures; current source-data corrections do not fix the parser itself.
- [ ] Continue the remaining **30 of 44** source-comparison papers; next chronological batch: January 2023 regional 1BR/2BR.

See [the January 2023 audit](../../../guidelines/pastpapers/igcse/reviews/2026-11-08-january-2023-biology-source-comparison.md). Unrelated local application changes were preserved and not deployed.

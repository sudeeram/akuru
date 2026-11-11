# AI-assisted exact past-paper evidence linking

Status: Completed
Created: 2026-11-11
Started: 2026-11-11
Completed: 2026-11-11

## Objective

Replace repetitive manual question/marking-scheme block linking with source-verified AI assistance. Start with **June 2025 Biology 2BR**, then expand to other papers after acceptance. Preserve the existing confidence threshold and approval requirements: high confidence alone must not bypass missing evidence, unresolved visuals or release gates.

Current pilot: [2BR accuracy](https://akuru.magicalinternational.com/admin/exam-documents/review/eea024fe-978f-4392-b330-c0011201cf63/accuracy). It contains six questions and 31 subparts. Correct PDF pages are associated, but exact question/scheme block references are missing. Curriculum mappings already exist, with Q1(c)(ii) remaining partial or uncertain. This work must not silently resolve that uncertainty.

Related: [past-paper analysis](../planned/TODO-IGCSE-PASTPAPER-ANALYSIS.md), [Biology roadmap](../ongoing/TODO-PEARSON-BIOLOGY-PAST-PAPERS.md), and [extraction guidelines](../../../guidelines/pastpapers/igcse/README.md). Extend existing review, provenance, job and approval infrastructure rather than creating a parallel approval system.

## Step 0 — Establish the evidence contract and pilot baseline

- [x] Inspect current source extraction, block kinds, review status, bounding boxes, exact-link validation and available Admin APIs. Identify the minimum schema/API additions; do not assume new migrations are required.
- [x] Snapshot pilot question revisions, analysis versions/content hashes, source-version checksums, existing links, visuals, confidence, curriculum decisions, approval states and release gates.
- [x] Define a version-bound proposal contract: question/subpart, source role/version, existing or proposed block identity, PDF page(s), source bounds, matching explanation, confidence and ambiguity/blocker status.
- [x] Distinguish extracted source text from reviewed interpretation. Every proposed block must be traceable to the original page; cleaned transcription must not overwrite raw extraction silently.
- [x] Record model, reasoning effort, processing time and guideline/prompt versions for each run. Use provider-confirmed identity when available or explicitly operator-confirmed identity for Codex work. Do not inherit historical model attribution automatically.

## Step 1 — Implement source-grounded matching

- [x] Use deterministic question labels, nested part labels, page ranges, wording and marks to narrow candidates before calling AI. Reuse cached extraction and page renders; submit only relevant evidence.
- [x] Compare candidate question and scheme blocks against original source text/layout and page images when necessary. Exact matching must handle OCR errors, columns, continuation pages and repeated labels on unrelated questions.
- [x] Associate shared stems, tables and diagrams without treating answer lines, page furniture, specimen candidate responses or unrelated neighbouring parts as question wording.
- [x] Preserve scheme alternatives, any-N caps, combined responses, dependencies, units and continuation instructions. Link every required block when evidence spans several regions or pages; a block-ID presence check alone is insufficient proof of a correct match.
- [x] Keep examiner-report guidance separate from the authoritative marking scheme. Existing report links must remain unchanged unless separately source-verified and explicitly included in the run.
- [x] Flag weak, competing or incomplete matches for Admin review. Matching confidence is separate from OCR confidence and the existing overall accuracy assessment; do not fabricate high scores.

## Step 2 — Support combined-block separation and safe persistence

- [x] Reuse reviewed exact blocks when they already exist. Detect duplicates so reruns do not create a second copy of the same source region or evidence link.
- [x] Where extraction combined subparts, create version-bound source regions/blocks with original page bounds and traceable text. Retain the original combined extraction and support multi-region evidence where needed.
- [x] Enforce authenticated Admin-only mutation, CSRF protection, source ownership/version checks, valid bounds and optimistic concurrency. Never accept arbitrary block IDs from a different source role, paper or document version.
- [x] Provide a dry run and durable, resumable operation receipts. Validate the whole proposed batch before writes; make per-question changes atomic and stop on stale content or conflicting human edits.
- [x] Audit proposed, applied, rejected and replaced links, including prior values and processing provenance. Define how an incorrect applied link is superseded safely without erasing history or modifying frozen Student attempts.
- [x] Apply only high-confidence, unambiguous source-verified associations automatically under a documented policy. Ambiguous proposals must not be labelled reviewed or used as a shortcut to approval.

## Step 3 — Complete the Admin review experience

- [x] Add an Admin action to analyse missing exact evidence for one question or a paper, with visible progress, completion counts and actionable failures. Reuse the existing job mechanism if processing exceeds a normal request.
- [x] Show proposed/matched question and scheme regions beside the relevant subpart, including source pages, excerpts/crops, confidence, reasoning and provenance.
- [x] Clearly distinguish proposed, linked, verified, rejected and ambiguous evidence. Allow corrections and selection of another valid region without requiring the Admin to repeat already verified obvious associations.
- [x] Replace repeated raw `exact_block_required` exception tuples with deduplicated, human-readable messages naming the affected subparts and source roles, with links to fix them.
- [x] Use clear linked/unlinked controls, toast feedback and dirty-state handling; retain the current question and selected subpart after saving.
- [x] Maintain keyboard access, readable mobile layouts and explicit accessible status labels.

## Step 4 — Preserve confidence and approval boundaries

- [x] Treat changed source links/blocks as material evidence changes: recompute the analysis content hash and visibly mark prior source assessments stale where required. Never simply rebind an old confidence score to changed evidence.
- [x] Perform a fresh source comparison for affected questions/subparts and append evidence-backed accuracy/provenance records. Preserve historical assessments and distinguish a new comparison from metadata-only corrections.
- [x] Preserve confirmed curriculum decisions, manual-marking rules, approved worked answers and unrelated source links. Protect existing human decisions through the established reopen/review workflow rather than silently approving or overwriting them.
- [x] Rerun the existing strict **greater than 75%** AI-approval policy only after evidence validation. Exactly 75% must not qualify; unresolved visuals and other review requirements still block approval.
- [x] Keep manual content approval, AI approval, automatic-scoring readiness and Student release distinct. Applying evidence links must not publish a paper or change Student access.

## Step 5 — Test and accept the June 2025 Biology 2BR pilot

- [x] Inspect all six questions/31 subparts against the original paper and scheme, including combined blocks, shared stems and source continuations. Do not limit validation to checking that IDs were saved.
- [x] Add regression cases for correct matches, wrong-question/role/version links, same wording under different labels, split/combined blocks, ambiguous candidates, missing pages, stale revisions and invalid bounds.
- [x] Test permissions/CSRF, duplicate-free retries, interrupted-run recovery, immutable source history and preservation of human decisions and frozen attempts.
- [x] Test stale-confidence invalidation, fresh reassessment, the strict approval threshold and retained visual/manual-scoring/release blockers.
- [x] Test actionable deduplicated UI messages, source previews, retained subpart selection and accessible controls.
- [x] Verify production read-back of source hashes, applied associations, assessment versions, provenance, confidence and approval/release states. Record unresolved publisher/source conflicts honestly; do not promise that every question becomes AI-approved.
- [x] Run a normal Admin browser acceptance check and record before/after counts, exact exceptions, test evidence and the model/effort used. Obtain a paid-evaluation budget if paid model calls are needed; never assume an earlier budget carries over.

## Step 6 — Controlled rollout and documentation

- [x] Commit and deploy only tested application changes needed for the feature, following the existing deployment process. Keep credentials, source PDFs and local proposal packages out of Git.
- [x] Complete and validate 2BR first, then June 2025 **1BR, 1B and 2B**, preserving their existing curriculum mappings and source-conflict flags.
- [x] Review the remaining imported Biology papers for eligibility. Apply in explicit session batches; preliminary native-extraction papers still need full source comparison, not merely evidence links plus copied confidence.
- [x] Update the extraction guidelines, Admin user guide, developer documentation and Biology TODO with actual acceptance results. Record which checks are automated and which still require judgement.

## Completion criteria

- [x] Correct exact question/scheme evidence is visible and linked for every unambiguous pilot subpart; genuine uncertainties have specific review actions.
- [x] No repetitive manual linking is required for verified matches, and no incorrect match is accepted solely to clear a gate.
- [x] Accuracy is current for the final evidence, provenance is recorded, and AI approval reflects all existing requirements.
- [x] Production acceptance passes with content history, Student isolation, assessment restrictions and release boundaries preserved.

Implementation and controlled June 2025 rollout completed. See [production acceptance and retained gates](../../../guidelines/pastpapers/igcse/reviews/2026-11-11-june-2025-exact-evidence-linking.md). All 156 subparts have exact evidence; 150 subparts and 3 parent questions are AI approved. Independent visual/source-conflict gates remain as documented; no Student release was performed. Remaining historical source-comparison batches continue under the Biology roadmap.

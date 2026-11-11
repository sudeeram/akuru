# Past-paper workflow, curriculum validation and automatic Tutor release

Status: In progress
Created: 2026-11-11
Started: 2026-11-11
Completed: Not completed

## Objective and agreed experience

Replace the ambiguous document-list “Awaiting review” summary with a source-aware workflow. Admins manually review image crops, labels and associations; they should not have to manually approve every high-confidence question/subpart. AI checks final content and curriculum evidence, applies eligible approval strictly above 75%, and automatically releases safe, eligible items for Tutor practice. Students may use released items while remaining items are reviewed. Formal-exam publication remains a separate explicit Admin workflow.

This plan covers frontend, backend, data/versioning, security, tests, documentation and controlled deployment. Creating it does not execute model calls, change production data, approve content, publish papers or deploy code. Obtain a fresh explicit budget before any paid implementation evaluation; do not reuse exhausted or earlier evaluation allowances.

## Existing foundations to reuse

- [Completed final-content reassessment](../completed/TODO-ADMIN-FINAL-CONTENT-REASSESSMENT.md): durable Admin jobs, original PDF/crop comparisons, current accuracy history, guarded AI approval, image/content queues and snapshot protection.
- [Completed exact evidence linking](../completed/TODO-AI-EXACT-EVIDENCE-LINKING.md): exact source proposals, source-version hashes, original-region previews and audit receipts.
- [Biology intake roadmap](../ongoing/TODO-PEARSON-BIOLOGY-PAST-PAPERS.md) and [extraction guidelines](../../../guidelines/pastpapers/igcse/README.md).
- Existing published-topic mappings, Student enrolment/cumulative coverage checks, Tutor practice release records and source fingerprints. Reassessment currently preserves mappings rather than generating/revalidating them, and Tutor release is currently an explicit Admin action.
- Local-only follow-up in `frontend/features/tutor-past-paper-releases.tsx` accepts human-approved or AI-approved statuses while retaining existing coverage/marking checks. Inspect its current Git/deployment status before integrating; do not assume this local fix is deployed.

## Four-step past-paper display

Add a **Workflow** table column with four numbered square badges, each with an accessible name, textual state, details and a link to its relevant action.

| Step | Meaning | Completion rule |
| --- | --- | --- |
| 1 · Extracted | Extract question content, marking points and examiner guidance; associate exact evidence and record initial source-specific confidence. | Extraction and expected question/subpart inventory reconciliation complete. Low confidence remains separately visible; successful OCR alone is insufficient. |
| 2 · Images reviewed | Admin reviews question/answer crops, labels and associations, including relevant scheme/report visuals. | Every required image decision is resolved. Complete automatically with an explicit “Not applicable” explanation when no relevant images exist. |
| 3 · Assessed | AI checks final saved content, reviewed visuals, curriculum mappings/evidence and marking readiness; eligible content is approved automatically. | Assessments/mapping checks are current and remaining low-confidence content or explicit blockers have been manually resolved. Model completion alone does not mean this step is complete. |
| 4 · Tutor practice released | Automatically release each approved, self-contained, eligible item without another Admin approval click. | Every required in-scope item is currently released for Tutor practice. Partial release stays amber. This is not formal-exam publication. |

Colours: grey = not started; blue = actively processing; amber = partial/attention required; green = complete. Use text/icons as well as colour. Processing failures must remain clearly visible and actionable, never appear complete. Show counts such as “Images reviewed: 4/6 questions” and “Tutor practice: 24/31 subparts available.” Step 4 is grey when none are released, amber for partial availability/blockers, and green only for complete current release. Individual steps may progress independently; released safe items remain usable while other parts need attention.

### Companion source documents

Do not reuse the four student-delivery steps for marking schemes or examiner reports. Use descriptive statuses with counts/details:

- Marking scheme: **1 · Extracted**, **2 · Linked to paper**, **3 · Evidence checked**.
- Examiner report: **1 · Extracted**, **2 · Linked to paper**, **3 · Guidance checked**.

Display three separate progress labels, not a single label that replaces its predecessor. Initially all three are **grey — Not started** when no corresponding activity has occurred. For existing/imported documents, derive their initial displayed states from recorded evidence rather than resetting completed work.

| Label | Marking-scheme activity that completes it | Examiner-report activity that completes it |
| --- | --- | --- |
| 1 · Extracted | Processing successfully captures the available pages, marking points and relevant diagrams, with extraction completeness verified. | Processing successfully captures the available pages, commentary and relevant examples, with extraction completeness verified. |
| 2 · Linked to paper | The source is associated with the correct examination session, subject and paper code. | The source is associated with the correct examination session and applicable paper or papers. |
| 3 · Evidence checked / Guidance checked | Final question reassessment verifies that exact linked scheme evidence supports the extracted answers, marking points and scoring rules for the applicable scope. | Final question reassessment verifies that relevant examiner commentary is correctly associated with questions and interpreted accurately for the applicable scope. |

Use **grey** for not started, **blue** for processing/checking underway, **amber** for partly completed, uncertain or blocked, and **green** for complete within the applicable paper scope. Include text, counts and actionable details; processing failures must remain explicit. These are independent milestones: association may exist before extraction completes, so do not fabricate a strict sequential dependency.

Example: uploading a scheme starts extraction in blue; successful complete extraction turns label 1 green. Matching it to the correct paper turns label 2 green. Final reassessment turns label 3 green only when its applicable evidence checks are complete; unresolved questions keep it amber. **Extraction complete does not mean extraction accuracy is approved.** Accuracy is evaluated during evidence checking. Verified absence of examiner commentary for a question is acceptable; missing or unchecked evidence is not.

- [ ] Implement and document these initial-state and transition rules in the server-owned companion-source summary contract.
- [ ] Test independent milestone transitions, existing-document state derivation, partial checks, failures, stale/superseded evidence and verified absence of report commentary.

Derive these states from associated source checks and questions, avoiding duplicate manual approval. Distinguish absent reports, unverified evidence and verified “no applicable examiner comment.” A source linked to several papers/regions must show per-paper scope; do not claim the entire document is checked because one linked question passed. The marking scheme remains authoritative for marks; reports provide supporting advice and cannot silently override contradictory marking instructions.

## Step 0 — Inspect contracts and define authoritative state rules

- [x] Inspect document-list statuses, extraction jobs/inventory, current approval policy, mappings/publication versions, scoring readiness, Tutor release fingerprints, formal-exam publication and Student access.
- [x] Capture read-only baselines for a pilot paper, sources, assessments, mappings, human image/content approvals, releases and Student access. Keep credentials/source material out of Git.
- [x] Define per-step/per-source states and denominators, distinguishing question counts, subpart counts, excluded items, superseded sources and missing companions. An incomplete/missing inventory must never produce green badges.
- [x] Define explicit treatment of excluded or permanently ineligible items: retain reasons and show released/required/excluded totals. Default to no silent denominator reduction or misleading whole-paper completion; record any approved exclusion policy.
- [x] Specify one server-owned readiness contract and policy version. Document which gates require judgement, and that confidence is an estimate rather than calibrated correctness.
- [x] Inspect existing schema before choosing additive migrations. Identify necessary structured mapping-assessment provenance, version dependencies, automated-release audit metadata and indexes; avoid duplicate workflow state stores.

## Step 1 — Add source-grounded curriculum assessment

- [x] Extend final reassessment to retrieve authorised published textbook topics and exact evidence for the same subject/course/specification. Reuse existing retrieval/citation infrastructure; never send the entire textbook unnecessarily.
- [x] Verify existing subpart mappings and propose missing mappings. Permit multiple topics where justified; enforce subject/textbook ownership and publication eligibility on the server.
- [x] Record **Supported**, **Partial or uncertain**, or **Outside current coverage**, with evidence, reasons, mapping confidence, actual model/effort provenance and referenced publication versions. Keep mapping confidence separate from wording/marking/extraction confidence.
- [x] Establish and document a conservative automatic-mapping acceptance policy. Do not assume overall accuracy above 75% proves the curriculum mapping. Weak, competing or incomplete evidence requires review rather than a forced association.
- [x] Preserve manual mapping decisions; flag a conflict for adjudication rather than silently replacing a human decision. Audit accepted AI mappings and explicit Admin changes.
- [x] Reference stable topic identities and exact published evidence, using visual-reference printed-page labels where available; do not invent permanent page references from changing generated content.
- [x] Keep content coverage separate from per-Student eligibility. Unpublished or unsupported content must not become eligible merely because a student is enrolled in the subject.

## Step 2 — Integrate final assessment and one shared release validator

- [x] Extend the existing queued reassessment flow to check final wording, boundaries, marks/options/shared stems, complete rubric alternatives/caps/dependencies, report associations and reviewed visual crops/labels/axes.
- [x] Validate curriculum evidence and marking readiness alongside these checks; a model recommendation must not mark unimplemented scoring rules executable.
- [x] Keep original-source checks and reviewed interpretations separate, recording specific discrepancies and source-specific confidence. Preserve known publisher/source conflicts until explicitly adjudicated.
- [x] Use current version/hash/history-bound assessments and strict **greater than 75%** approval. Exactly 75% remains in the manual-review queue. Preserve human decisions and history.
- [x] Implement a shared backend eligibility validator for current assessment/approval, exact evidence, all required visual decisions, supported curriculum, scoring readiness and independent answerability. Reuse it for automatic/manual release, readiness summaries and access validation as appropriate.
- [x] Return structured question/subpart blockers with source/part identifiers and actionable destinations. Keep image review and manual content review distinct; successful generation with unresolved issues remains amber.
- [x] Reassess only affected questions, preserving shared context and avoiding unnecessary model calls for unchanged current content. Reject concurrent edits and source/publication changes before saving.

## Step 3 — Automatically release safe Tutor practice items

- [x] After final reassessment persists and the existing approval policy runs, automatically release eligible items using the shared validator. No additional Admin release click for eligible content; keep manual withdrawal available.
- [x] Resolve the parent-question approval dependency explicitly: allow independently safe subparts to be released while siblings remain blocked only when all needed shared stem, visuals, evidence and source requirements pass. Do not merely remove the parent guard.
- [x] Support existing automatic scoring and the explicitly supported manual drawing path. Other unsupported manual-scoring items remain blocked; do not broaden marking modes incidentally.
- [x] Make release application idempotent, audited and transactionally consistent with the saved assessment/mapping snapshot. Record automated origin, policy version, content/mapping dependencies and reasons for non-release.
- [x] Decide and implement the safe retry boundary: recovering a release-write failure must not repeat a paid model call or duplicate releases.
- [x] Preserve explicit Admin withdrawals/exclusions. Background reassessment must not silently re-enable an intentionally withdrawn item; require a documented explicit re-enable policy/action.
- [x] Leave complete-paper formal-assessment publication and its answer/help restrictions unchanged. Show formal-exam availability separately from Tutor-practice completion.

## Step 4 — Extend invalidation, permissions and Student access

- [x] Extend version/fingerprint checks to relevant wording, marks, rubric, source links/versions, image approvals/crops/associations, mapping decisions and published textbook evidence versions.
- [x] Invalidate affected assessments/releases after material changes and explain the required follow-up. Do not let UI state or stale high confidence grant access.
- [x] Fail closed if required topic content is unpublished, archived, no longer supported or superseded without valid replacement evidence. Keep unaffected items available where policy permits.
- [x] Preserve immutable Student attempt/history snapshots; retain release and assessment audit history rather than deleting records to reset progress.
- [x] Retain authenticated role-scoped reads, Admin-only CSRF-protected mutation, source ownership, optimistic concurrency and safe job/idempotency checks.
- [x] Enforce current per-Student subject enrolment, cumulative topic coverage, account/feature release controls and assessment restrictions at use time. Global release is not permission for every student.

## Step 5 — Build progress/source-summary APIs

- [x] Return authoritative statuses, counts, current versions, processing state, unresolved blockers and action targets for each four-step badge. Derive from existing records rather than manually toggling completion flags.
- [x] Aggregate partial release safely using the defined required/excluded denominator. Never report complete solely because all available extracted rows passed when the expected inventory is incomplete.
- [x] Return companion-source extraction, association and scoped evidence/guidance-check summaries, including explicit no-comment/missing-source distinctions.
- [x] Include both content and image blockers in readiness summaries, not only automatic-marking issues. Keep accuracy, curriculum support, executable marking and release status separate.
- [x] Batch reads and avoid per-row/per-source N+1 queries. Add pagination/filter compatibility and suitable indexes only where needed.
- [x] Update OpenAPI and generated frontend contracts, with backward compatibility for existing consumers.

## Step 6 — Build the Admin document-list experience

- [x] Add the four numbered square badges in the past-paper Workflow column, using the agreed grey/blue/amber/green semantics and accessible non-colour state labels.
- [x] Show compact partial-progress counts, keyboard-accessible details and links to extraction, image review, final assessment/manual issues and Tutor release controls.
- [x] Update marking-scheme and examiner-report rows with their three descriptive statuses and scoped progress. Replace the ambiguous summary without hiding raw processing failures or useful detailed history.
- [x] Present image-review and content-review queues clearly; never suggest manually reviewing all high-confidence wording/marking points is required.
- [x] Refresh progress after jobs, manual reviews, publication changes and automatic releases without stale caches or cross-paper state leakage. Show loading/error/empty states rather than temporary false green completion.
- [x] Preserve unsaved edits and current selected question/subpart. Keep actionable toast feedback and avoid misleading success messages when some jobs failed.
- [x] Show Tutor practice release counts separately from formal-exam publication. Display withdrawals, exclusions and blockers with explanations.
- [x] Integrate the existing local AI-approved Tutor-release button correction, retaining all server gates and supported coverage/scoring conditions.

## Step 7 — Regression, security and acceptance tests

- [ ] Test complete/incomplete inventories; zero-image automatic completion; partial/all image reviews; failed jobs; excluded items and source replacements against the badge state rules.
- [ ] Test mapping generation/verification across multiple same-subject topics, missing/unpublished evidence, cross-subject rejection, uncertain/outside coverage, manual decision preservation and publication-version changes.
- [ ] Test exactly 75%, above 75%, stale/missing assessments, conflicting marking instructions, incomplete exact evidence and unresolved visuals. High confidence alone must never grant release.
- [ ] Test self-contained subpart release while a sibling is blocked, and rejection when shared context or a required visual is unresolved.
- [ ] Test automatic release, duplicate-free retries, interrupted work, atomic persistence and explicit withdrawal protection without repeating paid calls.
- [ ] Test invalidation at Student access time, sibling/family isolation, enrolment/cumulative-coverage changes and preserved historical attempts.
- [ ] Test companion-source summaries, no applicable report comment, multiple paper associations and absence of duplicate manual-review requirements.
- [ ] Run frontend tests, typecheck, lint, build, backend regressions, migration/drift and generated-contract checks. Use fixtures for routine tests; obtain an explicit bounded budget for any live model evaluation.
- [ ] Perform Admin browser acceptance and authorised Student checks: show partial Tutor availability, correct visual/answer behaviour and formal-assessment restrictions. Record actual results, not merely saved status flags.

## Step 8 — Pilot, documentation and controlled deployment

- [ ] Start with Biology June 2025 2BR after resolving its remaining manual image gates. Snapshot existing reviews and known curriculum/source conflicts; do not silently clear them to obtain a green workflow.
- [ ] Evaluate final content plus curriculum against approved sources, then verify automatic eligible approval/release and accurate partial-completion counts. Preserve all genuine manual-review blockers.
- [ ] Update Admin/user instructions, developer architecture/API documentation, extraction guidelines and linked roadmaps to explain the new lifecycle, automatic release/withdrawal policy and invalidation.
- [ ] Deploy only tested, reviewed changes using the existing encrypted-backup/migration/health-check procedure. Define rollback for application/schema and a safe audited disable/withdraw mechanism for automated releases; do not erase historical records.
- [ ] Verify production read-back, actual source/publication versions, current assessment/mapping provenance, release counts and Student access. Confirm no unintended formal-exam publication.
- [ ] Record pilot exceptions, spend, test/release evidence and remaining batches; move this plan to completed only when its acceptance criteria pass.

## Completion criteria

- [ ] Past-paper rows accurately show all four steps, and companion rows show their relevant source-check lifecycle.
- [ ] Admins review images and low-confidence/explicitly blocked content without repeating obvious source links or individual approval of eligible high-confidence content.
- [ ] Final reassessment includes curriculum evidence and automatically releases only safe eligible Tutor-practice items.
- [ ] Partial availability is amber with truthful counts; green means every required in-scope item is currently released under the explicit exclusion policy.
- [ ] Changes invalidate affected access safely, while human withdrawals, historical attempts, Student isolation and formal-exam restrictions remain protected.
- [ ] Production pilot, documentation and end-to-end acceptance are complete with genuine unresolved issues visibly retained.

## Implementation evidence — 2026-11-11

- Existing JSON analysis/release metadata supports the additive fields; Alembic reports no schema drift and no migration is required.
- Batched workflow summaries retain exclusions in the denominator. Raw extraction-job states are historical and are not mass-rewritten to manufacture completion.
- Final reassessment v2 includes bounded published passages, separate curriculum confidence/provenance, preserved human decisions and independent-answerability checks. Automatic mapping requires at least 90% mapping confidence plus exact evidence; content approval remains strictly above 75%.
- Automatic release uses the shared validator and a nested savepoint; saved assessments can recover release writes without repeating a paid model call. Configuration can pause new automatic releases; manual withdrawals are preserved.
- Production baseline captured read-only in ignored `tmp/workflow-release`. Q4/Q5 still have image gates and imported text parts still have manual-only scoring; these must not be silently changed to obtain green badges.
- Current corpus specification boundary is the configured Pearson Edexcel iGCSE subject library. Generic cross-awarding-body/specification matching is not introduced by this work.
- Local full regression and subsequent focused checks passed; final release/pilot/browser evidence is recorded below when executed. Paid live allowance: US$2 from AKURU-Evaluation, newly approved in this conversation.

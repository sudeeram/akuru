# iGCSE past-paper analysis and intake standard

Guideline ID: `akuru-igcse-pastpapers`

Version: `1.5.0`

Created: 2026-10-21

Last updated: 2026-11-11

Status: documented standard; automated enforcement is incomplete.

## Scope and required reading

Apply this standard when preparing questions here, in AKURU, or through another processing agent. The initial reference set is Pearson Edexcel International GCSE Chemistry, June 2025, standard 1C/2C. The reference corpus also includes June 2025 standard Biology 1B/2B. Regional papers remain distinct sources even when their syllabus is shared.

1. [Question-paper analysis](question-paper-analysis.md)
2. [Marking-scheme analysis](marking-scheme-analysis.md)
3. [Examiner-report analysis](examiner-report-analysis.md)
4. [Pearson Edexcel layout profile](pearson-edexcel-layout.md)
5. [Logical data contract](data-contract.md)
6. [Import and review validation](akuru-import-validation.md)
7. [Reviewed reference examples](reviewed-examples.md)
8. [Per-batch extraction checklist](extraction-checklist.md) — record executed checks, exact issues and review decisions.
9. [Accuracy confidence and extraction provenance](accuracy-confidence-and-provenance.md) — source-specific model identity, dated estimates and reassessment history independent of approvals.
11. [Workflow states and release](workflow-states-and-release.md) — initial states, companion-source transitions and planned approval/release policy.
10. [Source comparison and confidence reassessment](source-comparison-and-confidence-reassessment.md) — required procedure when reassessing imported content; compare sources, correct defects, then record a new evidence-backed assessment.

## Processing sequence

Identify sources and versions → extract text/layout and reconcile inventories → assemble questions, rubric rules and exact source associations → validate and import unapproved proposals → Admin reviews required images → final AI reassessment of saved content and curriculum → guarded AI approval strictly above 75% → automatic release of eligible Tutor-practice items. Formal-exam publication remains a separate explicit Admin action.

This is the agreed target workflow, not a statement that every stage is deployed. Until implemented and verified, retain the existing supported review/release actions. See [workflow states and transition rules](workflow-states-and-release.md).

MUST means required. SHOULD means the default; record a reason for an exception. Do not invent missing wording, source references, marking rules or examiner advice. Question wording and student-facing assets must not contain correct-answer information from the scheme or report.

## Versions and provenance

Record guideline ID/version, layout profile/version, import-format version, extractor version, source file hashes and document versions, processing time, and any AI provider/model used. Guideline and import-format versions are separate. Record versions at batch level with references from each question proposal.

Version 1.0.0 is the initial standard. Change the version and record the reason when rules change: patch for clarification, minor for compatible additions, major for changed interpretation or incompatible requirements. Preserve the version used by older batches. Reprocessing must not silently rewrite approved work or historical attempts.

## Current implementation boundary

AKURU already has version-bound Admin review, source links, subpart editing, visual review and separate release gates. The legacy pilot splitter closes parts at mark allocations; this standard requires label/layout boundaries instead. The review contract supports structured unit-credit scoring groups, accepted equivalents, combined responses, independent automatic-marking readiness, dedicated private model-answer crops and per-subpart drawing submissions. Drawing scoring remains manual; optional image-based marking proposals require human review. Dedicated answer slots, choice records, nested shared context, conditional zero-score rules, alternative allocation paths and annotated report examples remain planned.

Do not submit the logical contract directly to an existing API as though it were supported. Do not describe current imports as conformant until the checks and acceptance cases have passed.

Implementation: [analysis and intake conformance plan](../../../source-code/todo/planned/TODO-IGCSE-PASTPAPER-ANALYSIS.md).

## Use for subsequent papers

Read the source-specific rules, choose the appropriate layout profile, and complete the per-batch checklist before import and review. Apply standards to the source's actual content: a deliberately unlabelled graph or incomplete table must remain incomplete if the question asks the Student to supply that information. Separate what appears in the question from private answers and examiner examples.

These Markdown rules do not automatically configure OCR or enforce every gate in the current application. Record which checks were actually executed, flag missing automation, and retain unresolved issues for Admin review. Add regression cases for new failures; do not claim a new year/variant is covered merely because an earlier one passed.

## Change history

- 2026-11-11 — 1.5.0: agreed four-step paper workflow and independent companion-source milestones; manual image review, final curriculum-aware reassessment, guarded AI approval and planned automatic Tutor release. Added initial states, transition/invalidation rules and batch evidence requirements. Extraction fidelity rules and historical batch provenance remain unchanged; documentation does not deploy automation.


- 2026-11-04 — 1.4.0: reusable source-comparison/reassessment procedure based on Chemistry and Biology pilots; explicit baseline/revision protection, decimal and gap-fill checks, grouped-crop verification, subpart report continuations, source-conflict handling and independent acceptance evidence. Historical batch provenance remains unchanged.

- 2026-11-01 — 1.3.0: source-specific extraction/model provenance, independent accuracy estimates and append-only reassessment history. Existing review approvals stay unchanged when metadata is added. Unknown historical model identities must not be guessed.

- 2026-10-21 — 1.0.0: initial standard based on 1C Q1 visual review and Q2 boundary, scheme and report findings. No code deployment or content approval is implied.

- 2026-10-21 — 1.1.0: explicit server credit allocation, per-subpart caps, equivalent/combined responses and independent automatic-marking readiness. See the marking-scheme guideline for supported v1 limits. Local implementation does not imply production deployment.

- 2026-10-31 — 1.2.0: explicit graph/axis/table completeness and full-page crop verification, mixed-page extraction and confidence limits, diagram-answer and report-handwriting safeguards, batch acceptance checklist, and Q5/Q7 regression records. Synchronized the previously inconsistent standard header. Layout profile advanced separately to 1.1.0; existing batch versions and historical records remain unchanged. Documentation updates do not implement additional extraction automation.

## Recorded source reviews

- [June 2025 Chemistry 1C Q3–Q10 draft corrections and limitations](reviews/2026-10-21-june-2025-1c-q3-q10.md) — historical snapshot with dated follow-ups.
- [Reviewed examples](reviewed-examples.md) — includes later Q3, Q5(c)(ii) and Q7 visual corrections and their regression expectations.

- [2026-10-31 1C remaining questions and complete 2C source audit](reviews/2026-10-31-june-2025-1c-2c-guideline-audit.md) — authenticated production corrections; preserved Admin decisions and release gates.

- [2026-11-04 June 2025 Biology 1B/2B source comparison](reviews/2026-11-04-june-2025-biology-source-comparison.md) — source corrections, append-only reassessments and unresolved official-source conflicts.

- [2026-11-04 June 2024 Biology 1B/2B source comparison](reviews/2026-11-04-june-2024-biology-source-comparison.md) — 16 questions/77 subparts, five complete replacement crops and source-specific reassessments.

- [2026-11-04 June 2025 Biology regional 1BR/2BR source comparison](reviews/2026-11-04-june-2025-regional-biology-source-comparison.md) — 16 questions/80 subparts, complete crop inspection and honest source-conflict confidence limits.

- [2026-11-04 November 2024 Biology 1B/2B source comparison](reviews/2026-11-04-november-2024-biology-source-comparison.md) — 16 questions/74 subparts, two complete replacement crops, narrative report associations and source-specific confidence.

- [2026-11-08 June 2024 Biology regional 1BR/2BR source comparison](reviews/2026-11-08-june-2024-regional-biology-source-comparison.md) — 16 questions/77 subparts, eight complete replacement visuals, exact report associations and three explicitly retained publisher-source conflicts.

- [2026-11-08 November 2023 Biology standard 1B/2B source comparison and AI review](reviews/2026-11-08-november-2023-biology-source-comparison.md) — 16 questions/77 subparts, 20 verified crops, published-topic mappings and explicitly retained drawing/source-conflict approval gates.

- [2026-11-08 January 2023 Biology standard 1B/2B source comparison and AI review](reviews/2026-11-08-january-2023-biology-source-comparison.md) — 16 questions/78 subparts, 28 verified source crops, corrected multiline-label scheme associations and five explicitly retained content gates.

- [2026-11-08 January 2023 Biology regional 1BR/2BR source comparison and AI review](reviews/2026-11-08-january-2023-regional-biology-source-comparison.md) — 18 questions/72 subparts, restored gap-fill slots, 28 verified source crops and five retained content gates.

- [2026-11-09 June 2025 Biology curriculum mapping](reviews/2026-11-09-june-2025-biology-curriculum-mapping.md) — all four standard/regional papers; 155 supported subparts and one uncertain mapping, unchanged confidence assessments and explicit remaining evidence-block approval gates.

- [2026-11-11 Biology model attribution correction](reviews/2026-11-11-biology-model-attribution.md) — operator-confirmed GPT-6.1 Sol / Light recorded in 136 existing AI-assisted analyses across 17 papers; native-only records, confidence and approval states preserved.

- [2026-11-11 June 2025 Biology exact-evidence linking](reviews/2026-11-11-june-2025-exact-evidence-linking.md) — 554 source-region associations across all 156 subparts; current confidence, guarded AI approval and retained visual/source-conflict gates.

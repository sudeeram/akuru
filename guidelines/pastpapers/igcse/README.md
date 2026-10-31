# iGCSE past-paper analysis and intake standard

Guideline ID: `akuru-igcse-pastpapers`

Version: `1.2.0`

Created: 2026-10-21

Last updated: 2026-10-31

Status: documented standard; automated enforcement is incomplete.

## Scope and required reading

Apply this standard when preparing questions here, in AKURU, or through another processing agent. The initial reference set is Pearson Edexcel International GCSE Chemistry, June 2025, standard 1C/2C. Regional papers remain distinct sources even when their syllabus is shared.

1. [Question-paper analysis](question-paper-analysis.md)
2. [Marking-scheme analysis](marking-scheme-analysis.md)
3. [Examiner-report analysis](examiner-report-analysis.md)
4. [Pearson Edexcel layout profile](pearson-edexcel-layout.md)
5. [Logical data contract](data-contract.md)
6. [Import and review validation](akuru-import-validation.md)
7. [Reviewed reference examples](reviewed-examples.md)
8. [Per-batch extraction checklist](extraction-checklist.md) — record executed checks, exact issues and review decisions.

## Processing sequence

Identify sources and versions → extract text and layout → assemble questions and nested parts → propose rubric rules and report associations → validate → import unapproved proposals → Admin review → separate release gates.

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

- 2026-10-21 — 1.0.0: initial standard based on 1C Q1 visual review and Q2 boundary, scheme and report findings. No code deployment or content approval is implied.

- 2026-10-21 — 1.1.0: explicit server credit allocation, per-subpart caps, equivalent/combined responses and independent automatic-marking readiness. See the marking-scheme guideline for supported v1 limits. Local implementation does not imply production deployment.

- 2026-10-31 — 1.2.0: explicit graph/axis/table completeness and full-page crop verification, mixed-page extraction and confidence limits, diagram-answer and report-handwriting safeguards, batch acceptance checklist, and Q5/Q7 regression records. Synchronized the previously inconsistent standard header. Layout profile advanced separately to 1.1.0; existing batch versions and historical records remain unchanged. Documentation updates do not implement additional extraction automation.

## Recorded source reviews

- [June 2025 Chemistry 1C Q3–Q10 draft corrections and limitations](reviews/2026-10-21-june-2025-1c-q3-q10.md) — historical snapshot with dated follow-ups.
- [Reviewed examples](reviewed-examples.md) — includes later Q3, Q5(c)(ii) and Q7 visual corrections and their regression expectations.

- [2026-10-31 1C remaining questions and complete 2C source audit](reviews/2026-10-31-june-2025-1c-2c-guideline-audit.md) — authenticated production corrections; preserved Admin decisions and release gates.

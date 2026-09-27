# Textbook paragraph reconstruction and newline normalization

## Objective

Turn line-oriented native PDF and OCR extraction into accurate, readable
paragraphs before Admin review, while preserving the original evidence. Reduce
manual review work and improve retrieval, citations, flashcards, tutoring and
study materials without allowing automatic processing to rewrite textbook
meaning.

The implementation must be deterministic by default. It must not use OpenAI for
ordinary paragraph reconstruction. Uncertain structure must remain unchanged or
enter review with an explanation.

## Step 0 — Record the evidence and safety contract

- [x] Add paragraph reconstruction rules to the overall, backend and frontend
  architecture documents.
- [x] Define the three representations: immutable raw extraction, automatically
  reconstructed draft and Admin-reviewed publication text.
- [x] Confirm published Topic versions, citations and retrieval chunks are never
  modified by reprocessing.
- [x] Inventory current native PDF, Tesseract, reading-order, block-review,
  publication and retrieval paths affected by reconstructed blocks.
- [x] Decide whether existing JSON metadata and block records are sufficient or
  whether one reviewed additive migration is required.

**Acceptance:** the authoritative text and immutability rules are documented
before extraction behavior changes.

## Step 1 — Preserve richer line and layout evidence

- [x] Preserve Tesseract block, paragraph, line and word identities, confidence
  and normalized bounding boxes.
- [x] Preserve native PDF line spans, font size, style, baseline, coordinates and
  source block identity.
- [x] Record layout column, reading order, estimated line height, indentation and
  vertical gap without discarding the current source geometry.
- [x] Keep the raw line text byte-for-byte available for audit and comparison.
- [x] Version the line-evidence and reconstruction metadata formats.

**Acceptance:** every reconstructed paragraph can identify all source lines and
their locations on the original page.

## Step 2 — Build deterministic paragraph reconstruction

- [x] Add a pure, independently tested paragraph reconstruction service.
- [x] Join adjacent lines only when page, column, OCR paragraph, alignment,
  spacing, indentation, font and punctuation evidence support the decision.
- [x] Never join across pages, columns, layout regions or unrelated source
  blocks.
- [x] Preserve headings, subheadings, lists, figure captions, tables, formulas,
  equations, worked examples and text printed inside diagrams.
- [x] Produce a confidence, reason code and source-line list for every join or
  preserved boundary.
- [x] Fail closed by preserving an uncertain boundary and marking it for review.
- [x] Keep the algorithm configuration and version in extraction provenance.

**Acceptance:** the same source and algorithm version always produce the same
paragraphs and explainable boundary decisions.

## Step 3 — Add safe line-end dehyphenation

- [x] Join words split by a line-end hyphen only when geometry and lexical context
  indicate a printed line wrap.
- [x] Preserve genuine compound terms and minus signs.
- [x] Treat ambiguous chemical names, scientific notation and unfamiliar terms
  as review-required rather than silently changing them.
- [x] Retain the original split tokens and dehyphenation decision in metadata.

**Acceptance:** ordinary wrapped words are repaired without corrupting compound
words or scientific meaning.

## Step 4 — Integrate reconstruction into new extraction jobs

- [x] Run reconstruction after layout-aware ordering and before review blocks are
  persisted.
- [x] Apply equivalent behavior to scanned OCR pages and native-text PDFs.
- [x] Persist raw lines, reconstructed text, confidence, reasons and algorithm
  version alongside the review draft.
- [x] Ensure scientific-notation proposals run against reconstructed text while
  retaining their original source geometry.
- [x] Recalculate page and document review totals from reconstructed blocks.
- [x] Exclude this text reconstruction work from the required Visual Reference
  workflow because its OCR remains outside retrieval.

**Acceptance:** a new text-role upload reaches Admin review as readable paragraph
blocks rather than one review box per printed line.

## Step 5 — Add Admin paragraph review controls

- [x] Display reconstructed paragraphs as one review box with confidence and a
  plain-language explanation of uncertain joins.
- [x] Add **Join with previous**, **Split paragraph** and **Restore extracted
  version** actions.
- [x] Let the Admin inspect the contributing raw OCR lines and source-page crop.
- [x] Preserve scientific marks, captions, equations and reading order when a
  paragraph is joined or split.
- [x] Make controls keyboard, touch and screen-reader accessible with visible
  status feedback.
- [x] Audit automatic reconstruction and every manual join, split and restore
  without storing unnecessary personal data.

**Acceptance:** an Admin can correct paragraph boundaries without manually
copying and reformatting the entire page.

## Step 6 — Reprocess existing unpublished textbook sources safely

- [x] Add an Admin-only **Re-run paragraph reconstruction** action for text-role
  sources.
- [x] Show the algorithm version and a before/after comparison before applying a
  reconstructed draft.
- [x] Never overwrite manually reviewed blocks without explicit confirmation.
- [x] Reject reprocessing that would mutate a published Topic version or existing
  Student evidence.
- [x] Make the operation idempotent, retryable and auditable.
- [x] Recalculate readiness and quality reports after the new draft is accepted.

**Acceptance:** existing unpublished sources can benefit from the improvement
without losing review work or altering released learning content.

## Step 7 — Build the final reviewed-document workspace

- [x] Add an Admin-only **Review complete document** workspace after page and
  block review.
- [x] Assemble the current Topic source in reading order as a continuous,
  paginated document with headings, paragraphs, lists, formulas, tables, figure
  captions and approved visuals.
- [x] Keep visible page boundaries and Printed page labels so the assembled text
  can be compared with the original textbook.
- [x] Provide a synchronized source-page preview and a direct link from every
  assembled section to its source page and review block.
- [x] Allow safe editing of paragraph text, paragraph boundaries, headings,
  lists, captions and supported scientific notation from the assembled view.
- [x] Reuse the restricted scientific editor; do not accept arbitrary HTML or
  permit unsupported formatting.
- [x] Make edits update the underlying review draft rather than creating a second
  conflicting copy of the textbook.
- [x] Warn before edits that change text already referenced by approved figures,
  retrieval preflight or another reviewed relationship.
- [x] Add **Save draft**, **Preview Student version**, **Compare with extracted
  version** and **Confirm final reviewed document** actions.
- [x] Show unsaved changes, unresolved review items, missing page labels and
  publication blockers in a persistent summary.
- [x] Prevent final confirmation while required pages, blocks, scientific
  notation, selected visuals or source provenance remain unresolved.
- [x] Store final confirmation, reviewer, time, content hash and algorithm/editor
  versions in the audit and publication evidence.
- [x] Support keyboard navigation, responsive layouts, screen readers, print
  preview and a private PDF or HTML preview for Admin validation.
- [x] Never expose private source documents through public or Student URLs.

**Acceptance:** the Admin can read and correct the exact continuous document
AKURU will use, compare every section with its textbook page, and explicitly
confirm one authoritative reviewed draft before publication.

## Step 8 — Preserve reconstructed meaning downstream

- [x] Build retrieval chunks and embeddings from published reviewed paragraphs,
  not raw OCR lines.
- [x] Preserve exact page, block and source-line provenance in citations.
- [x] Verify Tutor context, flashcard evidence, study materials, assessments,
  source previews, search aliases and exports use the reviewed representation.
- [x] Ensure paragraph normalization does not merge subject, Topic, document,
  page or column boundaries.
- [x] Include reconstruction version and reviewed paragraph content in immutable
  publication hashes and manifests.

**Acceptance:** all Student-facing learning features receive readable paragraphs
while exact textbook provenance remains available.

## Step 9 — Add evaluation and regression protection

- [x] Add native PDF and scanned fixtures for one-column and two-column pages.
- [x] Cover headings, paragraphs, lists, captions, tables, equations, chemical
  formulae, diagrams, worked examples and line-end hyphenation.
- [x] Test column order, cross-boundary rejection, uncertain decisions and
  repeatability.
- [x] Measure correct joins, incorrect joins, paragraph-boundary accuracy,
  reading-order accuracy and protected-structure preservation.
- [x] Compare the number of review boxes and manual edits before and after
  reconstruction using representative Chemistry pages.
- [x] Add downstream retrieval, citation, flashcard and Tutor regression tests.
- [x] Test complete-document assembly, source-page navigation, edits flowing back
  to review blocks, unsaved-change protection, preview accuracy and final
  confirmation hashing.
- [x] Test authorization, CSRF protection, audit events and immutable published
  versions for reprocessing operations.

**Acceptance:** evaluated fixtures demonstrate fewer review blocks without an
unacceptable increase in incorrect joins or lost scientific structure.

## Step 10 — Documentation and controlled release

- [x] Update Admin and developer documentation with reconstruction status,
  correction controls and safe reprocessing instructions.
- [x] Regenerate the API contract if endpoints or response schemas change.
- [x] Run frontend and backend tests, type checking, linting, production build,
  migration drift checks and extraction evaluations.
- [x] Pilot with the Chemistry Topic PDFs before enabling the pipeline for all
  new text-role uploads.
- [x] Record baseline and post-change review effort and paragraph accuracy.
- [x] Deploy the exact reviewed commit and run production acceptance without
  modifying currently published Chemistry content.

**Done when:** new text-role uploads arrive as accurate, explainable paragraph
blocks; Admins can safely correct boundaries; existing unpublished documents can
be reprocessed; and every downstream learning feature uses reviewed paragraphs
with immutable source provenance.


## Completion evidence

- Deterministic reconstruction version: `paragraph-reconstruction-1.0.0`.
- Raw line geometry, identities, confidence and reconstruction reasons remain attached to each reviewed paragraph.
- New text-role extraction, safe unpublished-source reprocessing, paragraph boundary controls and final-document confirmation are implemented through authenticated Admin APIs.
- Topic publication requires a matching final-document confirmation for newly reconstructed content; later edits invalidate the confirmation hash.
- Chemistry-oriented one-column, two-column, scientific notation, caption, table, equation and dehyphenation fixtures passed the reconstruction evaluation, including a 25% reduction in review blocks without protected-structure loss.
- The generated OpenAPI contract is current. Local release verification passed 55 frontend checks, 135 backend tests, type checking, linting and the production build. Alembic reported no schema drift and no migration was required.
- The controlled release deploys code only. It does not reprocess or modify currently published Chemistry sources; Admins can apply reconstruction only to eligible unpublished text-role sources after reviewing the preview.

# Per-batch past-paper extraction checklist

Standard: `akuru-igcse-pastpapers` 1.5.0

Created: 2026-10-31

Last updated: 2026-11-11

Status: required review record; not all checks are automatically enforced by AKURU.

Use this checklist for every new paper and re-analysis batch. Copy it into the batch's private evidence/report location, record source and extractor versions, then record **passed**, **failed**, **not run** or **not applicable** for each check. Explain non-applicability. A checklist entry is evidence of a check actually performed, not permission to assume a result. Missing implementation must be recorded as not run, with a manual review action.

## Batch identity

Record batch ID, awarding body/qualification/subject/specification, year/session/component/variant, question/scheme/report inventory and missing companions, source file hashes and uploaded version references, guideline/profile/import-format/extractor versions, processing time, reviewer and any AI model/prompt provenance. Keep licensed images, credentials, personal information and private review payloads outside Git.

## Required checks

| ID | Check | Evidence / handling |
| --- | --- | --- |
| S01 | Source identities and companions match | Verify internal headings and covered components as well as filenames; distinguish absent material from failed extraction. |
| S02 | Originals and exact source versions retained | Hash each source; resolve PDF page, printed label, block and crop references. |
| L01 | Native/scanned/mixed content handled correctly | Use OCR where needed; detect duplicate extraction and broken glyphs in native text. |
| L02 | Reading order and question boundaries correct | Check columns, indentation, shared stems, nested parts and cross-page continuation. |
| L03 | Page furniture excluded without losing content | Inspect margins/barcodes/codes; retain meaningful instructions and figure labels. |
| Q01 | Wording, answer spaces and choices separated | Retain equation blanks and complete option sets; prevent dotted lines moving into the next part. |
| Q02 | Science notation, numbers and units preserved | Inspect charges, degree symbols, powers, signs, decimal precision and uncertain spans against the source. |
| Q03 | Question inventory and marks reconcile | Check each part, question total and complete paper; flag conflicts rather than inventing values. |
| V01 | Every required question visual present and correctly scoped | Shared visuals link to all relevant parts; unrelated figures and private answer diagrams are excluded. |
| V02 | Full-page comparison confirms crop completeness | Include all source-provided labels, axis titles/units/numbers/ticks, grid extents, legends and annotations; inspect the actual rendered crop. |
| V03 | Source task and geometry preserved | Keep blank grids/answer areas blank; do not add solution data; preserve aspect ratio and original-scale measurement access. |
| V04 | Tables retain relationships and source image | Check headings, units, merged headers, all cells and intended blank response cells. |
| V05 | Accessible description is useful and answer-safe | Describe supplied information; distinguish question visuals, private model answers and report examples. |
| M01 | Exact scheme rules extracted, not merely linked | Associate correct rows, notes, points, alternatives and source codes with each part. |
| M02 | Scoring semantics and maxima preserved | Check any-N caps, combinations, duplicates, dependencies, follow-through, exclusions, tolerances and units. Unsupported rules remain manual-only. |
| M03 | Diagram model answers complete and private | Include essential bonds/labels; review focused scheme crops separately from question illustrations. |
| R01 | Report commentary and examples correctly associated | Follow headings and cross-page context; retain general advice separately; do not guess missing comments. |
| R02 | Handwriting and examiner annotations faithfully preserved | Retain original images and uncertainty; distinguish literal candidate transcription, examiner comments and derived advice. |
| R03 | Incorrect examples cannot become scoring authority | Preserve review context; do not infer marks absent from the report or promote candidate errors into accepted answers. |
| I01 | Proposed import is authorized, stable and reviewable | Use supported contracts/authenticated APIs, idempotent references and expected revisions. No direct database bypass. |
| I02 | Corrections preserve unrelated reviewed work and snapshots | Compare proposed/saved changes; replace all affected crop links, retain old snapshot assets and remove only resolved warnings. |
| I03 | Draft, approval, scoring readiness and publication remain distinct | Record unresolved blockers; protect private answers until the relevant server-authorized reveal. |

## Workflow evidence

Apply [workflow states and release](workflow-states-and-release.md). Record these checks separately from extraction fidelity:

| ID | Check | Evidence / handling |
| --- | --- | --- |
| W01 | Extraction completeness and associations | Expected versus extracted inventory; source identity/version and per-paper companion associations. Completion is not accuracy approval. |
| W02 | Manual image decisions complete | Required crops, labels and associations resolved; record explicit Not applicable where appropriate. |
| W03 | Final assessment is current | Latest saved content/source/visual fingerprints, exact evidence, source-specific confidence and model provenance; independently checked published-topic mappings and evidence. |
| W04 | Approval and release decisions are auditable | Human/AI approvals distinguished; AI threshold strictly above 75% plus independent gates. Required/released/excluded counts, unresolved blockers and explicit withdrawals retained. Formal-exam release separate. |
| W05 | Companion summaries are scoped and current | Independent extraction/link/check milestones per paper; missing, unchecked and verified no-comment report outcomes distinguished. Recompute affected states after material changes. |

Record unavailable automation as not run; do not simulate approvals/releases to complete the checklist.

## Release decision and regression evidence

Record failed/not-run checks with the exact question/subpart, source page/region, reason, proposed action and resolution/reviewer. Apply [import/review gates](akuru-import-validation.md); an incomplete checklist is not a declaration that the batch is release-ready. An optional missing report and an essential missing scoring rule do not have the same impact.

Compare with [reviewed examples](reviewed-examples.md): Q2 boundaries/options and grouped credit, Q3 external labels, Q5(c)(ii) private displayed-formula answers, and Q7 graph axes/scales. Add new layout/subject failures as independently checked cases. Keep written reference cases separate from executable tests and record which tests were actually run.

## Reassessment batches

Also follow [source comparison and confidence reassessment](source-comparison-and-confidence-reassessment.md). Record the frozen baseline, source-specific inspection scope, intended corrections, saved revisions/content hashes, append-only assessment versions and final threshold counts. Keep source conflicts and any untranscribed handwritten material explicit. Existing extraction triage and approvals must not be overwritten to meet a confidence target.

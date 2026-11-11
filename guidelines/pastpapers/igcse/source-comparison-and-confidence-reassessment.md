# Source comparison and confidence reassessment

Guideline ID: `akuru-igcse-source-comparison`

Version: `1.1.0`

Parent standard: `akuru-igcse-pastpapers` 1.5.0

Created: 2026-11-04

Last updated: 2026-11-11

Status: reusable review procedure; not a fully automated extraction or approval service.

## Purpose and applicability

Apply this procedure after initial extraction/import, or when an existing paper needs reassessment. It is based on the Chemistry source reviews and the [June 2025 Biology 1B/2B comparison](reviews/2026-11-04-june-2025-biology-source-comparison.md). Use it for any supported iGCSE subject, component, series or regional variant, adapting the subject-specific checks to the actual source. Success on one paper does not prove another paper is correct.

The objective is faithful, usable questions, marking evidence and examiner guidance with honest uncertainty. It is **not** to make every percentage exceed a target. Do not raise an import-time cap, copy an earlier paper's scores, or use an Admin approval as evidence of accuracy. Source-comparison confidence is an estimated judgement, not a measured error rate or a guarantee of automatic marking.

## Step 1 — Freeze a source-bound baseline

1. Identify the qualification, subject, syllabus/specification, year, series, component and variant. Match the paper, final scheme and report by their contents as well as filenames. Distinguish absent companions, provisional schemes and source-cover discrepancies.
2. Verify local originals against uploaded document/version SHA-256 hashes. Retain the original PDF unchanged. Record PDF page numbers and printed-page labels separately.
3. Fetch the current review through authenticated Admin APIs. Save an ignored, access-restricted snapshot of question/subpart content, revisions, statuses, reviewer metadata, source references, visual assignments and analysis versions/content hashes.
4. Agree the scope explicitly: papers, question/subpart counts, totals and any paid evaluation budget. Do not call a paid model API without budget authorisation. Do not export Student records for a source-content review.
5. Keep source PDFs, extracted licensed text, crops, private snapshots and credentials outside Git. The committed audit should contain findings, counts, methods and limitations rather than a reproduction of the papers.

## Step 2 — Compare every question and subpart with the paper

Use native text/layout for navigation and extraction, then inspect rendered source pages. Do not treat readable extracted text as proof that the layout or figures are complete.

- Reconcile the full question/subpart inventory, individual allocations, question totals and paper total. Retain a genuinely unlabelled whole question without inventing a lettered subpart.
- Check wording, reading order, shared stems, passage context, nested parts, cross-page continuations and complete multiple-choice options.
- Distinguish answer space from meaningful blanks. A line starting with dots can contain required continuation words. Check the count and order of gap-fill slots against the scheme.
- Remove printing furniture without removing meaningful question content. Preserve numbers, decimal precision, signs, charges, powers, units, formulae and intentionally empty response regions.
- Check tables cell by cell: headings, units, row/column relationships, merged headers, data and intended blank cells. Keep a source image where text alone is ambiguous.
- Inspect the **actual uploaded crop**, not only a freshly rendered local source. Compare every essential diagram/photo/table/graph with its full page. Retain all labels, arrows, scale bars, axis names, units, ticks, legends and grid boundaries.
- Treat vector clusters as candidates rather than independent figures. A comparison diagram with several labelled objects may need one complete crop. Assign shared or part-specific visuals according to relevance; do not attach a graph to every part simply because it is on the same page.
- Keep blank graphs blank. Preserve aspect ratio and original-scale access where measurement is required. Accessible descriptions must not disclose scheme-derived answers.

Record located defects before assigning a new confidence score.

## Step 3 — Compare each part with its exact scheme row

The saved rubric must contain the source criteria and instructions, not merely a link to the scheme.

- Inspect rendered answer and additional-guidance columns together. Check row identity, continuations, alternatives, accepted equivalents, exclusions and source point codes where available.
- Do not turn introductory phrases into creditworthy points. Numbered-list recognition must not split decimal values such as `0.683`, `67.9` or `40.82`.
- Preserve maximum credit, any-N rules, dependencies, alternatives, duplicate-credit constraints, combined responses, error carried forward and subgroup caps.
- For calculations, retain correct-answer credit, partial-method credit, tolerances, rounding/significant figures and unit requirements. A criterion containing “two marks” is not automatically a one-mark point.
- For drawing/plotting answers, distinguish private official/model-answer evidence from Student-facing question visuals. Missing model answers or unsupported geometric assessment must remain explicit.
- If the current scoring schema cannot express a rule faithfully, retain the exact instructions in the supported review fields and keep the part manual-only. Do not claim the prose is an executable scoring rule.
- When the paper, scheme prose, mark column or report disagree, record each source location and the unresolved conflict. Preserve the original sources and the paper's recorded allocation pending adjudication. Never silently rewrite the scheme using general subject knowledge or a report example.

## Step 4 — Compare the examiner report at subpart scope

- Recognise headings with or without spaces, nested labels and Roman numerals outside parentheses. Check physical continuation pages, including pages with images but no native text.
- Preserve shared pages when two discussions start on the same page. Stop question-specific associations before summary, grade-boundary and publication appendices.
- Link the actual relevant subpart discussion. Do not attach every report page for a question to every subpart.
- Distinguish examiner commentary, candidate handwriting, examiner annotations/awarded marks and newly derived advice. Candidate errors must never become accepted answers.
- Typed examiner prose can also be wrong. Verify numerical/graph claims against the paper and scheme, retain the report unchanged, and flag contradictory wording in clearly attributed derived advice.
- Distinguish `not_available`, `not_checked` and `no_comment`. Only use `no_comment` after checking the relevant report discussion/headings; absence of a successful text extraction does not prove absence of commentary.
- State the inspection boundary. Reading all typed commentary plus selected handwritten examples is not complete literal handwriting transcription. Retain original images and uncertainty where no reliable transcription was made.
- Record source limitations such as a draft/typesetting notice, a verified cover misprint, unclear handwriting or a missing final report.

## Step 5 — Prepare and apply controlled corrections

1. Prepare a private before/after diff and validate it against the supported API schema. Check counts and totals again. Keep curriculum mappings and unrelated Admin decisions unchanged unless the task explicitly includes their review.
2. Re-read current revisions before writing. If someone has edited the baseline, stop that update and reconcile; do not overwrite their work or manufacture a new expected revision.
3. Use authenticated, CSRF-protected Admin APIs and expected revisions. No direct database bypass. Save durable receipts. After an ambiguous interrupted write, read back before retrying; never blindly repeat it.
4. Render and inspect a replacement crop before attaching it. Preserve old assets needed by historical snapshots. Record a reviewed visual decision separately from question/subpart approval.
5. Read back the saved content and associations. Verify only intended fields changed. Question approval, assessment readiness, curriculum coverage, publication and Student access are independent gates; do not change them to increase confidence.

## Step 6 — Record an evidence-backed reassessment

Create a new append-only **accuracy** assessment after the corrections are saved. Do not overwrite original extraction triage or represent a later comparison as the original extraction.

For each subpart, record:

- Separate paper, scheme and report check statuses, inspected PDF pages, confidence estimates and specific reasons.
- Remaining defects, source conflicts and inspection limitations. Use no percentage for a source that was not checked or was unavailable.
- Actual interpretation method/provider and model identity when known, guideline/prompt/method versions and processing time. Keep native/OCR extraction provenance separate. Do not guess an unknown model ID.
- The exact current question revision/content hash and source versions/hashes required by the API.

For each question:

- Constrain its score by its weakest subpart and the relevant source checks. One unresolved part can keep the whole-question score low while other parts remain high.
- Respect the existing API rule: a `not_checked` source cannot support overall confidence above 70%. A missing optional report and an unchecked available report are different cases.
- Use a score above 70% only when the recorded comparison supports it. There is no mandatory 80%, 90% or 95% band. Serious unresolved ambiguity should remain lower even when most text is correct.
- Explain that source fidelity is separate from calibrated accuracy, scientific correctness of the publisher's source, automatic-scoring readiness and approval.

Retain earlier assessments as history. A materially changed draft makes its prior assessment outdated and requires a comparison bound to the new content. Never report an outdated assessment as current.

## Step 7 — Verify and report the result

Read back every assessment and verify its current content hash, question revision, source manifest and subpart labels. Confirm assessment-only writes did not alter content or approval metadata. Check the saved crop bytes against the inspected render when crops changed.

Report at least:

| Evidence | Required result |
| --- | --- |
| Inventory | Papers, questions, subparts and reconciled marks |
| Confidence | Separate question/subpart counts **strictly above** the requested threshold; list equal/below-threshold cases |
| Distribution | Ranges and, where useful, mean subpart confidence; do not compare unlike stages as measured error rates |
| Corrections | Material wording, visual, rubric and report changes with source locations |
| Remaining work | Source conflicts, unchecked material, manual scoring and approval/release blockers |
| Regression | Relevant executed tests; distinguish synthetic tests from licensed-source visual inspection |
| Production safety | Preserved unrelated content/approvals and normal authenticated API access |
| Provenance | Actual method/model identity or explicit unknown identity, versions, timestamps and private evidence locations |

Update the dated audit and applicable TODO. Do not mark an entire collection or Student launch complete because a two-paper source comparison passed. Code deployment and source-data updates should have separate evidence; apply normal backup/release checks if production code changes.

## Reference outcome and its limits

The 2026-11-04 Biology pilot recorded **14/16 questions and 74/76 subparts above 70%**, after correcting real extraction/association defects. Two source-instruction discrepancies remained at 65% and 70%. Those figures are historical pilot results, **not** target scores or defaults for future papers. The questions remained unreviewed and manual-only; confidence recording did not publish them.

Detailed findings and executed test evidence: [June 2025 Biology source-comparison audit](reviews/2026-11-04-june-2025-biology-source-comparison.md).

## Final-content workflow integration — 2026-11-11

Follow [workflow states and release](workflow-states-and-release.md), standard 1.5.0, for the agreed target workflow. This adds policy requirements without changing historical batch evidence. Curriculum review may be included only when explicitly in scope; final workflow reassessment must verify current mappings and exact published textbook evidence, recording mapping confidence separately. Image review precedes final assessment. Eligible content strictly above 75% may receive audited AI approval, then automatic Tutor release once implemented and verified. Neither a high score nor a metadata-only reassessment authorises release. Preserve assessment-only behaviour unless the guarded approval/release workflow is explicitly selected and authorised. Record any approval/release changes separately from source corrections and confidence history, including unresolved blockers, partial release counts and invalidated checks.

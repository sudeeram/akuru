# Enforce iGCSE past-paper analysis guidelines

Created: 2026-10-21  
Status: partially implemented locally; generic extraction/conformance work remains planned.

Standard: [akuru-igcse-pastpapers 1.1.0](../../../guidelines/pastpapers/igcse/README.md).

This plan extends the existing [official-paper review workspace](../ongoing/TODO-OFFICIAL-PAPER-REVIEW-WORKSPACE.md) and [Pearson intake pilot](../ongoing/TODO-PEARSON-CHEMISTRY-PAST-PAPERS.md). Do not duplicate their approval, access or publication mechanisms. Guideline documentation is in place. Only the implementation evidence explicitly listed below is complete; the remaining tasks are not implied by the documents.

## Step 0 — Establish source fixtures and baseline failures

- [ ] Capture exact source hashes and version-bound fixtures for June 2025 1C Q1 and Q2; keep licensed sources outside Git.
- [ ] Record Q2 boundary/option/furniture/rubric/report failures and preserve existing Admin-reviewed Q1 as a non-regression case.
- [ ] Use synthetic public fixtures for layout and scoring cases; make any private-fixture test requirements explicit.

## Step 1 — Formalise the import contract and provenance

- [ ] Implement a versioned executable proposal schema for nested context, response layout, choices, rubric groups, report examples and issues.
- [ ] Record guideline, layout-profile, schema and extractor versions with immutable source identity and hashes.
- [ ] Review required model/API/migration changes; do not silently flatten unsupported scoring rules into ordinary marking points.
- [ ] Add stable identifiers, dry-run validation and idempotent imports with expected-revision conflicts.

## Step 2 — Fix question boundaries and page layout

- [ ] Replace mark-line termination with label/geometry boundaries and cross-page continuation.
- [ ] Preserve shared context, all answer choices including the final part, and structured response spaces.
- [ ] Exclude repeated page furniture using geometry plus patterns, with a safe review fallback for unusual layouts.
- [ ] Retain scientific notation and correctly scoped visual/table proposals; flag clipped labels and uncertain boundaries.
- [ ] Pass Q2 a/b/c(i)/c(ii)/d, eight-mark total, answer-slot, choice and page-furniture regressions.

## Step 3 — Populate marking-rule proposals

- [ ] Parse scheme table cells and continued rows into the matching subparts.
- [ ] Preserve any-N groups, score caps, alternatives, dependencies and scoped ACCEPT/ALLOW/IGNORE instructions.
- [ ] Separate source marking codes from semantic point types and keep choice correctness private.
- [ ] Show editable proposed rules beside exact scheme evidence; require explicit review before assessment use.
- [ ] Test Q2(a)'s any-two-of-four cap, combined-response rule, Q2(c)'s linked requirements and charge notation.

## Step 4 — Interpret report commentary and handwriting

- [ ] Separate general guidance, candidate images, transcripts, examiner comments and explicitly awarded marks.
- [ ] Associate continuation across pages and distinguish comments on a previous example from a newly introduced example.
- [ ] Add optional bounded vision transcription for relevant image regions, with visible uncertain spans and editable source comparison.
- [ ] Keep incorrect candidate responses out of trusted-answer retrieval; test missing reports and unmentioned subparts.

## Step 5 — Integrate validation and Admin review

- [ ] Implement import-blocking, approval-blocking and advisory issues with exact part/source locations.
- [ ] Keep incomplete draft saves available and make next actions clear without duplicate evidence-link confirmation.
- [ ] Show re-analysis as a diff; preserve Admin edits and existing approvals until an explicit revision decision.
- [ ] Test authentication, roles, CSRF, stale sources, concurrent edits, cross-paper sources and safe retries.
- [ ] Verify question payloads for formal assessments exclude rubric answers and examiner examples.

## Step 6 — Prove conformance and prepare release

- [ ] Run all reference cases plus representative 1C/2C questions and alternative-layout synthetic fixtures.
- [ ] Complete accessible Admin review acceptance for choices, nested context, rubric groups and annotated report examples.
- [ ] Record which rules were actually validated and which require manual review; update user/developer documentation.
- [ ] Prepare a reviewed rollout and selective re-analysis plan; do not bulk overwrite approved production questions.
- [ ] Deploy only as part of an authorised implementation release, then verify affected drafts through authenticated APIs. Question approval and Student publication remain separate decisions.

## Source-reviewed draft evidence

- 2026-10-21: [June 2025 1C Q3–Q10 re-analysis](../../../guidelines/pastpapers/igcse/reviews/2026-10-21-june-2025-1c-q3-q10.md). Manual draft corrections do not complete the generic implementation tasks above. Include the identified clipped crops, conditional scoring, capped groups and combined scheme blocks in regression coverage.

## Implemented locally — structured scoring (2026-10-21)

- [x] Add private versioned unit-credit rules for nested/disjoint groups, accepted equivalents, combined responses and required full-credit points.
- [x] Compile and freeze paper-specified subpart limits into official rubric versions and assessment snapshots; add migration 0013.
- [x] Enforce score caps in backend code after validated model evidence matching; retain raw decisions and final credit allocation.
- [x] Separate content approval from automatic-marking readiness in Admin controls and server release checks.
- [x] Avoid negative mastery/weakness evidence for capped correct points and unused optional alternatives.
- [x] Add synthetic Q2(a)-style scoring cases and authenticated workspace-to-official-rubric integration tests.
- [ ] Deploy the additive migration and application changes as a reviewed release, then configure Q2(a)'s equivalents/combined rule and confirm each subpart's readiness through the Admin API/UI.

This completes the Q2(a) any-two/combined-response capability locally, not the whole plan. Generic PDF parsing, conditional zero-score exclusions, alternate allocation paths, handwritten report interpretation and the remaining extraction rules are still planned. Existing production approvals are not changed by local development.

# January 2023 Biology standard 1B/2B — source comparison and AI review

Started: 2026-11-08. Completed and production-verified: 2026-11-08.

## Scope

Source-compare and correct the **existing** Pearson Edexcel International GCSE Biology January 2023 standard 1B and 2B workspaces against guideline 1.4.0. No duplicate imports, replacement source PDFs, textbook publication changes or Student release. All subparts retain manual-only assessment.

| Paper | Questions | Subparts | Marks | Questions above 75% | Subparts above 75% | Subpart range | Mean estimate |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| 1B | 10 | 47 | 110 | 7 | 44 | 70–90% | 88.2% |
| 2B | 6 | 31 | 70 | 6 | 31 | 85–90% | 89.2% |
| Total | 16 | 78 | 180 | 13 | 75 | 70–90% | 88.6% |

These percentages are informed source-fidelity estimates, not calibrated accuracy, human approval or automatic-marking readiness. Historical extraction triage remains separate and unchanged (previous subpart estimates 55–60%).

Production links:

- [1B review](https://akuru.magicalinternational.com/admin/exam-documents/review/7088b704-e93e-482e-85e6-aee43ea93f68) · [accuracy and review statuses](https://akuru.magicalinternational.com/admin/exam-documents/review/7088b704-e93e-482e-85e6-aee43ea93f68/accuracy)
- [2B review](https://akuru.magicalinternational.com/admin/exam-documents/review/e4643895-278b-4018-b8fa-e837dcc3cd0f) · [accuracy and review statuses](https://akuru.magicalinternational.com/admin/exam-documents/review/e4643895-278b-4018-b8fa-e837dcc3cd0f/accuracy)

## Executed source checks

- Verified all six local PDF SHA-256 values against production checksums before writes. Physical question/scheme/report page counts: **1B 32/25/9; 2B 20/22/9**.
- Inspected all 16 question/scheme contact sheets, all 31 existing production crop images, and all 11 rendered narrative-report pages: 1B pages 3–8 and 2B pages 3–7. These reports contain narrative discussion; no candidate handwriting was found in these inspected sections.
- Inspected 28 replacement crop renders: 27 question visuals and one private official-scheme answer. Preserved original source content, including deliberate blanks and source typesetting errors.
- Retrieved all 22 published Biology topic records and evidence. Mapped concepts to same-subject published topics, retaining question-supplied contexts as such. For example, micropropagation maps to Topics 20 and 22; the novel dialysis-device context draws on kidney and diffusion concepts rather than claiming the textbook contains that exact device description.
- Appended source-specific accuracy/provenance assessments with guideline 1.4.0, method `biology-source-comparison-v1` and January 2023 prompt version. Codex-assisted review; exact conversation model identity unavailable and not guessed. No paid model API calls.

## Corrections

### Question text and visuals

- Reconstructed milk nutrition, moth counts, potato mass, enzyme blanks, urinary-system choices, pin-trial/mode/median and cattle-genotype tables. Preserved row/column identity, units and empty Student answer cells.
- Restored superscripts/subscripts in formulae, genetic alleles, areas and standard form. Kept the photosynthesis equation answer private; corrected the question's inverse-square light-intensity formula without filling its answer.
- Removed barcode/control-character debris, isolated passage line numbers and flattened diagram-label fragments. Complete crops carry the original labels and spatial relationships.
- Replaced clipped flower and nutrition-panel images, an incomplete calorimeter label region and fragmented river graphs. All figure axes, arrows, legends and nearby explanatory labels remain inside their source crops.
- Attached each question visual only to applicable subparts; retained cross-page data/context where required. Unused candidate fragments were detached, not deleted from source storage.
- Attached the official septum-position answer crop privately to **1B Q2(a)(i)** and declared the drawing response. The unmarked question heart remains a separate question visual. No model-generated answer diagrams were invented.

### Exact rubrics and report associations

- Replaced broad links with subpart-specific paper, exact labelled scheme and narrative-report evidence. Preserved report continuations and flagged the 2B Q4 report's b(ii) heading that actually discusses b(i) calorimetry.
- Found a native table-parser failure: multiline question labels caused 2B Q3(b)(ii) criteria to be associated with Q2(b)(ii), Q5(a)(ii) criteria with Q2(a)(ii), and Q5(b)(iii) to be omitted. Filtered parser rows by independently checked source pages and manually reconstructed the missing exact rubrics. **The generic parser itself is not fixed by these data corrections.** Future batches must still verify both complete question labels and page identity; row presence alone is insufficient.
- Preserved MC answer letters, accepted calculation ranges, method-credit alternatives, combined-response rules, follow-through restrictions and per-subpart maxima. In particular, 2B Q2(b)(iii) awards two marks for all four mode/median values, not one per cell; Q3(b)(i) awards one mark for all three genotypes together.
- Recorded relevant combined responses and explicit feature–effect pair requirements. The two-pair maxima in 2B Q1(c) and Q4(b)(iii), CORMS alternatives and source-listed conditional credits remain manual interpretation, not a claim that a flat-point representation can score them automatically.
- Checked calculations independently, including 1B Q4's difference between percentages, Q6 cylinder area/final length, Q9 inverse-square distance, 2B population standard form and rainforest decrease.

## Source conflicts and remaining content gates

| Subpart | Handling |
| --- | --- |
| 1B Q3(a)(i) | **70%**: scheme p8 refers to more “(saturated) fat”, but both milk panels give 0.5 g saturated fat. Corrected criterion distinguishes total fat (5 g versus 2.5 g); source conflict retained for Admin adjudication. |
| 1B Q6(c)(i) | **70%**: report p6 says water enters potato in concentrated sucrose; measured mass loss and the scheme show water leaving. Corrected advice explicitly flags the contradiction. |
| 1B Q7(c) | **70%**: report p6 refers to stronger dogs surviving, although the question and scheme concern benefit to the prey species. Corrected advice retains the prey beneficiary. |
| 1B Q4(b)(i) | Plotting criteria checked, but no completed official model graph. An approved, correctly attributed worked graph is needed before content approval. The blank question grid is not an answer. |
| 2B Q3(b)(ii) | Genetic-cross criteria checked, but no official rendered worked cross. Needs an approved worked illustration; private text criteria are retained separately. |

Other source anomalies are explicitly recorded without silently changing the original PDFs:

- 1B Q6(c)(ii): incorrectly typeset intermediate equalities/signs; independently checked final range 4.28–4.3 cm agrees with the accepted answer.
- 2B Q5(a)(i): misprinted intermediate rainforest-axis ticks; original graph preserved. Clear endpoints give (41 200 − 40 000) / 25 = 48 km²/year, matching the scheme.
- 2B Q5(a)(ii): imprecise greenhouse “reflection” wording; reviewed criteria describe retention of outgoing heat and keep original evidence linked.

## Verification

- All save payloads schema-validated before writes; optimistic revisions and six source checksums verified. Current question content read back after correction; human statuses and historical extraction fields preserved.
- Focused Biology intake, accuracy/provenance, AI-approval, official-review and confidence tests: **73 passed**. Initial root-directory invocation lacked the backend import path; the corrected invocation was blocked from PostgreSQL by sandbox networking, and the approved rerun passed using rollback fixtures. Existing dependency deprecation warnings remain.
- Final explicit production AI-policy/read-back verification: **1B 6/10 questions and 43/47 subparts AI-approved; 2B 5/6 questions and 30/31 subparts AI-approved**. Total **11/16 questions and 73/78 subparts**. The five pending parts are exactly those listed above. All 16 current accuracy content hashes and read-back assessment payloads matched.
- All 28 production crop files matched equivalent 180-DPI original-PDF renders byte-for-byte. Seven protected Chemistry/previous Biology workspaces remained unchanged. Human-review metadata and historical extraction analyses were preserved.
- Unauthenticated requests to both protected review APIs returned **401**; the routed 1B accuracy-page frontend returned **200** over certificate-verified HTTPS.
- Both papers remain `wholePaperReady=false`, `assessmentReleaseReady=false`, `automaticAssessmentReady=false`; all 78 subparts remain `manual_only`. AI content approval is not Student release.
- No app deployment, service restart or schema migration was required: corrections used authenticated, CSRF-protected Admin APIs. No direct database writes. Unrelated local application changes were not deployed.
- Fourteen of 44 Biology papers now have this depth of source comparison; **30 remain**. The next chronological batch is January 2023 regional 1BR/2BR. This batch is complete with explicitly retained content gates, not a claim that the historical collection or Student-release work is complete.

Licensed source files, crops, credentials and private receipts remain in ignored source/temporary folders. Only the audit summary belongs in Git.

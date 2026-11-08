# January 2023 Biology regional 1BR/2BR — source comparison and AI review

Started: 2026-11-08. Completed and production-verified: 2026-11-08.

## Scope and confidence

Correct the **existing** Pearson Edexcel International GCSE Biology January 2023 regional 1BR and 2BR review workspaces against guideline 1.4.0. No duplicate imports or replacement source PDFs. Manual-only scoring and separate Student-release gates are retained.

| Paper | Questions | Subparts | Marks | Questions above 75% | Subparts above 75% | Subpart range | Mean estimate |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| 1BR | 11 | 45 | 110 | 10 | 44 | 70–90% | 88.6% |
| 2BR | 7 | 27 | 70 | 6 | 26 | 70–90% | 88.2% |
| Total | 18 | 72 | 180 | 16 | 70 | 70–90% | 88.5% |

Confidence is an informed source-fidelity estimate, not measured accuracy, human approval or automatic-scoring readiness. Historical extraction triage and prior analyses remain separate and preserved.

Production links:

- [1BR review](https://akuru.magicalinternational.com/admin/exam-documents/review/a3ff379a-1810-43d0-b5b4-094c6c68de9f) · [accuracy and review statuses](https://akuru.magicalinternational.com/admin/exam-documents/review/a3ff379a-1810-43d0-b5b4-094c6c68de9f/accuracy)
- [2BR review](https://akuru.magicalinternational.com/admin/exam-documents/review/367ab4b0-414c-4a60-ac4c-c8e017e206b2) · [accuracy and review statuses](https://akuru.magicalinternational.com/admin/exam-documents/review/367ab4b0-414c-4a60-ac4c-c8e017e206b2/accuracy)

## Executed inspection

- Verified six local PDF SHA-256 hashes against production source checksums before writes. Physical question/scheme/report page counts: **1BR 32/26/10; 2BR 24/16/6**. Native text extracted across all supplied pages.
- Inspected all 18 question/scheme contact sheets and all 30 existing production crop images against their source contexts. Read the full question-specific report commentary and inspected all nine corresponding rendered pages: 1BR PDF pages 3–8; 2BR pages 3–5. These inspected sections contain narrative, not handwritten candidate examples.
- Inspected all 28 final question-crop renders. Expanded bounds again where first local previews still clipped the food-web mouse label, test-tube edge, plant tips or reproductive-anatomy outline. Only the final inspected bounds were uploaded.
- Retrieved all 22 published Biology topic evidence sets and checked relevant source passages before mapping. Chemical coordination in plants maps to **Topic 12**, distinct from Topic 11 transport. Micropropagation maps to Topic 20/22; no reconstructed primary-PDF positions were invented as permanent textbook-page references.
- Recorded source-specific accuracy/provenance under `biology-source-comparison-v1`, guideline 1.4.0 and the January 2023 regional prompt version. Codex-assisted analysis; exact conversation model identity unavailable and not guessed. **No paid model API calls.**

## Material corrections

### Wording, tables and visuals

- Reconstructed gas composition, milk nutrition, ant treatments, chromosome-count choices, pollen-tube results, photosynthesis results, patient urine composition and field/species counts as rows with units and column relationships.
- Restored all **seven** chemical-coordination gap-fill slots and all **six** micropropagation slots. The initial micropropagation extraction had lost two blanks and surrounding wording. Restored the three photosynthesis equation blanks and retained the supplied `+ 6O₂` without leaking the answers.
- Preserved the intentionally empty species-B/field-Y mean. Retained the source milk-table fat unit **mg**, rather than silently substituting g. Restored squared units, genetic/calculation notation and food-chain arrows.
- Removed page furniture, passage line-number debris and flattened diagram text where a complete source crop carries the spatial relationships.
- Replaced the clipped food web, incomplete milk-table boundary, isolated lamp, fragmented wildflower illustrations without species captions, partial reproductive anatomy, and graph misclassified as a table with incomplete axes/key.
- All final visuals are source-only and scoped to relevant subparts. Measurement of 1BR Q2(a)(ii) must use the original-scale PDF; a responsive screen crop is not a physical millimetre ruler. Blank grids remain blank.

### Marking and examiner guidance

- Checked every subpart against its exact question-labelled scheme block and independently verified page range. Reconstructed 1BR Q7(c)(ii), whose multiline label was missed/mis-associated by the native parser. The generic parser remains a separate hardening task.
- Restored 2BR Q2(b)(ii)'s positive-colour criterion from its continuation on scheme p8. Split the three 2BR Q5(a) structure answers into separate one-mark criteria.
- Preserved correct-answer credit, accepted ranges, method alternatives, follow-through, per-part maxima and conditional pairing. Examples include magnification, per-mouse energy, calcium scaling, stomatal density and signed percentage-change differences.
- Explicitly retained matched pairs for wind-pollination features, abiotic-factor controls and named hormone/functions. Seven CORMS criteria remain capped at six marks; the source's time-to-remove-stain alternative is retained. Relevant combined responses are recorded, but these prose/flat-point records do not imply automatic scoring.
- Replaced broad report links with subpart-specific narrative page ranges and attributed summaries. The 1BR report paragraph labelled Q5(c) discusses Q5(d); Q5(c) is recorded as **no separate comment after checking**, rather than pretending the wrong paragraph is its direct commentary.
- Source errors are distinguished from extraction errors: the aphid is the only correct listed primary-consumer option, not the only primary consumer in the whole food web; the milk discussion mentions iron although the table has no iron data; the correct Q7(a) B row is retained despite incorrect distractor explanations.
- Flagged the 2BR Q1(d)(ii) report's apparent missing “not” about enzyme-collision answers. Retained the scheme's evaporation/diffusion explanation. Explained the sign typo in Q6(a)'s intermediate subtraction while preserving the accepted 94–106 difference range and method credit. Kept vaccination wording within its stated exam scenario rather than presenting it as personal medical guidance.

## Remaining content gates

| Subpart | Required follow-up |
| --- | --- |
| 1BR Q3(b)(iii) | **70%**: scheme p9 allows one mark for “excrete faeces”, while report p4 correctly warns against that terminology. Teach egestion; preserve the exact source exception for Admin adjudication. |
| 2BR Q3(b) | **70%**: report p4 says species A varies least within field X. Actual ranges A=6, B=10, C=3 show C varies least. Corrected advice flags the report claim; Admin adjudication retained. |
| 1BR Q3(b)(i) | Pyramid criteria checked, but no completed official drawing in the scheme. Needs an approved, correctly attributed worked illustration. |
| 1BR Q5(b) | Plotting criteria checked, but no completed official graph. Needs an approved worked illustration; the question grid remains blank. |
| 1BR Q8(b)(iii) | Genetic-cross criteria/probability checked, but no official rendered worked cross. Needs an approved worked illustration. |

No diagram was fabricated or mislabelled as official to bypass a content gate. Qualifying sibling subparts can receive AI approval independently; question-level approval remains blocked where appropriate.

## Verification

- Validated all 18 save payloads, 72 part allocations and 180 marks; checked optimistic revisions and six production source checksums. Saved durable private baselines and per-question/per-crop receipts.
- Corrected content read back after authenticated, CSRF-protected Admin API writes. Human statuses and historical triage preserved; no direct database writes.
- Focused local Biology intake, accuracy/provenance, AI policy, official review and confidence tests: **73 passed**, using local PostgreSQL rollback fixtures. Existing dependency deprecation warnings remain.
- Protected review APIs for both papers reject unauthenticated requests with **401**. Both accuracy-page frontend routes return **200** over certificate-verified HTTPS.
- Explicit final policy/read-back results: **1BR 8/11 questions and 41/45 subparts AI-approved; 2BR 6/7 questions and 26/27 subparts AI-approved**. Total **14/18 questions and 67/72 subparts**. Exactly the five listed content gates remain pending. All current accuracy content hashes and prepared assessment payloads matched the production read-back.
- All 28 production crop files matched equivalent 180-DPI original-PDF renders byte-for-byte. Nine protected workspaces remained unchanged: Chemistry 1C, June 2024 Biology, November 2023 standard Biology and January 2023 standard Biology.
- Both papers remain `wholePaperReady=false`, `assessmentReleaseReady=false` and `automaticAssessmentReady=false`; all 72 parts remain `manual_only`. No Student release or executable scoring changes.
- No app deployment, migration or service restart was required; unrelated local application changes were preserved. Source changes used the existing authenticated Admin APIs.
- Sixteen of 44 Biology papers now have this depth of source comparison; **28 remain**. The next supplied chronological batch is June 2022 standard 1B/2B, followed by its regional variants. This is a completed source-comparison batch with explicit outstanding content gates, not completion of the historical collection or Student release.

Source PDFs, extracted licensed content, crops, credentials and detailed receipts remain in ignored source/temporary folders. Only the audit summary belongs in Git.

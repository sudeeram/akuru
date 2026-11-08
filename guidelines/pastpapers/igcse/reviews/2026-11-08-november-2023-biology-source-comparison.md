# November 2023 Biology standard 1B/2B — source comparison and AI review

Started: 2026-11-08. Completed and production-verified: 2026-11-08.

## Scope

Update the **existing** Pearson Edexcel International GCSE Biology November 2023 standard 1B and 2B workspaces, using the 1.4.0 guidelines. No duplicate imports, source-document replacement, textbook publication or Student-release changes.

| Paper | Questions | Subparts | Marks | Questions above 75% | Subparts above 75% | Subpart range | Mean estimate |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| 1B | 10 | 45 | 110 | 9 | 44 | 70–90% | 88.8% |
| 2B | 6 | 32 | 70 | 6 | 32 | 88–90% | 89.8% |
| Total | 16 | 77 | 180 | 15 | 76 | 70–90% | 89.2% |

Confidence is an informed **source-fidelity estimate**, not measured accuracy, a human decision, or proof of automatic-marking readiness. The one deliberately low assessment is a genuine conflict in the official sources. Historical extraction triage and earlier analysis records remain preserved.

Production links:

- [1B review](https://akuru.magicalinternational.com/admin/exam-documents/review/f76cf6eb-6ac4-4ba9-ac94-e1efca190529) · [accuracy and review statuses](https://akuru.magicalinternational.com/admin/exam-documents/review/f76cf6eb-6ac4-4ba9-ac94-e1efca190529/accuracy)
- [2B review](https://akuru.magicalinternational.com/admin/exam-documents/review/d1c98f7b-4939-4a2a-bb78-d853e5567404) · [accuracy and review statuses](https://akuru.magicalinternational.com/admin/exam-documents/review/d1c98f7b-4939-4a2a-bb78-d853e5567404/accuracy)

## Source inspection

- Verified all six local PDF SHA-256 values against production document checksums before writes. Question/scheme/report page counts: 1B **36/24/9**, 2B **20/19/8**.
- Inspected all 16 combined question/scheme contact sheets and all 23 existing production candidate crops. Read the full question-specific narrative reports and inspected all 11 corresponding rendered pages: 1B PDF pages 3–8 and 2B pages 3–7. These reports contain narrative commentary, unlike the longer handwritten-example reports in some other sessions.
- Inspected 20 final crop renders: 19 question visuals and one private official-scheme answer diagram. The production crop bytes were compared with equivalent 180-DPI renders from the original PDFs.
- Retrieved the 22 published Biology topic records and evidence; checked relevant published passages before assigning topic support. Did not substitute reconstructed primary-PDF positions for permanent printed-page references.
- Recorded source-specific, append-only accuracy analyses with `biology-source-comparison-v1`, guideline 1.4.0 and the dated November 2023 prompt version. Analysis was Codex-assisted; exact conversation model identity was unavailable and is not guessed. **No paid API calls** were used.

## Corrections

### Wording and visual scope

- Reconstructed dilution, potato-mass, breathing-rate, sterilisation, catalase and mutation-rate tables, retaining units, original values and deliberately empty student answer cells.
- Restored all eight bacteria gap-fill blanks and their surrounding sentences; retained separate process-answer slots in the nitrogen-cycle question.
- Restored subscripts, superscripts, standard form and the hydrogen-peroxide reaction arrow. Removed barcode/control-character debris and passage line-number artifacts without deleting meaningful student blanks.
- Replaced the fragmented nitrogen cycle with its complete arrows, process labels and ion formulae. Replaced separate blood samples with the complete comparison and cell key. Replaced reproductive-anatomy fragments with complete labelled paired anatomy and a clean male-only crop.
- Reviewed the remaining source crops, with source-only accessible descriptions. Assigned visuals to applicable subparts; graph/table contexts from earlier pages remain linked where needed. Detached redundant candidate fragments without deleting their source assets.
- Attached the official marking-scheme sperm-duct-cut diagram privately to **1B Q8(b)(i)**. It is an answer visual, not a question illustration. The subpart now correctly declares a drawing response.

### Marking schemes and reports

- Linked each subpart to the exact question-labelled scheme block, rather than a broad page or unrelated neighbouring entry.
- Preserved MC option letters, decimal/area/standard-form calculations and alternative method-credit instructions. Calculation answers are not split at decimal points.
- Retained the six-mark maximum for seven CORMS criteria in 1B Q10. Recorded the explanation-point maximum in 2B Q5(b)(i), the treatment-point maximum in 2B Q6(b), and source-supported combined responses in the synapse/stem-cell criteria. These records do **not** turn on automatic marking; all 77 subparts remain `manual_only`.
- Replaced broad report associations with subpart-specific physical page ranges and concise attributed advice. Preserved source-heading errors as explicit notes, including 2B Q3's repeated a(ii) heading and 1B Q9's loose c heading.
- Clarified no **net** water movement at equilibrium and the finite-sample limitation of a genetic test cross, while retaining original source evidence.

### Curriculum coverage

- Confirmed 74 subpart mappings against published Biology topic content.
- Left **1B Q8(b)(i), Q8(b)(ii), Q8(c)** as `partial_or_uncertain`: Topic 9 supports reproductive anatomy and fertilisation, but the specific sterilisation procedures and clinical comparison were not confirmed as fully taught in the published textbook. This is not a claim of full cumulative Student eligibility.
- No invented printed-page numbers, curriculum access changes or automatic textbook revisions.

## Remaining genuine gates

| Subpart | Handling |
| --- | --- |
| 1B Q4(a) | **70%**: report PDF p4 reverses the blood-cell comparison. Diagram and scheme indicate fewer red cells and more white cells in the blood condition. Explicitly flagged for Admin adjudication; not AI-approved. |
| 1B Q3(b)(ii) | Source content checked, but scheme gives plotting criteria without an official completed graph. Needs an approved, correctly attributed worked-answer diagram before content approval. The blank question grid is not a model answer. |
| 1B Q5(b)(i) | Source content checked, but scheme supplies genetic-cross criteria without an official rendered cross. Needs an approved worked-answer illustration; do not relabel text criteria or fabricate an official diagram. |

AI approval is distinguished from manual approval and publication. Root questions containing one of these pending parts remain unreviewed; other qualifying subparts can be AI-approved independently. Student release and validated scoring remain separate gates.

## Verification and approval-policy fix

- Six source checksums, optimistic revisions, all 16 save payloads, 77 part allocations and 180 marks checked. Durable private per-crop/per-question receipts and pre-change baselines retained.
- Corrected content read back; historical extraction fields and human decisions preserved. Fresh analyses verified against current content hashes. Five protected Chemistry/other Biology workspaces remained unchanged.
- Twenty production crop files verified byte-for-byte. Private answer assets stay on their exact scheme version.
- Found an existing substring bug in the visual requirement: “suitable” and “notable” were treated as references to a “table”. Fixed whole-word singular/plural detection; real diagram/table requirements still block missing visuals. Added four database-backed regression cases.
- Focused intake, staging, accuracy and AI-approval tests: **74 passed**; adjacent official-review/private answer-visual tests: **21 passed**, for **95 relevant tests** in total. Existing dependency deprecation warnings remain. The initial sandbox run could not connect to PostgreSQL; the approved rerun passed. One root-directory invocation lacked the backend import path and was corrected.
- Deployed tested fix `b3357ab0b2b51747c1f462584211b0cb9f91aa96` after the standard encrypted database/document backup. Migration remains `0020_question_ai_approval`; no new migration was needed. HTTPS, security headers, routed entry points, service health, backup/retention timers and loopback binding passed release acceptance. Protected API requests without authentication return 401; the accuracy-page frontend route returns 200. The local Python HTTPS check required its installed CA bundle; certificate verification remained enabled.
- Final explicit AI-policy/read-back verification: **1B 7/10 questions and 42/45 subparts AI-approved; 2B 6/6 questions and 32/32 subparts AI-approved**. Total **13/16 questions and 74/77 subparts**. The three remaining parts are exactly the genuine gates listed above; the substring bug no longer blocks Q7/Q9. All current accuracy hashes, 20 crop bytes and five protected workspaces verified again after deployment. Student release and manual-only scoring are unchanged.
- Twelve of 44 Biology papers now have this depth of source comparison; **32 remain**. This is a completed comparison/AI-review batch with explicitly pending content adjudication, not a claim that all questions are released to Students.

Licensed sources, crop images, payloads, credentials and detailed receipts stay in ignored `tmp/biology-november2023-review/` and the ignored source collection; only this summary belongs in Git.

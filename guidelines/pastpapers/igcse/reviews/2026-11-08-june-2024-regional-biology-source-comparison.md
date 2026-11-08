# June 2024 Biology regional 1BR/2BR — source comparison

Started: 2026-11-08. Completed: 2026-11-08.

## Scope and outcome

Corrected the **existing** production draft workspaces for Pearson Edexcel International GCSE Biology June 2024 regional 1BR and 2BR. No duplicate papers were imported. The work applies the 1.4.0 source-comparison procedure, separately from the standard June 2024 papers.

| Paper | Questions | Subparts | Marks | Questions above 75% | Subparts above 75% | Subpart range | Mean subpart estimate |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| 1BR | 10 | 46 | 110 | 9 | 45 | 70–92% | 87.8% |
| 2BR | 6 | 31 | 70 | 4 | 29 | 70–92% | 86.6% |
| Total | 16 | 77 | 180 | 13 | 74 | 70–92% | 87.3% |

The above-70% counts are the same as the above-75% counts. Three subparts deliberately remain at 70% because of publisher-source conflicts. These estimates judge source fidelity after comparison, **not empirically measured correctness, validated automatic scoring, or Admin approval**. Original extraction-triage records remain historical and become non-current where the content has changed; their stored content/provenance is preserved.

Production links:

- [1BR question review](https://akuru.magicalinternational.com/admin/exam-documents/review/941ca3a3-8f3e-4c34-83d4-584f0fed6d9f) · [accuracy assessment](https://akuru.magicalinternational.com/admin/exam-documents/review/941ca3a3-8f3e-4c34-83d4-584f0fed6d9f/accuracy)
- [2BR question review](https://akuru.magicalinternational.com/admin/exam-documents/review/1e947ce0-7633-4207-9b4b-1a2ad9c25981) · [accuracy assessment](https://akuru.magicalinternational.com/admin/exam-documents/review/1e947ce0-7633-4207-9b4b-1a2ad9c25981/accuracy)

## Inspection and provenance

- Matched all six original local PDF SHA-256 values to production document checksums before corrections. Question/scheme/report lengths are 36/27/117 PDF pages for 1BR and 24/17/75 for 2BR.
- Inspected all 16 combined question/scheme contact sheets, all 36 actual saved production crops, and eight complete replacement crops rendered from the original question PDFs.
- Read the typed question-specific report commentary and checked exact subpart headings and physical continuation ranges. Image-only continuation pages remain linked, notably the extended 1BR Q8(a)(i) genetic-diagram discussion.
- Inspected 40 selected report page renders: 1BR pages 5, 11, 19, 24, 32, 40, 43, 51, 57, 65, 77, 79, 82, 88, 91, 94, 99, 104, 110 and 113; 2BR pages 8, 11, 14, 19, 23, 26, 29, 34, 38, 40, 44, 49, 53, 56, 58, 59, 62, 66, 69 and 72.
- Candidate examples, including incorrect answers and handwriting, remain private original evidence. No exhaustive handwriting transcription is claimed. Introductory examiner commentary is attributed and kept distinct from model answers and source-comparison notes.
- Appended source-specific accuracy/provenance records with method `biology-source-comparison-v1`, guideline 1.4.0, prompt version and UTC processing time. Interpretation was Codex-assisted; exact conversation model identity was not exposed, so no model name/ID was guessed. No paid OpenAI API calls were made.

## Corrections

### Question text and diagrams

- Removed barcode/footer debris and redundant dotted response lines without supplying student answers. Removed passage line-number artifacts from 2BR Q1 while retaining the questions' line references.
- Reconstructed table contexts for the red-cell MC options, amylase trials, water balance, degu seasonal measurements, heat-strain groups and gas-exchange indicator results. Original values, units and intentionally missing answer cells remain intact; original table images are available alongside the text.
- Restored the airway-order arrows, cubic/square units, carbon-dioxide subscripts and standard-form calculation notation.
- Created eight inspected replacement visuals: 1BR onion cells with all labels; paired Before/After micrographs; seasonal graph with full four-item key; coronary-risk graph with full scale and smoker key; complete pedigree with all five individuals and four-symbol key; photosynthesis graph with complete axis arrows and curve labels; 2BR paired fish-farm photos with original captions; and the full A–E test-tube comparison with labels.
- Assigned applicable visuals to subparts rather than displaying every question candidate everywhere. The paired fish-farm photographs remain shared passage context. Replaced fragments were detached from question candidate lists, not deleted from source storage. Original unchanged assets retain their existing visual-review state; the eight inspected replacements have reviewed-crop receipts. Question/subpart approval was not granted.

### Marking criteria

- Re-extracted answer-column criteria separately from official guidance; narrowed scheme links to the actual rubric page. Non-credit introductory text is not an awardable point.
- Repaired missing MC points in 2BR Q2(a), Q3(a)(i) and Q3(a)(ii).
- Kept decimal values, rounding, standard form and partial-credit alternatives together, including 1BR pollen magnification, alveolar area, amylase mean and percentage increase; 2BR water loss, scaled food-water input and deforestation calculations.
- Preserved the “two consumers for one mark” rule in 1BR Q5(a)(ii), structure/function pairing in Q3(b)(iii)/Q7(a)(i), combined-response credit in Q3(a)(iii), Q4(c)(iv), Q8(a)(iii) and Q10, and genetic-diagram follow-through limits in Q8(a)(i).
- Preserved combined credit for 2BR degu ratios, arteriolar constriction and the both-definitions-for-one-mark gene/genome response.
- Source instructions are visible in manual-only readiness notes. These corrections do **not** assert that every conditional rubric is implemented as executable scoring rules. All 77 parts remain `manual_only`.

### Reports and unresolved source conflicts

Report links now follow the specific subpart discussion and its physical continuation pages. Unrelated broad report links were removed where the report provides no dedicated comment; the accuracy record explicitly uses `no_comment` rather than inventing advice.

| Subpart | Confidence | Source limitation and handling |
| --- | ---: | --- |
| 1BR Q7(b)(ii) | 70% | Report PDF p77 calls smokers with few alleles lowest risk; the graph and scheme show non-smokers with few alleles lowest. The contradiction is explicitly flagged and must not be taught as correct. |
| 2BR Q2(b)(ii) | 70% | Scheme PDF p7 prints `0071` in an intermediate calculation; report p26 says multiplication by 100 despite the required mass scaling being by 110. Correct final range is 0.77–0.80 litres; source originals and conflict notes remain available for manual adjudication. |
| 2BR Q3(b) | 70% | Scheme PDF p11 includes “no information on age”, but the paper supplies mean ages 24 and 69. The draft flags this invalid unqualified alternative; legitimate limitations such as small samples and no repeats remain. |

Additional notes clarify less water absorption rather than absolute zero absorption in 1BR Q8(a)(ii), and the difference between the 1% intermediate and total global loss in 2BR Q5(a)(i). These are source-bound review notes, not silent edits to the original PDFs.

## Verification and remaining gates

- All 16 correction payloads validated against `SaveReviewQuestion`; 77 subpart allocations reconcile with 180 marks. Expected revisions and six source checksums were checked before writes.
- Durable per-crop/per-question receipts and immutable pre-change baselines are retained privately. Corrected question content was read back and compared with the prepared payloads; server-resolved exact-block links may augment supplied page evidence.
- All eight production replacement crop files matched the inspected 180-DPI local renders byte-for-byte.
- All 16 appended assessments were checked against their current question revisions/content hashes and prepared source-specific estimates. Approval, curriculum/coverage decisions, textbook evidence and historical extraction records were preserved. A protected Chemistry 1C workspace was unchanged.
- Focused Biology/Chemistry intake and staging regressions: **51 passed**, with five existing PyMuPDF/SWIG deprecation warnings. The initial repository-root test invocation lacked the backend import path; rerunning from the backend directory passed.
- Private baselines, report maps, renders, payloads, authenticated-write receipts and read-back verification live under ignored `tmp/biology-june2024-regional-review/`; licensed PDFs and credentials remain outside Git.
- Admin visual/content/coverage acceptance, any source-conflict adjudication, scoring validation and Student release remain separate gates. No paid calls, application deployment, API restart, question approval, or Student release was performed.

Ten of the 44 Biology papers have now received this depth of source comparison. **34 remain**. November 2023 standard 1B/2B is the next proposed chronological batch; do not increase the remaining drafts' preliminary confidence without equivalent source checks.

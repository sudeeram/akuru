# June 2024 standard Biology 1B/2B source comparison

Started: 2026-11-04

Completed: 2026-11-04 (this two-paper comparison; Admin acceptance/release remains open)

Standard: `akuru-igcse-pastpapers` 1.4.0; procedure `akuru-igcse-source-comparison` 1.0.0.

## Scope and production result

Compared June 2024 standard Pearson Edexcel International GCSE Biology 4BI1 **1B and 2B**, following the June 2025 pilot. Authenticated Admin APIs were used for revision-protected draft corrections, inspected replacement crops and append-only accuracy assessments. No application code deployment, database migration, paid AI API call, question approval, curriculum change or Student release was performed.

| Paper | Questions | Subparts | Marks | Questions >70% | Subparts >70% | Subparts >75% | Mean subpart confidence | Range |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1B | 10 | 45 | 110 | 10 | 45 | 45 | 90.8% | 80–94% |
| 2B | 6 | 32 | 70 | 6 | 32 | 32 | 90.8% | 85–94% |
| Total | 16 | 77 | 180 | 16 | 77 | 77 | 90.8% | 80–94% |

Import-time extraction estimates were 55–60% (zero questions/subparts above 70%). The new figures describe a later source-fidelity judgement after actual comparison and correction. They are **not** an empirically measured accuracy rate, automatic-marking validation, or a claim that candidate handwriting has been exhaustively transcribed. Original extraction history is retained.

Production review links:

- [June 2024 Biology 1B](https://akuru.magicalinternational.com/admin/exam-documents/review/5435246d-1b36-47ee-83fe-24c581ae860e)
- [June 2024 Biology 2B](https://akuru.magicalinternational.com/admin/exam-documents/review/16482b69-6e93-41ef-a3e4-b6b988779cab)

The dedicated confidence page is the same URL with `/accuracy` appended.

## Source identity and inspection

Local and production SHA-256 checks agreed for all six source PDFs; source versions remained bound to their original documents. The PDFs have 32/24 question pages, 24/23 scheme pages and 109/99 report pages for 1B/2B respectively. All 16 question/source-scheme contact sheets were visually inspected, covering every question and its rubric. All **31 actual saved production crops** were downloaded and inspected, then five replacement crops were rendered and inspected before creation.

All typed question-specific report commentary was read. Headings and physical continuation ranges were checked at subpart scope, including image-only pages that native-text extraction omits. **29 selected report pages** were rendered and inspected: 1B pages 4, 7, 12, 31, 38, 42, 49, 55, 60, 67, 79, 83, 89, 101 and 104; 2B pages 16, 23, 26, 37, 45, 52, 59, 60, 67, 77, 82, 87, 93 and 95. Handwritten examples remain original private evidence, distinct from derived examiner advice. Complete literal handwriting transcription is not claimed.

Interpretation provenance records Codex-assisted comparison, guideline/prompt versions and UTC processing time. Exact conversation model identity was not exposed, so no model ID was guessed. This did not use the configured paid OpenAI API accounts.

## Material corrections

### Question wording and visuals

- Restored all seven meaningful gap-fill positions and the lost respiration/acid continuation in 1B Q3, rather than treating dotted answer regions as disposable lines.
- Restored food-chain, aerobic-respiration and protein-synthesis arrows; chemical subscripts, cubic units and the red-cell table's power of ten.
- Expressed the feed-conversion fraction unambiguously as a division; retained tables as original images alongside their text.
- Replaced the fragmented 1B Q1 food web with the complete web, labels and connecting arrows (paper PDF page 2).
- Replaced the clipped tick with its complete drawing and A–B measurement line (1B page 4). Measurement still requires original PDF scale; a resized web image is not a calibrated ruler.
- Replaced the clipped pedigree with all A–H individuals and the four-symbol key (1B page 24).
- Replaced the fragmented duckweed jars with a complete A–D apparatus comparison and labels (1B page 26).
- Replaced the separated lamp/potometer candidates with one complete apparatus crop (2B page 7).
- Assigned relevant diagrams/tables to the corresponding subparts. Original unchanged assets remain subject to Admin visual approval; five inspected replacements have their own reviewed-crop decisions. No question/subpart was approved by this work.

### Marking schemes

- Re-extracted exact answer-column criteria and retained additional-guidance text with narrowed scheme-page links.
- Repaired missing MC marking points in 2B Q1(a) and Q4(a)(i), avoiding empty point text after parser filtering.
- Preserved calculation results, decimal precision, rounding and partial credit for magnification, percentages, cell counts, ratios and fish growth/feed calculations.
- Retained named-substance/function matching for 1B Q1(b)(ii), combined credit for sexual reproduction involving fusion of gametes in Q2(d), and the conditional digestion fallback in Q8(c)(i).
- Preserved overall/group limits for 2B Q1(e) (negative/positive groups) and Q4(b) (fluid protection plus capped placenta criteria), combined distance/time credit in Q2(a)(i), and complete alternative lipid-test routes in Q6(a)(ii).
- Kept C/O/R/M/S practical criteria distinct in 1B Q10. These instructions are not claimed to be fully executable scoring rules. All 77 parts remain `manual_only`.

### Examiner reports

- Replaced broad question-level report associations with exact subpart discussions and physical continuation pages. No dedicated MC commentary was invented where absent.
- Added clearly attributed, concise advice derived from typed examiner commentary, rather than treating candidate responses as model answers.
- Flagged the following source wording limitations instead of silently teaching them as correct.

## Remaining limitations and priorities

| Location | Confidence constraint | Review note |
| --- | ---: | --- |
| 1B Q1(b)(i) | 85% paper check | Physical measurement must use original PDF scale; display resizing must not be treated as an accurate ruler. |
| 1B Q9(b)(ii) | 80% report check | Report PDF 101 calls magnesium-deficient leaves “almost white”; the actual table gives colour 2/5, whereas white is 0/5. Use the table and scheme. |
| 2B Q6(b)(iii) | 85% report check | Report PDF 87 uses “low efficiency” in a low-index context. Lower feed-conversion index represents more efficient conversion. Corrected advice identifies this distinction. |

Admin content/visual/coverage approval and separate Student/scoring release gates remain outstanding. No new AI-generated drawing answers or geometric marking have been introduced. Lower confidence is not reserved only for source-instruction conflicts: the recording preserves these remaining ambiguities and operational limitations.

## Verification and evidence

- All 16 payloads validated against `SaveReviewQuestion`; 77 subpart allocations reconcile with the 180 paper marks. Labels, allocations, statuses, curriculum decisions and textbook evidence were preserved.
- Production source hashes and expected revisions were checked before writes. Durable receipts prevent blind replay; current content, approval and reviewer metadata were checked again during assessment writes.
- All 16 new accuracy records were read back and matched to current revisions/content hashes and the prepared source-specific estimates. Original extraction records remain historical.
- All five production crop files matched the inspected local renders byte-for-byte at the production renderer's 180 DPI.
- Protected Chemistry 1C and both June 2025 Biology workspaces were re-read and matched their pre-batch snapshots, including approvals and analysis metadata.
- Focused Biology/Chemistry intake regression suite: **47 passed**; five existing PyMuPDF/SWIG deprecation warnings. No application code changed, so no application deployment or API restart was needed.
- Private source-bound baselines, desired changes, report maps, renders, correction receipts, assessment payloads and final verification: ignored `tmp/biology-june2024-review/`. Source PDFs/crops and credentials remain outside Git.

This completes the June 2024 standard batch, not the full collection. June 2025 and June 2024 standard papers together account for four of 44 papers. The other **40 papers** still need this depth of source comparison before their preliminary confidence can be reassessed. June 2023 standard 1B/2B is the next proposed batch; regional papers remain separate components.

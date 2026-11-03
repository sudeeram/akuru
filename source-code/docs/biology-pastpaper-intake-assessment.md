# Biology past-paper intake assessment

Examined: 2026-11-04
Status: initial local assessment snapshot, before imports. See [the implementation runbook](pearson-biology-intake.md) and delivery plan for subsequent production intake.

## Scope and evidence

Source root: `pastpapers/igcse/biology/` (Git-ignored).

Every one of the 132 PDFs was opened with PyMuPDF; every page was checked for native text availability, and every file was hashed. Cover identity was compared with the filename, and paper total markers were reconciled. Representative rendered pages from June 2025 question papers, schemes and a handwritten report example, the ambiguous January 2020 report cover and the June 2021 final scheme cover were visually inspected. This is an intake audit, **not** a line-by-line review of all 3,723 pages or approval of any question, crop, rubric or report interpretation.

The [132-file inventory](biology-pastpaper-inventory-2026-11-04.csv) records paths, hashes, size, page counts, native-text counts, identity issues and paper-total checks. Full extracted text, per-page diagnostics and visual checks remain in ignored `tmp/biology-paper-audit/`; no licensed PDF or extracted question content is added to Git.

## Findings

- 132 readable PDFs, approximately 149 MiB, across 13 supplied exam sessions (June 2019 through June 2025).
- 44 question papers (1,176 pages), 46 schemes (995 pages, including two provisional extras), 42 reports (1,552 pages).
- 44 candidate paper sets: 26 standard 1B/2B and 18 regional 1BR/2BR. Both variants remain distinct source identities.
- 369 top-level question-total markers; all 44 paper totals reconcile to 110 marks (Paper 1) or 70 (Paper 2). This does not validate subpart wording, extraction order or scoring rules.
- All PDFs contain native text. No wholly textless PDF was found. 244 pages have fewer than 80 non-whitespace native characters; this heuristic includes covers, blank answer areas and image-based content and must not be equated with 244 OCR failures.
- No identical SHA-256 duplicate files. Semantic duplicates and provisional/final changes still need comparison.
- No Biology specification PDF is supplied in this tree. Retain and review the official 4BI1 specification separately before rules-based mock generation.

## Session inventory

| Session | Supplied components | Papers | Schemes | Reports | Notes |
| --- | --- | ---: | ---: | ---: | --- |
| June 2019 | 1B, 1BR, 2B, 2BR | 4 | 4 | 4 | No missing companions detected within supplied components. |
| January 2020 | 1B, 1BR, 2B, 2BR | 4 | 4 | 4 | PaperBR identity issue; report requires verification. |
| November 2020 | 1B, 1BR, 2B, 2BR | 4 | 4 | 4 | No missing companions detected within supplied components. |
| January 2021 | 1B, 1BR, 2B, 2BR | 4 | 4 | 4 | No missing companions detected within supplied components. |
| June 2021 | 1B, 2B | 2 | 4 | 0 | Two provisional schemes in addition to final results schemes; no reports supplied. |
| November 2021 | 1B, 2B | 2 | 2 | 2 | No missing companions detected within supplied components. |
| January 2022 | 1B, 1BR, 2B, 2BR | 4 | 4 | 4 | No missing companions detected within supplied components. |
| June 2022 | 1B, 1BR, 2B, 2BR | 4 | 4 | 4 | No missing companions detected within supplied components. |
| January 2023 | 1B, 1BR, 2B, 2BR | 4 | 4 | 4 | No missing companions detected within supplied components. |
| November 2023 | 1B, 2B | 2 | 2 | 2 | No missing companions detected within supplied components. |
| June 2024 | 1B, 1BR, 2B, 2BR | 4 | 4 | 4 | No missing companions detected within supplied components. |
| November 2024 | 1B, 2B | 2 | 2 | 2 | No missing companions detected within supplied components. |
| June 2025 | 1B, 1BR, 2B, 2BR | 4 | 4 | 4 | No missing companions detected within supplied components. |

Do not interpret an absent component/session as a missing download without checking Pearson's actual series availability. This audit checks the supplied corpus, not completeness against Pearson's entire archive.

## Exceptions that require explicit handling

1. **January 2020 PaperBR:** question and results scheme internally identify 2BR. The `Examinerreport-PaperBR-January2020.pdf` cover identifies 2B. Its extracted text is not identical to the separately named 2B report, so do not simply deduplicate or assign it to 2BR. Compare report commentary with both exact question papers and, if necessary, obtain Pearson's authoritative report. Quarantine the report association until resolved; the 2BR question/scheme pair can be reviewed independently.
2. **June 2021:** 1B and 2B each have a final Results scheme and a Provisional scheme. They are different files with different normalized extracted text. Prefer the verified final scheme for active assessment; preserve provisional material as nonauthoritative history, not a second active marking source. Reports are not supplied. Do not invent examiner advice or borrow another session's report.
3. **November 2024:** schemes are under `Mark-Scheme`, whereas other folders use `Mark-scheme`. Intake must be case-insensitive and check internal identity.
4. **Shared qualification covers:** some Paper 1 sources also name Science Double Award 4SD0. Retain that source metadata but import this collection as Biology 4BI1; do not create accidental duplicate Science courses.

## Extraction and review implications

The representative June 2025 sources show labelled organism diagrams, multiple-choice boxes, breathing graphs, table-based marking points and handwritten candidate responses embedded in reports. Use native text and geometry first, source renderings for all meaningful visuals and targeted OCR/vision for image-only regions. A page with substantial native text can still contain essential handwriting or diagrams absent from that text.

Preserve labels outside diagram outlines, all graph axes/ticks/units and complete table relationships. Attach visuals at the correct shared-stem or subpart scope. Keep printed labels and immutable source PDF coordinates separate from reflowed textbook pages. Do not remove intentional blank grids/response cells or replace source-provided drawing tasks with solved images.

Marking requires actual extracted and reviewed points, alternatives, caps and dependencies, not merely a linked scheme page. Candidate examples in reports are not accepted answers. Unsupported biological drawing, measurement or conditional scoring rules remain manual-marking-only. AI-generated worked answers are separately labelled, reviewed and private until the authorized help/reveal workflow.

## Recommended sequence

Pilot **June 2025 standard 1B and 2B**, with all questions/subparts and exact schemes/reports. Then standard papers by series, followed by a regional pilot and the remaining regional series. Biology's 22-topic textbook collection is already published according to the prior rollout evidence, but validate current production versions and learner coverage again at import time. Topic names alone do not establish specification-statement coverage or eligibility.

Existing AKURU official-paper review, exact evidence links, answer-visual controls, source-bound confidence/provenance and release gates should be reused. Existing Chemistry catalogue/pilot builders have hard-coded 4CH1 and C components; parameterise or replace their intake adapters rather than rename files and run them unchanged. General extraction conformance remains incomplete: see [the shared plan](../todo/planned/TODO-IGCSE-PASTPAPER-ANALYSIS.md).

## Official reference

[Pearson 4BI1 specification, Issue 3 September 2024](https://qualifications.pearson.com/content/dam/pdf/International%20GCSE/Biology/2017/specification-and-sample-assessments/international-gcse-biology-2017-specification1.pdf): Paper 1 is 120 minutes/110 marks; Paper 2 is 75 minutes/70 marks and can assess all content including bold B statements. Textbook unit numbering is not a substitute for this qualification specification. Preserve issue/version applicability to historical papers and distinguish linear 4BI1 from modular qualifications.

Implementation plan: [Biology past-paper intake](../todo/ongoing/TODO-PEARSON-BIOLOGY-PAST-PAPERS.md).

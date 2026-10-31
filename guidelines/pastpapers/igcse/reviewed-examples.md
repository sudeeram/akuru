# Reviewed reference examples

Standard: `akuru-igcse-pastpapers` 1.2.0

Last updated: 2026-10-31

These are reference cases for future executable regression tests. A written example is not a passing test or automatic approval of regenerated content. Original licensed PDFs remain in the ignored `pastpapers/` folder; do not commit full papers, handwritten crops, credentials or private production data with these guidelines.

## Case 1: June 2025 Chemistry 1C, Question 1

Production API verification on 2026-10-19 confirmed question revision 7 and all parts approved, with exact paper/scheme blocks and approved diagram/table descriptions. This is historical evidence, not a claim about the current live state.

Regression expectations: preserve a/b/c identities and appropriate visual associations; require an explicit visual decision; retain approved descriptions and reviewer edits on re-analysis; do not reintroduce old unapproved candidates. Any broader content assertion requires renewed source inspection.

## Case 2: June 2025 Chemistry 1C, Question 2

Source analysis on 2026-10-21: question PDF pages 4–5; scheme PDF page 5; report PDF pages 8–11 inspected for commentary and example continuation. Q2 was not approved by this analysis.

| Part | Marks | Expected extraction |
| --- | --- | --- |
| a | 2 | Observation question with two response slots; scheme offers any two of four observations with a two-mark cap and scoped notes |
| b | 1 | Products question with four choices A–D; correct choice retained privately as A |
| c(i) | 3 | Inherits universal-indicator context; explanation requires colour, pH and alkaline nature, with scheme alternatives |
| c(ii) | 1 | Inherits the same context; ion formula preserves charge and accepted equivalent notation |
| d | 1 | Flame-test question and four choices A–D retained on the continuation page; correct choice retained privately as C |

Expected total: eight marks. No scientific diagram required. Answer lines must not start the next part; `(1)`/`(2)` must not end the content region; final choices must not be dropped. Printing codes, barcodes and side warnings must not appear in prompts.

Report expectations: link the Q2(a) example to its following-page examiner comment; distinguish Q2(c)(i) and (ii) advice; associate comments with the correct response even when another example follows on the same page. Preserve incorrect candidate answers as examples, not accepted answers. Preserve uncertain handwriting and charges for review.

Historical pilot causes: `separate_subparts` in the legacy draft-bank builder closes a part at a mark line, and the initial seed flow linked schemes without complete structured marking rules. Later reviewed data/scoring work does not prove the generic extractor fixes these causes. These cases must fail before the corresponding pipeline fixes and pass afterward.

## Case 3: June 2025 Chemistry 1C, Question 3 — diagram labels

Verified on 2026-10-22 against question-paper PDF page 6. The chromatography diagram includes five inks V–Z, all spots, the horizontal start line and solvent front, and both identifying labels to the right of the drawn border. A crop stopping at the border loses essential question information.

Production Q3 revision 9 replaces the clipped crop with a verified wider crop, attached to parts a–d, and an accessible description identifying both lines. Existing question/subpart review statuses were preserved; unrelated questions were unchanged. The obsolete clipped-crop warning was removed, while the original-scale measurement instruction for part d was retained.

Regression expectation: both labels must be visible and legible alongside the complete diagram. Labels outside a drawn border must survive extraction/cropping; no answer or calculated distance is added to the description.

## Case 4: June 2025 Chemistry 1C, Question 5(c)(ii) — private diagram answers

Source-reviewed on 2026-10-29 against marking-scheme PDF page 8, SHA-256 `a3e855a616c73d1d3921ab8a7778853451edea2de4add40bdbb27f18efae2c98`. Separate displayed butane and 2-methylpropane crops include every required bond and atom label, excluding adjacent scheme answers. They are linked privately to c(ii)'s M1/M2 points, one mark each. Production revision advanced 7 → 8 while the question/subpart statuses and unrelated parts were preserved; this is historical update evidence, not a current approval claim.

Regression expectation: both correct structures remain legible, atom labels/bonds are not clipped and rotating one structure does not make a second isomer. These are model-answer assets, never question illustrations. Direct Student retrieval must follow submitted-attempt authorization; image display alone does not establish safe automatic drawing scoring. Manual assessment remains required pending the scientific evaluation gate.

## Case 5: June 2025 Chemistry 1C, Question 7 — labelled graph and results table

Verified/corrected on 2026-10-31 against question-paper PDF page 16, SHA-256 `d860cbae11a72b38853a3a5f3176845ee117a0b5a6a01b4bb766f7bb88bfb06f`. The original proposed graph crop retained the plotting grid but omitted axis titles and clipped scale numbers. It was not complete despite the source text/results table being available elsewhere.

The verified replacement contains the complete blank grid, Y-axis **Temperature in °C** with 20.0/25.0/30.0 labels, and X-axis **Volume of sulfuric acid in cm³** with 0.0/10.0/20.0/30.0/40.0 labels. Normalized page bounds `(x0=0.17, y0=0.425, x1=0.825, y1=0.91)` are specific to this document. Do not reuse these coordinates for another layout.

Production revision advanced 6 → 7. The replacement graph was linked wherever the old graph occurred: c(i), c(ii), c(iii), d and e. The separate results-table asset and unrelated fields/part statuses were preserved; only the resolved clipped-axis warning was removed. Authenticated API read-back confirmed the saved associations, and downloaded crop pixels matched a rendering of the verified original source. The corrected visual was reviewed; the question was not approved or published by this update.

Regression expectation: detect loss of either axis title/unit, numbered scale or grid edge; retain table headings/values/precision and appropriate shared-part links. A blank graph must not receive scheme-derived plotted points, anomaly circles or best-fit lines. Private marking rules must preserve graph-dependent readings rather than require a fixed intersection value. A written reference is not an executed automated regression test.

## Extend the corpus

Add independently checked cases for multi-page subparts, shared diagrams, labelled graphs, merged scheme rows, any-N groups, dependencies, formula charges, handwriting uncertainty, incomplete companions, alternate layouts and regional variants. Record exact source hashes and local fixture locations in the private fixture manifest. Use synthetic equivalents in public tests when licensed originals cannot be committed.

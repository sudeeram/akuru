# Reviewed reference examples

Standard: `akuru-igcse-pastpapers` 1.1.0  
Last updated: 2026-10-21

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

Known cause: `separate_subparts` in the pilot draft-bank builder closes a part at a mark line. The current seed flow also links schemes without populating structured marking rules. These cases must fail before the corresponding fixes and pass afterward.

## Case 3: June 2025 Chemistry 1C, Question 3 — diagram labels

Verified on 2026-10-22 against question-paper PDF page 6. The chromatography diagram includes five inks V–Z, all spots, the horizontal start line and solvent front, and both identifying labels to the right of the drawn border. A crop stopping at the border loses essential question information.

Production Q3 revision 9 replaces the clipped crop with a verified wider crop, attached to parts a–d, and an accessible description identifying both lines. Existing question/subpart review statuses were preserved; unrelated questions were unchanged. The obsolete clipped-crop warning was removed, while the original-scale measurement instruction for part d was retained.

Regression expectation: both labels must be visible and legible alongside the complete diagram. Labels outside a drawn border must survive extraction/cropping; no answer or calculated distance is added to the description.

## Extend the corpus

Add independently checked cases for multi-page subparts, shared diagrams, labelled graphs, merged scheme rows, any-N groups, dependencies, formula charges, handwriting uncertainty, incomplete companions, alternate layouts and regional variants. Record exact source hashes and local fixture locations in the private fixture manifest. Use synthetic equivalents in public tests when licensed originals cannot be committed.

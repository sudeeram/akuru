# June 2025 standard Biology 1B/2B source comparison

Started: 2026-11-04 (Asia/Colombo).
Status: completed for this two-paper source-comparison batch; production read-back passed.
Scope: 16 questions, 76 subparts, 180 marks. Other Biology series and regional variants are outside this reassessment.

## Method and evidence

Compared the saved production drafts with their exact original native PDFs, full rendered question/mark-scheme pages, every existing production question crop (22), and the examiner reports' typed commentary. Report headings and physical continuation ranges were checked throughout; 24 representative report pages were rendered and inspected, including handwritten answers, plotting examples, partially credited work and incorrect examples. A full literal transcription of every handwritten candidate answer is **not** claimed.

The six original source hashes were checked against the source-bound banks and production document records. Private before/after snapshots, correction receipts, rendered comparisons and append-only analysis evidence remain in ignored `tmp/biology-june2025-review/`. Licensed content and credentials are not committed.

Interpretation provenance: `codex_assisted`, OpenAI (Codex conversation), guideline `akuru-igcse-pastpapers` 1.3.0, prompt `biology-june2025-source-comparison-v1`, assessment method `biology-source-comparison-v1`. The conversation's exact model ID was not exposed and remains unrecorded. Original native extraction history is preserved separately. No paid OpenAI API calls were made.

## Corrections applied through authenticated Admin APIs

- Restored damaged decimal/scientific-notation values and explicit calculation/partial-credit/rounding guidance. Removed non-credit introductory phrases from point lists and separated the genetic-cross and experimental-design criteria.
- Kept scheme additional guidance, alternatives, any-N limits, exclusions, error-carried-forward and subgroup limitations visible in manual-marking instructions. These instructions are not claimed to be fully executable scoring rules.
- Restored all eight gap positions and their continuation wording in 1B Q8(b); normalised unambiguous powers/units in the saved draft text.
- Corrected report associations to individual subparts, recovered missed no-space headings and included image-only physical continuation pages. Parts without specific report commentary are explicitly assessed as `no_comment` rather than receiving invented advice.
- Added concise derived examiner advice, distinct from candidate transcription and official scoring authority. Flagged contradictory report prose for 2B Q3(b)(ii) and Q5(c); the actual data/graphs and scheme remain authoritative.
- Replaced 1B Q7's three incomplete blood-component crops with a complete source crop retaining P, Q, R, S and T. The locally inspected crop is attached only to the three identification subparts. Old assets are retained; no frozen source was deleted. The replacement is a reviewed visual crop; question/subpart approvals remain unchanged. Other proposed visuals remain proposed.

## Confidence results

These are subjective, source-specific confidence estimates, not measured accuracy percentages. Question confidence is constrained by the weakest subpart. The earlier 45–60% extraction triage snapshots are retained as historical records and are not rewritten.

| Component | Questions above 70% | Subparts above 70% | Mean subpart confidence | Subpart range |
| --- | --- | --- | --- | --- |
| 1B | 9 / 10 | 45 / 46 | 87.9% | 65–90% |
| 2B | 5 / 6 | 29 / 30 | 88.6% | 70–91% |
| Total | 14 / 16 | 74 / 76 | — | 65–91% |

| Paper | Question confidence |
| --- | --- |
| 1B | Q1 88; Q2 88; Q3 88; Q4 65; Q5 88; Q6 88; Q7 88; Q8 88; Q9 88; Q10 88 |
| 2B | Q1 90; Q2 90; Q3 80; Q4 90; Q5 80; Q6 70 |

The supplied 1B report contains a typesetting-draft notice. This is recorded as a source limitation; the report was not silently represented as a verified final edition.

## Remaining source conflicts and release gates

- **1B Q4(b)(ii), 65%:** question PDF page 13 asks for three advantages/three marks; scheme PDF page 11 says four/four marks. Report PDF pages 45–48 treats full credit as three. Retained the question allocation, documented all three sources and held automatic marking.
- **2B Q6(b)(i), 70%:** scheme PDF page 21 says three points but its mark column and question PDF page 22 award two. Retained two marks and flagged the contradictory instruction.
- **2B Q3(b)(ii):** report PDF page 44 incorrectly locates the largest fall between light levels 1 and 2; data, scheme and report examples support 2 and 3.
- **2B Q5(c):** report PDF page 77 incorrectly describes water loss decreasing after day five. The source graph/scheme show increasing loss after watering. Original prose remains available, with a correction in derived advice.
- All 16 questions and 76 subparts remain unreviewed, all parts manual-only, and no Student release or curriculum decision was changed. Admin content/crop approval, exact-block review, automatic-scoring validation and any model-answer requirements remain separate.

## Shared extraction regressions

Native-layout extractor `pearson-native-layout-v1.2` now retains meaningful words after leading dotted gaps, protects decimal values from numbered-list splitting, omits description preambles from marking points, and preserves no-space report headings/image-only physical continuations. Synthetic tests exercise each failure. This does not automatically re-extract or overwrite the other 42 Biology papers.

Validation: 31 focused intake tests passed; complete backend suite 366 passed, one skipped (existing dependency deprecation warnings). No frontend files or schema migrations are part of this change.

Production acceptance: all six source hashes, 16 current accuracy records and 76 subpart assessments were verified through authenticated APIs. Confidence writes preserved content/revisions/approvals. The replacement crop bytes match the inspected local render. Existing Chemistry 1C retains all ten approvals. No Student release was enabled.

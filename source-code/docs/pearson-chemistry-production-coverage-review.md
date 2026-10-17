# June 2025 Chemistry 1C/2C: production textbook coverage review

Prepared 17 October 2026. This is a **coverage triage**, not an approved question bank, exact rubric, or Student release. It compares the unreleased June 2025 standard 1C/2C pilot bank with the two Chemistry topics currently published in production AKURU: Topic 1, *States of Matter* (content v2), and Topic 2, *Elements, Compounds and Mixtures* (content v1). The source PDFs, rendered review pages, production textbook excerpts and all 87 detailed subpart decisions remain in the Git-ignored `.pilot-review` directory. The reproducible decision script is `scripts/review-pearson-chemistry-topic-coverage.py`.

| Coverage decision | Subparts | Marks | Meaning |
|---|---:|---:|---|
| Supported by a published topic | 5 | 12 | The actual assessed idea is found in Topic 2; source image and rubric approval are still required. |
| Partial or uncertain | 3 | 3 | Related principles occur in Topic 2, but the exact application is not clearly taught there. |
| Outside published topics | 79 | 165 | A lexical hit must not be treated as curriculum coverage. |

Only **1C Question 3 (chromatography, 11 marks)** is wholly within the currently published topics. This does **not** make it ready for AKURU import or Student practice. Its chromatogram must accompany both pages of the question; the diagram determines the spot comparisons and Rf measurement. Its exact marking scheme is on 1C scheme PDF page 6. A visual spot-check confirmed the scheme's linked explanation requirement for part (a), the dependence of one mark on another in part (b), the distinction between a single spot and an immobile dye in part (c), and the accepted measurement range and final two-significant-figure answer in part (d). The 1C examiner report discusses these four parts on report PDF pages 13, 16, 19 and 21 respectively. These findings guide the eventual exact rubric review; no marking points have been imported.

An OCR-cleaned **local candidate** for this question is saved as `.pilot-review/1C-Q3-review-candidate.json`. It has a shared stem, four labelled parts, the required chromatogram page, 11 reconciled provisional marking points and paraphrased examiner guidance. Every source-visual, prompt, rubric, guidance and mapping approval flag remains false. This candidate is not in Git or the production AKURU database.

**2C Question 1 is mixed.** Part (a)(i), identifying a compound from the choice box, is supported by Topic 2 page 3. Parts (a)(ii) and (a)(iv) need confirmation that students have been taught the particular examples and Periodic Table classification. Part (b)(i) uses fractional distillation, taught on Topic 2 page 8, but applies it to crude-oil fractions; the chapter mentions crude-oil processing without teaching the fractions themselves. The diatomic-molecule part (a)(iii) and kerosene-use part (b)(ii) lack support in the published chapters. The exact scheme is 2C scheme PDF page 4; the report comments on (b)(i) and (b)(ii) at report PDF pages 4 and 5. The question's two paper pages and shared choice box must remain together. **Do not map or release this whole question as Topic 2-only.**

| Paper | Question | Decision with current two topics |
|---|---|---|
| 1C | 1 | Outside: atomic particles and electron configuration. |
| 1C | 2 | Outside: lithium reactions, alkaline solution and flame test. |
| 1C | 3 | Supported by Topic 2 pages 10–13; diagram and exact rubric still pending import approval. |
| 1C | 4 | Outside: ionic formulae and quantitative chemistry. |
| 1C | 5 | Outside: organic chemistry and combustion. |
| 1C | 6 | Outside: rusting, reactivity, redox and yield. |
| 1C | 7 | Outside: neutralisation investigation and graph interpretation in that context. |
| 1C | 8 | Outside: giant covalent structures. |
| 1C | 9 | Outside: covalent structures, polymers and organic reactions. |
| 1C | 10 | Outside: fuel-energy/enthalpy experiment and calculations. |
| 2C | 1 | Mixed as detailed above; not whole-question eligible. |
| 2C | 2 | Outside: rates and reaction profiles. |
| 2C | 3 | Outside: isotopes, ionic bonding and electrolysis. |
| 2C | 4 | Outside: organic reactions and esterification. |
| 2C | 5 | Outside: titration and quantitative preparation. |
| 2C | 6 | Outside: equilibrium and yield. |

The local `production-topic-triage.json` and `.csv` list every subpart, its marks, coverage decision, reason, question/scheme PDF pages, and published textbook extraction page where relevant. Those extraction page numbers must not be assumed to be the book's printed-page labels. The production lexical report suggested a passage for **all 87 subparts**, showing why lexical overlap alone is inadequate: 79 of those subparts assess material outside the published topics.

No official-material question, marking point, topic mapping or Student assignment was inserted in production. The production past-paper document count remained zero after private staging. The next controlled milestone is to finish an accurate prompt, diagram attachment, exact scheme rubric and examiner guidance for **1C Question 3**, test it in an isolated AKURU environment, then review an Admin-only import. The other questions can be revisited as more textbook topics are published.

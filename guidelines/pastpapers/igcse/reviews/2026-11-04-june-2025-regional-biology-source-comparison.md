# June 2025 Biology regional 1BR / 2BR source comparison

Started: 2026-11-04. Completed: 2026-11-04.

## Scope and method

Apply `akuru-igcse-source-comparison` 1.0.0 under the parent past-paper guideline 1.4.0 to the two June 2025 regional papers. This is a later source comparison and draft correction, not the original extraction and not Admin acceptance. Standard and regional companions stay distinct.

- 1BR: 10 questions, 49 subparts, 110 marks; question/scheme/report PDFs contain 32/31/137 pages.
- 2BR: 6 questions, 31 subparts, 70 marks; question/scheme/report PDFs contain 20/15/74 pages.
- Compared all question and scheme page renders and native text, inspected all 30 actual saved production crops, read typed examiner commentary throughout, and rendered 19 selected report pages including image-only continuations. Existing crops retain their required labels/axes; none was replaced.
- Handwritten candidate examples remain available as original report images. This comparison does not claim exhaustive handwriting transcription.
- Corrected through authenticated, CSRF-protected, optimistic-revision Admin APIs. Frozen baselines and durable receipts remain in ignored local storage. No direct database writes, paid API calls, application deployment or service restart.

## Corrections

Restored valid decimal calculations, significant figures, correct MC answers and marking criteria. Reconstructed table rows/columns, including the ten-column 2BR Q4 quadrat table with original blank cells rather than fabricated zero entries. Reconstructed the 1BR Q4 vitamin-C ranking slots and kept the provided lime position. Removed graph-axis numerals from prose while preserving the actual graphs, scales, units and labels.

Restored the fifth placenta criterion in 1BR Q5(a)(iii), the sixth energy-loss criterion across the scheme-page boundary in 1BR Q7(a)(iii), all five flower criteria in 2BR Q1(e), and all ten evaluation criteria in 2BR Q4(b)(iv). Preserved continuation guidance for 2BR Q4(b)(ii).

Assigned relevant existing figures/tables to subparts, retained both contraceptive graph panels, complete food-web arrows, pedigree key, blank plotting grid, apparatus labels and nephron/eye labels. Kept answers and private scheme/report material separate from question visuals. Linking an existing unapproved visual does not approve it.

Replaced broad examiner-report associations with exact subpart heading and physical continuation ranges, including image-only pages. No dedicated report comment was invented for MC items without one. Commentary is a paraphrase, not a new scoring authority.

All parts remain manual-only: any-N caps, practical rubrics, combined responses and error-carried-forward instructions are preserved in criterion/guidance text but this batch does not implement or validate automatic scoring rules.

## Source conflicts requiring attention

| Component / part | Located discrepancy | Treatment |
|---|---|---|
| 1BR Q3(b)(i) | Scheme PDF 8 prints `2400 / 62.5 = 40`; question gives 2500 and full-credit report PDF 23 uses 2500. | Correct draft calculation is 2500/62.5 = 40:1; retain explicit source-conflict note, 80% confidence. |
| 1BR Q8(c)(i) | Report PDF 106 says all three populations increase; the table, introductory commentary and candidate example show initial decreases and no lizard recovery. | Use the actual table and scheme; flag erroneous report sentence, 83% report confidence. |
| 2BR Q1(b) | Report PDF 10 reverses seed/ovule in one example comment. | Use scheme PDF 4 and report introduction PDF 8: ovule becomes seed; ovary becomes fruit. Flag comment, 83% report confidence. |
| 2BR Q6(b)(iii) | Scheme PDF 14 prose says two points; question and marks column allocate three. Four criteria are listed, and report PDFs 69–71 credit reabsorption, PCT and active transport. | Preserve three-mark allocation and all four criteria, but keep 70% scheme confidence and manual-only marking pending Admin adjudication. |

Do not raise confidence simply to meet a threshold. Estimates are source-fidelity judgments, not calibrated probabilities or content approval.

## Production references

- [1BR review](https://akuru.magicalinternational.com/admin/exam-documents/review/99a01ebb-1f5f-4213-97f3-9e4d6773ac17)
- [2BR review](https://akuru.magicalinternational.com/admin/exam-documents/review/eea024fe-978f-4392-b330-c0011201cf63)

| Component | Role | Document ID | Source SHA-256 |
|---|---|---|---|
| 1BR | Paper | `99a01ebb-1f5f-4213-97f3-9e4d6773ac17` | `5ff9d6a860df76549d5b74ff158035cedf9eeebc2c97514a5ceaa15881f8c4a9` |
| 1BR | Scheme | `b622061d-5295-4daf-a9f1-11773de08f13` | `5ce33e59a2f824aa88d0ebf5fac29988b68b8bb52becfb9f2da402cb99036fed` |
| 1BR | Report | `f4fcc8d2-6453-4d6f-98e2-8eec34c209e1` | `dbd105183c6a46d951a2059a235482a2935c3fa880372c96ba174e9fe7ec1d4d` |
| 2BR | Paper | `eea024fe-978f-4392-b330-c0011201cf63` | `4fc008178a2f75939934b11276b34b61cea356ac548373f0d1cc44ff6a2f6f52` |
| 2BR | Scheme | `c8617e93-b3f9-484a-9180-fa212e8b0382` | `87e2408405db4916ece9c773bf0b7c5f0963b8ec4d457bb5378467ccfbf1eeaf` |
| 2BR | Report | `41d1dfdd-8aed-4813-b868-ae304d48fa5b` | `f8b6921d858da1bf6698978c7cf7d66fb3fcb2f9ddf48ed7a92b879c93a17e0d` |

## Confidence and acceptance evidence

Each question receives an append-only assessment with paper/scheme/report checks, source pages, reasons and provenance. Question confidence is constrained by its lowest-confidence subpart. Historical extraction assessments remain in history. Provider is recorded as Codex-assisted; exact conversation model identity was unavailable and is not inferred.

Local Biology/Chemistry intake regressions: **47 passed**; five PyMuPDF/SWIG deprecation warnings. No shared application code changed.

Confidence read-back results are listed below. Admin content, visual, curriculum and scoring acceptance, and Student release remain separate pending actions.

| Paper | Questions above 70% | Subparts above 70% | Subparts above 75% | Mean subpart confidence | Subpart range |
|---|---:|---:|---:|---:|---:|
| 1BR | 10 / 10 | 49 / 49 | 49 / 49 | 90.6% | 80–94% |
| 2BR | 5 / 6 | 30 / 31 | 30 / 31 | 90.5% | 70–94% |

Initial extraction proposals were 55–60%. The new assessments describe the later corrected/source-compared draft; they do not rewrite those original extraction estimates. The one subpart not exceeding 70% is 2BR Q6(b)(iii), for the located scheme conflict above.

Final production verification passed: all six source hashes match, all 16 current accuracy assessments match their corrected question revisions/content hashes, and all 30 downloaded crop files match the inspected baseline bytes. The four previously compared Biology workspaces (June 2024/2025 standard 1B/2B) and the reviewed Chemistry 1C workspace are unchanged. All 16 regional questions remain unapproved, all 80 subparts remain manual-only, and neither whole-paper readiness nor assessment release is enabled. A transient read-only TLS timeout was retried successfully.

Collection progress: six of 44 Biology papers have now received this deeper source comparison; 38 retain their preliminary draft status pending equivalent work. Admin acceptance is still required for all six batches' questions before any Student release.

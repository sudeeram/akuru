# June 2025 Biology 1BR — four-step readiness evaluation

Started and completed: 2026-11-19. Scope: **read-only production evaluation**, source/crop inspection and local graph-rendering feasibility. No production content changes, approvals, releases, paid model calls, commit, push or deployment.

[Production paper](https://akuru.magicalinternational.com/admin/exam-documents/review/99a01ebb-1f5f-4213-97f3-9e4d6773ac17).

## Current production state

The paper already contains **10 questions, 49 subparts, 110 marks**. All 49 subparts have exact paper and scheme block links and saved supported topic mappings. The ten saved accuracy analyses are current against their saved content, but use the older `exact-evidence-source-comparison-v1` method and `legacy` confidence policy, not the final four-step assessment policy.

| Step | Observed state | Work needed |
| --- | --- | --- |
| 1 — Extracted | Complete: 10/10 questions; all 49 parts have exact paper and scheme blocks | Retain the existing import and original extraction history; check source-specific exceptions below rather than reimport |
| 2 — Images reviewed | 0/10 questions complete; all 20 supplied crops are unapproved | Correct the Q5(b)(ii) graph-caption crops, replace generic accessible descriptions with source-faithful descriptions, validate subpart associations, then approve checked visuals |
| 3 — Final assessment | 0/49 counted as current final comparisons by the workflow | Record extraction-only final findings against the completed visual/content revision, explicit source adjudications and current published curriculum evidence; apply guarded approval above 75% |
| 4 — Tutor practice released | 0/49 released | Release eligible supported, self-contained parts only after current gates pass; verify existing source/review data and final inventory |

There are **48 AI-approved subparts**, one unreviewed part (Q6(a)(i)), and **zero AI/human-approved aggregate questions**. Those older subpart approvals are not proof that current visual/final-assessment gates have passed. Eleven parts currently pass the per-part Tutor eligibility endpoint, but none is released. Thirty-seven parts are explicitly blocked by visual review, with the remaining part Q6(a)(i) blocked by its unreviewed state. These are current backend results, not a proposed release plan.

Saved confidence: **49/49 above 75%**, range **80–94%**, mean **90.6%**. These are older estimates; this evaluation does not update or certify them. All 49 parts retain legacy manual-only scoring metadata. That metadata does not require a semantic-scoring certificate for the agreed indicative Tutor-feedback objective.

## Source and visual findings

### Q5(b)(ii): real graph-caption crop defect

Original question PDF page 14 labels the upper sperm-concentration chart **Graph 1** and the lower sperm-motility chart **Graph 2**. Current crop index 10 excludes its own Graph 1 caption. Current crop index 11 includes that preceding Graph 1 caption above the lower graph and excludes its own Graph 2 caption. Its axes/data remain visible, but the misplaced caption is misleading.

Replace both source crops with their own complete original captions, axes, units and tick labels. Retain both as Q5(b)(ii) question visuals. Do not regenerate the experimental graphs or change their measurements. The saved prose distinguishes the two graphs correctly, so this is primarily a crop correction.

### Q6(a)(i): worked graph preparation

The five-mark graph question is the only unreviewed subpart. It is typed as a drawing but has no answer visual and `answerVisualRequired=false`. Before release, provide a separate approved, explicitly AI-generated worked graph and intentionally set the appropriate answer-visual requirement. Leave the supplied blank question grid unchanged.

Original paper PDF page 16 and scheme PDF page 17 agree on seven time/mass pairs: 0/15, 5/17, 10/20, 15/23, 20/26, 25/27 and 30/27, in minutes/grams. The source asks for **straight joins between adjacent points**, not one regression line or a smoothed curve. Preserve the five scale/line/axes/plot/units criteria, original graphical tolerance and five-mark maximum.

Local feasibility passed using the existing `graph-v1` renderer: seven verified points, six two-point straight joins and correctly labelled linear axes. A private local preview exists under ignored `tmp/biology-june2025-1br-evaluation/q6-graph-feasibility.png`. It is not imported, approved or attached. No new rendering feature appears necessary for this example.

### Q3(b)(i): publisher calculation typo

The scheme PDF page 8 gives the correct final answer **40:1**, but its example working prints `2400 / 62.5 = 40`. That division is inconsistent. The question supplies a villus volume of 2500µm³; correct working is `2500 / 62.5 = 40`. The existing saved rubric already gives correct working and preserves the scheme's partial-credit outcomes. Explicitly record the typo adjudication in the new source findings; do not turn the typo into a student answer requirement or discard official partial credit. Existing confidence is 80%, not an automatic reason for rejection.

### Q8(c)(i): contradictory examiner-report sentence

The source table and scheme show initial decreases; insect/beetle populations later partly recover, while lizards do not. Report PDF page 106 says all three groups “increase” while also saying lizards do not increase. Retain the question data and official scheme as scoring authority and explicitly exclude/correct the misleading report sentence in derived guidance. Do not change the original report PDF or use its wording to cap extraction confidence under the newer policy.

### Other questions

Q1, Q2, Q4, Q7, Q9 and Q10 need their existing visual candidates/descriptions/associations reviewed and a current final source/curriculum assessment. Q3, Q5 and Q8 also need those ordinary checks in addition to their specific findings. The remaining inspected crops retain their main labels, graph axes, food-web arrows, pedigree key, result tables and intentionally blank answer spaces. This is not blanket approval of every association or exhaustive handwriting re-transcription.

## Curriculum and evidence

All 49 saved mapping decisions are supported and reference 12 Biology topics. Read-only requests confirmed that all 12 still expose published evidence. However, **none of the 49 current accuracy findings contains a bound `curriculum` assessment**. The next pass must verify the semantic matches, bind current publication/chunk hashes and record coverage confidence/acceptance. Existing topic selection alone is insufficient for Step 3. Do not fabricate evidence, force unrelated matches or substitute reconstructed-PDF pagination for stable textbook references.

## Checks actually executed

- Authenticated read-only Admin review, review-package, readiness, source-issue, visual-crop, release and workflow requests.
- Confirmed 10 current legacy source analyses, 49 exact paper/scheme associations, 48 AI-approved parts, 110 marks, 20 unapproved crops and zero releases.
- Downloaded and SHA-256-compared all 20 current crop images with the prior locally inspectable crop files; all matched. Inspected all four crop contact sheets, and targeted original Q5/Q6 paper pages and scheme calculation/graph pages.
- Checked original report text for the identified contradictory sentence; historical source-comparison reports were consulted, not mistaken for fresh complete re-review of the 137-page report.
- Queried published evidence for all 12 referenced topics. This checks availability, not full per-part semantic acceptance.
- Parsed/rendered and visually inspected a local Q6 worked-graph feasibility draft using existing trusted code. No model API call or production draft was created.

Machine-readable baseline, crop hashes, workflow/readiness responses, published-topic responses and the local graph preview remain in ignored `tmp/biology-june2025-1br-evaluation/`.

## Recommended continuation

Use the existing Paper 2 process, one question at a time: source/crop checks and corrections → separate visual/answer approval → current source and publication-bound curriculum findings with explicit source decisions → guarded AI approval and Tutor release → whole-paper 49/49 acceptance. No reimport is needed. No requirement has been identified for the owner to repeat all text reviews or fund paid backend assessment calls. A genuinely new source ambiguity discovered during completion must remain explicit rather than be cleared just to obtain green labels.


Follow-up: the [four-step completion](2026-11-19-june-2025-biology-1br-completion.md) was finished later on 19 November 2026. The above figures describe the initial read-only evaluation, not the current released state.

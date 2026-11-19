# June 2025 Biology 1BR — four-step completion

Started: 2026-11-19  
Completed: 2026-11-19  
Scope: June 2025 regional Biology 1BR only; 10 questions, 49 subparts, 110 marks.

[Production workflow](https://akuru.magicalinternational.com/admin/exam-documents/past-papers?q=June%202025%201BR&subject=biology) · [Question review](https://akuru.magicalinternational.com/admin/exam-documents/review/99a01ebb-1f5f-4213-97f3-9e4d6773ac17) · [Accuracy](https://akuru.magicalinternational.com/admin/exam-documents/review/99a01ebb-1f5f-4213-97f3-9e4d6773ac17/accuracy)

## Result

| Milestone | Verified production result |
| --- | --- |
| 1 — Extracted | 10/10 questions; 49 exact question/scheme rows reconcile; 110 marks |
| 2 — Images reviewed | 10/10 questions; all selected question visuals reviewed; two separate AI-generated answer examples approved and attached |
| 3 — Assessed | 49/49 current final source comparisons, publication-bound curriculum findings and AI-approved subparts; 10/10 aggregate questions AI-approved |
| 4 — Tutor practice released | 49/49 enabled, current Tutor-practice releases; zero excluded or unresolved parts |

All four labels are complete. Formal-exam publication remains **false**, as intended. No paid model calls, direct production database writes, Student account changes or source-PDF replacements were used. Existing manual-only storage metadata remains indicative AI feedback, not a requirement to obtain semantic-scoring certificates for Tutor practice.

## Step 1 — source preparation

Frozen baseline and source manifests were checked against all three local original PDF hashes. Native extraction reconciled all 49 official scheme rows and the 110-mark total. Saved question wording, original shared stems, marks, exact paper/scheme/report links and original extraction history were preserved.

Restored verbatim official answer-column/additional guidance alongside the interpreted points. Added explicit any-N limits and source-authorised combined responses for short diffusion path, controlled water bath, quadrats, inheritance wording and the CORMS investigation. Split the two distinct investigation-control marks rather than treating them as one flat point. Represented the four calculation questions as exclusive full/partial score bands, so equivalent or partial outcomes are not added together. Local allocation checks passed **2,997 combinations**; these checks validate allocation, not semantic interpretation of unrestricted Student answers.

Q6(a)(i) and Q9(b)(ii) are deliberately configured as drawing responses with required model-answer visuals. The earlier evaluation identified Q6; the full pass also caught Q9's genetic-diagram instruction despite its old `text` classification.

## Step 2 — visual and answer review

Inspected the source-bound crop contact sheets and targeted original pages. All 20 prior crop files matched their production hashes before changes. Replaced generic candidate descriptions with source-faithful captions/accessibility descriptions without adding answer names to unlabelled anatomy or completing answer cells.

- **Q5(b)(ii):** replaced both graph crops. The upper sperm-concentration graph now includes its own **Graph 1** caption. The lower motility graph includes its own **Graph 2** caption and no longer inherits Graph 1 above it. Numbered axes, units and experimental data are preserved. The two old miscaptioned crops were rejected and removed from active assignments.
- **Q10:** recreated the same verified source crop with a reviewed accessible description, using the ordinary revision-protected whole-question review API. Its genuine empty subpart label was preserved; no artificial part was added.
- **Q6(a)(i):** imported and separately approved an AI-generated worked graph from the seven verified time/mass pairs. It uses six straight joins, the original time/mass units and suitable linear scales. No regression fit, smoothed curve or invented measurements. The original blank question grid remains a question visual.
- **Q9(b)(ii):** imported and separately approved an AI-generated PTC cross. Tt × Tt gives TT, Tt, Tt, tt; with independent sex inheritance, male-and-taster probability is 3/8. The original pedigree and key remain unfilled question evidence.

Both worked examples show the permanent **AI-generated worked answer — not an official Pearson answer** label, explanation, limitations and a 90% estimated example confidence. Delegated review notes identify Codex; they do not claim owner/human scientific sign-off. The examples use private generated-answer assets, not question images.

## Step 3 — current assessment and source decisions

All 49 parts now use `final-source-accuracy-v3` and extraction-only `extraction-v1`, replacing the older final-readiness interpretation while retaining historical analyses. Estimated source confidence is **80–85%**, with Q3(b)(i) conservatively retained at 80%. This is not a calibrated correctness probability. Report fidelity and source discrepancy decisions are independent of extraction confidence.

Mapped all 49 parts to reviewed current chunks from the 12 already-selected published Biology topics. Each accepted curriculum finding records publication/version, document version, chunk/page/hash and the current mapping hash. Exam-specific numbers, formulas and practical methods remain source-provided context rather than claims that the textbook reproduces the exact exam. No coverage reason was rewritten around unstable reconstructed-PDF pagination.

Two explicit source issues were recorded and resolved through audited developer-review APIs:

1. **Q3(b)(i):** the question supplies 2500µm³, sperm volume is 62.5µm³, and the official final ratio is 40:1. The scheme example numerator 2400 is a publisher typo. The correct final answer, partial-credit outcomes and original PDF remain unchanged. The typed adjudication is `publisher_ambiguity_adjudicated`.
2. **Q8(c)(i):** the table/scheme show initial population decreases and no lizard recovery. The contradictory report sentence saying all three increase is excluded from derived guidance with `report_guidance_excluded`. The original report remains intact; scheme-based interpretation is authoritative.

After image review and current source/curriculum assessment, the normal server policy AI-approved all 49 eligible parts and all ten parent questions strictly above 75%. No hand-edited client approval verdicts or manufactured scoring certificates were submitted.

## Step 4 — guarded release and acceptance

The authenticated readiness endpoint reported every part eligible with no blockers. Prior release/withdrawal history was checked; no explicit withdrawal was overridden. Released parts question by question with exact saved revisions and self-contained-context confirmation, including the genuine unlettered Q10.

Verified:

- 49/49 current releases; release calls did not mutate source content or approval data.
- Three original source manifests/hashes, all wording/shared stems, 110 marks, exact evidence links, saved topic selections and original extraction analyses unchanged.
- Both generated examples remain approved/current; unauthenticated private preview requests return **401**.
- Both discrepancy decisions remain current and audited.
- Admin browser shows the approved PTC example and the paper table shows all four complete workflow stages.
- All **22 previously completed Paper 2 sets still show four complete steps and 692/692 current Tutor releases**.

No live Student/model conversation was charged for this verification. Readiness, release snapshots, access checks and Admin UI were tested; the established Student reveal lifecycle remains in place.

## Implementation and evidence

Runtime commit **`4dbf854656368fce305b27c023c4a725332fcf5b`** adds the strictly bounded `ptc_cross` template, distinct from roan codominance, and renderer provenance v3. It was committed/pushed to `codex/biology-tutor-rollout` and deployed after encrypted backup. No migration was required. Source/visual/curriculum/release updates were then applied through authenticated, CSRF-protected APIs.

- Worked-answer/schema/render/lifecycle tests: **34 passed**.
- Source-rubric allocation combinations: **2,997 passed**.
- Frontend typecheck and generated API contract freshness passed.
- Production build, schema-drift, health, HTTPS/header, route/fallback and loopback-binding acceptance passed.
- Deployment evidence: `/data/akuru/release-evidence/deployed-4dbf854656368fce305b27c023c4a725332fcf5b-20261119T174557Z.txt`.

Private inputs, original-page renders, immutable source receipts, per-step API requests/results, allocation checks, current publication evidence, screenshots and final acceptance remain under ignored `tmp/biology-june2025-1br-completion/`. Original licensed PDFs/full question text are not committed.

See the [initial read-only evaluation](2026-11-19-june-2025-biology-1br-evaluation.md) for the before-state and the [reusable worked-diagram guidance](../biology-worked-diagrams.md) for the crop-caption and drawing-response lessons.

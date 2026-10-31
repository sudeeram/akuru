# June 2025 Chemistry 1C and 2C guideline audit

Performed: 2026-10-31. Standard: `akuru-igcse-pastpapers 1.2.0`; profile: `pearson-edexcel-igcse 1.1.0`.

## Scope and provenance

Reviewed remaining unapproved whole questions 1C Q8–Q10 and every question in standard 2C (six questions, 38 subparts, 70 marks). Regional papers are outside this batch. All six local source PDF hashes were checked against the production originals. No AI provider was used; the source PDFs, typed examiner commentary and original page renders were inspected directly.

The old graphite crop was created on 2026-10-17, before the initial guidelines. The diamond crop was created on 2026-10-31 and was still too tight. This demonstrates a candidate-extraction gap as well as legacy data; the Markdown rules alone do not enforce label completeness.

## Executed corrections

- Replaced Q8 diamond/graphite crops with complete separately labelled images; retained their respective subpart scope.
- Replaced 1C Q10 apparatus crop with all printed apparatus labels. Its existing complete results-table crop was retained.
- Added private official-scheme answer images for 1C Q9(a)(i), Q9(a)(iii) and 2C Q4(c)(iv). These are answer evidence, not question visuals.
- Corrected all 38 2C subpart prompts: removed response-line and footer debris, restored equations, completion blanks, relevant context and multiple-choice options to their proper parts. Preserved marks.
- Added 71 distinct 2C marking criteria, including allowed alternatives, follow-through and conditions. Criteria count differs from maximum paper marks because Q4(b)(ii) permits any two of three criteria. Applied its explicit cap.
- Scoped 2C apparatus, choice box, isotope/conductivity tables, atoms, blank response axes, burette scale and titration tables to their applicable parts; intentionally blank student-response areas remain blank.
- Linked typed examiner commentary to 32 of the 38 2C parts. For six parts without located part-specific commentary, recorded that absence. Candidate examples remain original source images; no handwriting transcription or invented examiner advice was added.
- Rechecked the existing 1C Q8–Q10 report associations against actual report headings and commentary; retained the accurate associations.
- Preserved conditional scoring warnings using explicit manual-only readiness where the current rule model cannot enforce them. Added supported capped groups without automatically approving assessment readiness.

Seventeen new source crops were downloaded from production and pixel-compared with renders from the exact originals. Full-page checks covered captions, axis titles, scales, units, table boundaries and apparatus extremities. No licensed source text or crop image is included in this Git report.

## Authenticated application and preservation

Applied through authenticated Admin APIs with CSRF protection and expected-revision checks. Snapshots were checked immediately before writes; every saved question was read back and compared with the intended complete payload. Existing Admin subpart statuses, curriculum mappings, coverage reasons and textbook evidence were preserved. Already approved 1C Q1–Q7 were verified unchanged. No questions or papers were published, student records changed, or old assets deleted.

Question revision transitions: 1C Q8 6→7, Q9 9→10, Q10 4→5; 2C Q1 2→3, Q2 4→5, Q3 4→5, Q4 1→2, Q5 3→4, Q6 1→2. Whole-question statuses remain `needs_correction` for 1C Q8–Q10 and `unreviewed` for 2C. These are proposals for Admin confirmation, not an assertion that release gates have passed.

Private local evidence: ignored `tmp/guidelines-update-evidence.json`, before/after API snapshots and downloaded crop comparisons. Source originals remain in the ignored pastpapers directory and production storage.

## Remaining human/release gates

- Admin must confirm corrected content, evidence and coverage, then approve/release separately.
- 2C Q2(c), Q2(e) and Q3(c) need verified private model drawings: the official schemes provide criteria but no drawn model answer. Their drawing/manual-only/answer-required gates remain explicit. Examiner candidate examples must not be substituted for official answers. Live AI configuration is deferred by the owner; the existing graph renderer does not cover every qualitative curve, energy profile or ionic diagram.
- Conditional zero-score rules, cross-part dependencies and alternative allocations not represented by the current scoring contract remain manual-only. A correct displayed marking scheme is not automatic-scoring readiness.
- Native-text label expansion improves new crop proposals only. It cannot guarantee complete extraction on scanned, rotated or complex pages and does not silently replace existing approved assets.

## Verification and rollout

Backend suite: 229 passed, one skipped, seven existing dependency warnings. Three new synthetic regressions cover separate structure captions without chaining, external axis labels without question/footer debris, and preservation of intentionally blank axes. Actual Q8 candidate bounds were also checked against the original PDF.

Production content corrections are complete. Code rollout evidence follows.

### Production rollout evidence

Code release `f507b4fd957508a09bd31314fb3999378d9273d8` deployed successfully on 2026-10-31 at 13:09:35 UTC. Fresh encrypted backup manifest: `/data/akuru/backups/akuru-20261031T130839Z.manifest`. Deployment evidence: `/data/akuru/release-evidence/deployed-f507b4fd957508a09bd31314fb3999378d9273d8-20261031T130935Z.txt`.

No migration was added; production remains at `0016_generated_worked_answers`, with no schema drift. API, worker and web restarted successfully. The production acceptance script passed HTTPS/security headers, routed entry points, fallback boundaries, service health, operational timers and loopback bindings. Post-deployment authenticated read-back matched every 1C/2C question payload, revision and status to the verified correction snapshot; both papers remain unreleased. Browser preview loading is checked separately and is not implied by the API/pixel checks.

Production browser inspection confirmed both corrected Q8 structures loaded with their printed captions (240px diamond and 301px graphite source crops). Offscreen full-page crop-selection previews are lazy-loaded and were excluded from crop-load assertions; these are separate from the displayed question images.

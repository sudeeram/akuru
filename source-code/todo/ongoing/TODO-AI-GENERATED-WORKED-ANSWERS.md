# AI-generated worked answers for graph and drawing questions

Created: 2026-10-31
Started: 2026-10-31
Status: ongoing — implementation and automated validation complete; production deployment/browser acceptance in progress. Live OpenAI configuration and Q7 generation deferred by the owner on 2026-10-31.

## Objective

Provide clearly labelled, Admin-approved AI-generated worked answers where an official marking scheme describes the required work but does not include a usable reference visual. First pilot: June 2025 Chemistry 1C Q7(c)(i), (ii) and (iii). Students should be able to request help in practice and see permitted worked feedback after formal assessment submission and result release.

Every generated answer must retain the visible label **AI-generated worked answer — not an official Pearson answer**, including after Admin approval. It is an illustrative solution, not a replacement marking scheme or evidence that automatic drawing assessment is ready.

Reuse the [answer-visual infrastructure](../ongoing/TODO-MARK-SCHEME-ANSWER-VISUALS.md), existing AI provider/account routing, private storage, audited Admin APIs and release snapshots. Follow the [iGCSE extraction guidelines](../../../guidelines/pastpapers/igcse/README.md). Do not require completion of unrelated automatic drawing-assessment work.

## Step 0 — Verify sources and define the pilot

- [x] Re-read the current Q7 review, exact paper data, marking instructions and relevant examiner guidance. Verify whether a usable official plot exists before labelling it absent.
- [x] Capture exact subpart identities, source hashes/versions, reviewed table values, axes, units, scales, graph requirements and any official tolerances. Do not invent missing values or tolerances.
- [x] Define outputs for c(i) plotted points, c(ii) the identified anomaly and explanation, and c(iii) the two straight best-fit lines excluding the anomaly as instructed. Provide a complete worked graph as well as progressive subpart views.
- [x] Record ambiguous requirements as blockers; verify any derived intersection/readings if included, with appropriate precision. Preserve valid alternative fits and follow-through from a Student's own graph.
- [x] Establish a synthetic regression fixture and private pilot evidence; keep licensed source pages and credentials outside Git.

## Step 1 — Add versioned generated-answer contracts

- [x] Inspect existing answer-visual constraints before extending them: generated assets must have explicit generated provenance rather than pretending to be a crop from a scheme PDF.
- [x] Design additive migrations/models and API schemas for a worked-answer bundle containing text steps, structured graph data, visual assets and subpart/marking-point associations.
- [x] Store source revision/hash references, generation model/provider identifier, prompt-template version, generation time, validation results, renderer version, asset hashes and review/audit details. Never store credentials in provenance.
- [x] Support draft, awaiting review, approved, rejected, superseded and stale states; define permitted transitions and actionable errors. Keep approval separate from publication and scoring readiness.
- [x] Freeze approved content into release/attempt snapshots. Relevant question, data or scheme changes mark the current generated answer stale and require review; historical snapshots retain their original answer.

## Step 2 — Generate and validate accurate worked solutions

- [x] Add an Admin-triggered asynchronous generation job through the existing AI provider layer, with bounded context/output, timeout/retry limits, idempotency and visible job status.
- [x] Ground requests in reviewed question and scheme evidence; use examiner guidance as supporting advice, never as an alternative rubric. Treat document content as untrusted input.
- [x] Request a structured solution and explanation. Render graphs using trusted plotting code from validated data; do not execute model-authored code or rely on a generative image model for numeric graph accuracy.
- [x] Validate table-to-point equality, coordinate ranges, units, axis labels, scales, anomaly selection, line construction and consistency between explanation and image. Distinguish deterministic checks from scientific decisions requiring human review.
- [x] Preserve intentionally blank question grids. Generated solutions are separate private answer assets and never replace the question visual.
- [x] Produce readable, bounded-size images with accessible descriptions and a text/data equivalent. Support subpart-specific overlays without revealing later steps prematurely.
- [x] Reuse a reviewed answer across Students; avoid per-Student generation. Deduplicate by relevant source and generator versions, record usage/cost and require deliberate regeneration to replace a draft.
- [x] Fail safely for ambiguous data, unsupported diagrams, provider failure or invalid output; never publish a guessed or partially validated answer.

## Step 3 — Build the Admin review experience

- [x] Add an AI-generated worked answer section to the existing question review page with Generate, job progress, preview, edit, regenerate, approve and reject controls.
- [x] Display original question, exact scheme evidence, source versions and validation findings alongside the generated steps and graph.
- [x] Allow corrections to explanation and structured plotting data followed by deterministic re-rendering and validation. Edits invalidate previous approval.
- [x] Let Admins verify each subpart and the complete solution; show the AI-generated label throughout. Do not automatically approve existing question/subpart content or alter other visual links.
- [x] Preserve unsaved changes and selected subpart; use descriptive toast feedback, accessible controls and expected-revision conflict handling.
- [x] Provide authenticated, audited API operations for the same workflow so future source preparation can use supported APIs rather than direct database edits.

## Step 4 — Deliver controlled Student help

- [x] Add Show worked answer in permitted practice feedback with progressive steps and an optional complete graph. Display only approved, current, released content.
- [x] Record that help was revealed; apply existing assisted-practice rules so a copied/revealed answer does not falsely increase independent mastery.
- [x] For formal assessments, enforce submission AND feedback-release permissions on the backend. Do not expose solution text, coordinates, image URLs or assets in question-taking responses.
- [x] Keep generated solutions distinguishable from official scheme extracts. Explain that valid graphs may vary within scheme rules and that follow-through depends on the Student's own work.
- [x] Add mobile-friendly zoom/fullscreen, keyboard access, readable scientific notation and accessible graph descriptions.
- [x] Enforce Student/family isolation, permission-aware asset retrieval and cache clearing on logout/account changes. Avoid prefetching unreleased answers.

## Step 5 — Protect assessment integrity and test

- [x] Keep official marking points, caps, tolerances and follow-through authoritative; generated examples must not silently become scoring criteria or enable automatic drawing marking.
- [x] Test numerical plotting, labels/units, anomaly exclusion, alternative valid line fits, progressive reveal and image/text agreement using synthetic fixtures.
- [x] Test stale-source invalidation, concurrent edits, repeated generation, failure/retry, approval transitions, publication and historical attempt snapshots.
- [x] Test unauthorized access, cross-Student access, guessed asset IDs, pre-submission and pre-result-release leakage, including graph data and caches.
- [ ] Test the complete Admin generation/edit/approval/release and Student practice/formal-feedback journeys on desktop/mobile, including accessibility and existing official answer visuals.
- [ ] Have the Q7 pilot scientifically reviewed against the source; record evidence and limitations. Do not count a successful API response as proof that the answer is correct.

## Step 6 — Document and release safely

- [x] Update developer architecture, Admin/Student user documentation and iGCSE guidelines with generated-answer provenance, review/reveal rules and the Q7 example.
- [ ] Ship behind a feature flag with a migration/rollback plan; back up production before deployment and preserve all existing reviews and attempts.
- [ ] Generate and review the production Q7 pilot through authenticated APIs/UI, release only approved answers and verify with authorized Admin and Student accounts.
- [ ] Run production health/security checks and confirm formal-assessment answers remain hidden until permitted. Record release evidence, then move this plan to completed only when all required acceptance checks pass.

## Completion criteria

- Q7(c)(i–iii) has a verified, approved and released progressive worked answer with accurate plots and explanations.
- Students always see the AI-generated label and only access answers in permitted contexts.
- Official marking remains authoritative; automatic drawing assessment remains separately gated.
- Generation is reusable and bounded in cost, source changes invalidate current approval, and previous attempts remain reproducible.

## Deferred scope

Unrestricted generation for arbitrary scientific diagrams, real-time personalized graph generation, and autonomous drawing assessment are future extensions. The first implementation should support the verified graph workflow well and explicitly reject unsupported cases.


## Validation and deliberate deferrals

- Backend release suite: 226 passed, 1 skipped; existing dependency warnings only.
- Frontend unit suite: 103 passed; TypeScript and targeted lint passed.
- Disposable PostgreSQL migration: upgrade/check/downgrade/re-upgrade/check passed; local application data unchanged.
- The production owner explicitly deferred OpenAI credentials on 2026-10-31. New generation will remain disabled; no live model-generated Q7 answer or Student paper release is claimed.
- The 1C source audit identifies Q7(c)(i–iii), with optional support for Q7(d), as the graph pilot. Q5 and Q9 have official scheme diagrams and should use those original sources.
- Remaining content acceptance after configuration: generate Q7, scientifically review each step, approve/attach, then complete existing question/whole-paper/curriculum release gates. Do not approve other incomplete questions merely to make a pilot visible.

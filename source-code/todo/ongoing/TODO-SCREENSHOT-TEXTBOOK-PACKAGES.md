# Screenshot textbook packages

Started: 2026-11-01. Scope: local development and tests; no production deployment authorised in this task.

- [x] Prepare source-first Topic 1 pilot and comparison benchmark; keep licensed derivatives ignored.
- [x] Recommend resolutions for four pilot exceptions; final Admin decisions remain explicit.
- [x] Add bounded, validated ZIP packaging and Admin preview/import into a separate supporting draft.
- [x] Preserve source pages, printed labels, figures, tables, exercise hierarchy and provenance.
- [x] Add explicit whole-package review with per-exception notes and optimistic content hash; do not publish or replace a primary source automatically.
- [x] Add Admin import/review UI using existing editable document review and visual approval.
- [x] Test authentication/CSRF, scope, malicious archives, duplicate imports, draft isolation, review and publication gates.
- [x] Test retrieval/citation/visual grounding locally; distinguish deterministic integration checks from live AI teaching evaluation.
- [x] Document operator workflow and remaining human/release gates.

Human/release gates: whole-document and visual approval, measured owner review effort, Topic 2 generalisation, live-model teaching quality and any production replacement/deployment remain outstanding. No test should silently approve these decisions.

## Local implementation evidence — 2026-11-01

- Final backend suite: 263 passed, 1 skipped (existing optional test), 7 dependency warnings.
- Prepared-package tests: 16 passed, including private Topic 1 source import/publish/visual-reference checks, and Parent/Student denial. Private fixtures are not committed; the synthetic scenario remains usable in CI.
- Frontend suite: 108 passed. Typecheck, lint, production build and generated-contract check passed. Existing build chunk-size/route-classification notices remain.
- Reusable isolated browser test: `source-code/frontend/tests/prepared-textbook-import-browser.mjs`; mocked API workflow and desktop/mobile checks passed. This is not a full live-browser-to-database test.
- Six targeted local-embedding relevance probes passed. A broad practical query finds the measurement table; a separate calculation query checks the worked solubility result. Integrity preflight alone does not establish pedagogical quality.
- No new dependencies, migrations, persistent test content, production writes, paid model calls, Git commits or deployments. Used the already bundled patched Node 24.22.1, without installing another local runtime.

## Pending human / live release validation

- [x] Owner accepted all four recommended scientific/numerical clarifications on 2026-11-01 in the conversation. Applied to a separate ignored `ai-prepared-reviewed-v1` candidate; original frozen pilot preserved.
- [ ] Admin approves the complete prepared document and its selected visuals through the application workflow.
- [ ] Measure the owner's actual content-review time.
- [x] Run bounded live text-Tutor teaching evaluation with the Evaluation key: 22 unique cases, baseline and retests; US$0.387078 estimated cumulative spend of a US$2 ceiling. See the sanitised guideline review record.
- [ ] Complete Student browser acceptance and any flashcard-specific live content-quality evaluation; these are not established by the service-level Tutor run.
- [ ] Evaluate Topic 2 screenshots when supplied.
- [ ] Authorise and perform any production import/replacement/deployment separately.

Keep this plan ongoing until the human/live evaluation gates are resolved; the local implementation checkboxes above do not mark production release complete.

Acceptance scope: the owner approved the four clarifications, not production import, whole-document/visual approval or deployment. The reviewed candidate ZIP passed the existing package validator. Owner review duration was not supplied and is not inferred from chat timing.

## Live teaching evaluation — 2026-11-01

- Fixed normal-turn tool schema mismatch, scoped source/figure ranking, exercise-only answer evidence and short-follow-up retrieval. Tutor prompts now version 1.0.2.
- Final reviewed set: 21 satisfactory outcomes, 1 partial boiling/evaporation explanation; single-sample development checks, not a global accuracy claim. Missing-evidence fallback is safe but generic.
- 52 paid generations over all baseline/retest phases; 147,479 input and 9,212 output tokens; only the Evaluation key used. Disposable schemas and storage removed.
- Final backend suite: 270 passed, 1 skipped. No production changes, commits or pushes.
- Local provider setting corrected from unsupported `enabled` to `openai`, matching the owner's intent. Other secrets/settings were preserved.
- [ ] Review the partial explanation and compact repeated clarification context before release.

## Authorized production text pilot — 2026-11-01

Owner authorized a one-student production teaching trial using the AKURU-backend project. Scope: existing published Chemistry Topic 1, selected student only; no screenshot-package import, source replacement or implicit whole-document/visual approval. A temporary model/prompt/content-version-pinned pilot gate preserves the production requirement for full release gates outside the pilot. Voice, next-topic recommendations and assessed practice stay disabled. The selected topic's existing publication has no approved visual crops in its immutable manifest; citation pages remain the available evidence. Production verification and operator instructions will be recorded separately after deployment.

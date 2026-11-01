# Screenshot textbook packages

Started: 2026-11-01. Initial scope: local development and tests. Updated scope: owner subsequently authorized deployment and a one-student production text Tutor pilot; source replacement and whole-package/visual approval remain separate.

- [x] Prepare source-first Topic 1 pilot and comparison benchmark; keep licensed derivatives ignored.
- [x] Recommend resolutions for four pilot exceptions; final Admin decisions remain explicit.
- [x] Add bounded, validated ZIP packaging and Admin preview/import into a separate supporting draft.
- [x] Preserve source pages, printed labels, figures, tables, exercise hierarchy and provenance.
- [x] Add explicit whole-package review with per-exception notes and optimistic content hash; do not publish or replace a primary source automatically.
- [x] Add Admin import/review UI using existing editable document review and visual approval.
- [x] Test authentication/CSRF, scope, malicious archives, duplicate imports, draft isolation, review and publication gates.
- [x] Test retrieval/citation/visual grounding locally; distinguish deterministic integration checks from live AI teaching evaluation.
- [x] Document operator workflow and remaining human/release gates.

Human/release gates: whole-document and visual approval, measured owner review effort, Topic 2 generalisation, further teaching-quality review and any production source replacement remain outstanding; see the separately authorized production pilot below. No test should silently approve these decisions.

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
- [x] Complete Student browser acceptance for the authorized text pilot with the owner's normal Student sign-in.
- [ ] Complete any flashcard-specific live content-quality evaluation; this is not established by the Tutor runs.
- [ ] Evaluate Topic 2 screenshots when supplied.
- [x] Obtain authorization and deploy the code for a controlled one-student production text pilot.
- [ ] Separately authorize and review a production screenshot-package import/source replacement if desired.

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


## Production acceptance — 2026-11-01

- Code release `00bf7b4` committed/pushed and deployed with the standard encrypted backup, migration/schema check (no changes) and service restart.
- Protected runtime: AKURU-backend credential alias configured through authenticated Admin API; model `gpt-6.1-sol`, prompt `1.0.2`, published Topic 1 version 2. Temporary pilot expires 2026-11-15 16:32 UTC.
- Owner signed in normally as the selected Student. Created AKURU Chemistry tutor in the UI, selected the single available pilot topic, obtained a correct solid/liquid explanation and short follow-up, and opened the authorized source-page image. Out-of-topic request returned an evidence-insufficient response without a paid call. Setup session ended normally and summary/transcript retained.
- Two paid backend calls: 8,830 input and 306 output tokens; estimated US$0.020720 at the previously verified uncached standard rates. This is separate from the Evaluation ledger; actual billed cached/rate accounting may differ.
- Anonymous Tutor/configuration APIs returned 401. Read-only production policy check confirmed second student disabled; no additional Student credentials/sessions were synthesized. Voice, assessed practice and next-topic features remain gated off. Parent summaries were generated on session end, not separately tested in the Parent UI.
- Published source manifest has no approved figure crops. Source pages load; displaying separately approved crops requires a later explicit publication. The new screenshot draft remains local and unapproved for whole-document/visual publication.
- HTTPS/header/routing/service/timer/private-port acceptance passed. Existing npm dependency advisories remain separately tracked in `TODO-NPM-DEPENDENCY-SECURITY.md`; this release is not their remediation.
- Detailed acceptance record is protected on the server at `/data/akuru/release-evidence/text-pilot-20261101-acceptance.json`.

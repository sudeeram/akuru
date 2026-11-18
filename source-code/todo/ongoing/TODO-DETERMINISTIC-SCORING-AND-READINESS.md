# Deterministic scoring and readiness from the development workflow

Created: 2026-11-18
Started: 2026-11-18
Status: ongoing
Priority: high
First acceptance paper: Pearson Edexcel Biology June 2025 2BR, Q1–Q6 (31 subparts)

## Required outcome

From this Codex/developer workflow, we must be able to retrieve original evidence, analyse a question/subpart, configure all supported scoring rules, submit reviewed answer fixtures, run the **actual production marking implementation without paid model calls**, persist its validation evidence, and set **“All scoring rules represented and checked”** through authenticated AKURU APIs. A separate Admin-browser editing or validation exercise must not be necessary.

The same workflow must apply to future papers and supported scoring patterns, not just Q3(b). Inspect every Q1–Q6 subpart and give it either a current, defensible readiness certificate or precise outstanding blockers. Do not promise that every open explanation, drawing or ambiguous publisher instruction can become automatically markable. Unsupported/ambiguous student responses must be referred for review rather than guessed or silently scored zero.

“All scoring rules represented and checked” is the existing UI wording for `assessmentReadiness=automatic`. Under the new deterministic policy, the server must derive it from current executable rules and a passing validation run, not accept an unverified client assertion. Keep source extraction accuracy, source-issue decisions, curriculum coverage, content approval, scoring readiness and Student release as separate gates.

## Starting point and boundaries

- Calculation score bands and their Admin editor are already deployed in commit `e2c6de3`. They allocate weighted marks after model evidence matching; they do **not** parse a student's numerical answer.
- Q3(b) now has `P_FULL` / `P_PARTIAL` bands, corrected examiner advice, human-approved content and current source assessment v10 at 98%. It deliberately remains manual-only. Eight local allocation fixtures supplied the expected matches; no paid scoring validation was run. These fixtures are not an end-to-end answer-recognition certificate.
- The present scoring-validation job calls the model twice per answer. Its eight-sample limit is inadequate for a comprehensive deterministic suite and must not constrain the new path.
- The current assessment evaluator also checks model-release policy and reserves model quota before marking. Deterministic dispatch must be integrated before those model-only operations, while retaining authentication, assessment ownership, source authorisation and release checks.
- No paid OpenAI calls, fallback inference, account switching, key configuration or model quotas are needed for deterministic preparation, validation or marking. General Tutor teaching is a separate feature; it must not be called implicitly to finish deterministic scoring.
- Preserve all human decisions, original source versions, earlier analyses, scoring runs, Student results and unrelated Tutor releases. Do not manufacture model-response IDs, token usage, model confidence or a historical live-validation pass.

## Step 0 — Freeze the contract and establish a fresh inventory

- [x] Move this plan to `todo/ongoing` when implementation starts; record the start date.
- [x] Fetch a fresh authenticated snapshot of Q1–Q6, original paper/scheme/report references, current assessments, scoring rules, approvals, source issues and Tutor releases. Private source copies and credentials stay outside Git.
- [ ] Produce a 31-row inventory with answer type, official maximum, accepted alternatives, exclusions, caps, combinations, dependencies/follow-through, source conflicts, missing evidence, scoring engine candidate and current readiness basis.
- [x] Separate the three proofs: rule/allocation tests, actual answer-recognition tests, and live-model behaviour tests. Only the second can certify this new deterministic path; mocked expected matches cannot substitute for it.
- [ ] Define supported-response coverage and abstention as part of readiness. A supported deterministic question may refer an ambiguous response for review; it must not claim to understand all unrestricted natural language.
- [x] Specify legacy treatment explicitly: identify existing automatic items without the new certificate, retain their recorded history, and propose targeted remediation. Do not silently convert legacy approvals into deterministic certificates or bulk revoke unrelated releases.

## Step 1 — Add versioned machine-readable answer rules

- [ ] Design a backwards-compatible rubric schema extending the existing structured rules with an explicit engine/matcher policy and stable criterion IDs. Preserve version-1/2 serialization and fingerprints when new fields are absent; verify with historical snapshots.
- [ ] Represent numeric full/partial alternatives, exact decimal/rational values, source-authorised ranges/tolerances, notation, significant figures/decimal places, units, allowed omission of supplied units, and explicit exclusions. Preserve the entered lexical form: numerically equal answers can have different rounding compliance.
- [ ] Represent fixed-choice option mappings and reviewed short-answer aliases; optionally support labelled answer slots and explicitly keyed multi-answer responses. Never lose W/X/Y-to-answer associations.
- [ ] Connect matcher outcomes to existing score bands, group maxima, any-N limits and combined-response rules. Keep evidence matching separate from allocation; prevent additive alternatives and duplicate credit.
- [ ] Define a bounded, versioned representation for source-authorised method/working stages and prerequisite/follow-through rules. Mark unsupported interactions as blockers instead of flattening them into independent points.
- [ ] Bind each rule to exact question/scheme evidence and any explicit source adjudication. Do not infer tolerances, spelling allowances or partial marks from common practice or examiner examples.
- [ ] Publish a capability matrix for valid matcher/allocator combinations. Address current version-2 restrictions on dependencies and selective groups only with explicit semantics and regression tests.

## Step 2 — Implement the safe answer-recognition engines

- [ ] Implement typed results such as `matched`, `no_credit` and `requires_review`, with rule IDs, exact answer evidence and reason codes. Keep parse failure distinct from a recognised wrong answer.
- [ ] Use bounded decimal/rational arithmetic, not binary float equality, for numerical matching. Support reviewed scientific forms such as `5.7e-2`, `5.7 × 10^-2` and superscript exponent notation.
- [ ] Preserve and validate signs, powers, significant trailing zeroes, decimal places, units and dimensions. Apply conversions only where the reviewed scheme permits them; a unit printed after an answer box may make an omitted typed unit acceptable.
- [ ] Identify the final answer without confusing intermediate working, question data or quoted alternatives with the student's conclusion. Prefer a structured final-answer field where appropriate; reject or refer conflicting finals and unsupported free-form working.
- [ ] Recognise permitted calculation stages using an allowlisted, bounded arithmetic representation tied to source values. Do not award a method mark merely because an unrelated line contains “×5”.
- [ ] Implement fixed-choice/fixed-name matching with reviewed normalization and aliases. Handle negation, corrections and multiple conflicting choices conservatively. Avoid broad fuzzy spelling or keyword matching.
- [ ] For labelled identifications, require explicit label-to-answer correspondence or the defined structured input; never award all terms simply because they appear somewhere in the response.
- [ ] Limit input length, expression depth, exponent magnitude and execution time. No `eval`, arbitrary Python, executable rules, unbounded regex, network calls or code supplied in an imported package.
- [ ] Keep open explanations/discussions, handwriting interpretation, diagrams and unsupported semantic variants out of deterministic certification. Finite reviewed phrase recognition may be used only for its documented response grammar; an unmatched valid paraphrase must not silently receive zero.

## Step 3 — Integrate real marking, feedback and Student state

- [ ] Dispatch frozen supported rubrics to the deterministic engine in both Tutor practice and formal assessments before model routing, model-only evaluation gates, quota reservation or paid feedback generation.
- [ ] Reuse server allocation and per-subpart/full-question caps. Preserve namespacing and frozen rules when preparing complete-paper assessments; support mixed-engine papers without applying a model gate/quota to deterministic parts.
- [ ] Produce deterministic source-grounded marking explanations and feedback templates, identifying the awarded band/method and applicable scheme instruction. Do not fabricate a model-generated teaching response or report feedback that has not passed its own source gate.
- [ ] Persist the actual engine/version, rule fingerprint, credited IDs, awarded/max marks and recognition reasons in immutable assessment results. Use explicit deterministic provenance and zero model usage; distinguish this from model confidence and extraction confidence.
- [ ] Preserve per-student/family ownership and mastery isolation. Only final released results may affect mastery; referred/unscored answers must not count as incorrect or completed automatic results.
- [ ] Give Students a clear pending-review/clarification state for ambiguous answers and a supported way to clarify a final answer during practice. Keep formal-exam timing/submission restrictions and answer-reveal rules intact.
- [ ] Never send a referred answer to a paid model automatically. A future explicitly authorised model-assisted validation/scoring path remains separately labelled and gated.

## Step 4 — Persist reproducible scoring-validation evidence

- [ ] Add reviewed migrations for durable validation runs/cases and readiness bindings if existing audit/job tables cannot provide the required immutable, queryable record. Decide and document this before implementing persistence; never store only a free-text readiness note.
- [ ] Each run records paper/question/subpart, request/idempotency key, authenticated actor, relevant source/rubric/response-format hashes, engine and policy versions, fixture-set hash, timestamps, case results, coverage, invariants, execution origin and pass/fail/block reasons.
- [ ] Store synthetic canonical answer fixtures and independently reviewed expected scores/credited IDs; prohibit Student PII in reusable fixture packages. Keep licensed source reproductions in private storage, with only safe references/hashes in Git.
- [ ] Have the **server execute its own trusted deployed matcher and allocator** on supplied answer inputs and calculate actual outcomes. Never accept client-supplied marking decisions, totals, pass flags, engine claims or local test reports as proof of a production pass.
- [ ] Compare the deployed engine/version against the reviewed package and local runner. A local pass may be preview evidence; only a matching server-side replay can update production readiness.
- [ ] Make pass/history records append-only. Derive current/stale status from relevant hashes and engine compatibility; retain the original records when a question is edited or a validation is superseded.
- [ ] Scope invalidation to the affected part and its actual shared context. A sibling-only edit should not invalidate unrelated certificates/releases; changing common data or a global scoring rule must invalidate every affected part.

## Step 5 — Add authenticated APIs and a repeatable developer CLI

- [ ] Provide Admin-only preview/import/validate/status/readiness endpoints, integrating with existing review APIs where sensible. Enforce CSRF/session rules, authorization, rate limits, bounded payloads, optimistic revision/hash checks and auditable mutations.
- [ ] Build a versioned prepared scoring package: paper identity, exact source references, rule definitions, source-based interpretation notes, engine requirements, synthetic fixtures, expected scores, provenance and explicit blockers.
- [ ] Supply CLI commands to fetch, inspect, lint, preview differences, apply rules, validate/replay, inspect evidence, refresh source assessment and request readiness/release. Use normal authenticated APIs; no direct production SQL or server-private Python imports as the routine authoring interface.
- [ ] Provide dry-run and one-subpart modes; resume a paper batch with per-part receipts, idempotency keys and concurrency protection. A retry must not overwrite another Admin's changes, duplicate certificates or repeat completed paid work.
- [ ] Support ignored credential files and redact credentials, student data and raw licensed documents from console output. No passwords/API keys in command arguments, Git or validation packages.
- [ ] Complete source comparison, explicit publisher-issue adjudication and approved curriculum mapping from this workflow where source evidence permits. Ambiguity can be escalated here for a decision; no browser-only action may be required.

## Step 6 — Enforce the readiness transition and release boundaries

- [ ] Centralize the readiness decision: complete supported executable rubric + approved exact scheme evidence + passing current answer-to-score validation + required case coverage + no unresolved scoring/source contradiction.
- [ ] Reject direct `assessmentReadiness=automatic` writes without the required current proof for the new policy. A checkbox, high extraction percentage or externally asserted pass must not bypass this rule.
- [ ] Treat purely numeric/choice certification separately from optional live-model certification. Do not require an OpenAI key, a paid validation job or the UI's paid-model confirmation for a deterministic pass.
- [ ] Atomically record the validation and set “All scoring rules represented and checked” when eligible; return structured remaining blockers otherwise. Content approval is preserved, not automatically manufactured by a scoring pass.
- [ ] Invalidate readiness for materially changed rules, answer format, relevant source/shared context or incompatible engine policy. Preserve existing immutable results and mark new scoring/release eligibility accurately.
- [ ] Keep curriculum, current final-content assessment, reviewed visuals, independent answerability and publication gates separate. Scoring readiness alone must not release a question or complete paper.
- [ ] Allow the authenticated CLI to restore previously withdrawn-for-scoring Tutor parts after all gates pass and the intended restoration is explicitly recorded. Respect unrelated explicit Admin withdrawals. Require a separate explicit whole-exam publication action.

## Step 7 — Complete Admin and Student frontend support

- [ ] Add engine/capability selection and readable numeric/choice/method rule editors to the existing scoring panel. Display criteria, official evidence, scores, units/rounding and unsupported restrictions without hiding them in JSON.
- [ ] Add “Validate without model calls”, validation history and current certificate status. Clearly separate deterministic, legacy/manual-attested and model-validated readiness bases.
- [ ] Show case-by-case input, expected/actual marks and credited IDs, abstention reasons, rule coverage and current/stale status. Support larger bounded deterministic suites instead of the current eight-example model limit.
- [ ] Explain why readiness is blocked and where the developer-prepared package/receipt is recorded. The Admin UI is an optional inspection/edit route; every required operation must also be available through the CLI/APIs.
- [ ] Make saved readiness/source/release states update correctly after API-driven work, with query invalidation, useful toast messages and accessible status labels. Preserve selected question/subpart and unsaved-change protections.
- [ ] For Students, support the final-answer/labelled fields required by each engine and display accurate marks or pending-review status, without leaking marking rules before allowed reveal.

## Step 8 — Prove Q3(b) end to end first

- [ ] Fetch its latest production revision and exact original scheme/report evidence; do not use the November 18 snapshot as an unchecked write target.
- [ ] Encode the two-significant-figure result, scientific notation, scheme-listed one-mark values and explicit `0.572` exclusion in machine-readable rules. Preserve the distinction between a final answer and an unrounded intermediate value.
- [ ] Test every listed band outcome plus zero, full working ending correctly, conflicting answers, wrong signs/magnitude, missing/supplied/wrong units, extra significant figures, decimal/scientific equivalents, invalid input and oversized exponents. If an edge case is not authorised by the scheme, refer it instead of inventing an allowance.
- [ ] Derive any accepted unrounded-value range/representation from reviewed source meaning. Do not use an unrestricted string prefix such as `0.05729*` as a numerical rule.
- [ ] Execute the actual matcher and allocator locally, then replay the same fixture package through the production Admin API with model/network inference explicitly disabled. Assert zero provider calls, token reservations and AI charges.
- [ ] Obtain a passing current certificate and set readiness through the server policy; refresh the source assessment if changed content requires it. Preserve its human approval and unchanged sibling content/releases.
- [ ] Restore its former Tutor release only after source/coverage/visual/release validation succeeds. Exercise actual Student answer submission and deterministic result display without paid calls, using an authorised test account and removing/segregating test performance data.

## Step 9 — Work through Q1–Q6 one subpart at a time

This is a triage sequence, not advance permission to mark every item automatic. Re-read the actual prompt and complete original scheme, including continued rows, for each case.

| Items | Proposed route and essential checks |
| --- | --- |
| Q1(a), Q1(b), Q1(c)(ii), Q1(d), Q1(e), Q1(f), Q1(g) | Review conceptual/explanatory criteria, any-N caps, combinations, semantic alternatives and source issues. Do not mistake allocation support for free-text understanding. Use a supported bounded response grammar only where faithful; otherwise record a precise manual/semantic-engine blocker. Q1(e)'s earlier lower extraction estimate requires source review independently of scoring. |
| Q1(c)(i) | Inspect its complete one-mark prompt and answer before deciding whether fixed-name recognition is sufficient. |
| Q2(a) | Label-bound W/X/Y identifications; correct terminology in the wrong slots must not earn credit. |
| Q2(b) | Iris-response explanation: multiple muscle actions and pupil change, contradiction/negation and independent credits. Do not certify unrestricted prose using keyword presence. |
| Q3(a), Q6(a)(i–iii) | Apparatus/MCQ/structure recognition; preserve option-to-label mappings, aliases and conflicting-choice handling. |
| Q3(b) | First deterministic score-band pilot from Step 8. |
| Q3(c), Q3(d)(i–ii), Q3(e) | Practical reasoning/explanations and capped alternatives; review supported grammar, source fidelity and current curriculum uncertainty separately. |
| Q4(a), Q4(b)(i), Q4(b)(iv) | Definition, sampling method and extended discussion; inspect any-N/combined credits and omitted converse/variation allowances. Open discussion remains a semantic/manual case unless genuinely supported. |
| Q4(b)(ii) | Multi-stage density calculation: species selection, table coordinates/blanks, sampled area, full result and all scheme-authorised partial pathways. Verify unusual extracted allowances directly against the original row rather than copying OCR. |
| Q4(b)(iii) | Fixed species identification, while preserving the report warning that blank cells contribute to variation. |
| Q5(a) | Percentage calculation: correct numerator/denominator, accepted unrounded/rounded full answers and source-specific partial outcomes; do not reuse Q3(b)'s significant-figure rule blindly. |
| Q5(b–d) | Cloning sequence, immunity explanation and data discussion. Review capped criteria, combinations and missing converse-control guidance; avoid unsupported semantic certification. |
| Q6(b)(i) | Concentration/volume conversion and source-authorised calculation/working partial credit. |
| Q6(b)(ii–iii) | Protein/glucose explanations; exact physiological meaning and capped credits. Resolve b(iii)'s internal scheme prose/marks-column contradiction with an explicit source-based decision before certification; scheme-over-report precedence alone does not resolve an internal scheme contradiction. |

- [ ] For all 31 subparts, retain source comparisons, supported/unsupported classification, rule changes, actual validation evidence and final readiness/release outcomes in a resumable report.
- [ ] Do not silently rewrite publisher sources. Record interpretations/adjudications with exact evidence and distinguish them from the official wording.
- [ ] Preserve approved visuals and final content where unchanged; remediate only identified deficiencies. Do not require the Admin to repeat obvious evidence links or manually tick every point when an audited API workflow has completed the same checks.
- [ ] Complete each supported subpart before moving on; if blocked, record why and continue independent parts. Finish with an honest inventory of automatic, manual and still-unresolved items rather than raising confidence to conceal limitations.

## Step 10 — Regression, privacy and release gates

- [ ] Test parser boundaries, arithmetic/rounding/units, alternatives, caps, dependencies where supported, duplicate credit, ambiguous answers and malicious inputs. Include property/invariant tests: bounded marks, no duplicate credit, equivalent supported notation and deterministic repeatability.
- [ ] Use source-derived positive, partial, negative and near-miss cases; mutation tests must catch wrong denominators, signs, magnitudes, extra answers and contradictory wording. Keep some independently reviewed holdout cases separate from initial rule-authoring fixtures.
- [ ] Test Admin auth/CSRF, cross-family/student denial, idempotency, concurrent edits, stale hashes, engine upgrades, failed validation, audit persistence and direct readiness-bypass attempts.
- [ ] Test the same rules through CLI/API, server validation, full-paper compilation, Tutor practice and formal-assessment execution. Prove with fail-on-call provider stubs that supported deterministic paths never contact or reserve quota for a model.
- [ ] Test mixed-engine assessments and abstentions: no paid fallback, no false zero/mastery penalty, no premature answer reveal and no unrelated sibling release loss.
- [ ] Run backend/frontend tests, generated contract checks, migrations on disposable databases where needed, typecheck, lint, build and authenticated role checks. Paid evaluation is optional and requires separate explicit approval; it is not a deterministic release prerequisite.
- [ ] Update extraction guidelines, architecture, API contracts, developer docs and Admin/Student instructions. Document capability boundaries and the exact authenticated commands needed to complete readiness from this end.

## Step 11 — Deploy, prove production and close the plan

- [ ] Commit/push only reviewed changes and deploy through the component-aware release script with required backup, forward migrations, timings and acceptance checks. This plan authorises no production changes merely by being written.
- [ ] Replay Q3(b)'s approved deterministic package against the deployed engine, verify the readiness certificate is current and compare actual Student scoring with expected results without model calls.
- [ ] Continue the Q1–Q6 rollout, preserving history, family isolation and existing safe releases; make any whole-paper publication an explicit reviewed action.
- [ ] Provide production links and a final per-part report: engine, readiness, certificate, source confidence, coverage, release status and remaining blockers. No unqualified “paper complete” statement while unresolved parts remain.
- [ ] Demonstrate the same fetch → analyse → prepare → apply → server-validate → readiness → guarded release workflow on a new supported question from another paper. No new hard-coded paper IDs or browser-only steps.
- [ ] Record completion date and evidence, move this plan to `todo/completed`, and update the plan index only when all required work is complete.

## Definition of done

A supported question/subpart can be taken from original source analysis to **“All scoring rules represented and checked”** entirely through this developer/chat workflow and authenticated APIs, with a current server-replayed answer-to-score certificate and no paid model dependency. The production Student marking path uses the same certified executable rules. All Q1–Q6 parts have been analysed and either completed through that path or explicitly reported as requiring an unsupported semantic capability/source decision. Neither a mock pass, a confidence percentage nor a manually asserted status can stand in for the required evidence.

## Related implementation and plans

- [Existing calculation score bands](../../backend/docs/calculation-score-bands.md)
- [Marking-scheme extraction guidelines](../../../guidelines/pastpapers/igcse/marking-scheme-analysis.md)
- [Past-paper analysis conformance](../planned/TODO-IGCSE-PASTPAPER-ANALYSIS.md)
- [Core assessment roadmap](../ongoing/TODO.md)

## Implementation evidence — 2026-11-18

- Core schema, bounded recognizers, authenticated server replay/certificates, no-model assessment dispatch, Admin controls, Student answer fields and developer CLI implemented locally.
- Backend regression: 595 passed, 1 skipped; additional changes require final checks before release. Ten source-reviewed candidate packages pass 135 local actual answer-to-score cases. This is preview evidence, not a production certificate.
- Existing audit records provide durable validation storage; no migration needed. Capability limits and developer commands are documented in [the backend guide](../../backend/docs/deterministic-scoring-and-readiness.md).
- Remaining release gates include production replay/rollout, complete per-part source/blocker report, another-paper demonstration and mixed-subpart compilation/sibling-release freshness work. Do not mark the plan complete before these are resolved.

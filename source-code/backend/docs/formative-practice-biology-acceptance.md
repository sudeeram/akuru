# Biology June 2025 2BR formative-practice acceptance

Date: 18 November 2026. Runtime release: `6be2a8d0ccbeeb9bd61824a432517df4caf454b5`.
Status: completed — deployed, authenticated API acceptance and normal Student browser checks passed. Documentation closed 19 November 2026 (Asia/Colombo).

## Implemented learning workflow

Approved/current source content can receive indicative feedback without manual grading or a deterministic certificate. Counted topic sets (1–20 independently answerable items) persist privately per Student. New exam-style questions use authorised published topic content and approved examples, a hidden suggested rubric, structural checks and a separate model check before serving each item. Generated items are labelled and never inserted into the official paper bank.

The existing single-question path remains usable. Existing certified bounded recognition can run without inference; unsupported prose can receive formative semantic feedback. The shared credit allocator applies caps and scoring bands. Unsupported allocation/drawing interpretation provides honest guidance without an invented score. Indicative set scores do not assert certified mastery.

## Authenticated production source reconciliation

Only paper `eea024fe-978f-4392-b330-c0011201cf63` was reconciled through Admin APIs. Readiness preview passed all 31 subparts. Guarded release enabled the 17 previously scoring-blocked parts; all 31 are enabled/current, versus 14 before this delivery. Source data, revisions, source-analysis hashes/versions, approvals and all ten certificate IDs were compared with the baseline and preserved. No source extraction, new scoring certification, formal-paper publication or Chemistry data update was performed.

Private baseline, preview, receipt and after-state: ignored `tmp/formative-production/`. Raw licensed documents, Student transcripts, credentials and model responses are not committed.

## Verification

- Full backend suite: 631 passed, 1 skipped. Final scoped selection/permission regression: 38 passed.
- Frontend: all 123 tests passed; typecheck, lint, build and generated contract checks passed.
- Generated persistence was tested through real Tutor invocation/quota commits, replacing only the external provider with a fixture. Related suite: 10 passed, no paid calls.
- Schema consistency: Alembic reports no new upgrade operations. A deployment check caught an index/constraint representation mismatch; the ORM was aligned with the existing valid migration before service rollout. No data reset or destructive corrective migration was needed.
- Live AKURU-Evaluation sample: one generated Coordination question plus independent check; correct/partial/irrelevant answers received 5/5, 1/5 and 0/5. Original Biology Q1(d)'s any-two allocation capped credit at 2/2. Six calls: estimated US$0.036932, conservative charged bound US$0.047367 of the explicitly approved US$1 ceiling. Private persistent ledger: `tmp/formative-practice-evaluation/budget-ledger.json`. This is a small sample, not a measured general accuracy guarantee.
- Initial production Student check using the authorised pilot Student account: request for five Coordination questions returned two available items with an explicit shortfall, showed the approved eye diagram, hid the answer initially, and revealed the correct W/X/Y guidance as assisted practice. Resume on the second item and completion of the two-item set were verified. A deterministic 0.057 response produced 2/2 in chat; refreshing exposed a missing JSON feedback write in the private set. Explicit SQLAlchemy JSON dirty tracking fixes it; semantic and deterministic reload regressions pass (15 related tests). Production retry/reload/completion and the formerly manual-only item subsequently passed on `6be2a8d`.

## Responsiveness and access

Initial production testing identified repeated validation of the entire released bank and an obsolete single-card refresh. The final update filters initial eligibility by requested topics, revalidates only the frozen set's needed release IDs, and skips the legacy refresh when a set is present. Each request still checks current permissions and source availability; no cross-request authorisation cache was introduced.

## Next Biology delivery

All 44 supplied Biology paper sets are already imported. Extraction completion does not mean final source review/release is complete. The next recommended batch is the final review/release of **June 2025 standard 1B**, then **2B**, followed by **1BR**. Latest inventory before this delivery: 1B has 10 questions/46 subparts with image checks complete for 3/10 questions; 2B has 6/30 with 0/6; 1BR has 10/49 with 0/10. These are workflow counts, not claims of zero extraction accuracy. June 2025 2BR is the accepted formative pilot. Further paper analysis belongs to the existing Biology intake roadmap; do not reimport or blanket-release all 44 papers.

## Rollback

Use the previous reviewed runtime and normal service acceptance procedure if required. Keep additive table `tutor_question_sets` and its private history; do not run its destructive downgrade or remove Student records to roll back application code. Guarded release withdrawal is available for individual content issues. Existing formal-assessment safeguards and older frozen attempts remain unchanged.


## Final Student and release acceptance

The authorised pilot Student's normal production session verified second-question reload/resume and completed the two-item Coordination set with assisted/skipped responses correctly separated from scores. Q3(b) was answered with 0.057: the retained validated recognizer awarded 2/2 without a paid production call. After the JSON fix, Retry feedback persisted the result; full reload retained the score, saved answer, better-answer panel and completion state. The set completed with a 2/2 summary. Formerly manual-only Q1(d) was selected with its approved context and visuals, then the QA set was stopped. No active QA set remains. No certified mastery was inferred from these set results. Private visual evidence: `tmp/formative-production/student-feedback.jpg`.

The final runtime passed all schema/health/HTTPS/routing/service acceptance checks. Evidence: `/data/akuru/release-evidence/deployed-6be2a8d0ccbeeb9bd61824a432517df4caf454b5-20261118T175328Z.txt`. Full final suite: 631 backend passed, 1 skipped; final persistence regressions: 15 passed. Source review data remained unchanged; 31 live releases and all four complete paper-workflow stages were verified through authenticated APIs.

The owner explicitly approved removal of only rollout snapshots `20261118T172331Z` and `20261118T172927Z` (six encrypted archive/manifest files). Pre-change/latest snapshots and earlier backups were retained. The final deployment made a fresh encrypted backup; no retention setting or security gate was weakened. Follow-on source work is recorded in the existing Biology intake roadmap, starting with the recommended June 2025 standard 1B final review/release.


## Live production generated-question cycle

With separate explicit approval of up to US$0.25 from **AKURU-backend**, The authorised pilot Student session requested one new Coordination question. Generation and its independent check succeeded, the question was labelled AKURU-generated and its answer was initially hidden. A partial answer identifying ear receptors and impulses reaching the brain received an indicative 2/5, two correct points, three missing points, a complete receptor–CNS–effector answer and a specific uncertainty note. Reload retained feedback; completion produced a 2/5 summary and revision suggestions. No active QA set remains. Private screenshot: `tmp/formative-production/student-generated-feedback.jpg`.

Read-only operational invocation records confirmed exactly three completed `gpt-6.1-sol` calls with one attempt each: 3,581 input tokens and 1,272 output tokens. At the recorded evaluation rates, estimated cost is US$0.019882; the conservative recorded-usage bound is US$0.026007, below US$0.25. This production spend is separate from the six-call US$0.036932 Evaluation-project estimate. Student requests fell from 70 to 67 and remaining text tokens from 20,832 to 15,979; no allowance or quota configuration was changed. Private usage/budget evidence is retained in `tmp/formative-production/backend-usage-final.json` and `backend-budget.json`.

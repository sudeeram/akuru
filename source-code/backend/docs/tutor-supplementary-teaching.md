# Bounded supplementary text teaching

Implemented locally: 2026-11-02. Live scenario evaluation passed; production activation remains pending.

## Behaviour and source honesty

The text Tutor first searches the selected Student's authorized published topic. Exact short concepts now have a lexical fallback, rather than requiring two overlapping terms. Curated morphological aliases, NFKC scientific-notation normalization and one bounded previous Student question support short follow-ups. Explicit new questions override that context. Chapter-question-only material is not factual answer evidence. Results are deduplicated before the existing bounded source limit.

The supplementary path uses a separate structured schema and prompt 2.0.0. `groundedContent` must have real authorized citation references. `additionalContent` has no citations and is labelled **Additional explanation**, explicitly not an official Pearson answer. Mixed answers keep both sections separate. Clarification, uncertainty and outside-scope responses have neither teaching sections nor citations. Existing transcripts without these fields remain readable without being relabelled.

Scope is anchored to the selected subject/topic and the learner's current grade. Related concepts require the reviewed policy in `app/services/tutor_teaching.py`; initial aliases cover States of Matter. Other topics retain grounded explanations; broadening supplementary concepts requires a policy review and evaluation. This is not unrestricted general chat. Known privacy/injection and advanced/out-of-scope requests are redirected before retrieval/provider calls. These checks complement, rather than replace, the model safety prompt and existing safety-event service. They do not constitute a complete scientific verifier.

A source contradiction should be identified as uncertain and referred for review. The Tutor must not rewrite published sources, invent official pages/examiner guidance, infer learner mistakes or treat a model confidence percentage as measured accuracy. Additional explanations can still contain model errors; semantic evaluation and the controlled pilot remain necessary.

## Boundaries and persistence

Past-paper chat routing still runs first and retains its separately released subparts and assessment restrictions. No changes to marking, mock generation, formal-assessment blocking, automatic mastery or study-plan updates are authorized by this feature.

The existing provider/account router, model pin, quota reservation and audited invocation/token records are reused. A durable per-session request claim prevents concurrent retries making duplicate paid calls. The existing `tutor_paper_chat_requests` table is reused as the chat operation registry despite its historical name; no migration is required. A claim without a completed response fails closed with a recoverable 409 rather than risking another charge. Operators should investigate interrupted requests; the UI can send a new request after the Student reloads.

Existing TutorTurn JSON stores answer basis, section content and retrieval provenance: query strategy, policy version, current topic content-version ID/number, retrieval outcome, available/used citation references and related concepts. Provider/model/prompt metadata remain on the turn and invocation. No new credentials or unbounded prompt logs are introduced. Student transcripts and Admin support views retain labels; any retained textual summary includes the canonical labelled reply.

## Enablement and rollback

`AKURU_TUTOR_SUPPLEMENTARY_ENABLED` defaults to false. The original textbook-only prompt remains 1.0.2. To activate the existing one-Student pilot, retain every existing pilot field and add `supplementary_prompt_version: "2.0.0"` and `supplementary_evidence_sha256` identifying the operator-reviewed evaluation record, then enable the flag. Existing Student, topic, content version, model, expiry, formal-assessment and source gates remain mandatory. Do not invent a general-release evaluation. A non-pilot release must pass its separately registered `tutor_supplementary` workflow gate.

Rollback only this feature by setting the supplementary flag false and restarting API/worker. Grounded text teaching then returns to prompt 1.0.2 while the existing pilot remains scoped. Retain transcripts, usage and evaluation evidence. Do not remove pilot restrictions or reset Student data.

Use the standard encrypted-backup/reviewed-release deployment and acceptance scripts. Secure environment changes must preserve root:akuru 0640 ownership and every unrelated value. The Evaluation key stays separate from production AKURU-backend and OpenClaw.

## Verification

Deterministic tests: `tests/test_tutor_teaching.py`, existing retrieval, pilot, privacy, session, assessment and safety regressions; frontend `tests/tutor-chat.test.mjs` checks labels, safe formatting and legacy compatibility. The full Tutor fixture supports `/?supplementary` and `/mobile?supplementary` after a frontend build. It is synthetic, loopback-only and makes no paid calls.

Predeclared semantic cases: `evaluations/tutor/supplementary-teaching-cases.json`. Use `scripts/evaluate_prepared_tutor.py --supplementary` with the separately authorized Evaluation budget. Without `--live`, it runs a zero-cost schema/persistence pipeline check, not a teaching-quality evaluation. The prepared screenshot candidate is a local fixture, not the current production v2.2 source; production must also be checked with the normal authorized Student session. Preserve the original cumulative evaluation ledger and retain any new phase's budget record separately.

Baseline production audit on 2026-11-02 found a detailed evaporation explanation on PDF page 6 among 54 active Topic 1 version-2 chunks. The failure of “What is evaporation?” was a single-term retrieval threshold issue, not missing textbook content. Five chunks mention evaporation, with a chapter-exercise tail excluded from factual ranking. The nine-case local live evaluation passed for the controlled pilot; production acceptance remains pending. See `evaluations/tutor/supplementary-teaching-20261102.json`.

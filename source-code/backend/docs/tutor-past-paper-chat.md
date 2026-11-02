# Tutor past-paper chat

Implemented: 2026-11-02. This is separate from related-concept supplementary teaching and from full mock exams.

## Source release and schema

Production review workspaces are not automatically Student assessment banks. An Admin uses **Release approved subparts for Tutor chat** in the paper review workspace to attest that an individual subpart is self-contained with its shared stem and visuals. A release requires approved question/subpart content, supported published topic mappings, exact paper/scheme blocks, reviewed visuals and explicit automatic marking readiness (or manual drawing readiness). Dependent subparts with detected references to prior answers are blocked; the Admin must not attest that an unresolved dependency is self-contained.

Migration `0018_tutor_past_paper_chat` creates `tutor_paper_releases` and durable `tutor_paper_chat_requests` idempotency claims. An interrupted claimed request fails closed rather than repeating mutations or charging for marking again; the Student can reopen saved practice and use a new explicit action. Each immutable JSON snapshot records the reviewed subpart, shared context, source document versions, exact evidence, marking rules, topic references, examiner guidance and approved answer visuals. It records the Admin, review revision and fingerprint. Only the enabled flag is mutable. Re-review/source changes invalidate selection until re-released. Withdrawal blocks current access without deleting historical attempt records. Confidence-only review changes currently invalidate releases conservatively too.

`assessment_questions` has nullable `source_question_version_id` and nullable `tutor_paper_release_id`, with an XOR constraint requiring exactly one source. Existing full-paper assessment publication remains unchanged. Tutor chat creates normal practice Assessments, immutable AssessmentQuestions, curriculum snapshots and TutorPractice rows. It reuses answer storage, drawing uploads, assessment marking, assistance events and Student mastery. Do not downgrade migration 0018 after release-backed attempts exist; disable the feature and retain the compatible schema during code rollback.

## Routing, authorization and costs

`tutor_past_papers.handle` runs after normal session/Tutor authorization and request replay, before textbook retrieval. Common selection, question identity, hint, answer, reveal, stop and mock requests use deterministic routing. Ambiguity is clarified; no model invents an official question or rubric. Session/subject/year/component filters must match. Selection avoids already-seen items when possible and the previous item where alternatives exist. Current scope is one self-contained subpart at a time, with a 60-minute practice window.

`AKURU_TUTOR_PAST_PAPER_CHAT_ENABLED` defaults false. `AKURU_TUTOR_PAST_PAPER_CHAT_STUDENT_IDS` is a JSON array of authorized Student UUIDs; an empty array denies everyone. These settings do not override normal Tutor audience/topic/model/expiry gates. In the text pilot, a Student can practise separately released exam items in the same subject if all their mapped topics are covered and published, while the ordinary text-teaching anchor stays unchanged. This does not enable arbitrary Tutor topics, voice or general guided-practice tools.

All routes require normal cookie authentication; changes require Student/Admin role and CSRF as applicable. Server checks ownership, enrolment, cumulative Grade/Term coverage, published topic content, live release fingerprint, private assets, feature/audience switches and formal-assessment blocking. Assessment asset/evaluate endpoints also check this authorization; knowing an assessment or asset UUID is insufficient. API rate limits remain in place. Missing/mismatched sources yield an availability explanation rather than a false textbook OCR error.

Selection, question lookup, hints and exact approved-answer reveal make **zero model calls**. Scored text submissions reuse the authoritative two-pass assessment service only after its automatic-feedback release gate matches the configured model/prompt. Both passes use the existing account router, pilot model pin, per-child Tutor quotas and AI invocation records. The normal family assessment usage accounting also remains. If the evaluation gate or provider is unavailable, the answer remains saved, no score is fabricated, and approved marking guidance is still available. Manual drawings retain manual review and approved answer visuals; no unvalidated visual score is published.

## Answer visibility and persistence

Pre-answer payloads omit marking guidance, alternatives, scheme/report page links and answer visuals. “Show approved answer” reveals exact reviewed marking guidance, accepted alternatives and available reviewed examiner advice, not a model-authored official answer. Approved AI-generated answer visuals retain their origin label. Before submission, reveal records `worked_answer`, ends the active question and creates no fake Student response, score or mastery. Viewing feedback after a real submission does not retrospectively mark the original attempt as assisted. Hints retain their existing assistance weighting.

Transcripts include the structured `pastPaper` state, intent/tool result and release provenance through the attempt. GET current practice re-authorizes access on reload. Question/scheme/report page links return private image bytes, never raw JSON. A direct current-source link follows the latest item in that session; use completed assessment snapshots for retained historical evidence, not the current-item link as a permanent bookmark.

## API additions

- Admin GET `/api/v1/admin/official-paper-reviews/{paper_id}/chat-releases`.
- Admin POST `/api/v1/admin/official-paper-reviews/{paper_id}/questions/{number}/chat-release`: `partLabel`, current `revision`, `confirmSelfContained`, `enabled`. `enabled=false` withdraws releases for that subpart.
- Student GET `/api/v1/tutoring/sessions/{session_ref}/past-paper`.
- Student GET `/api/v1/tutoring/sessions/{session_ref}/past-paper/assets/{asset_id}`.
- Existing Student POST `agent-turns` accepts ordinary chat text and returns optional `pastPaper`; no new unauthenticated endpoint.

## Operations and verification

Release only approved source items; never update review approval/coverage to enlarge the pool. Keep production flags disabled during deployment/migration, release reviewed items through the authenticated Admin API/UI, then enable only the agreed audience. Record release IDs, source fingerprints, tests and zero-cost live selection/reveal checks. Development uses deterministic providers and transactional local database fixtures. New paid evaluation needs a separately agreed ceiling and the Evaluation key; do not reset its cumulative ledger.

Disable the past-paper flag or clear its Student list to roll back this feature while retaining normal textbook teaching. Keep the protected server environment root:akuru 0640, back up before deployment and run normal release acceptance. Do not remove the text-pilot restriction or assessment quality gate to make a demonstration pass.

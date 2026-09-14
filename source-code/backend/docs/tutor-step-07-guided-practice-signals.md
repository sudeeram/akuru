# Tutor Step 7 — Guided practice and bounded signals

Tutor guided practice reuses the assessment domain rather than introducing Tutor-owned marking. `POST /api/v1/tutoring/sessions/{sessionRef}/practice` filters the existing covered, published, confirmed question pool to the session's active unit and uses its deterministic selector to create one `practice` assessment. `tutor_practices` retains the exact session, Student, subject, unit, assessment and question relationship.

Only one active question exists per tutor session. Switching profiles retains it. The unit-switch service rejects a move while the question is active, preventing a unit/question mismatch. Starting after submission creates another authoritative practice assessment.

The hint endpoint delegates to `assessments.record_hint`, which verifies an active practice assessment, returns staged hints and writes idempotent `assessment_interactions`. The answer endpoint delegates to `assessments.save_answer`. Submission delegates to `assessments.submit` and the existing two-pass AKURU assessment service. The Tutor response exposes marking decisions, learner evidence, improvements and explanations only when the latest result is `published`; `needs_review` details remain unavailable until the review workflow publishes them. Subsequent structured Tutor turns receive that authoritative result as a server-controlled tool result.

Validated Step 6 signal proposals are copied to append-only `tutor_signals` after the assistant turn is stored. Every row records Student, session, turn, active unit, category, observation, evidence references, confidence, provider, model, prompt and prompt version. There are no update or delete APIs. Student and linked Parent reads return a bounded presentation without internal IDs or provider/model details. These observations are advisory: mastery, deterministic next-unit ranking and study-plan generation have no dependency on `tutor_signals`.

Every practice, text Tutor and voice-transcript endpoint calls the shared tutor access guard. A live mock or official paper therefore blocks all three throughout the formal attempt.

# Formative topic practice and generated questions

Implemented: 18 November 2026. Pilot: Biology June 2025 2BR.

## Product policy

Content eligibility is independent of certified scoring. `tutor_past_papers.validate_release` retains source version/approval, discrepancy, exact evidence, curriculum, visual and independent-answerability checks, but does not require `assessmentReadiness=automatic` or a deterministic certificate. The scoped `_validate_question(..., formative=True)` bypasses scoring-certification checks only; ordinary editing/formal workflows retain their existing behaviour. Workflow step 3 no longer includes a scoring-readiness gate. Explicit release/withdrawal and model/audience access remain enforced.

The old `assessmentReadiness` values and ten pilot certificates are preserved as historical/optional implementation metadata. The deterministic engine hash files are unchanged. No migration fabricates “all rules checked” or rewrites human approval, extraction confidence or Student results. Formal exam publication remains separate; no claim of official grading is introduced.

## Storage and routes

Migration `0023_tutor_question_sets` adds `tutor_question_sets`. Each row belongs to an authenticated Student and Tutor session, with a unique start request and at most one active set per session. It stores requested count, source kind, topic references, position, frozen items, private rubric/answers/feedback, source/model provenance and a durable provider-operation guard. Existing assessment history is untouched.

- `POST /api/v1/tutoring/sessions/{session_ref}/agent-turns`: normal cookie/CSRF-protected Student chat mutations. `tutor_question_sets.handle` runs after capability/discovery routes and before the old single-item adapter and textbook generation.
- `GET /api/v1/tutoring/sessions/{session_ref}/question-set`: authenticated Student-owned current/latest set, redacted before submission/reveal.
- `GET /api/v1/tutoring/sessions/{session_ref}/question-set/assets/{asset_id}`: current question assets only; answer assets require submission/reveal/skip. No raw document or arbitrary asset access. Private/no-store responses, safe missing-file errors.

All retrieval/mutations recheck enrolment, covered published topics, live released items, active session and the formal-assessment help block. Generated sets also bind published topic versions and example release IDs. Withdrawn/changed sources fail closed; frozen history does not become perpetual source permission.

## Selection and lifecycle

The bounded parser accepts 1–20 items, named topics/codes and unit/module groups; default count is one. Subject chat may span accessible topics, while Topic chat stays in its active topic. Unknown or ambiguous explicit topics require clarification. Original selection deduplicates current releases, filters exact paper identity when supplied and all mapped topics, shuffles, then prefers releases not previously used by that Student. Short inventory is stated explicitly.

A set persists selected IDs/snapshots. Answer, reveal, skip, next, stop, retry and reload do not rerandomise it. Only answer/reveal/skip completion permits advancement; hints mark assistance but do not reveal guidance or prevent later submission. Completed/assisted/skipped answers cannot be replaced. Saved answers survive provider failure and retry uses the same answer. No question-set result updates certified mastery or another Student's profile.

The normal owned-session lock is retained until the set and processing guard commit together. Provider calls may commit their own usage, so a durable `processing_key` blocks concurrent mutations. Request claims and saved Tutor exchanges prevent ordinary retries from invoking twice. A crashed guard is recoverable after a conservative 30-minute window; an interrupted same request never silently replays paid inference. New explicit retries may incur another call. The guard is cleared only after saving the exchange. Old private set data is included in explicit Admin transcript-retention cleanup, respecting its recorded latest activity.

## Generated questions

Generation is lazy: one candidate per item, not an entire 20-item batch. Bounded published textbook chunks and up to three relevant approved paper/scheme examples guide original command words, demand and answer depth. Source text is untrusted input, not instructions. Structured output includes prompt, marks (1–6), unique one-mark criteria, suggested answer, authorised topic references and requested difficulty. No generated images or tasks needing missing visuals are served.

A second model call checks scientific correctness, solvability/data, rubric consistency, grounding and original wording. Structural validation and the check must pass before the item is stored/served. Duplicate exact prompts are rejected. These checks reduce defects; they do not prove perfect science or Pearson equivalence. Failed candidates remain hidden and allow an explicit retry. Suggested rubrics are model-generated, not official scheme points. Student payloads hide all answers until submission/reveal. Generated items remain private and never create official bank/source-analysis rows.

## Feedback and existing single-item compatibility

`tutor_question_sets._feedback` makes one accounted structured semantic-feedback call, returning exact criterion matches, correct points, mistakes, omissions, a better answer, explanation and uncertainty. The server supplies official codes/criteria and applies the shared `marking_rules` allocator, including any-N caps, bands, dependencies and combined-response rules. Awarded matches need exact Student evidence. Invalid output has no fabricated score; an unsupported allocation yields guidance without a total.

Existing valid deterministic rules are optionally verified and executed first. Supported recognition returns source-bound feedback without paid inference; unsupported grammar falls through to indicative semantic feedback. Invalid/missing certificates do not prevent learning and are not upgraded into certificates. Drawing interpretation unsupported by this text channel yields explicit guidance without a score, not a human-grading queue.

The old one-item adapter marks newly created practice rubrics `formativeFeedback=True` and uses `evaluate_legacy_practice` to persist normal `AssessmentResult` records with an indicative flag. Existing frozen attempts keep their prior evaluator; formal assessment marking code/engine hash is unchanged. The compatibility adapter must not wrap the existing accounted generator in a second quota invocation. Question-set feedback stays in private set/turn records rather than inserting official question-bank entries or certified mastery results.

All paid calls reuse Tutor invocation/account routing, pinned-model policy and child usage accounting. Generated provenance includes generation/check models and response IDs; feedback retains its model/response ID. No client IDs, model instructions or imported expected decisions grant source access.

## Frontend and operations

`TutorQuestionSetCard` displays progress, separate question/answer entry, reviewed visuals, saved response, indicative score, correct/missing/mistaken points, improved answer, explanation and expandable marking guidance. Tutor room loads current set state on reload. Existing single cards remain supported. Certified-scoring controls are optional/collapsed rather than blockers for formative release.

Regenerate OpenAPI and TypeScript contracts after schema changes. Deploy the additive migration through the reviewed backup/release workflow. Reconcile only the authorised pilot paper through authenticated preview/readiness and release APIs; preserve explicit withdrawals and unrelated papers. Rollback code to the prior release if necessary and leave the additive table intact; do not drop Student practice history to undo a deployment.

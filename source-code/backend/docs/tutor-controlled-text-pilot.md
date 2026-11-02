# Controlled one-student text tutoring pilot

This is a temporary production pilot, not approval of a general Student release. The full database-backed Tutor release gates remain required in production. No passing corpus/run is fabricated for a single-topic trial.

`AKURU_TUTOR_TEXT_PILOT` is an optional JSON runtime setting, stored in the protected server environment. When present, it replaces the Tutor audience with exactly one student and one published topic. It permits only text, the verified learner-context service, approved source search/opening and published visuals. Voice, assessed practice and next-topic recommendations remain unavailable. Existing enrolment, cumulative coverage, session ownership, CSRF, private asset authorization, quotas, transcript/safety logging and formal-assessment blocking still apply.

Required fields: `student_id`, `subject_id`, `topic_id`, `topic_content_version_id`, `model`, `prompt_version`, `evidence_sha256`, `expires_at` (timezone required). UUIDs are internal server configuration, not displayed to students. The evidence hash identifies the operator-reviewed pilot record under `/data/akuru/release-evidence`. Set a short expiry (initial pilot: fourteen days); expired pilots fail closed. A superseded content version closes topic access until revalidated. Requests are model/prompt pinned, and the account router cannot fail over to a different model for pilot requests. No new migration is required.

Enable `AKURU_TUTOR_TEXT_ENABLED=true`, `AKURU_TUTOR_TOOLS_ENABLED=true`, `AKURU_TUTOR_VOICE_ENABLED=false`, and leave `AKURU_TUTOR_RELEASE_GATES_REQUIRED=true`. Configure only the AKURU-backend project credential for its existing account alias; the Evaluation/OpenClaw keys must not be copied here. Preserve the protected environment's root:akuru 0640 ownership/permissions and restart API/worker after validation. An enabled database `AIProviderAccount` with the alias, unique priority and validated model is also required.

Before activation, take the usual encrypted backup, run regressions, verify the published topic's source/coverage and record the evidence hash. After activation, test authenticated Student UI/API teaching, citations/figures, a denied second student, off-topic/voice/practice denial and private endpoints without authentication. Record real provider/token usage. Production student conversations charge AKURU-backend; the Evaluation US$2 ledger does not cap this account.

Initial deployment uses the already Admin-reviewed/published Topic 1 content. The newly prepared screenshot package remains a separate local draft; owner acceptance of four clarification notes does not imply whole-document or visual approval, and deployment must not silently replace the current primary source.

Rollback: set both text and tools flags false and restart API/worker. Keep the pilot setting while disabling to avoid accidentally falling back to any broad release. Retain transcripts/audit/evidence and API usage records; do not reset passwords or delete learning data. Restore the previous reviewed code release only if required; no schema migration is introduced by this pilot.

For a wider release, complete the full evaluation corpus/staging/audience progression and remove the temporary pilot configuration only after the broader release has been separately authorized.

## Tutor chat presentation

The Student conversation uses `frontend/features/tutor-chat-elements.tsx` and `frontend/app/tutor-chat.css`. The layout is inspired by the PreSkool chat reference, implemented with AKURU components/assets without third-party chat scripts or remote avatars. Direct, unoptimized static images avoid the unsupported optimizer path; missing images have a fallback. Textbook evidence uses a native, keyboard-accessible disclosure, keyed per reply and closed by default.

The small answer formatter renders text-only paragraphs, bold spans, inline code and ordered/unordered lists as React nodes. It does not interpret raw HTML, Markdown links or model-created URLs. Formula Unicode and ordinary Student input are preserved. No backend contract, source access, AI prompt or model change is involved.

Local visual fixture: `node source-code/frontend/tests/tutor-chat-preview.mjs` from the repository root after a frontend build. It prints a loopback-only URL, mocks the API with synthetic conversations and makes no paid calls. `/mobile?missing-avatar` renders a 390px frame and tests the missing-avatar path. Stop the fixture after testing. Unit checks are in `frontend/tests/tutor-chat.test.mjs`.

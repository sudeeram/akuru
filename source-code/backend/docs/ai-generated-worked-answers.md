# AI-generated worked answers

Created: 2026-10-31

## Scope and trust

The first renderer supports a verified two-dimensional data table, plotted crosses, anomaly circles and ordinary least-squares straight lines. It rejects arbitrary generated code and unsupported diagram types. The AI proposes a declarative `GraphSolution`; trusted PyMuPDF code renders PNGs. No image-generation API or new plotting dependency is needed.

The answer always displays **AI-generated worked answer — not an official Pearson answer**, including a permanent label inside each PNG. Official marking criteria, caps, tolerances and follow-through remain authoritative. Displaying a worked example does not enable automatic marking of drawings.

## Data and workflow

Migration `0016_generated_worked_answers` adds `generated_worked_answers` and the `worked_answer` assessment-interaction kind. It leaves existing reviews and attempts intact. A generated draft stores its source manifest/hash, verified graph input, source question revision, provider/model, prompt and renderer versions, usage, structured solution, review notes/audit and attached asset identities.

1. Admin saves the ordinary question review and verifies source axes, table values and selected subparts.
2. `POST /api/v1/admin/official-paper-reviews/{paper}/questions/{number}/worked-answers` accepts the expected question revision, graph input and an explicit verification note. A matching successful draft is reused unless replacement is requested. One pending generation per question is enforced under a question lock.
3. The existing document worker polls durable queued drafts. The existing OpenAI account router supplies structured generation with its configured timeout, output cap and bounded retries. An interrupted processing job fails after 30 minutes rather than silently charging for another call.
4. Source-value equality, axes, ranges, point indices, anomalous-point exclusion from fitting, renderability and selected subparts are checked. Scientific correctness still requires review. Failure produces a safe error code, never published content.
5. Admin previews each generated step, edits explanatory text/fit instructions when necessary, and approves or rejects with a review note and expected draft revision. Editing removes approval. Verified source coordinates cannot be edited in a solution; create a new draft to correct them.
6. A separate attach operation checks the current question revision, approved draft and source fingerprint. It stores immutable private PNG assets associated with the exact scheme version, explicitly marked `generatedAnswer`, not `reviewCrop`. Each part receives a generated-origin `AnswerVisual` with explanation, graph-data equivalent and limitations. Existing official answer crops are retained. An already-approved question must first be reopened.
7. Normal question and whole-paper review/release gates still apply. Attaching an answer neither approves the question nor releases the paper. Existing release and assessment snapshots freeze the private answer associations.

`GET .../worked-answers` lists drafts and computes stale status from current relevant source content. Question statuses, coverage notes and answer attachment changes alone do not stale a solution; wording, criteria, scoring rules, source evidence and document versions do. A new release rejects stale, altered or cross-question generated associations. Existing attempts continue to access their frozen approved answer assets even if a later draft changes.

Admin preview is private/no-store. Mutations require an authenticated Admin and CSRF token, record audit events, and reject conflicting revisions. Never put generated assets in question illustrations, public storage or unauthenticated download endpoints.

## Student reveal and mastery

Released generated answers appear beside official model answers in feedback, with a separate label and expandable steps. Graphs use the existing bounded image/zoom viewer. Source values and explanations provide a text alternative.

For an active practice assessment only, `POST /api/v1/assessments/{assessment}/questions/{question}/worked-answer` verifies Student ownership and the deadline, then records one idempotent `worked_answer` interaction and returns approved generated answers from the frozen rubric. The question is excluded from independent mastery evidence. Both ordinary practice and tutor guided-practice screens expose this action only when a released generated answer exists.

Mock and official-paper attempts reject this help endpoint. Direct answer-image requests remain blocked before submission. A previous practice reveal cannot bypass the formal-mode check. Existing AKURU feedback policy releases rubric/model answers after a submitted or expired-and-submitted assessment; an expired unsubmitted attempt is insufficient. There is currently no additional delayed-feedback-release setting: any future change must gate both rubric responses and answer-image retrieval together.

## Configuration and operations

`AKURU_WORKED_ANSWERS_ENABLED=false` is the safe default. It gates new generation and worker processing; Admin review of existing drafts and previously frozen Student feedback remain available. The capabilities endpoint reports the flag and whether an enabled, healthy account has a configured server credential. No keys are returned.

To enable later:

1. Configure `AKURU_OPENAI_ACCOUNT_KEYS` in the protected server environment and add/enable the matching credential alias, priority and API model through Admin OpenAI accounts. The feature uses this router, not a Codex login or the standalone legacy key setting.
2. Set `AKURU_WORKED_ANSWERS_ENABLED=true`; restart both `akuru-api` and `akuru-worker`.
3. Verify capabilities, generate one draft, inspect source checks and scientific content, approve, attach and follow the ordinary review/release flow.

Generate once and reuse the approved result across Students. Provider usage is recorded on the generation provenance and existing provider-attempt records. There is no per-Student generation cost for viewing a stored answer.

Deployment uses the existing encrypted database/document backup and reviewed-release scripts. To stop new generation, disable the flag and restart API/worker. Prefer a forward fix over a schema downgrade after content has been used. The tested migration downgrade preserves assistance evidence as ordinary hint records, but does not preserve generated-draft records; restore a reviewed backup if rollback must retain those drafts. Never remove existing private answer files while historical attempts reference them.

## Acceptance evidence

Tests cover source equality and geometry; numeric least-squares fitting; PNG output; Admin/CSRF/revision gates; duplicate jobs and reuse; approval/attachment; stale source rejection; practice reveal, formal blocking, direct URLs and family isolation. The migration is tested through upgrade/check/downgrade/upgrade/check on a disposable database. Synthetic browser fixtures exercise desktop/mobile UI without creating real Students or spending tokens.

The reviewed 1C source assessment is recorded in `ai-generated-worked-answers-1c-audit.md`. Live production AI generation remains deferred until credentials are configured by the owner; synthetic results must not be presented as a live provider test.


## Production release record — 2026-10-31

Release `39d4ae7` was deployed with migration 0016, after encrypted backup. Production schema check, API/worker/web health, authenticated Admin desktop/mobile review, unauthenticated API rejection and synthetic Admin/Student browser acceptance passed. The backend suite passed 226 tests (1 skipped) and the frontend suite passed 103 tests.

The feature remains in its safe generation-disabled state because the owner deferred OpenAI configuration. There are no generated production answers, and no current paper review was modified. Enabling credentials and the flag later does not publish any answer: generation, scientific review, attachment and normal release gates still apply.

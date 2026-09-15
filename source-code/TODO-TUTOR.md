# AKURU Tutor Agent implementation roadmap

This is the ordered delivery backlog for the configurable, unit-aware text and voice Tutor Agent. The authoritative product and architecture decisions are in [docs/tutor-agent-plan.md](docs/tutor-agent-plan.md). Existing curriculum, assessment, mastery, media, security and operational rules remain in [docs/architecture.md](docs/architecture.md) and [TODO.md](TODO.md).

Complete the steps in order unless an item explicitly says it can run in parallel. Check a box only after the step's acceptance criteria and tests pass.

Status: `[ ]` not started, `[~]` in progress, `[x]` complete, `[!]` blocked with the reason recorded beside it.

## Tutor Step 0 — Protect existing learning and assessment boundaries

**Goal:** Establish a verified baseline before adding conversational access to student data and content.

- [x] Record the current full frontend, backend and PostgreSQL integration verification result.
- [x] Catalogue the existing enrolment, curriculum, RAG, mastery, study-planner, media, OpenAI routing, quota and formal-assessment services the tutor will call.
- [x] Define practice versus formal-assessment states in one reusable backend policy.
- [x] Add a server-side guard that denies tutor hints and voice in every formal-assessment state.
- [x] Add feature flags for text tutor, voice tutor and tutor tools, defaulting to disabled in production.
- [x] Document the new data flows and threat boundaries without placing provider credentials in the browser.

**Completed:** `assessment_access.py` now owns practice/formal classification, fails closed for unknown modes, protects existing hints and provides the mandatory guard for future text, voice and tool endpoints. The authenticated Student capability endpoint combines that guard with independent backend-only release flags. The service catalogue, provider boundary, microphone-header boundary and configuration are documented in [Tutor Step 0 foundation](backend/docs/tutor-step-00-foundation.md).

**Validation:** The pre-change baseline passed with 23 frontend and 79 backend tests. The completed step passes contract generation/checking, 23 frontend and 84 backend tests, TypeScript, lint and the production frontend build. No dependency or database migration was added.

**Done when:** Existing checks pass, formal assessments fail closed against tutor access, and production can enable or disable text and voice independently.

## Tutor Step 1 — Add tutor profiles and curated avatars

**Goal:** Let each student create multiple safe, reusable tutor identities from controlled options.

- [x] Add `tutor_profiles`, immutable `tutor_profile_versions`, `tutor_avatars` and `tutor_voice_presets` tables.
- [x] Support masculine, feminine and neutral presentation.
- [x] Support controlled tone, friendliness, enthusiasm, speed, communication character, explanation depth and teaching style values.
- [x] Use **Childlike**, **Balanced** and **Authoritative** communication-character labels, with Balanced as the default unless configured otherwise.
- [x] Seed child-safe fictional superhuman avatar presets based on the AKURU BOT visual family.
- [x] Exclude text-prompt avatar generation, real-person imitation, voice cloning and per-profile approval workflows.
- [x] Let students create multiple tutors, freely rename owned tutors and select any Admin-published preset.
- [x] Validate names for length and unsuitable content without exposing internal UUIDs.
- [x] Add Student profile management, Parent read-only visibility and Admin preset/voice management screens.
- [x] Add family-isolation, role-authorization, enum-validation and immutable-version tests.

**Completed:** Students can create, rename, edit and remove multiple profiles from controlled persona values and five curated AKURU BOT hero assets. Every edit creates an immutable complete version behind a stable public reference. Parents have read-only access to linked children; Admin manages preset availability and order without receiving provider voice references or permission to impersonate a Student. Disabled presets remain renderable for historical profiles but cannot be newly selected. Backend and frontend behavior is documented in [Tutor Step 1 backend](backend/docs/tutor-step-01-profiles.md) and [Tutor Step 1 frontend](frontend/docs/tutor-step-01-profiles.md).

**Validation:** Migration `a31c0f4e8b72` applies cleanly and Alembic reports no drift. `npm run verify` passes with 24 frontend and 85 backend tests, the generated OpenAPI contract, TypeScript, lint and the production frontend build. Tests cover CSRF, role and family isolation, immutable version history, hidden UUID/provider fields, name validation, Admin preset changes and soft deletion.

**Done when:** A student can safely manage multiple tutor profiles from curated values, siblings cannot access one another's profiles, and historical sessions can retain the exact profile version used.

## Tutor Step 2 — Add sessions, transcripts and tutor switching

**Goal:** Preserve one coherent learning conversation when a student changes tutors.

- [x] Add `tutor_sessions`, `tutor_turns`, `tutor_turn_sources` and `tutor_session_profile_events` tables.
- [x] Start each session inside one enrolled subject and one currently eligible unit.
- [x] Allow an explicit move to another eligible unit within the same subject and record the transition.
- [x] Allow switching between the student's tutor profiles without ending the session.
- [x] Generate a compact backend-owned handover summary for the newly selected tutor.
- [x] Preserve the subject, active unit, transcript, authorized citations and current practice state across a switch.
- [x] Store the selected immutable tutor-profile version on every switch event and applicable turn.
- [x] Store text and voice transcripts by default; never store raw audio.
- [x] Add idempotent turn creation and switch requests.
- [x] Build the Student conversation shell, transcript view and in-session tutor switcher.
- [x] Test concurrent switches, retries, session ownership and cross-family isolation.

**Completed:** Students can start a practice-only tutor session in a cumulatively covered unit, retain an ordered text or voice transcript, change tutors, and move between eligible units in the same subject. Every turn and switch points to an immutable tutor-profile version. Profile changes create a compact backend-owned handover while retaining subject, unit, practice state and authorized source relationships. PostgreSQL row locks and request-key uniqueness serialize competing mutations and make retries idempotent. The Student Tutor room and implementation details are documented in [Tutor Step 2 backend](backend/docs/tutor-step-02-sessions.md) and [Tutor Step 2 frontend](frontend/docs/tutor-step-02-sessions.md).

**Validation:** Migration `c14d7a2f9e01` applies cleanly and Alembic reports no drift. `npm run verify` passes with 25 frontend and 86 backend tests, the generated OpenAPI contract, TypeScript, lint and the production frontend build. Tests cover covered-unit eligibility, immutable turn attribution, retained handover context, repeated and competing switches, request retries, ownership isolation and the absence of raw-audio storage.

**Done when:** Switching tutors changes the persona on subsequent turns without losing or leaking learning context, and every retained turn can be traced to the tutor profile used.

## Tutor Step 3 — Build the grounded learner-context service

**Goal:** Give tutors accurate knowledge of a student's demonstrated strengths and weak points.

- [x] Create a read-only learner-context service over mastery, mastery confidence, dimensions, trends, assessed attempts, marking decisions, mistake taxonomy and current study-plan data.
- [x] Restrict context to the authenticated student, active enrolled subject and eligible units.
- [x] Calculate recurring mistake counts with explicit topic, evidence records and time windows.
- [x] Distinguish strong, weak, declining, improving, low-confidence and insufficient-evidence units.
- [x] Return structured evidence for every personalised statement the tutor may make.
- [x] Use cautious phrasing when evidence quantity, variety or recency is insufficient.
- [x] Create pseudonymous provider context with no username, email or unnecessary family data.
- [x] Log learner-context version and evidence references used by each tutor operation.
- [x] Add tests for examples such as five sulphuric-acid mistakes this week and strong Unit 1 Algebra skills.
- [x] Test that siblings, uncovered units and unassessed model claims never enter the context.

**Completed:** The authenticated learner-context operation composes only published assessment results, unit-verified mastery events, dimensions, marking decisions, assessed mistake diagnoses and approved current study-plan items. Deterministic signals distinguish strong, weak, improving, declining, low-confidence and insufficient-evidence states. Each personalised statement names its evidence references and whether cautious wording is required. The provider projection is pseudonymous and omits account and family identity. Immutable operation logs retain the context version, evidence manifest and replayable snapshot. See [Tutor Step 3 learner context](backend/docs/tutor-step-03-learner-context.md).

**Validation:** Migration `df4c92a10b33` applies cleanly and Alembic reports no drift. The release checks pass with 25 frontend and 89 backend tests, the generated OpenAPI contract, TypeScript, lint and the production frontend build. Tests prove five assessed sulphuric-acid mistakes in seven days, a strong Unit 1 Algebra statement backed by two events, cautious handling of stale evidence and an unassessed 10/10 database value, cumulative coverage filtering, sibling isolation, pseudonymisation and idempotent operation replay.

**Done when:** Every statement about the student is reproducible from authorized evidence and the tutor cannot invent a strength, weakness, count or time window.

## Tutor Step 4 — Build deterministic next-unit recommendations

**Goal:** Answer “What should I improve next?” using explainable AKURU evidence.

- [x] Build a deterministic ranking service for covered units using mastery, confidence, trend, recurring assessed mistakes, scheduled assessments and reviewed recommendations.
- [x] Return the recommended unit, reason, evidence and a suitable next activity.
- [x] Keep results inside current enrolment and cumulative Grade + Term coverage.
- [x] Exclude conversational tutor signals from automatic ranking and study-plan changes.
- [x] Let the tutor explain the ranked result conversationally without changing it.
- [x] Require explicit student action before moving the active session to the recommended unit.
- [x] Add no-evidence and no-eligible-unit responses.
- [x] Test repeatability, tie-breaking, progression changes and cross-subject rejection.

**Completed:** Algorithm `next-unit-v1` ranks cumulatively covered units from verified mastery gaps, confidence, trends, assessed recurring mistakes, reviewed recommendations, current study-plan items and published current-term assessment blueprints. Every factor exposes its fixed points, explanation and evidence references. The API returns a suitable activity and a constrained tutor explanation brief. Tutor turns and persona settings are excluded. The Student Tutor room displays the advice and requires a separate **Move to this unit** action. See [Tutor Step 4 backend](backend/docs/tutor-step-04-next-unit.md) and [Tutor Step 4 frontend](frontend/docs/tutor-step-04-next-unit.md).

**Validation:** `npm run verify` passes with 26 frontend and 91 backend tests, the generated OpenAPI contract, TypeScript, lint and the production frontend build. Tests cover fixed factor scoring, stable tie-breaking, repeated results, conversation exclusion, progression changes, cross-subject rejection, no-evidence behavior and confirmation before a session unit changes. No database migration was required.

**Done when:** The same authoritative evidence produces the same recommendation, its reason is visible, and tutor conversation alone cannot alter it.

## Tutor Step 5 — Build exact textbook retrieval and citation

**Goal:** Let tutors teach from the correct approved textbook and reference exact pages.

- [x] Extend approved retrieval for tutor queries using course, subject, textbook edition, unit, publication and student-eligibility filters before vector ranking.
- [x] Return document version, displayed textbook title, edition, PDF page, printed page label, bounding box, passage, confidence and authorized asset reference.
- [x] Resolve printed-page labels separately from physical PDF page indexes.
- [x] Require an exact retrieval result before the tutor mentions a page number.
- [x] Link each citation to an authorized page or crop and preserve existing private-file access checks.
- [x] Let the student ask for a fuller explanation grounded in the cited passage and nearby approved context.
- [x] Return an evidence-insufficient response rather than inventing a page, edition or quotation.
- [x] Add subject fixtures for equations, diagrams, tables and differently numbered front matter.
- [x] Evaluate citation precision, unit isolation and edition correctness.

**Completed:** Tutor source search filters the current Student session to its eligible active unit and exact published iGCSE textbook content/document version before pgvector ranking. Results include separate PDF and printed-page locations, approved block type, bounding box, passage, score and opaque private asset link. Opening a citation or nearby passage repeats authorization and exact-version checks; changing units invalidates the former citation. The Tutor room provides exact source search, page/crop opening and nearby approved context. See [Tutor Step 5 backend](backend/docs/tutor-step-05-exact-retrieval.md) and [Tutor Step 5 frontend](frontend/docs/tutor-step-05-exact-retrieval.md).

**Validation:** `npm run verify` passes with 27 frontend and 92 backend tests, migration drift checking, generated OpenAPI, TypeScript, lint and the production build. Fixtures cover equations, diagrams, tables, Roman-numbered front matter, printed page 101 on PDF page 2, wrong-edition failure, unit isolation, confidence failure and private authorized assets.

**Done when:** A statement such as “refer to page 101” always opens the correct authorized edition and supporting content, and invented or cross-edition page references fail validation.

## Tutor Step 6 — Implement the structured text Tutor Agent

**Goal:** Deliver safe, source-grounded tutoring through the existing ordered OpenAI provider layer.

- [x] Add versioned Tutor API routers, schemas, service and repository boundaries.
- [x] Add versioned prompts for explanation, questions, guided practice, Socratic practice, revision, exam technique and French conversation.
- [x] Define structured output for response content, citations, follow-up choices, tool results and proposed non-authoritative signals.
- [x] Add strictly scoped tools for learner context, next-unit recommendation, approved source search, authorized source opening, mastery summary, study-plan context, guided practice and deterministic media.
- [x] Derive student identity and scope from the authenticated session rather than tool arguments supplied by the model.
- [x] Route complete turns through the ordered OpenAI account router with bounded retries, usage recording and one logical operation ID.
- [x] Treat source documents and student messages as untrusted content that cannot modify system or tool rules.
- [x] Validate every provider response and citation before persisting or returning it.
- [x] Add fake-provider tests for tool authorization, prompt injection, malformed output, failover and insufficient evidence.
- [x] Complete the Student text conversation UI with citations, visual content, error recovery and accessible keyboard interaction.

**Completed:** The versioned structured Tutor endpoint runs seven teaching modes through server-controlled learner, retrieval, recommendation, practice-availability and approved-media tools. Authenticated session scope fixes the Student, subject and unit. Untrusted messages and evidence stay outside system instructions; structured output, citations and signal evidence are validated before an idempotent exchange is stored with operation/provider/model/prompt provenance. Missing subject evidence activates a deterministic evidence gate. The Tutor room now renders grounded citations, approved visuals, follow-up choices, mode selection and retry-safe keyboard submission. See [Tutor Step 6 backend](backend/docs/tutor-step-06-structured-text-agent.md) and [Tutor Step 6 frontend](frontend/docs/tutor-step-06-structured-text-agent.md).

**Validation:** `npm run verify` passes with 28 frontend and 94 backend tests, migration drift checking, generated OpenAPI, TypeScript, lint and the production build. Coverage includes all versioned modes, malformed schema rejection, prompt-injection containment, authenticated scope, invented citation rejection, idempotent replay, provider provenance/usage, existing ordered-account failover tests and evidence-insufficient behavior.

**Done when:** A student can hold a grounded text conversation, receive personalised but evidence-backed help, and cannot use the tutor to broaden curriculum or bypass authorization.

## Tutor Step 7 — Connect guided practice and bounded tutor signals

**Goal:** Let a tutor teach through practice without becoming an unreviewed assessment authority.

- [x] Create eligible individual practice through the existing deterministic question-selection service.
- [x] Preserve active unit and question state when switching tutors.
- [x] Offer staged hints only in practice mode and record their use.
- [x] Submit answers through the existing AKURU assessment service.
- [x] Show assessment feedback, marking evidence and improved answers only when the practice workflow permits it.
- [x] Add append-only `tutor_signals` with session, unit, evidence, confidence, prompt and model provenance.
- [x] Display appropriate tutor observations to Students and Parents.
- [x] Prevent tutor signals from automatically changing mastery, next-unit recommendations or study plans.
- [x] Verify tutor and voice endpoints remain unavailable throughout every formal assessment.

**Completed:** A session-bound guided-practice workflow filters the existing deterministic eligible pool to the active covered unit, retains the exact question through tutor switches, blocks unit movement while active, records staged hints, saves answers and submits through the authoritative assessment/marking services. Only published feedback reaches the Tutor. Validated provider observations are copied to an append-only provenance table and displayed to the Student and linked Parent as non-authoritative; mastery, recommendation and planner services remain independent. See [Tutor Step 7 backend](backend/docs/tutor-step-07-guided-practice-signals.md) and [Tutor Step 7 frontend](frontend/docs/tutor-step-07-guided-practice-signals.md).

**Validation:** `npm run verify` passes with 29 frontend and 94 backend tests, migration drift checking, generated OpenAPI, TypeScript, lint and the production build. Integration coverage verifies active-unit eligibility, deterministic practice creation, recorded staged hints, tutor-switch retention, active-practice unit blocking, authoritative submission feedback, append-only bounded signals, Parent scoping, no mastery side effect and text/practice/voice blocking during a live formal assessment.

**Done when:** The tutor supports eligible practice and discusses its authoritative assessment result, while tutor observations remain separate, explainable and non-authoritative.

## Tutor Step 8 — Add per-child AI quotas and Admin controls

**Goal:** Control text and voice cost separately for every child.

- [x] Add `student_ai_quotas` and append-only `student_ai_usage` with configurable accounting periods.
- [x] Define per-child allowances for requests, text tokens and voice minutes.
- [x] Let Admin create, increase, reduce and disable a child's allowance with an audit reason.
- [x] Keep provider account budgets separate from student-facing quota calculations.
- [x] Reserve and settle usage atomically so simultaneous sessions cannot exceed the allowance.
- [x] Handle failed, cancelled and account-failover operations without double charging.
- [x] Expose remaining allowance to the student in understandable units.
- [x] Add Admin per-child quota and usage screens without showing provider secrets or internal UUIDs.
- [x] Add warning, exhausted and renewed-period states with text fallback rules where applicable.
- [x] Test sibling independence, concurrent debits, Admin authorization, adjustments and audit history.

**Done when:** Each child can use tutoring only within their configured allowance, Admin can safely change it, and account switching never duplicates usage charges.

## Tutor Step 9 — Add transcript retention, parent summaries and safety events

**Goal:** Retain useful learning history while giving parents visibility and Admins controlled cleanup.

- [x] Retain text and voice transcripts by default without automatic expiry.
- [x] Generate structured educational summaries containing units covered, activities, demonstrated strengths, difficulties and suggested next steps.
- [x] Make summaries and allowed usage data visible only to the linked parent and authorized Admin.
- [x] Define and implement the detailed full-transcript visibility policy for Students, Parents and Admin support access.
- [x] Add `tutor_safety_events` with severity, source turn, action, notification and review status.
- [x] Notify the linked parent when a safety event occurs without exposing harmful content unnecessarily.
- [x] Add Admin safety-event review and audited support access.
- [x] Build an Admin dry-run preview and explicit purge operation for transcripts older than a selected number of days.
- [x] Preserve required security/audit events and aggregate usage while deleting selected transcript content.
- [x] Integrate transcript data with encrypted backups, child-data deletion and incident procedures.
- [x] Test parent-child isolation, notification idempotency, purge boundaries, backup/restore and audit provenance.

**Done when:** Parents receive useful summaries and safety notifications, transcripts remain until an authorized purge, and deletion cannot cross family or audit boundaries.

## Tutor Step 10 — Add realtime voice and French voice tutoring

**Goal:** Enable natural spoken practice without exposing long-lived credentials or storing raw audio.

- [x] Add an authenticated endpoint that creates short-lived OpenAI Realtime session credentials for an owned Tutor session.
- [x] Select one healthy configured OpenAI account for each realtime connection without exposing its permanent key.
- [x] Build browser WebRTC audio and data-channel integration with live captions.
- [x] Add start, pause, mute, interrupt, repeat, slower, text fallback and end controls.
- [x] Apply the selected voice, speed and bounded persona settings.
- [x] Reconnect through the next healthy account using the saved transcript and server-generated context when a connection fails.
- [x] Rebuild realtime instructions and handover context when a student switches tutors.
- [x] Debit per-child voice minutes accurately across connection, reconnect and cancellation events.
- [x] Store the transcript and provider metadata but no raw audio.
- [x] Provide French voice conversation, vocabulary and pronunciation practice in the initial French voice release.
- [x] Enforce voice only during practice and reject it during every formal assessment from the backend.
- [x] Test captions, interruption, network recovery, account failover, tutor switching, quota exhaustion and formal-assessment denial.

**Done when:** A student can safely converse by voice within their individual allowance, French supports voice, switching tutors preserves context and no raw audio or permanent credential reaches AKURU storage or the browser.

## Tutor Step 11 — Add tutor visuals and accessible learning aids

**Goal:** Let tutors use existing approved visual capabilities when they improve understanding.

- [x] Expose deterministic equations, plots, geometry, circuits and force diagrams through bounded tutor tools.
- [x] Deliver approved source images and reviewed conceptual illustrations through authorized media endpoints.
- [x] Keep official source visuals distinct from explanatory media.
- [x] Preserve source, prompt, generator, review and asset provenance already required by Step 18.
- [x] Add alt text, keyboard operation, zoom and readable equation fallbacks.
- [x] Prevent the tutor from generating or presenting unreviewed assessment-critical diagrams.
- [x] Test subject/unit authorization, asset access, citation linking and accessibility.

**Done when:** Visual explanations are accurate, accessible and authorized, and they never replace or contradict official evidence.

## Tutor Step 12 — Add evaluation and controlled release gates

**Goal:** Prove tutoring quality, personalisation, safety and operational behavior before student release.

- [x] Build Admin-reviewed evaluation cases across all enabled iGCSE subjects and representative mastery levels.
- [x] Measure factual, mathematical and source-grounding accuracy.
- [x] Verify exact textbook edition/page citations and rejection of invented references.
- [x] Verify personalised claims, recurring-error counts, confidence language and next-unit recommendations against database evidence.
- [x] Evaluate every available persona combination for age suitability and academic consistency.
- [x] Test prompt injection, cross-subject retrieval, sibling isolation, unsupported-unit requests and formal-assessment leakage.
- [x] Evaluate tutor switching, handover accuracy and absence of cross-student context.
- [x] Evaluate French voice, captions, interruption, latency, reconnect and quota behavior.
- [x] Review every published avatar and voice preset for child safety and AKURU brand suitability.
- [x] Add separate release gates and kill switches for text, voice and individual tutor tools.
- [x] Run security, privacy, accessibility, cost and retention tests in CI and the production-like staging environment.
- [x] Release first to Admin testing, then a parent-visible pilot, then eligible students.

**Done when:** Every enabled subject and modality meets documented thresholds, any failed gate blocks that feature, and rollback controls have been demonstrated.

Implementation is complete. Tutor capabilities remain disabled for production students until Admin-reviewed subject corpora, passing production-like staging runs and the ordered release stages have been completed with real evaluation evidence.

## Deferred beyond the first Tutor release

- [ ] Raw-audio recording or playback history.
- [ ] Voice cloning or imitation of real people.
- [ ] Text-prompt or free-form generated tutor avatars.
- [ ] Photorealistic tutor avatars.
- [ ] Automatic mastery or study-plan changes based only on tutor conversation.
- [ ] Tutor availability during timed mocks or any other formal assessment.
- [ ] Tutor-initiated contact outside a student-started or scheduled AKURU learning activity.

## Definition of done for every Tutor step

- Code and migrations are committed.
- Relevant authorization, family-isolation and domain tests pass against PostgreSQL.
- Frontend type checking, linting, tests and production build pass when affected.
- FastAPI OpenAPI and the typed frontend contract agree.
- Documentation, environment examples and operational runbooks are updated.
- No secret, raw audio, answer key or unnecessary private student data appears in logs or fixtures.
- AI-derived records include source provenance, model, prompt version, confidence and review state where applicable.
- Personalised claims cite structured learner evidence and never rely on unsupported model memory.
- The step's acceptance criteria have been demonstrated locally before deployment.

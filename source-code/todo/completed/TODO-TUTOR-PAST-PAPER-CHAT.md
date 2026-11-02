# Past-paper questions, approved answers and practice in Tutor chat

Created: 2026-11-02
Started: 2026-11-02
Completed: 2026-11-02
Status: completed — implemented, tested, committed, pushed and verified on production for the authorized one-student practice pilot.
Priority: high — let Students use reviewed iGCSE past papers through the existing chat interface.

## Outcome and scope

After implementation and controlled release, a Student can ask “Can you ask me a question from an iGCSE Chemistry paper?”, receive an eligible actual past-paper question, answer it, request help, and see its approved answer and available examiner guidance. Students can also discuss an identified paper/question/subpart. This is a reusable subject-aware feature, initially validated against approved Chemistry 1C/2C material; it is not restricted in code to Chemistry Topic 1.

Creating this plan does not enable the feature. Full timed mock exams and newly generated exam questions are a later phase, not prerequisites for completing this plan. Existing formal-assessment help restrictions remain in force.

## Existing foundation and current gap

- The text Tutor currently searches textbook evidence and applies a missing-citation gate before providing a response. An exam-practice request can therefore receive a misleading textbook-extraction refusal.
- Guided practice already has start, answer, hint and submit services backed by assessments. Reuse and extend these rather than building a parallel marking engine or separate Student performance store.
- The current production text pilot deliberately disables assessed guided practice. Implementing a chat intent alone cannot bypass this restriction; controlled practice release and eligibility verification are required.
- Admin approval of questions does not prove that an eligible Student-ready assessment bank exists. Inspect question/subpart approval, exact scheme readiness, publication, topic mappings and cumulative coverage before promising availability.

## Step 0 — Audit readiness and agree the initial release boundary

- [x] Trace the existing Tutor, guided-practice, official-paper and assessment paths, including their separate question representations and publication/release gates. Document any bridge required from reviewed official questions to Student practice.
- [x] Read-only audit Chemistry 1C/2C: identify which approved questions/subparts have exact schemes, usable visuals, approved answer assets, curriculum mappings and sufficient published evidence.
- [x] Produce a readiness list with eligible items and explicit blockers. Do not change approval, coverage or manual-marking flags simply to make a question selectable.
- [x] Define the initial permitted Student audience, subjects/topics and paper versions. Confirm that the published topics and cumulative Grade/Term coverage permit at least one genuine end-to-end practice question; otherwise prepare the missing reviewed content through existing Admin workflows.
- [x] Record baseline requests and current failures, including the user's exact request, named question lookup, answer requests and follow-up questions.

## Step 1 — Route chat requests to the correct evidence workflow

- [x] Introduce explicit intents for textbook explanation, past-paper question selection, named paper/question discussion, practice answer, hint, approved-answer reveal, examiner guidance and next question.
- [x] Use bounded same-session context to resolve “that question”, “part b” and “show the answer”. Clarify missing paper/session/component or ambiguous question references rather than guessing.
- [x] Prefer deterministic commands/context for common requests; use a validated structured model decision only where needed. Bound paid routing calls and token usage.
- [x] Route exam requests before the textbook-only missing-evidence gate. A valid exam evidence result must not require an unrelated textbook citation.
- [x] Keep content permissions and assessment state authoritative on the server. Model-provided IDs, requests to ignore coverage and text embedded in documents cannot grant access or reveal answers.
- [x] Return accurate distinctions between no matching paper, no approved question, outside permitted coverage, ambiguous request and feature not released. Do not blame textbook extraction for these cases.

## Step 2 — Add authorized exam lookup and question selection

- [x] Expose bounded Tutor tools/services for listing available papers, resolving a named question/subpart and selecting an eligible practice item. Reuse authenticated assessment/source APIs and exact paper identity checks.
- [x] Enforce Student enrolment, subject ownership, approved published question/scheme versions and cumulative topic coverage. Where all mapped topics must be covered, preserve that rule.
- [x] Permit independently eligible subparts only when approved shared stems, dependencies, visuals and marking rules make them self-contained. Do not extract a subpart that relies on an unavailable preceding answer.
- [x] Return exact reviewed wording, shared stem, labels, choices, marks, tables/equations, accessible question visuals and paper/session/component/question references. Do not let the model rewrite an official question silently.
- [x] Support explicit paper/question filters, and choose another eligible item on “next question” with bounded repeat avoidance. Report exhausted availability honestly.
- [x] Audit and fix any deterministic selection that repeatedly serves the same first question; make selection testable and preserve idempotency on retries.
- [x] Keep unreleased sources and answer-only assets out of pre-answer Student payloads, tool context and private file endpoints.

## Step 3 — Connect the conversation to guided practice and approved answers

- [x] Maintain explicit practice state: question presented, awaiting answer, answer saved, submitted/reviewed, answer revealed, completed or abandoned. Keep a conversational explanation distinct from a scored submission.
- [x] Reuse assessment attempts and immutable source/rubric snapshots. Persist question, Student answer, feedback, help/reveal events and outcomes under the authenticated Student; isolate every Student's history and performance.
- [x] Wait for the Student's response rather than sending the answer with the question. Interpret an answer against the active item; clarify if it is unclear whether the Student is answering or asking a new question.
- [x] Support explicit “show the approved answer” in practice without requiring a fabricated Student response or a marking call. Record revealed/skipped items so they cannot be counted as unaided correct answers or mastery evidence.
- [x] Present the exact approved mark-scheme points, alternatives, group caps and combined-response rules. Where no canonical prose answer exists, label the content “Approved marking guidance”; do not invent an official model answer.
- [x] Show approved marking-scheme diagrams and approved AI-generated worked answers where applicable, retaining the **AI-generated** label. Missing worked answers must not trigger unapproved live generation.
- [x] Explain how an answer could improve using the exact approved scheme; separately label AI explanations and cite actual examiner comments. Missing reports must not prevent otherwise valid practice, and advice must not be invented or borrowed from another paper.
- [x] Reuse drawing/image submission and existing marking limitations. Preserve manual-marking-required outcomes; do not award a reliable automatic score to an unsupported diagram/plot response.
- [x] Keep deterministic constraints authoritative over model marking. Prevent double submission, duplicate marking charges and duplicate performance events on retries.
- [x] Block practice assistance during an active formal assessment using existing server rules, including direct API and alternate-chat attempts.

## Step 4 — Complete the Student chat experience

- [x] Support the feature through ordinary chat text, with optional clear actions: Answer, Hint, Show approved answer, Explain the marking and Next question. Do not require discovering an advanced settings panel.
- [x] Render readable question/subpart cards, marks, equations, choices and appropriately sized diagrams, followed by the Student response and clearly separated approved answer/AI explanation.
- [x] Provide collapsible authorized Paper, Marking scheme and Examiner report evidence with useful source/page labels. Render documents/images rather than opening raw JSON; respect review/source-access rules.
- [x] Keep question selection and named-question discussion within the allowed subject/topic scope. If a requested question is unavailable, explain why and offer an available alternative without exposing draft material.
- [x] Preserve active practice, revealed-answer status and source versions when reopening an authorized conversation. Handle deleted/revoked content safely without rewriting completed historical snapshots.
- [x] Preserve auto-scroll, responsive layout, keyboard/screen-reader support, loading/error states and session-expiry handling. Prevent concurrent sends from corrupting the active question state.

## Step 5 — Contracts, provenance, costs and release controls

- [x] Review existing TutorPractice, assessment, transcript and invocation records first; add only necessary fields/tables with a reviewed migration if required. Update backend/OpenAPI/TypeScript contracts together and retain old transcript compatibility.
- [x] Record intent, selected paper/question/subpart and version, evidence IDs, answer origin, reveal/help state and marking provenance. Record actual model/provider/prompt versions where a model is used; do not infer historical extraction models.
- [x] Reuse OpenAI account priorities, model pinning, usage accounting, applicable per-child limits and existing evaluation controls. Exact question selection and approved-answer retrieval should not require a paid generation call.
- [x] Add independently controllable past-paper-chat release controls. Preserve current text teaching when practice is disabled; update pilot/evaluation evidence explicitly rather than silently broadening the existing text-only pilot.
- [x] Keep authentication, ownership, CSRF, rate limits, private asset access and audit records effective on every new tool/API. No keys or passwords in frontend code, logs or committed fixtures.

## Step 6 — Tests and acceptance evidence

- [x] Add integration tests for intent routing, same-session follow-ups, ambiguous paper references, no eligible bank, named subparts, covered/uncovered topics, missing report and exact component/scheme matching.
- [x] Test shared stems, multiple choice, scientific notation, diagrams, approved answer visuals, grouped scoring and manual marking. Verify no answer or scheme leakage before the permitted reveal/feedback stage.
- [x] Test Student isolation, Parent/Admin permissions, unpublished content, revoked access, prompt injection, formal-exam blocking, pilot restrictions, retries, resumption and answer-reveal effects on performance.
- [x] Test approved-answer reveal without an AI call and without submitting a fake answer. Distinguish approved scheme content from supplementary teaching and AI-generated worked answers in stored records and UI.
- [x] Browser-test the complete normal Student flow on desktop and mobile, including source links, scrolling, a named-question discussion, “next question”, errors and session expiration.
- [x] Run relevant backend/frontend tests, typecheck, lint, contract checks and production build. Use deterministic provider fixtures for routine tests.
- [x] Predeclare a small live evaluation and agree any additional spend ceiling before paid evaluation. Use the Evaluation key and preserve its cumulative ledger; do not assume a fresh budget.
- [x] Compare feedback with the approved scheme and report, record limitations and verify that eligible source selection works against the actual intended production bank.

## Step 7 — Document and release the verified feature

- [x] Update Student/Parent/Admin user docs and developer architecture with commands, readiness requirements, supported question types, answer labels, scoring limitations and troubleshooting.
- [x] Obtain implementation/deployment authorization as applicable, commit/push reviewed changes, back up production and deploy through the normal reviewed release workflow.
- [x] Enable only the agreed pilot audience and eligible content after the practice gates pass. Use normal authorized sign-in for production checks; do not manufacture Student sessions.
- [x] Verify the exact request “Can you ask me a question from igcse chemistry paper?” produces an eligible question, not the textbook-extraction refusal. Complete an answer/help/reveal/next-question cycle and a named-paper question discussion.
- [x] Verify source/asset authorization, health/security acceptance, usage records and Student isolation; retain release evidence and a rollback/disable procedure.
- [x] Mark complete only when the released Student flow works end to end; record remaining content blockers separately.

## Definition of done

A permitted Student can ask about available reviewed iGCSE papers in chat, request an eligible question, respond, obtain appropriate feedback and reveal its approved marking guidance/available approved answer visuals. Follow-ups retain the correct question and sources. Official evidence is never fabricated, unreleased answers never leak, unsupported automatic marking remains blocked, and each Student's results remain private and separate. A whole textbook need not be published: only questions supported by the permitted published topics and required review/release gates are offered.

## Later phase — Curriculum-based mock exams

Create a separate implementation plan after this flow is verified. Reuse the assessment engine to assemble approved questions against a versioned curriculum/specification blueprint, marks, duration, cumulative coverage and topic/difficulty balance. Distinguish practice from timed formal exams, lock assistance and solutions appropriately, snapshot sources and rubrics, and provide post-submission feedback. Newly generated questions require their own quality/review gates and must never be labelled actual Pearson questions.

## Related plans and implementation references

- `../planned/TODO-TUTOR-SUPPLEMENTARY-TEACHING.md` — related-concept explanations; independent of official-question selection and marking authorization.
- `../ongoing/TODO-PEARSON-CHEMISTRY-PAST-PAPERS.md` and `../ongoing/TODO-OFFICIAL-PAPER-REVIEW-WORKSPACE.md` — source intake, approval and paper review.
- `../ongoing/TODO-TUTOR.md` — existing Tutor workflows and release gates.
- `source-code/backend/app/services/tutor_agent.py`, `tutor_practice.py`, `assessment_access.py`, `assessments.py` and assessment marking/review services.
- `source-code/frontend/features/tutor-sessions.tsx`, `answer-visuals.tsx` and `drawing-submissions.tsx`.


## Implementation and local verification — 2026-11-02

- Added migration 0018: immutable, explicitly released approved subparts and durable request-idempotency claims; assessment question sources use an XOR constraint. Clean disposable-database upgrade/downgrade/re-upgrade and Alembic metadata checks passed.
- Reused existing TutorPractice, Assessment, answers, drawing uploads, marking rules, two-pass marking, Student quotas and mastery. Added Admin release/withdraw UI and authenticated APIs, deterministic chat routing and Student exam cards with private source-page images.
- Initial read-only production audit: all 1C questions approved, 2C unreviewed, no published OfficialMaterialVersion bank. Only 1C Q3(a/b/c) currently has confirmed automatic readiness plus supported topic mappings. Q1(a/c) and Q3(d) remain unreleased because readiness is unreviewed; no review/coverage values were changed to expand the bank.
- Release scope: the existing authorized pilot Student only, existing Tutor text pilot audience/expiry retained. Exam items may use covered published topics in the same subject; ordinary textbook teaching remains anchored to the original pilot topic.
- Live evaluation is predeclared as normal-browser selection, hint, reveal, named lookup, next question and saved-answer checks against actual approved evidence, with **zero paid AI calls**. Two-pass marking is tested with deterministic provider fixtures; production automatic scoring remains blocked unless its separate genuine evaluation release passes. No new Evaluation budget is assumed or ledger reset.
- Supplementary free-form concept teaching and full mock exams remain separate plans. The exam discussion path currently serves exact approved guidance/examiner advice and practice actions; it does not generate new official answers.
- Production deployment and acceptance evidence will be recorded below before this plan is closed.

## Production acceptance — 2026-11-02

- Application commits: `17aa996` (feature), `d069750` (exact paper/subpart reference safeguard). Both pushed to GitHub and deployed with the reviewed release script, encrypted backups and migration checks.
- Full final backend suite: **296 passed, 1 existing skip**. Frontend: **115 passed**; typecheck, lint, generated API contract and build passed. Disposable clean migration upgrade/downgrade/re-upgrade and local/production Alembic metadata checks passed.
- Released **June 2025 1C Q3(a), Q3(b), Q3(c)** through the authenticated Admin API. Approvals, textbook content and coverage were not changed. No 2C material was released.
- Activated only the existing pilot Student after verifying VM `vm02-large`, reviewed SHA, protected environment symlink/permissions, eligible source readiness and unchanged remaining runtime settings. A protected environment backup is retained; the original text-pilot expiry and gates remain intact.
- Normal signed-in Student browser checks passed: original request returned Q3(b), diagram loaded, hint worked, exact marking guidance and reviewed examiner advice appeared, and the scheme link opened a real private image rather than JSON. Next selected Q3(c), a labelled deployment-check answer saved without a score, and named lookup selected Q3(a). A new browser page restored the same approved practice state.
- Actual production browser layouts checked at **439px and 1280px**: no horizontal overflow or broken images; question diagram loaded with its start-line/solvent-front labels. An additional synthetic desktop fixture was checked and stopped afterward.
- All four new read/release endpoint probes returned **401 without authentication**. Formal assessment, sibling isolation, CSRF, coverage revocation, source staleness, request replay and two-pass accounting were covered by integration tests.
- **Zero paid provider calls**, **zero assessment scores** and no score-based mastery from verification. Three test practice attempts remain as auditable records; the single test response is explicitly labelled deployment verification, not Student performance. No fake credentials/sessions or passing evaluation records were created.
- Standard production HTTPS, security-header, route/fallback, service/timer and loopback checks passed. Runtime evidence: `/data/akuru/release-evidence/tutor-past-paper-chat-20261102-acceptance.json`; deployment receipts are retained beside it. Screenshots are ignored local artifacts under `tmp`.
- Remaining content/release limitations: Q1(a/c), Q3(d) and 2C still require their genuine readiness/review steps; automatic scoring is independently gated, and full mock exams/supplementary teaching remain outside this completed phase. Existing dependency-audit remediation remains in its separate security plan; no dependencies were changed by this feature.

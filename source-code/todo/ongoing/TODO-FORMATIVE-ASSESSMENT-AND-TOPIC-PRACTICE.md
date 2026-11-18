# Formative AI feedback and topic-based past-paper practice

Created: 2026-11-18
Status: ongoing
Started: 2026-11-18
Implementation requested by the user; production rollout follows tests and targeted acceptance.
Priority: high; complete before resuming analysis of the remaining Biology papers.
Acceptance paper: Biology June 2025 2BR, `eea024fe-978f-4392-b330-c0011201cf63` (six questions, 31 subparts).

## Product decision

AKURU is a learning platform. Students need an **indicative AI score**, explanations of correct points, mistakes and omissions, and a better answer grounded in the approved marking scheme. Feedback must acknowledge uncertainty; perfect marking accuracy and human grading are not prerequisites for practice.

Students must also be able to ask, for example, **“Give me 10 questions from Coordination”** in Biology Tutor chat. Select authorised, approved past-paper content and present questions one at a time. The design is subject-independent; Biology is the acceptance pilot. Students may also explicitly request **new AKURU-generated exam-style questions**, grounded in authorised topic content and the patterns of approved past papers; these remain distinct from original past-paper items.

## Retire requirements, preserve useful capabilities

- Remove “Manual marking required”, deterministic certification and validated automatic-exam readiness as mandatory release gates for formative practice/feedback. Do not simply relabel unvalidated items as certified automatic marking.
- Retire compulsory human grading/referral queues for this workflow. Uncertain feedback should say so and still provide trustworthy marking guidance; a failed model request must not invent a score.
- Keep existing deterministic rules/certificates as optional scoring implementations, including exact numeric/choice support. Preserve their history and tests; no wholesale deletion or forced revalidation.
- Retain approved wording, marking points, caps/alternatives, source adjudications, reviewed visuals, curriculum mapping, provenance, confidence, audit history and per-student access/isolation.
- Keep source conflicts and absent/unreliable evidence as real blockers. The marking scheme governs examiner-report contradictions; unresolved contradictions within an authoritative scheme still need adjudication.
- Future timed mocks may use indicative AI feedback after submission. Do not claim official Pearson grading, certified exam accuracy or automatically publish complete papers as part of this change.

This decision supersedes the mandatory-certification/manual-only release requirements in the [deterministic scoring plan](../ongoing/TODO-DETERMINISTIC-SCORING-AND-READINESS.md), [completed Tutor paper-chat plan](../completed/TODO-TUTOR-PAST-PAPER-CHAT.md) and [completed auto-release plan](../completed/TODO-PAST-PAPER-WORKFLOW-AND-AUTO-TUTOR-RELEASE.md) **for formative learning**. Preserve historical completion records; reconcile outstanding checklists and documentation explicitly during implementation.

## Step 0 — Audit dependencies and freeze acceptance baselines

- [x] Move this plan to ongoing and record its start date when implementation starts.
- [x] Inspect current Tutor selection, assessment dispatch, developer-review APIs, release/readiness services, background jobs, formal assessment publication and frontend gates. Identify every consumer of manual-only/automatic readiness and certificates before changing semantics.
- [x] Export a fresh private source/release baseline for the acceptance paper and inventory all 31 subparts: approval, confidence currency, curriculum, dependencies/visuals, scoring engine and actual Student eligibility.
- [x] Define separate content eligibility, release permission, scoring implementation and feedback outcome contracts. Indicative AI grading must not need a false deterministic certificate or an “all rules checked” assertion.
- [x] Record migrations/backfill requirements after this audit; reuse current schemas where safe. Define rollback without deleting Student history or overwriting human decisions.

## Step 1 — Make formative eligibility independent of scoring certification

- [x] Centralise server-side formative eligibility: approved/current question and scheme evidence, resolved blocking source issues, reviewed required visuals, accepted curriculum and existing release policy.
- [x] Preserve same-subject enrolment, cumulative topic coverage, self-contained subpart/dependency checks and formal-assessment help restrictions.
- [x] Remove manual-only/certificate requirements from formative selection, Tutor release, auto-release jobs and relevant readiness diagnostics. Retain genuinely necessary content gates.
- [x] Preserve human-approved and valid AI-approved states. Do not require the Admin to repeat reviews solely because the scoring policy changed.
- [x] Support an authenticated, previewable/idempotent targeted reconciliation of existing eligible content. Show newly eligible and still blocked parts with reasons before applying; do not bulk release unrelated papers.
- [x] Preserve old scoring fields/certificates for compatibility where necessary; replace misleading active UI wording with “Indicative AI feedback” or the actual scoring implementation. Clearly separate release availability from scoring support.

## Step 2 — Deliver useful source-grounded feedback

- [x] Reuse the existing model router and assessment service; supply the actual question/shared stem, Student response, exact approved scheme, caps/alternatives and relevant examiner guidance. No unrestricted web sources or model-generated official evidence.
- [x] Return structured indicative score/maximum, correct points, mistakes, omissions, improvement advice, improved answer, uncertainty and source references. Validate output and enforce mark caps server-side.
- [x] Label the improved prose answer as AKURU's suggested answer based on the scheme; distinguish exact official marking guidance and approved answer visuals. Do not attribute generated prose to Pearson.
- [x] Use existing deterministic scoring where suitable; ambiguous/unsupported answers may fall through to formative AI feedback instead of a compulsory human queue. Do not silently award zero on parser failure.
- [x] Handle drawings/plots honestly: use existing supported submissions and approved answer visuals; if response interpretation is unavailable, explain the limitation and offer guidance without pretending to have evaluated an unseen drawing.
- [x] Keep answers and answer-only images hidden until submission or explicit practice reveal. Revealed/skipped/assisted answers must not count as unaided mastery evidence.
- [x] Reuse authenticated per-child attempts, frozen source/rubric versions, idempotency, model/usage auditing and existing budget controls. Never mix Student results or treat indicative scores as validated exam results.
- [x] On timeout/provider failure, retain the response and allow safe retry without duplicate attempts/charges. Distinguish “feedback unavailable” from zero marks; handle malicious instructions inside Student answers as untrusted data.

## Step 3 — Add requested-count topic practice in Tutor chat

- [x] Parse bounded count and topic requests, including topic codes/names, unit requests, aliases and same-session follow-ups. Resolve ambiguity explicitly; allow subject chat to select topics without confusing its scope with the practice focus.
- [x] Define count limits, omission defaults and the counting unit. Prefer one independently answerable subpart per practice item; display shared stems, dependencies and marks. Never count one multipart question inconsistently.
- [x] Select only eligible released items from the requested authorised scope, with randomised order and repeat avoidance. Tell the Student when fewer suitable items exist; offer that smaller set, never silently broaden topics or invent past-paper items.
- [x] Persist a student/session-owned practice set with selected item IDs and frozen versions, requested/available counts, position, answers, feedback and completed/skipped/abandoned state. Retries or reloads must not regenerate a different set.
- [x] Present one question at a time, wait for the response, give feedback, then offer the next question. Support hints, explicit answer reveal, skip, resume and exit with clear state transitions.
- [x] Keep chat context tied to the active question for “why?”, “that answer” and “next”; distinguish answering from asking a teaching question. Do not advance twice on repeated sends.
- [x] Provide progress and an end-of-set summary with strengths and suggested topic revision. Keep any existing mastery updates student-specific and distinguish assisted/indicative evidence.

## Step 3A — Generate new exam-style topic questions in Subject chat

- [x] Support requests such as “Can you generate new questions from Topic XX?”, “Generate five Coordination questions” and count/difficulty follow-ups within Subject chat. Distinguish generation intent from selecting original past-paper questions; clarify ambiguous topic/count requests using the same bounded defaults and limits.
- [x] Ground generation in the authorised published topic content and relevant specification where available, plus approved same-subject past-paper examples and their marking schemes. Use examples to infer command words, structure, demand, mark allocation and expected answer depth; do not reuse another subject's questions or exceed the Student's cumulative coverage.
- [x] Retrieve a small, relevant set of examples rather than sending whole textbooks/papers to the model. Record source versions, model provenance and usage; reuse the existing account router and budget controls. If suitable approved examples are unavailable, explain that limitation rather than claiming a verified Pearson-style match.
- [x] Create original questions with fresh contexts/data, not copied or lightly paraphrased papers. Clearly label every item **“AKURU-generated exam-style question”**, never an official Pearson question or prediction. Keep the selected topic and requested difficulty explicit; do not imply measured exam equivalence.
- [x] Produce a structured question, command word, maximum marks, necessary data and a hidden suggested answer/marking rubric together. Check topic grounding, scientific correctness, solvability, consistent numerical values/units, mark totals and answer/rubric agreement before serving it. Reject/retry boundedly on failed checks; never silently substitute an unverified item.
- [x] Initially support text, calculations and accessible text/structured tables that the existing interface can render reliably. Reuse only relevant authorised approved visuals with accurate associations; do not generate images or describe a missing diagram as visible. Decline or offer a text-compatible alternative when a new diagram/graph is essential and unsupported.
- [x] Reuse the same Student-owned counted practice-set lifecycle, one-at-a-time presentation, answer hiding, hints/reveal, resume, progress and formative feedback. Freeze each generated item and rubric so retries or model changes cannot alter the question after the Student answers.
- [x] Distinguish generated-item provenance and model-generated suggested marking guidance from official scheme evidence in payloads, citations, UI and history. Use the frozen generated rubric plus approved underlying topic evidence for indicative feedback; acknowledge uncertainty without inventing official marking points.
- [x] Keep generated questions private to their Student/session by default. No automatic insertion into the approved shared question bank, source-confidence records, official-paper inventory or Admin approvals. Any later shared-bank publication is separate work.
- [x] Test explicit generation versus original-paper selection, topic ambiguity, unavailable examples, counts, coverage isolation, alternative responses, numerical/rubric consistency, missing visuals, duplicate retries and failure recovery. Include representative recall, explanation/application and calculation cases where the chosen topic supports them.
- [x] Add production acceptance: in Biology Subject chat request newly generated questions from an eligible topic, verify labelling/grounding and hidden answers, submit a response and inspect indicative feedback. Live generation/evaluation uses paid inference; obtain an explicit test budget before making these calls.

## Step 4 — Simplify Admin and Student presentation

- [x] Update contracts/query caches, Tutor controls, paper status labels and release diagnostics to show content approval, Student availability and remaining source/access blockers without implying a human marker is required.
- [x] Keep the established four-stage paper workflow coherent: final assessment/current content approval leads to guarded formative Tutor release, subject to content and access gates rather than deterministic certificates.
- [x] In Student chat, show question X of Y, original paper/subpart reference, marks, approved visuals, response controls and readable feedback. Make the indicative nature of scoring clear without repetitive warnings.
- [x] Distinguish the Student's response, scheme-grounded improved answer and examiner advice; retain collapsible references, accessibility, mobile layout and reliable scroll/loading/error behaviour.
- [x] Update user-docs, developer-docs, backend/frontend architecture as relevant and past-paper extraction/release guidelines. Reconcile superseded active roadmap requirements; do not erase historical records or mark unrelated work complete.

## Step 5 — Verify the shared implementation

- [x] Test all 31 pilot subparts: 17 former manual-only cases can receive formative feedback when otherwise eligible, and existing 14 automatic cases/certificates still work. Source approval and content confidence remain unchanged unless an actual source correction occurs.
- [x] Test current human/AI approval, missing evidence, stale source changes, source conflicts, unreviewed visuals, incomplete dependencies and coverage restrictions. Unauthorised items remain inaccessible via selection, IDs, files and answer endpoints.
- [x] Test topic/count selection, insufficient inventory, repeat avoidance, resume/reload, next/skip/reveal, duplicate submissions, concurrent requests, user/session switching and cross-student access.
- [x] Evaluate feedback on fully correct, partially correct, wrong, alternative/contradictory and blank answers; verify caps, any-N rules, combined responses and source precedence. A fixture test proves contract/logic, not live-model quality.
- [x] Test malformed model outputs, prompt injection, timeout/retry, provider unavailability, missing configuration and usage accounting. No fabricated score or claim of reliable drawing interpretation.
- [x] Run relevant backend/frontend/security/contract checks and browser acceptance. Use fixtures for routine tests; obtain explicit budget approval before any paid live evaluation. Prior task budgets are not automatically available.

## Step 6 — Deploy and accept Biology June 2025 2BR

- [ ] Commit/push and deploy only after implementation is requested and checks pass, using the normal reviewed backup/deployment/rollback workflow.
- [ ] Use authenticated Admin APIs to preview and apply the pilot eligibility/release reconciliation. No direct production SQL bypass, source approval fabrication or blanket release of other papers.
- [ ] Confirm former manual-only cases are selectable only where all retained content/access gates pass; report any genuine remaining source/dependency blockers individually.
- [ ] With an authorised Student session, test “Give me 5 questions from Coordination”, answer a question, inspect indicative feedback/improved answer and complete/resume the set. Verify another topic and insufficient-availability request.
- [ ] Record deployed revision, test evidence, Student-visible behaviour, remaining limitations and rollback instructions. Preserve existing attempts, source history and per-child performance.

## Step 7 — Resume the remaining Biology papers

- [ ] Only after pilot acceptance, refresh the live inventory against local supplied papers and the [Biology intake roadmap](../ongoing/TODO-PEARSON-BIOLOGY-PAST-PAPERS.md). Distinguish already imported, source-reviewed, curriculum-mapped and Tutor-released papers; do not assume any particular batch is still missing.
- [ ] Agree the next latest incomplete batch from that inventory and continue one paper at a time using the updated extraction guidelines and authenticated developer-review APIs.
- [ ] For each batch, validate exact question/scheme/report links, crops/labels, marking instructions, source conflicts, confidence/provenance and curriculum; apply the established above-75% AI-approval policy with its retained content gates.
- [ ] Release eligible content for formative practice without repeating source reviews or generating scoring certificates solely to unlock it. Record source exceptions that genuinely require human input.
- [ ] No paid model calls are implied by source preparation in this development chat; paid backend evaluations need a separately agreed budget. No Chemistry edits or formal-exam publication are included.

## Completion criteria

A Student can request either original approved past-paper questions or explicitly labelled newly generated exam-style questions from a topic, work through a counted set, answer approved questions (including formerly manual-only written questions), receive source-grounded indicative feedback and a better answer, and resume/complete the set. No human grading or deterministic certificate is required to unlock this learning flow. Source quality, authorised coverage, answer protection and Student isolation remain enforced. The Biology 2BR pilot is verified on production before further paper analysis resumes.


## Implementation evidence (in progress)

Shared formative eligibility and private counted sets are implemented; generated questions use a hidden structured rubric and a separate content check. Existing single-item cards retain compatibility, including optional certified recognition without model calls; unsupported prose can receive formative feedback. The deterministic engine hash files remain unchanged. One additive migration, no status/Student-results rewrite.

Live AKURU-Evaluation checks used the explicitly approved US$1 ceiling and private persistent ledger. A generated Coordination question passed its content check; full/partial/wrong responses received 5/5, 1/5 and 0/5. An original Biology Q1(d) any-two case was capped at 2/2. This is a small behaviour sample, not a general accuracy guarantee. Private evidence: `tmp/formative-practice-evaluation/` (never committed). Production Student browser acceptance and targeted release reconciliation remain to be recorded below.

Step 7 is the follow-on Biology intake handoff: inventory and recommend the next batch after this feature's acceptance. Actual further-paper analysis belongs to the existing Biology intake roadmap and does not authorise blanket releases or unrelated paper edits.

Pre-deployment validation: 631 backend tests passed, 1 skipped; final focused regression 53 passed. All 123 frontend tests, typecheck, lint, build and contract check passed. Existing engine hash files are unchanged. Live evaluation conservative charged bound US$0.047367; actual estimate recorded in the private ledger.
